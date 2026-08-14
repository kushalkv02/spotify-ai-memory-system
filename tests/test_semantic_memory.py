"""Unit tests for the Chroma semantic-memory boundary (no Chroma server needed)."""
from __future__ import annotations

from unittest.mock import MagicMock

from graph.repositories.chroma_memory_repository import ChromaMemoryRepository
from graph.services.memory_service import MemoryService
from graph.services.semantic_memory_service import SemanticMemoryService
from interaction_api.integrations.graph_client import GraphClient


def test_chroma_query_is_user_scoped_and_returns_similarity() -> None:
    collection = MagicMock()
    collection.query.return_value = {
        "documents": [["The listener enjoys relaxed electronic music"]],
        "metadatas": [[{"version_id": "v1", "user_id": "listener", "importance": 0.8}]],
        "distances": [[0.2]],
    }
    repository = ChromaMemoryRepository()
    repository._get_collection = MagicMock(return_value=collection)  # type: ignore[method-assign]

    result = repository.query("listener", "calm synth music", limit=3)

    assert result == [{
        "version_id": "v1", "user_id": "listener", "importance": 0.8,
        "summary": "The listener enjoys relaxed electronic music",
        "semantic_score": 0.9, "memory_class": "semantic",
    }]
    assert collection.query.call_args.kwargs["where"] == {"$and": [
        {"user_id": "listener"}, {"subject_scope": "user"},
        {"$or": [{"status": "active"}, {"status": "corrected"}]},
    ]}


def test_memory_store_projects_the_durable_memory_to_semantic_index() -> None:
    semantic = MagicMock(spec=SemanticMemoryService)
    service = MemoryService(semantic_memory_service=semantic)
    service.repo = MagicMock()
    service.repo.create_memory.return_value = {
        "memory_id": "m1", "version_id": "v1", "user_id": "listener",
        "summary": "Likes ambient electronic music", "status": "active",
    }

    service.store_memory("listener", "Likes ambient electronic music")

    semantic.try_index.assert_called_once_with(service.repo.create_memory.return_value)


def test_recommendation_memory_context_combines_semantic_and_recent_graph_facts() -> None:
    combined = GraphClient._combine_memory_sources(
        [{"version_id": "semantic", "summary": "Matches the current mood"}],
        [
            {"version_id": "semantic", "summary": "Duplicate structured record"},
            {"version_id": "recent", "summary": "Latest structured preference"},
        ],
        limit=2,
    )

    assert [item["version_id"] for item in combined] == ["semantic", "recent"]


def test_semantic_retrieval_failure_falls_back_to_structured_memories() -> None:
    repository = MagicMock()
    repository.query.side_effect = RuntimeError("Chroma temporarily unavailable")
    service = SemanticMemoryService(repository=repository)

    assert service.try_retrieve("listener", "something calm") == []
