from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass
class Album:
    album_id: str
    title: str
    release_year: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_node(cls, node: dict[str, Any]) -> "Album":
        return cls(
            album_id=node["album_id"],
            title=node.get("title", ""),
            release_year=node.get("release_year"),
        )
