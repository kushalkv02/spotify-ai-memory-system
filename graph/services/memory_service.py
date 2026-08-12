"""Temporal memory orchestration and policy-aware hybrid retrieval."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import math
import uuid
from collections import defaultdict
from typing import Any, Iterable, Protocol

from ..models.memory import Memory
from ..repositories.memory_repository import MemoryRepository


class EmbeddingProvider(Protocol):
    """The caller supplies an approved embedding provider; this layer never embeds raw event payloads."""

    def embed(self, text: str) -> list[float]: ...


class MemoryService:
    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self.repo = MemoryRepository()
        self.embedding_provider = embedding_provider

    @staticmethod
    def _stable_version_id(memory_id: str, source_event_id: str | None) -> str:
        # Event retries produce the same node, while an ordinary call gets a
        # distinct assertion version under its stable memory fact id.
        material = source_event_id or uuid.uuid4().hex
        digest = hashlib.sha256(f"{memory_id}:{material}".encode()).hexdigest()[:16]
        return f"{memory_id}:v:{digest}"

    def store_memory(
        self, user_id: str, summary: str, importance: float = 0.5,
        track_ids: list[str] | None = None, *, memory_id: str | None = None,
        source_event_id: str | None = None, source: str = "user", confidence: float = 1.0,
        subject_scope: str = "user", explicitness: float = 0.0,
        surface_policy: str = "default", valid_from: datetime | None = None,
        source_action: str | None = None, entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> dict[str, Any]:
        if not 0 <= confidence <= 1 or not 0 <= explicitness <= 1:
            raise ValueError("confidence and explicitness must be between 0 and 1")
        # Source events are the idempotency boundary for automated writes.
        # Interactive writes without a source event deliberately create a new
        # assertion unless the caller supplies a stable memory id.
        if memory_id is None and source_event_id:
            memory_id = f"memory_{hashlib.sha256(source_event_id.encode()).hexdigest()[:16]}"
        memory_id = memory_id or f"memory_{uuid.uuid4().hex[:12]}"
        when = valid_from or datetime.now(timezone.utc)
        memory = Memory(
            memory_id=memory_id, version_id=self._stable_version_id(memory_id, source_event_id),
            user_id=user_id, summary=summary, importance=importance, track_ids=track_ids or [],
            valid_from=when, recorded_at=datetime.now(timezone.utc), source=source,
            confidence=confidence, subject_scope=subject_scope, explicitness=explicitness,
            surface_policy=surface_policy, source_event_id=source_event_id,
            source_action=source_action, entity_type=entity_type, entity_id=entity_id,
        )
        return self.repo.create_memory(memory)

    def correct_memory(
        self, user_id: str, previous_version_id: str, summary: str, *,
        contradiction: bool = False, track_ids: list[str] | None = None,
        source_event_id: str | None = None, subject_scope: str = "user",
        confidence: float = 1.0, source: str = "user_correction",
    ) -> dict[str, Any]:
        old = self.repo.get_memory(previous_version_id, user_id, subject_scope, include_history=True)
        if not old:
            raise ValueError("memory does not exist in the authorized subject scope")
        memory_id = old["memory_id"]
        memory = Memory(
            memory_id=memory_id, version_id=self._stable_version_id(memory_id, source_event_id),
            user_id=user_id, summary=summary, importance=old.get("importance", .5),
            track_ids=track_ids or [], valid_from=datetime.now(timezone.utc),
            recorded_at=datetime.now(timezone.utc), source=source, confidence=confidence,
            status="corrected", subject_scope=subject_scope, explicitness=1.0,
            surface_policy=old.get("surface_policy", "default"), source_event_id=source_event_id,
        )
        return self.repo.revise_memory(previous_version_id, memory, disposition="contradicted" if contradiction else "superseded")

    def expire_memory(self, user_id: str, version_id: str, subject_scope: str = "user") -> bool:
        return self.repo.expire_memory(version_id, user_id, subject_scope)

    def expire_state_memories(self, user_id: str, *, entity_type: str, entity_id: str) -> int:
        return self.repo.expire_state_memories(user_id, entity_type, entity_id)

    def store_embedding(self, user_id: str, version_id: str, embedding: Iterable[float], *, field: str = "summary", subject_scope: str = "user") -> None:
        self.repo.store_embedding(version_id, user_id, embedding, field, subject_scope)

    def index_memory_summary(self, user_id: str, version_id: str, *, subject_scope: str = "user") -> None:
        """Embed only the approved ``summary`` field and retain its stable version id."""
        if not self.embedding_provider:
            raise RuntimeError("no approved embedding provider is configured")
        memory = self.repo.get_memory(version_id, user_id, subject_scope)
        if not memory:
            raise ValueError("memory does not exist in the authorized subject scope")
        self.store_embedding(user_id, version_id, self.embedding_provider.embed(memory["summary"]), subject_scope=subject_scope)

    def retrieve(
        self, user_id: str, *, intent: str = "", related_track_ids: list[str] | None = None,
        surface: str = "default", query_embedding: list[float] | None = None,
        limit: int = 8, context_budget: int = 1800, subject_scope: str = "user",
    ) -> list[dict[str, Any]]:
        """Retrieve a diverse, bounded context pack from scoped hybrid candidates."""
        if limit < 1 or context_budget < 1:
            return []
        if query_embedding is None and intent and self.embedding_provider:
            query_embedding = self.embedding_provider.embed(intent)
        candidates = self.repo.hybrid_candidates(user_id, query_embedding, related_track_ids or [], max(limit * 4, 20), subject_scope)
        ranked = sorted(candidates, key=lambda item: self._score(item, intent, surface), reverse=True)
        selected: list[dict[str, Any]] = []
        used_chars = 0
        cluster_count: defaultdict[str, int] = defaultdict(int)
        for item in ranked:
            memory = item["memory"]
            # Track references act as a cluster key; fall back to the stable
            # fact id.  Cap cluster repetition before the context is built.
            cluster = self._cluster(memory)
            if cluster_count[cluster] >= 2:
                continue
            cost = len(memory.get("summary", ""))
            if selected and used_chars + cost > context_budget:
                continue
            selected.append({**memory, "retrieval_score": round(self._score(item, intent, surface), 6)})
            cluster_count[cluster] += 1
            used_chars += cost
            if len(selected) == limit:
                break
        return selected

    @staticmethod
    def _cluster(memory: dict[str, Any]) -> str:
        return str(memory.get("cluster_id") or memory.get("memory_id"))

    @staticmethod
    def _score(candidate: dict[str, Any], intent: str, surface: str) -> float:
        m = candidate["memory"]
        # Intent is represented by vector relevance; lexical overlap offers a
        # deterministic boost when a caller has no embedding provider.
        words = {word for word in intent.lower().split() if len(word) > 2}
        lexical = len(words.intersection(m.get("summary", "").lower().split())) / max(len(words), 1)
        recorded = m.get("recorded_at", "")
        try:
            age_days = max(0.0, (datetime.now(timezone.utc) - datetime.fromisoformat(recorded.replace("Z", "+00:00"))).total_seconds() / 86400)
        except (TypeError, ValueError):
            age_days = 365.0
        recency = math.exp(-age_days / 90.0)
        policy = 1.0 if m.get("surface_policy", "default") in {"default", surface} else 0.15
        return (
            .30 * candidate.get("vector_score", 0.0) + .15 * candidate.get("graph_score", 0.0)
            + .12 * lexical + .12 * float(m.get("explicitness", 0.0))
            + .11 * float(m.get("confidence", 0.0)) + .08 * recency
            + .06 * min(1.0, float(m.get("repetition", 1)) / 5.0)
            + .06 * policy - .20 * float(m.get("negative_feedback", 0.0))
        )

    def recent_memories(self, user_id: str, limit: int = 20, subject_scope: str = "user") -> list[dict[str, Any]]:
        return self.repo.get_recent_for_user(user_id, limit, subject_scope)

    def get_memory(self, user_id: str, version_id: str, subject_scope: str = "user", include_history: bool = False) -> dict[str, Any] | None:
        return self.repo.get_memory(version_id, user_id, subject_scope, include_history)

    def memories_referencing_track(self, user_id: str, track_id: str, limit: int = 20, subject_scope: str = "user") -> list[dict[str, Any]]:
        return self.repo.get_referencing_track(track_id, user_id, limit, subject_scope)
