"""Persistence for derived decisions, intentionally separate from raw input."""
import json

from ..models.event import ExtractedMemory
from .postgres_client import PostgresClient


class MemoryDecisionRepository:
    def __init__(self, pg_client: PostgresClient):
        self.pg_client = pg_client

    async def record(self, decision: ExtractedMemory) -> bool:
        """Persist a decision and return whether it is a new semantic memory."""
        async with self.pg_client.pool.acquire() as conn:
            async with conn.transaction():
                duplicate = None
                if decision.retain_as_memory and decision.semantic_key:
                    duplicate = await conn.fetchrow(
                        "SELECT id FROM memory_decisions WHERE retain_as_memory AND semantic_key = $1 LIMIT 1",
                        decision.semantic_key,
                    )
                await conn.execute(
                    """INSERT INTO memory_decisions
                    (event_id, memory_class, retain_as_memory, confidence, policy_class,
                     summary, entities, semantic_key, source_event_ids)
                    VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8,$9::uuid[])""",
                    decision.event_id, decision.memory_class.value, decision.retain_as_memory,
                    decision.confidence, decision.policy_class, decision.summary,
                    json.dumps(decision.entities), decision.semantic_key, decision.source_event_ids,
                )
                # Lineage includes every equivalent event, while graph memory
                # is created only for the first semantic statement.
                if duplicate:
                    await conn.execute(
                        "UPDATE memory_decisions SET source_event_ids = array_append(source_event_ids, $1) WHERE id = $2",
                        decision.event_id, duplicate["id"],
                    )
                return not bool(duplicate)
