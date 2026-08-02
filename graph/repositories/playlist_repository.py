from __future__ import annotations

from typing import Any

from ..models.playlist import Playlist
from .base_repository import BaseRepository


class PlaylistRepository(BaseRepository):
    label = "Playlist"
    id_field = "playlist_id"

    def create_playlist(self, playlist: Playlist) -> dict[str, Any]:
        node = self.merge(playlist.to_dict())
        query = """
        MATCH (p:Playlist {playlist_id: $playlist_id})
        MATCH (u:User {user_id: $owner_user_id})
        MERGE (u)-[:OWNS]->(p)
        """
        self.client.execute_write(
            query, {"playlist_id": playlist.playlist_id, "owner_user_id": playlist.owner_user_id}
        )
        return node

    def add_track(self, playlist_id: str, track_id: str, position: int | None = None) -> None:
        query = """
        MATCH (p:Playlist {playlist_id: $playlist_id})
        MATCH (t:Track {track_id: $track_id})
        MERGE (p)-[r:INCLUDES]->(t)
        SET r.position = $position
        """
        self.client.execute_write(
            query, {"playlist_id": playlist_id, "track_id": track_id, "position": position}
        )
