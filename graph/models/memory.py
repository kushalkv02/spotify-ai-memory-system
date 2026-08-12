from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


@dataclass
class Memory:
    """An immutable version of a memory fact.

    ``memory_id`` identifies the fact across revisions.  ``version_id`` is the
    id of this particular assertion, so corrections can be represented without
    overwriting the assertion that was originally recorded.
    """

    memory_id: str
    user_id: str
    summary: str
    importance: float = 0.5
    track_ids: list[str] = field(default_factory=list)
    version_id: str | None = None
    valid_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_to: datetime | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "user"
    confidence: float = 1.0
    status: Literal["active", "superseded", "contradicted", "expired", "corrected"] = "active"
    subject_scope: str = "user"
    explicitness: float = 0.0
    repetition: int = 1
    negative_feedback: float = 0.0
    surface_policy: str = "default"
    source_event_id: str | None = None
    source_action: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # Neo4j's temporal type accepts ISO-8601 values.  Keep created_at as a
        # compatibility alias for existing consumers and indexes.
        data["version_id"] = self.version_id or self.memory_id
        data["valid_from"] = self.valid_from.isoformat()
        data["recorded_at"] = self.recorded_at.isoformat()
        data["valid_to"] = self.valid_to.isoformat() if self.valid_to else None
        data["created_at"] = data["recorded_at"]
        data.pop("track_ids")  # relationship, not a node property
        return data

    @classmethod
    def from_node(cls, node: dict[str, Any]) -> "Memory":
        return cls(
            memory_id=node["memory_id"],
            user_id=node.get("user_id", ""),
            summary=node.get("summary", ""),
            importance=node.get("importance", 0.5),
            version_id=node.get("version_id"),
            source=node.get("source", "user"),
            confidence=node.get("confidence", 1.0),
            status=node.get("status", "active"),
            subject_scope=node.get("subject_scope", "user"),
        )
