"""Append-only repository for the raw_events table."""
import json

from ..models.event import RawEventRecord, ValidatedEvent
from ..utils.exceptions import DuplicateEventError, PersistenceError
from .postgres_client import PostgresClient


class EventRepository:
    def __init__(self, pg_client: PostgresClient):
        self.pg_client = pg_client

    async def insert(self, event: ValidatedEvent) -> RawEventRecord:
        query = """
            INSERT INTO raw_events
                (event_id, user_id, session_id, category, schema_version,
                 occurred_at, received_at, payload, client_metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb)
            RETURNING id, event_id, user_id, session_id, category, schema_version,
                      occurred_at, received_at, payload, client_metadata,
                      is_important, importance_score, processed_at
        """
        try:
            async with self.pg_client.pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    event.event_id,
                    event.user_id,
                    event.session_id,
                    event.category.value,
                    event.schema_version,
                    event.occurred_at,
                    event.received_at,
                    json.dumps(event.payload),
                    json.dumps(event.client_metadata),
                )
        except Exception as exc:  # asyncpg.UniqueViolationError for dup event_id
            if "unique" in str(exc).lower():
                raise DuplicateEventError(f"event_id already ingested: {event.event_id}") from exc
            raise PersistenceError(str(exc)) from exc

        return self._row_to_record(row)

    async def get_by_event_id(self, event_id: str) -> RawEventRecord | None:
        query = "SELECT * FROM raw_events WHERE event_id = $1"
        async with self.pg_client.pool.acquire() as conn:
            row = await conn.fetchrow(query, event_id)
        return self._row_to_record(row) if row else None

    async def mark_processed(self, event_id: str, is_important: bool, importance_score: float) -> None:
        query = """
            UPDATE raw_events
            SET is_important = $2, importance_score = $3, processed_at = now()
            WHERE event_id = $1
        """
        async with self.pg_client.pool.acquire() as conn:
            await conn.execute(query, event_id, is_important, importance_score)

    @staticmethod
    def _row_to_record(row) -> RawEventRecord:
        data = dict(row)
        data["payload"] = json.loads(data["payload"]) if isinstance(data["payload"], str) else data["payload"]
        data["client_metadata"] = (
            json.loads(data["client_metadata"]) if isinstance(data["client_metadata"], str) else data["client_metadata"]
        )
        return RawEventRecord(**data)
