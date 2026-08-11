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
                    subject_scope TEXT NOT NULL DEFAULT 'user',
                    surface TEXT NOT NULL DEFAULT 'unknown',
                    locale TEXT NOT NULL DEFAULT 'und',
                    occurred_at TIMESTAMPTZ NOT NULL,
                    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    consent_state TEXT NOT NULL DEFAULT 'pending',
                    source_event_id TEXT,
                    idempotency_key TEXT,
                    payload JSONB NOT NULL,
                    client_metadata JSONB NOT NULL DEFAULT '{}',
                    is_important BOOLEAN,
                    importance_score DOUBLE PRECISION,
                    processed_at TIMESTAMPTZ
                )
            """)
            # `CREATE TABLE IF NOT EXISTS` does not upgrade a running dev DB.
            for statement in (
                "ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS subject_scope TEXT NOT NULL DEFAULT 'user'",
                "ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS surface TEXT NOT NULL DEFAULT 'unknown'",
                "ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS locale TEXT NOT NULL DEFAULT 'und'",
                "ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS consent_state TEXT NOT NULL DEFAULT 'pending'",
                "ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS source_event_id TEXT",
                "ALTER TABLE raw_events ADD COLUMN IF NOT EXISTS idempotency_key TEXT",
            ):
                await conn.execute(statement)
            await conn.execute("UPDATE raw_events SET idempotency_key = event_id::text WHERE idempotency_key IS NULL")
            await conn.execute("ALTER TABLE raw_events ALTER COLUMN idempotency_key SET NOT NULL")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_events_user_id ON raw_events (user_id)")
            await conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS raw_events_user_idempotency_key "
                "ON raw_events (user_id, idempotency_key)"
            )
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_decisions (
                    id BIGSERIAL PRIMARY KEY,
                    event_id UUID NOT NULL REFERENCES raw_events(event_id),
                    memory_class TEXT NOT NULL,
                    retain_as_memory BOOLEAN NOT NULL,
                    confidence DOUBLE PRECISION NOT NULL,
                    policy_class TEXT NOT NULL,
                    summary TEXT,
                    entities JSONB NOT NULL DEFAULT '{}',
                    semantic_key TEXT,
                    source_event_ids UUID[] NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """)
            await conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS memory_decisions_event_id_idx "
                "ON memory_decisions(event_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS retained_memory_semantic_key_idx "
                "ON memory_decisions(semantic_key) WHERE retain_as_memory"
            )

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
