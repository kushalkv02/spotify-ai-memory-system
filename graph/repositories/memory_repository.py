from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any, Iterable

from ..models.memory import Memory
from .base_repository import BaseRepository


class MemoryRepository(BaseRepository):
    """Persistence boundary for temporal, subject-scoped memory facts.

    A ``Memory`` node is one asserted version, never a mutable current-state
    record.  The stable ``memory_id`` is shared with its vector; ``version_id``
    makes corrections and contradictions auditable.
    """

    label = "Memory"
    id_field = "version_id"
    _EMBEDDABLE_FIELDS = frozenset({"summary"})
    _CURRENT_STATUSES = ("active", "corrected")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _validate_scope(user_id: str, subject_scope: str) -> None:
        if not user_id or not subject_scope:
            raise ValueError("user_id and subject_scope are required at the memory query boundary")
        # This graph currently supports only a user's personal identity scope.
        # Refuse arbitrary scopes rather than treating them as optional filters.
        if subject_scope != "user":
            raise ValueError("only the 'user' subject scope is authorized for personal memory")

    def create_memory(self, memory: Memory) -> dict[str, Any]:
        self._validate_scope(memory.user_id, memory.subject_scope)
        props = memory.to_dict()
        # The version id is deterministic when supplied by an event source;
        # MERGE therefore makes retried deliveries idempotent.
        query = """
        MATCH (u:User {user_id: $user_id})
        MERGE (m:Memory {version_id: $version_id})
        ON CREATE SET m = $properties
        WITH u, m
        // A version id can never be rebound to a different identity scope.
        // This check occurs before any relationship is merged or mutated.
        WHERE m.user_id = $user_id AND m.subject_scope = $subject_scope
        MERGE (u)-[about:HAS_MEMORY]->(m)
        ON CREATE SET about.valid_from = $valid_from, about.valid_to = $valid_to,
                      about.recorded_at = $recorded_at, about.source = $source,
                      about.confidence = $confidence, about.status = $status,
                      about.subject_scope = $subject_scope
        RETURN m
        """
        result = self.client.execute_write(query, {**props, "properties": props})
        if not result:
            raise ValueError("memory version is not authorized for this subject or the subject does not exist")

        for track_id in sorted(set(memory.track_ids)):
            self.client.execute_write(
                """
                MATCH (m:Memory {version_id: $version_id, user_id: $user_id, subject_scope: $subject_scope})
                MATCH (t:Track {track_id: $track_id})
                MERGE (m)-[r:REFERENCES]->(t)
                ON CREATE SET r.valid_from = $valid_from, r.valid_to = $valid_to,
                              r.recorded_at = $recorded_at, r.source = $source,
                              r.confidence = $confidence, r.status = $status,
                              r.subject_scope = $subject_scope
                """,
                {**props, "track_id": track_id},
            )
        return result[0]["m"]

    def revise_memory(
        self, previous_version_id: str, replacement: Memory, *, disposition: str = "superseded"
    ) -> dict[str, Any]:
        """Record a correction/contradiction and close the prior validity range."""
        self._validate_scope(replacement.user_id, replacement.subject_scope)
        if disposition not in {"superseded", "contradicted", "corrected", "expired"}:
            raise ValueError("invalid memory disposition")
        if replacement.version_id == previous_version_id:
            raise ValueError("a revision must have a new version_id")

        close_at = replacement.valid_from.isoformat()
        query = """
        MATCH (old:Memory {version_id: $previous_version_id, user_id: $user_id, subject_scope: $subject_scope})
        WHERE old.status IN ['active', 'corrected']
        SET old.status = $disposition, old.valid_to = $close_at
        WITH old
        MATCH (u:User {user_id: $user_id})
        MERGE (new:Memory {version_id: $version_id})
        ON CREATE SET new = $properties
        MERGE (old)-[lineage:SUPERSEDED_BY]->(new)
        ON CREATE SET lineage.recorded_at = $recorded_at, lineage.valid_from = $close_at,
                      lineage.source = $source, lineage.confidence = $confidence,
                      lineage.status = $disposition, lineage.subject_scope = $subject_scope
        MERGE (u)-[:HAS_MEMORY]->(new)
        RETURN new
        """
        props = replacement.to_dict()
        result = self.client.execute_write(query, {
            **props, "properties": props, "previous_version_id": previous_version_id,
            "disposition": disposition, "close_at": close_at,
        })
        if not result:
            raise ValueError("the prior memory is missing, inactive, or belongs to another subject")
        # Relationships are versioned too.  This is intentionally after the
        # atomic lineage write, so a retry remains safe.
        for track_id in sorted(set(replacement.track_ids)):
            self.client.execute_write(
                """
                MATCH (m:Memory {version_id: $version_id, user_id: $user_id, subject_scope: $subject_scope})
                MATCH (t:Track {track_id: $track_id})
                MERGE (m)-[r:REFERENCES]->(t)
                ON CREATE SET r.valid_from = $valid_from, r.valid_to = $valid_to,
                              r.recorded_at = $recorded_at, r.source = $source,
                              r.confidence = $confidence, r.status = $status,
                              r.subject_scope = $subject_scope
                """, {**props, "track_id": track_id},
            )
        return result[0]["new"]

    def expire_memory(self, version_id: str, user_id: str, subject_scope: str = "user") -> bool:
        self._validate_scope(user_id, subject_scope)
        result = self.client.execute_write(
            """
            MATCH (m:Memory {version_id: $version_id, user_id: $user_id, subject_scope: $subject_scope})
            WHERE m.status IN ['active', 'corrected']
            SET m.status = 'expired', m.valid_to = $now
            RETURN m.version_id AS version_id
            """, {"version_id": version_id, "user_id": user_id, "subject_scope": subject_scope, "now": self._now()},
        )
        return bool(result)

    def expire_state_memories(self, user_id: str, entity_type: str, entity_id: str, subject_scope: str = "user") -> int:
        """Close memories created by a reversible like/follow state action."""
        self._validate_scope(user_id, subject_scope)
        if entity_type not in {"track", "artist"} or not entity_id:
            raise ValueError("a canonical track or artist entity is required")
        result = self.client.execute_write(
            """
            MATCH (:User {user_id: $user_id})-[:HAS_MEMORY]->(m:Memory {user_id: $user_id, subject_scope: $subject_scope})
            WHERE m.status IN ['active', 'corrected']
              AND (
                  (m.entity_type = $entity_type AND m.entity_id = $entity_id
                   AND m.source_action IN ['like', 'follow_artist'])
                  OR (
                      m.source IN ['event:playback', 'event:ui_action']
                      AND m.summary CONTAINS $entity_id
                      AND (
                          $entity_type = 'artist'
                          OR EXISTS { MATCH (m)-[:REFERENCES]->(:Track {track_id: $entity_id}) }
                      )
                  )
              )
            SET m.status = 'expired', m.valid_to = $now
            RETURN count(m) AS expired_count
            """,
            {"user_id": user_id, "subject_scope": subject_scope, "entity_type": entity_type,
             "entity_id": entity_id, "now": self._now()},
        )
        return int(result[0]["expired_count"]) if result else 0

    def get_recent_for_user(self, user_id: str, limit: int = 20, subject_scope: str = "user") -> list[dict[str, Any]]:
        self._validate_scope(user_id, subject_scope)
        query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_MEMORY {subject_scope: $subject_scope}]->(m:Memory {user_id: $user_id, subject_scope: $subject_scope})
        WHERE m.status IN ['active', 'corrected']
          AND m.valid_from <= $as_of AND (m.valid_to IS NULL OR m.valid_to > $as_of)
        RETURN m ORDER BY m.recorded_at DESC LIMIT $limit
        """
        result = self.client.execute_read(query, {"user_id": user_id, "subject_scope": subject_scope, "as_of": self._now(), "limit": limit})
        return [r["m"] for r in result]

    def get_memory(self, version_id: str, user_id: str, subject_scope: str = "user", include_history: bool = False) -> dict[str, Any] | None:
        self._validate_scope(user_id, subject_scope)
        history_filter = "" if include_history else "AND m.status IN ['active', 'corrected']"
        result = self.client.execute_read(
            f"""
            MATCH (u:User {{user_id: $user_id}})-[:HAS_MEMORY {{subject_scope: $subject_scope}}]->(m:Memory {{version_id: $version_id, user_id: $user_id, subject_scope: $subject_scope}})
            WHERE true {history_filter}
            RETURN m
            """, {"version_id": version_id, "user_id": user_id, "subject_scope": subject_scope},
        )
        return result[0]["m"] if result else None

    def get_referencing_track(self, track_id: str, user_id: str, limit: int = 20, subject_scope: str = "user") -> list[dict[str, Any]]:
        self._validate_scope(user_id, subject_scope)
        query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_MEMORY {subject_scope: $subject_scope}]->(m:Memory {user_id: $user_id, subject_scope: $subject_scope})-[r:REFERENCES {subject_scope: $subject_scope}]->(:Track {track_id: $track_id})
        WHERE m.status IN ['active', 'corrected'] AND r.status IN ['active', 'corrected']
        RETURN m ORDER BY m.recorded_at DESC LIMIT $limit
        """
        return [r["m"] for r in self.client.execute_read(query, {"track_id": track_id, "user_id": user_id, "subject_scope": subject_scope, "limit": limit})]

    def store_embedding(self, version_id: str, user_id: str, embedding: Iterable[float], field: str = "summary", subject_scope: str = "user") -> None:
        self._validate_scope(user_id, subject_scope)
        if field not in self._EMBEDDABLE_FIELDS:
            raise ValueError(f"embedding field {field!r} is not approved")
        vector = list(embedding)
        if not vector or not all(isinstance(value, (int, float)) and isfinite(value) for value in vector):
            raise ValueError("embedding must be a non-empty finite numeric vector")
        self.client.execute_write(
            """
            MATCH (u:User {user_id: $user_id})-[:HAS_MEMORY {subject_scope: $subject_scope}]->(m:Memory {version_id: $version_id, user_id: $user_id, subject_scope: $subject_scope})
            SET m.embedding = $embedding, m.embedding_field = $field, m.embedding_recorded_at = $recorded_at
            """, {"version_id": version_id, "user_id": user_id, "subject_scope": subject_scope, "embedding": vector, "field": field, "recorded_at": self._now()},
        )

    def hybrid_candidates(self, user_id: str, query_embedding: list[float] | None, track_ids: list[str], limit: int, subject_scope: str = "user") -> list[dict[str, Any]]:
        """Union relational and semantic candidates, with scope in each branch."""
        self._validate_scope(user_id, subject_scope)
        params = {"user_id": user_id, "subject_scope": subject_scope, "track_ids": track_ids, "limit": limit, "as_of": self._now()}
        graph_query = """
        MATCH (u:User {user_id: $user_id})-[:HAS_MEMORY {subject_scope: $subject_scope}]->(m:Memory {user_id: $user_id, subject_scope: $subject_scope})
        WHERE m.status IN ['active', 'corrected'] AND m.valid_from <= $as_of AND (m.valid_to IS NULL OR m.valid_to > $as_of)
          AND (size($track_ids) = 0 OR EXISTS { MATCH (m)-[:REFERENCES {subject_scope: $subject_scope}]->(t:Track) WHERE t.track_id IN $track_ids })
        RETURN m, 1.0 AS graph_score LIMIT $limit
        """
        rows = self.client.execute_read(graph_query, params)
        if not query_embedding:
            return [{"memory": row["m"], "graph_score": row["graph_score"], "vector_score": 0.0} for row in rows]
        vector_query = """
        CALL db.index.vector.queryNodes('memory_embedding_idx', $limit, $embedding) YIELD node, score
        MATCH (u:User {user_id: $user_id})-[:HAS_MEMORY {subject_scope: $subject_scope}]->(node:Memory {user_id: $user_id, subject_scope: $subject_scope})
        WHERE node.status IN ['active', 'corrected'] AND node.valid_from <= $as_of AND (node.valid_to IS NULL OR node.valid_to > $as_of)
        RETURN node AS m, score AS vector_score
        """
        vector_rows = self.client.execute_read(vector_query, {**params, "embedding": query_embedding})
        merged: dict[str, dict[str, Any]] = {}
        for row in rows:
            merged[row["m"]["version_id"]] = {"memory": row["m"], "graph_score": row["graph_score"], "vector_score": 0.0}
        for row in vector_rows:
            key = row["m"]["version_id"]
            entry = merged.setdefault(key, {"memory": row["m"], "graph_score": 0.0, "vector_score": 0.0})
            entry["vector_score"] = row["vector_score"]
        return list(merged.values())

    def delete_memory(self, *_: Any, **__: Any) -> None:
        raise RuntimeError("memory facts are append-only; expire or revise them instead")
