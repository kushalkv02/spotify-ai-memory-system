from __future__ import annotations

from typing import Any, Optional

from ..models.track import Track
from .base_repository import BaseRepository


class TrackRepository(BaseRepository):
    label = "Track"
    id_field = "track_id"

    def create_track(self, track: Track) -> dict[str, Any]:
        return self.merge(track.to_dict())

    def get_track(self, track_id: str) -> Optional[dict[str, Any]]:
        return self.get_by_id(track_id)

    def search_by_title(self, title_fragment: str, limit: int = 20) -> list[dict[str, Any]]:
        query = """
        MATCH (t:Track)
        WHERE toLower(t.title) CONTAINS toLower($fragment)
        RETURN t
        LIMIT $limit
        """
        result = self.client.execute_read(query, {"fragment": title_fragment, "limit": limit})
        return [r["t"] for r in result]
