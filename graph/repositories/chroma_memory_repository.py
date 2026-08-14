"""ChromaDB persistence for semantically retrievable memory summaries.

Neo4j remains the authoritative temporal record.  This repository holds only
the approved summary text plus enough metadata to enforce the same user and
subject-scope boundary during vector retrieval.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class ChromaMemoryRepository:
    """Small, lazy ChromaDB adapter used by the memory services.

    The lazy import means the graph package can still be used for structured
    Neo4j-only workflows when the optional vector dependency is not installed.
    """

    _COLLECTION = "memory_summaries"

    def __init__(self, persist_directory: str | None = None) -> None:
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIRECTORY", ".chroma"
        )
        self._collection: Any | None = None

    def _get_collection(self) -> Any:
        if self._collection is not None:
            return self._collection
        try:
            import chromadb
        except ImportError as exc:  # pragma: no cover - depends on deployment extras
            raise RuntimeError("ChromaDB is not installed; install the chromadb dependency") from exc

        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=self.persist_directory)
        # Cosine distance makes the returned distance directly useful as a
        # semantic-similarity signal irrespective of embedding magnitude.
        self._collection = client.get_or_create_collection(
            name=self._COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        return self._collection

    @staticmethod
    def _metadata(memory: dict[str, Any]) -> dict[str, str | float | int | bool]:
        """Chroma metadata supports scalar values only."""
        values: dict[str, str | float | int | bool] = {
            "memory_id": str(memory["memory_id"]),
            "version_id": str(memory["version_id"]),
            "user_id": str(memory["user_id"]),
            "subject_scope": str(memory.get("subject_scope", "user")),
            "status": str(memory.get("status", "active")),
            "source": str(memory.get("source", "memory")),
            "surface_policy": str(memory.get("surface_policy", "default")),
            "recorded_at": str(memory.get("recorded_at", "")),
        }
        for field, default in (("importance", 0.5), ("confidence", 1.0), ("explicitness", 0.0)):
            try:
                values[field] = float(memory.get(field, default))
            except (TypeError, ValueError):
                values[field] = default
        return values

    def upsert(self, memory: dict[str, Any]) -> None:
        if not memory.get("summary"):
            return
        self._get_collection().upsert(
            ids=[str(memory["version_id"])],
            documents=[str(memory["summary"])],
            metadatas=[self._metadata(memory)],
        )

    def delete(self, version_id: str) -> None:
        self._get_collection().delete(ids=[version_id])

    def query(self, user_id: str, intent: str, limit: int, subject_scope: str = "user") -> list[dict[str, Any]]:
        if not intent.strip() or limit < 1:
            return []
        result = self._get_collection().query(
            query_texts=[intent],
            n_results=limit,
            where={"$and": [
                {"user_id": user_id},
                {"subject_scope": subject_scope},
                {"$or": [{"status": "active"}, {"status": "corrected"}]},
            ]},
            include=["documents", "metadatas", "distances"],
        )
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        memories: list[dict[str, Any]] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            # Cosine distance is in [0, 2]; normalize it to a bounded score.
            similarity = max(0.0, min(1.0, 1.0 - float(distance) / 2.0))
            memories.append({
                **(metadata or {}), "summary": document or "",
                "semantic_score": round(similarity, 6), "memory_class": "semantic",
            })
        return memories
