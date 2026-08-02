"""
Async Postgres client (asyncpg pool). Kept intentionally lightweight —
this is the interim home for the 'PostgreSQL (Raw Immutable Events)' box
until a standalone event-store service exists.
"""
import asyncpg

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PostgresClient:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or settings.postgres_dsn
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        logger.info("Connecting to Postgres...")
        self.pool = await asyncpg.create_pool(
            dsn=self.dsn,
            min_size=settings.postgres_pool_min_size,
            max_size=settings.postgres_pool_max_size,
        )
        await self._ensure_event_schema()
        await self._ensure_account_schema()

    async def _ensure_event_schema(self) -> None:
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS raw_events (
                    id BIGSERIAL PRIMARY KEY,
                    event_id UUID NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    category TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    occurred_at TIMESTAMPTZ NOT NULL,
                    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    payload JSONB NOT NULL,
                    client_metadata JSONB NOT NULL DEFAULT '{}',
                    is_important BOOLEAN,
                    importance_score DOUBLE PRECISION,
                    processed_at TIMESTAMPTZ
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_events_user_id ON raw_events (user_id)")

    async def _ensure_account_schema(self) -> None:
        """Create the small account store used by the authentication API.

        Keeping this migration idempotent makes a fresh local Postgres setup
        usable without a separate migration runner.
        """
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY,
                    login TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    last_login_at TIMESTAMPTZ
                )
            """)

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()

    async def ping(self) -> bool:
        if not self.pool:
            return False
        async with self.pool.acquire() as conn:
            return (await conn.fetchval("SELECT 1")) == 1


postgres_client = PostgresClient()
