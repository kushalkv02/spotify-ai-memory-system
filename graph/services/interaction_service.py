"""
Bridges interaction-api events into the graph layer.

Receives validated events from the Interaction API and dispatches them
to the appropriate GraphService method.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .graph_service import get_graph_service


class InteractionService:
    def __init__(self) -> None:
        self.graph = get_graph_service()

    async def handle_event(
        self,
        *,
        user_id: str,
        category: str,
        payload: dict[str, Any],
        occurred_at: datetime,
    ) -> dict[str, Any]:
        """
        Dispatch an interaction event to the appropriate GraphService method.

        Parameters
        ----------
        user_id
            Spotify user ID.

        category
            High-level event category (playback, ui_action, chat, etc.).

        payload
            Event-specific payload.

        occurred_at
            Timestamp supplied by the Interaction API.
        """

        # -------------------------
        # Playback Events
        # -------------------------
        if category == "playback":

            action = payload.get("action")

            if action == "play":
                return self.graph.record_play_event(
                    user_id=user_id,
                    track_id=payload["track_id"],
                    user_display_name=payload.get("user_display_name"),
                    track_title=payload.get("track_title"),
                    ms_played=payload.get("ms_played"),
                    context=payload.get("context"),
                    session_id=payload.get("session_id"),
                    occurred_at=occurred_at,
                )

            elif action == "like":
                return self.graph.like_track(
                    user_id=user_id,
                    track_id=payload["track_id"],
                    occurred_at=occurred_at,
                    user_display_name=payload.get("user_display_name"),
                    track_title=payload.get("track_title"),
                    artist_id=payload.get("artist_id"),
                    artist_name=payload.get("artist_name"),
                )

            elif action == "unlike":
                return self.graph.unlike_track(
                    user_id=user_id,
                    track_id=payload["track_id"],
                )

            elif action == "skip":
                return self.graph.record_skip_event(
                    user_id=user_id,
                    track_id=payload["track_id"],
                    occurred_at=occurred_at,
                    user_display_name=payload.get("user_display_name"),
                    track_title=payload.get("track_title"),
                    ms_played=payload.get("ms_played"),
                    context=payload.get("context"),
                    session_id=payload.get("session_id"),
                )

        # -------------------------
        # UI Events
        # -------------------------
        elif category == "ui_action":

            action = payload.get("action_type")

            if action == "follow_artist":
                return self.graph.follow_artist(
                    user_id=user_id,
                    artist_id=payload["artist_id"],
                    user_display_name=payload.get("user_display_name"),
                    artist_name=payload.get("artist_name"),
                    occurred_at=occurred_at,
                )
            elif action == "unfollow_artist":
                return self.graph.unfollow_artist(
                    user_id=user_id,
                    artist_id=payload["artist_id"],
                )

        # Chat messages are represented by their linked Memory node. Ensure
        # the user exists before GraphClient creates that memory relationship.
        elif category == "chat":
            return self.graph.ensure_user(
                user_id=user_id,
                display_name=payload.get("user_display_name") or "Listener",
            )

        raise ValueError(
            f"Unsupported event: category={category!r}, payload={payload}"
        )
