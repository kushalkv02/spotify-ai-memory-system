from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Preference:
    preference_id: str
    user_id: str
    kind: str          # e.g. "genre", "artist", "mood"
    value: str          # e.g. "psychedelic rock"
    strength: float = 0.5
    sentiment: str = "like"
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["updated_at"] = self.updated_at.isoformat()
        return data


