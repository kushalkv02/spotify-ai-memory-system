from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class Session:
    session_id: str
    user_id: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    device: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["started_at"] = self.started_at.isoformat()
        data["ended_at"] = self.ended_at.isoformat() if self.ended_at else None
        return data

    @classmethod
    def from_node(cls, node: dict[str, Any]) -> "Session":
        return cls(
            session_id=node["session_id"],
            user_id=node.get("user_id", ""),
            device=node.get("device"),
        )
