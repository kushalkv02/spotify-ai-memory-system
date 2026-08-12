"""
GraphService is the primary entry point for the rest of the app
(interaction_service today, the FastAPI Interaction API later).

`record_play_event` is the original function: give it a user_id and a
track_id (plus optional display name / title so it can create the
nodes on first sight) and it will:
  1. MERGE the User node
  2. MERGE the Track node
  3. CREATE a new (User)-[:PLAYED]->(Track) relationship with event
     properties (timestamp, ms_played, context, session_id)

`like_track` / `unlike_track`, `record_skip_event`, and
`follow_artist` / `unfollow_artist` follow the same shape for the
other interaction signals — see engagement_repository.py for how each
relationship type is modeled (state vs. event).

Every call is visible immediately in Neo4j Desktop / Neo4j Browser —
there's no batching or async queue in this layer.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from ..models.artist import Artist
from ..models.track import Track
from ..models.user import User
from ..repositories.artist_repository import ArtistRepository
from ..repositories.engagement_repository import EngagementRepository
from ..repositories.playback_repository import PlaybackRepository
from ..repositories.track_repository import TrackRepository
from ..repositories.user_repository import UserRepository


class GraphService:
    def __init__(self) -> None:
        self.users = UserRepository()
        self.tracks = TrackRepository()
        self.artists = ArtistRepository()
        self.playback = PlaybackRepository()
        self.engagement = EngagementRepository()

    # -- entity upserts ---------------------------------------------------
    def ensure_user(self, user_id: str, display_name: str, **kwargs: Any) -> dict[str, Any]:
        return self.users.create_user(User(user_id=user_id, display_name=display_name, **kwargs))

    def ensure_track(self, track_id: str, title: str, **kwargs: Any) -> dict[str, Any]:
        return self.tracks.create_track(Track(track_id=track_id, title=title, **kwargs))

    def ensure_artist(self, artist_id: str, name: str, **kwargs: Any) -> dict[str, Any]:
        return self.artists.create_artist(Artist(artist_id=artist_id, name=name, **kwargs))

    # -- the core event -----------------------------------------------------
    def record_play_event(
        self,
        user_id: str,
        track_id: str,
        *,
        user_display_name: Optional[str] = None,
        track_title: Optional[str] = None,
        ms_played: Optional[int] = None,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Record `user_id` played `track_id`.

        If `user_display_name` / `track_title` are given, the User /
        Track nodes are created (MERGE) first if they don't already
        exist — handy while there's no frontend yet and you're calling
        this directly with brand-new ids. If they're omitted, the User
        and Track are assumed to already exist and a ValueError is
        raised if either is missing.
        """
        if user_display_name:
            self.ensure_user(user_id, user_display_name)
        if track_title:
            self.ensure_track(track_id, track_title)
 
        return self.playback.record_play(
            user_id=user_id,
            track_id=track_id,
            ms_played=ms_played,
            context=context,
            session_id=session_id,
            occurred_at=occurred_at.isoformat() if occurred_at else None,
        )

    # -- likes (state) -----------------------------------------------------
    def like_track(
        self,
        user_id: str,
        track_id: str,
        *,
        occurred_at: Optional[datetime] = None,
        user_display_name: Optional[str] = None,
        track_title: Optional[str] = None,
        artist_id: Optional[str] = None,
        artist_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Like `track_id` for `user_id`, creating (User)-[:LIKED]->(Track).
        Idempotent — liking an already-liked track just refreshes the
        timestamp rather than erroring or duplicating the edge.
        """
        print(f"User {user_id} liking track {track_id} (artist: {artist_id}) at {occurred_at}")
        if user_display_name:
            self.ensure_user(user_id, user_display_name)
        if track_title:
            self.ensure_track(track_id, track_title)
        if artist_id and artist_name:
            self.ensure_artist(artist_id, artist_name)
            self.artists.link_performed(artist_id, track_id)
        return self.engagement.like_track(
            user_id=user_id,
            track_id=track_id,
            liked_at=occurred_at.isoformat() if occurred_at else None,
        )

    def unlike_track(self, user_id: str, track_id: str) -> None:
        self.engagement.unlike_track(user_id=user_id, track_id=track_id)

    # -- skips (event) -----------------------------------------------------
    def record_skip_event(
        self,
        user_id: str,
        track_id: str,
        *,
        occurred_at: Optional[datetime] = None,
        user_display_name: Optional[str] = None,
        track_title: Optional[str] = None,
        ms_played: Optional[int] = None,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Record that `user_id` skipped `track_id`, creating a NEW
        (User)-[:SKIPPED]->(Track) event each time — mirrors
        record_play_event, but for the "stopped it early" signal.
        """
        if user_display_name:
            self.ensure_user(user_id, user_display_name)
        if track_title:
            self.ensure_track(track_id, track_title)
        return self.engagement.record_skip(
            user_id=user_id,
            track_id=track_id,
            skipped_at=occurred_at.isoformat() if occurred_at else None,
            ms_played=ms_played,
            context=context,
            session_id=session_id,
        )

    # -- follows (state) -----------------------------------------------------
    def follow_artist(
        self,
        user_id: str,
        artist_id: str,
        *,
        occurred_at: Optional[datetime] = None,
        user_display_name: Optional[str] = None,
        artist_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Follow `artist_id` for `user_id`, creating
        (User)-[:FOLLOWED]->(Artist). Idempotent, same pattern as like_track.
        """
        if user_display_name:
            self.ensure_user(user_id, user_display_name)
        if artist_name:
            self.ensure_artist(artist_id, artist_name)
        return self.engagement.follow_artist(
            user_id=user_id,
            artist_id=artist_id,
            followed_at=occurred_at.isoformat() if occurred_at else None,
        )

    def unfollow_artist(self, user_id: str, artist_id: str) -> None:
        self.engagement.unfollow_artist(user_id=user_id, artist_id=artist_id)

    def follow_album(self, user_id: str, album_id: str) -> None:
        self.engagement.follow_album(user_id=user_id, album_id=album_id)

    # methods for reasoning service
    def get_followed_artists(self, user_id: str) -> list[dict[str, Any]]:
        return self.engagement.get_followed_artists(user_id=user_id)
_graph_service: Optional[GraphService] = None


def get_graph_service() -> GraphService:
    """Process-wide singleton, mirroring get_client() in neo4j_client.py."""
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service
