from __future__ import annotations

from typing import Any

from ..models.memory import Memory
from ..queries.memory_queries import MEMORIES_REFERENCING_TRACK
from .base_repository import BaseRepository


class MemoryRepository(BaseRepository):
    label = "Memory"
    id_field = "memory_id"

    def create_memory(self, memory: Memory) -> dict[str, Any]:
        node = self.merge(memory.to_dict())

        query = """
        MATCH (m:Memory {memory_id: $memory_id})
        MATCH (u:User {user_id: $user_id})
        MERGE (m)-[:ABOUT]->(u)
        MERGE (u)-[:HAS_MEMORY]->(m)
        """
        self.client.execute_write(query, {"memory_id": memory.memory_id, "user_id": memory.user_id})

        for track_id in memory.track_ids:
            self.client.execute_write(
                """
                MATCH (m:Memory {memory_id: $memory_id})
                MATCH (t:Track {track_id: $track_id})
                MERGE (m)-[:REFERENCES]->(t)
                """,
                {"memory_id": memory.memory_id, "track_id": track_id},
            )
        return node

    def get_recent_for_user(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        query = """
        MATCH (m:Memory)-[:ABOUT]->(u:User {user_id: $user_id})
        RETURN m
        ORDER BY m.created_at DESC
        LIMIT $limit
        """
        result = self.client.execute_read(query, {"user_id": user_id, "limit": limit})
        return [r["m"] for r in result]

    def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        """Return one memory node, or ``None`` when it does not exist."""
        return self.get_by_id(memory_id)

    def get_referencing_track(self, track_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Return memories linked to ``track_id``, newest first."""
        query = f"{MEMORIES_REFERENCING_TRACK}\nLIMIT $limit"
        return self.client.execute_read(query, {"track_id": track_id, "limit": limit})

    def delete_memory(self, memory_id: str) -> None:
        """Delete a memory and all of its graph relationships."""
        self.delete(memory_id)

    
