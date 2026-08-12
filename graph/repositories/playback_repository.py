"""
Manages the (:User)-[:PLAYED]->(:Track) relationship — the core
interaction event of the whole system. This is deliberately NOT a
BaseRepository subclass: a "playback" isn't a node, it's an edge, and
every call creates a brand-new relationship instance so listening
history is fully preserved (Neo4j allows many parallel relationships
of the same type between the same two nodes).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from ..neo4j_client import get_client


class PlaybackRepository:
    def __init__(self) -> None:
        self.client = get_client()

    def record_play(
        self,
        user_id: str,
        track_id: str,
        *,
        played_at: Optional[str] = None,
        occurred_at: Optional[str] = None,
        ms_played: Optional[int] = None,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create (User)-[:PLAYED]->(Track) with event properties.

        Assumes the User and Track nodes already exist — GraphService
        ensures that before calling this. Raises ValueError if either
        node is missing, so a bad event fails loudly instead of
        silently doing nothing.
        """
        query = """
        MERGE (u:User {user_id:$user_id})
        MERGE (t:Track {track_id:$track_id})
        CREATE (u)-[r:PLAYED {
            played_at: $played_at,
            ms_played: $ms_played,
            occurred_at: $occurred_at,
            context: $context,
            session_id: $session_id
        }]->(t)
        RETURN u.user_id AS user_id, t.track_id AS track_id, t.title AS track_title,
               r.played_at AS played_at, r.ms_played AS ms_played, r.context AS context
        """
        params = {
            "user_id": user_id,
            "track_id": track_id,
            "played_at": played_at or datetime.now(timezone.utc).isoformat(),
            "occurred_at": occurred_at or datetime.now(timezone.utc).isoformat(),
            "ms_played": ms_played,
            "context": context,
            "session_id": session_id,
        }
        result = self.client.execute_write(query, params)
        if not result:
            raise ValueError(
                f"Could not record play: User '{user_id}' or Track '{track_id}' not found "
                "in the graph. Ensure both exist before recording an event."
            )
        return result[0]

    def get_recent_plays(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        query = """
        MATCH (u:User {user_id: $user_id})-[r:PLAYED]->(t:Track)
        RETURN t.track_id AS track_id, t.title AS title, r.played_at AS played_at, r.context AS context
        ORDER BY r.played_at DESC
        LIMIT $limit
        """
        return self.client.execute_read(query, {"user_id": user_id, "limit": limit})

    def count_plays(self, user_id: str, track_id: str) -> int:
        query = """
        MATCH (:User {user_id: $user_id})-[r:PLAYED]->(:Track {track_id: $track_id})
        RETURN count(r) AS c
        """
        result = self.client.execute_read(query, {"user_id": user_id, "track_id": track_id})
        return result[0]["c"] if result else 0
