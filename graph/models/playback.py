"""
Playback is modeled as a (:User)-[:PLAYED]->(:Track) RELATIONSHIP rather
than a node, so multiple plays of the same track by the same user are
each their own edge with their own timestamp/context. This dataclass
represents the *properties* carried on that relationship.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class Playback:
    user_id: str
    track_id: str
    played_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ms_played: Optional[int] = None
    context: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["played_at"] = self.played_at.isoformat()
        return data
