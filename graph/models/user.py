from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class User:
    user_id: str
    display_name: str
    email: Optional[str] = None
    consent_given: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_node(cls, node: dict[str, Any]) -> "User":
        return cls(
            user_id=node["user_id"],
            display_name=node.get("display_name", ""),
            email=node.get("email"),
            consent_given=node.get("consent_given", False),
        )
