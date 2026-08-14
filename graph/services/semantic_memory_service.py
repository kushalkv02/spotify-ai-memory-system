"""Semantic-memory index service backed by ChromaDB."""
from __future__ import annotations

import logging
from typing import Any

from ..repositories.chroma_memory_repository import ChromaMemoryRepository

logger = logging.getLogger(__name__)


class SemanticMemoryService:
    """Best-effort vector projection of the durable Neo4j memory record."""

    def __init__(self, repository: ChromaMemoryRepository | None = None) -> None:
        self.repository = repository or ChromaMemoryRepository()

    def index(self, memory: dict[str, Any]) -> None:
        self.repository.upsert(memory)

    def remove(self, version_id: str) -> None:
        self.repository.delete(version_id)

    def retrieve(self, user_id: str, intent: str, limit: int = 6, subject_scope: str = "user") -> list[dict[str, Any]]:
        return self.repository.query(user_id, intent, limit, subject_scope)

    def try_retrieve(
        self, user_id: str, intent: str, limit: int = 6, subject_scope: str = "user",
    ) -> list[dict[str, Any]]:
        """Return no semantic matches when Chroma is temporarily unavailable.

        Semantic search enriches recommendations but Neo4j remains the durable
        store, so a vector-index outage must not make an already-stored chat
        turn or its structured recommendation evidence unavailable.
        """
        try:
            return self.retrieve(user_id, intent, limit, subject_scope)
        except Exception as exc:
            logger.warning("Semantic memory retrieval unavailable: %s", exc)
            return []

    def try_index(self, memory: dict[str, Any]) -> None:
        try:
            self.index(memory)
        except Exception as exc:  # Neo4j write is durable even if the index is briefly unavailable.
            logger.warning("Semantic memory indexing unavailable: %s", exc)

    def try_remove(self, version_id: str) -> None:
        try:
            self.remove(version_id)
        except Exception as exc:  # pragma: no cover - defensive operational path
            logger.warning("Semantic memory removal unavailable: %s", exc)
