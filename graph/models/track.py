from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass
class Track:
    track_id: str
    title: str
    duration_ms: Optional[int] = None
    genre: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_node(cls, node: dict[str, Any]) -> "Track":
        return cls(
            track_id=node["track_id"],
            title=node.get("title", ""),
            duration_ms=node.get("duration_ms"),
            genre=node.get("genre"),
        )
