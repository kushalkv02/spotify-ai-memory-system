from __future__ import annotations

from typing import Any

from ..models.album import Album
from .base_repository import BaseRepository


class AlbumRepository(BaseRepository):
    label = "Album"
    id_field = "album_id"

    def create_album(self, album: Album) -> dict[str, Any]:
        return self.merge(album.to_dict())

    def link_contains(self, album_id: str, track_id: str) -> None:
        query = """
        MATCH (al:Album {album_id: $album_id})
        MATCH (t:Track {track_id: $track_id})
        MERGE (al)-[:CONTAINS]->(t)
        """
        self.client.execute_write(query, {"album_id": album_id, "track_id": track_id})

    def link_released(self, artist_id: str, album_id: str) -> None:
        query = """
        MATCH (ar:Artist {artist_id: $artist_id})
        MATCH (al:Album {album_id: $album_id})
        MERGE (ar)-[:RELEASED]->(al)
        """
        self.client.execute_write(query, {"artist_id": artist_id, "album_id": album_id})
