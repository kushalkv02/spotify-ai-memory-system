from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Artist:
    artist_id: str
    name: str
    genres: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_node(cls, node: dict[str, Any]) -> "Artist":
        return cls(
            artist_id=node["artist_id"],
            name=node.get("name", ""),
            genres=node.get("genres", []),
        )
