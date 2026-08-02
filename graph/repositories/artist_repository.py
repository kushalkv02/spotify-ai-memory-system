from __future__ import annotations

from typing import Any

from ..models.artist import Artist
from .base_repository import BaseRepository


class ArtistRepository(BaseRepository):
    label = "Artist"
    id_field = "artist_id"

    def create_artist(self, artist: Artist) -> dict[str, Any]:
        return self.merge(artist.to_dict())

    def link_performed(self, artist_id: str, track_id: str) -> None:
        query = """
        MATCH (ar:Artist {artist_id: $artist_id})
        MATCH (t:Track {track_id: $track_id})
        MERGE (t)-[:BY]->(ar)
        """
        self.client.execute_write(query, {"artist_id": artist_id, "track_id": track_id})
