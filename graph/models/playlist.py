from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Playlist:
    playlist_id: str
    name: str
    owner_user_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_node(cls, node: dict[str, Any]) -> "Playlist":
        return cls(
            playlist_id=node["playlist_id"],
            name=node.get("name", ""),
            owner_user_id=node.get("owner_user_id", ""),
        )
