"""
Tools for engagement signals beyond plain plays: likes, skips, and
artist follows. Mirrors playback_tools.py in shape — likes/follows are
idempotent state (mcp.tool functions just call through to
GraphAdapter, which calls the MERGE-based repository methods), skips
are events like plays (each call adds new history).
"""
from __future__ import annotations

from typing import Optional

from mcp.server.fastmcp import FastMCP

from ..adapters.graph_adapter import GraphAdapter
from ..schemas.tool_schemas import SkipTrackInput
from ..utils.formatting import to_text


def register(mcp: FastMCP, adapter: GraphAdapter) -> None:
    # -- likes -----------------------------------------------------------
    @mcp.tool()
    def like_track(
        user_id: str,
        track_id: str,
        user_display_name: Optional[str] = None,
        track_title: Optional[str] = None,
    ) -> str:
        """
        Like a track: creates (User)-[:LIKED]->(Track). Idempotent —
        liking an already-liked track just refreshes the timestamp.
        """
        return to_text(
            adapter.like_track(
                user_id, track_id, user_display_name=user_display_name, track_title=track_title
            )
        )

    @mcp.tool()
    def unlike_track(user_id: str, track_id: str) -> str:
        """Remove a like: deletes the (User)-[:LIKED]->(Track) relationship."""
        return to_text(adapter.unlike_track(user_id, track_id))

    @mcp.tool()
    def get_liked_tracks(user_id: str, limit: int = 50) -> str:
        """List a user's liked tracks, most recently liked first."""
        return to_text(adapter.get_liked_tracks(user_id, limit=limit))

    # -- skips -----------------------------------------------------------
    @mcp.tool()
    def skip_track(payload: SkipTrackInput) -> str:
        """
        Record that a user skipped a track (stopped it early), writing
        a NEW (User)-[:SKIPPED]->(Track) event. Each skip is preserved
        as its own event, same as record_play.
        """
        result = adapter.record_skip(
            user_id=payload.user_id,
            track_id=payload.track_id,
            user_display_name=payload.user_display_name,
            track_title=payload.track_title,
            ms_played=payload.ms_played,
            context=payload.context,
            session_id=payload.session_id,
        )
        return to_text(result)

    @mcp.tool()
    def get_recent_skips(user_id: str, limit: int = 20) -> str:
        """List a user's most recent skip events, most recent first."""
        return to_text(adapter.get_recent_skips(user_id, limit=limit))

    # -- follows -----------------------------------------------------------
    @mcp.tool()
    def follow_artist(
        user_id: str,
        artist_id: str,
        user_display_name: Optional[str] = None,
        artist_name: Optional[str] = None,
    ) -> str:
        """Follow an artist: creates (User)-[:FOLLOWED]->(Artist). Idempotent."""
        return to_text(
            adapter.follow_artist(
                user_id, artist_id, user_display_name=user_display_name, artist_name=artist_name
            )
        )

    @mcp.tool()
    def unfollow_artist(user_id: str, artist_id: str) -> str:
        """Unfollow an artist: deletes the (User)-[:FOLLOWED]->(Artist) relationship."""
        return to_text(adapter.unfollow_artist(user_id, artist_id))

    @mcp.tool()
    def get_followed_artists(user_id: str) -> str:
        """List the artists a user follows."""
        return to_text(adapter.get_followed_artists(user_id))
