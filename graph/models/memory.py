from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class Memory:
    memory_id: str
    user_id: str
    summary: str
    importance: float = 0.5
    track_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data.pop("track_ids")  # relationship, not a node property
        return data

    @classmethod
    def from_node(cls, node: dict[str, Any]) -> "Memory":
        return cls(
            memory_id=node["memory_id"],
            user_id=node.get("user_id", ""),
            summary=node.get("summary", ""),
            importance=node.get("importance", 0.5),
        )
