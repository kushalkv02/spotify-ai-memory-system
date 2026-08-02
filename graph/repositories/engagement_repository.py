"""
Manages engagement relationships beyond plain playback:

  (:User)-[:LIKED]->(:Track)      state — a user either likes a track or
                                    doesn't, so this is MERGEd (one edge,
                                    re-liking just refreshes the timestamp)
                                    and can be explicitly removed via unlike.

  (:User)-[:SKIPPED]->(:Track)    event — mirrors PLAYED: a user can skip
                                    the same track many times, so each skip
                                    is its own CREATEd edge, preserving
                                    full history instead of overwriting.

  (:User)-[:FOLLOWED]->(:Artist)  state — same MERGE/unfollow pattern as
                                    LIKED.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from ..neo4j_client import get_client


class EngagementRepository:
    def __init__(self) -> None:
        self.client = get_client()

    # -- likes (state) -----------------------------------------------------
    def like_track(
        self, user_id: str, track_id: str, liked_at: Optional[str] = None
    ) -> dict[str, Any]:
        query = """
        MERGE (u:User {user_id:$user_id})
        MERGE (t:Track {track_id:$track_id})
        MERGE (u)-[r:LIKED]->(t)
        SET r.liked_at = $liked_at
        RETURN u.user_id AS user_id, t.track_id AS track_id, r.liked_at AS liked_at
        """
        params = {
            "user_id": user_id,
            "track_id": track_id,
            "liked_at": liked_at or datetime.now(timezone.utc).isoformat(),
        }
        result = self.client.execute_write(query, params)
        if not result:
            raise ValueError(
                f"Could not like track: User '{user_id}' or Track '{track_id}' not found."
            )
        return result[0]

    def unlike_track(self, user_id: str, track_id: str) -> None:
        query = """
        MATCH (:User {user_id: $user_id})-[r:LIKED]->(:Track {track_id: $track_id})
        DELETE r
        """
        self.client.execute_write(query, {"user_id": user_id, "track_id": track_id})

    def is_liked(self, user_id: str, track_id: str) -> bool:
        query = """
        MATCH (:User {user_id: $user_id})-[r:LIKED]->(:Track {track_id: $track_id})
        RETURN count(r) > 0 AS liked
        """
        result = self.client.execute_read(query, {"user_id": user_id, "track_id": track_id})
        return bool(result[0]["liked"]) if result else False

    def get_liked_tracks(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        query = """
        MATCH (:User {user_id: $user_id})-[r:LIKED]->(t:Track)
        RETURN t.track_id AS track_id, t.title AS title, r.liked_at AS liked_at
        ORDER BY r.liked_at DESC
        LIMIT $limit
        """
        return self.client.execute_read(query, {"user_id": user_id, "limit": limit})

    # -- skips (event) -----------------------------------------------------
    def record_skip(
        self,
        user_id: str,
        track_id: str,
        skipped_at: Optional[str] = None,
        ms_played: Optional[int] = None,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        query = """
        MERGE (u:User {user_id:$user_id})
        MERGE (t:Track {track_id:$track_id})
        CREATE (u)-[r:SKIPPED {
            skipped_at: $skipped_at,
            ms_played: $ms_played,
            context: $context,
            session_id: $session_id
        }]->(t)
        RETURN u.user_id AS user_id, t.track_id AS track_id,
               r.skipped_at AS skipped_at, r.ms_played AS ms_played
        """
        params = {
            "user_id": user_id,
            "track_id": track_id,
            "skipped_at": skipped_at or datetime.now(timezone.utc).isoformat(),
            "ms_played": ms_played,
            "context": context,
            "session_id": session_id,
        }
        result = self.client.execute_write(query, params)
        if not result:
            raise ValueError(
                f"Could not record skip: User '{user_id}' or Track '{track_id}' not found."
            )
        return result[0]

    def get_recent_skips(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        query = """
        MATCH (:User {user_id: $user_id})-[r:SKIPPED]->(t:Track)
        RETURN t.track_id AS track_id, t.title AS title,
               r.skipped_at AS skipped_at, r.ms_played AS ms_played
        ORDER BY r.skipped_at DESC
        LIMIT $limit
        """
        return self.client.execute_read(query, {"user_id": user_id, "limit": limit})

    # -- follows (state) -----------------------------------------------------
    def follow_artist(
        self, user_id: str, artist_id: str, followed_at: Optional[str] = None
    ) -> dict[str, Any]:
        query = """
        MERGE (u:User {user_id:$user_id})
        MERGE (ar:Artist {artist_id:$artist_id})
        MERGE (u)-[r:FOLLOWED]->(ar)
        SET r.followed_at = $followed_at
        RETURN u.user_id AS user_id, ar.artist_id AS artist_id, r.followed_at AS followed_at
        """
        params = {
            "user_id": user_id,
            "artist_id": artist_id,
            "followed_at": followed_at or datetime.now(timezone.utc).isoformat(),
        }
        result = self.client.execute_write(query, params)
        if not result:
            raise ValueError(
                f"Could not follow artist: User '{user_id}' or Artist '{artist_id}' not found."
            )
        return result[0]

    def unfollow_artist(self, user_id: str, artist_id: str) -> None:
        query = """
        MATCH (:User {user_id: $user_id})-[r:FOLLOWED]->(:Artist {artist_id: $artist_id})
        DELETE r
        """
        self.client.execute_write(query, {"user_id": user_id, "artist_id": artist_id})

    def get_followed_artists(self, user_id: str) -> list[dict[str, Any]]:
        query = """
        MATCH (:User {user_id: $user_id})-[r:FOLLOWED]->(ar:Artist)
        RETURN ar.artist_id AS artist_id, ar.name AS name, r.followed_at AS followed_at
        ORDER BY r.followed_at DESC
        """
        return self.client.execute_read(query, {"user_id": user_id})

    def follow_album(self, user_id: str, album_id: str) -> None:
        query = """
        MERGE (u:User {user_id:$user_id})
        MERGE (al:Album {album_id:$album_id})
        MERGE (u)-[r:FOLLOWED]->(al)
        """
        self.client.execute_write(query, {"user_id": user_id, "album_id": album_id})
