"""
Creates Memory nodes in the graph. The actual "is this important?" /
LLM-summarization logic (the Memory Decision Engine + Memory Generator
in your architecture diagram) lives upstream of this — by the time
something reaches `store_memory`, it has already been judged important
and summarized. This service just persists it and links it to the
user/tracks it's about.
"""
from __future__ import annotations

import uuid
from typing import Any

from ..models.memory import Memory
from ..repositories.memory_repository import MemoryRepository


class MemoryService:
    def __init__(self) -> None:
        self.repo = MemoryRepository()

    def store_memory(
        self,
        user_id: str,
        summary: str,
        importance: float = 0.5,
        track_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        memory = Memory(
            memory_id=f"memory_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            summary=summary,
            importance=importance,
            track_ids=track_ids or [],
        )
        return self.repo.create_memory(memory)

    def recent_memories(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.repo.get_recent_for_user(user_id, limit=limit)

    def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        return self.repo.get_memory(memory_id)

    def memories_referencing_track(
        self, track_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        return self.repo.get_referencing_track(track_id, limit=limit)

    def delete_memory(self, memory_id: str) -> None:
        self.repo.delete_memory(memory_id)
