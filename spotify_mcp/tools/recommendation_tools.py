"""Tools that surface graph-native track recommendations."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..adapters.graph_adapter import GraphAdapter
from ..utils.formatting import to_text


def register(mcp: FastMCP, adapter: GraphAdapter) -> None:
    @mcp.tool()
    def recommend_collaborative(user_id: str, limit: int = 10) -> str:
        """
        Recommend tracks via collaborative filtering: tracks played by
        other users who share listening history with this user.
        """
        return to_text(adapter.recommend_collaborative(user_id, limit=limit))

    @mcp.tool()
    def recommend_by_artist_affinity(user_id: str, limit: int = 10) -> str:
        """Recommend tracks by artists this user already listens to a lot."""
        return to_text(adapter.recommend_by_artist(user_id, limit=limit))

    @mcp.tool()
    def recommend_by_genre_affinity(user_id: str, limit: int = 10) -> str:
        """Recommend unplayed tracks from genres the user plays most often."""
        return to_text(adapter.recommend_by_genre(user_id, limit=limit))

    @mcp.tool()
    def recommend_by_mood(user_id: str, limit: int = 10) -> str:
        """Recommend tracks by mood."""
        return to_text(adapter.recommend_by_mood(user_id, limit=limit))

    @mcp.tool()
    def structured_recommendation_reply(
        user_id: str, intent: str = "", genre: str | None = None, limit: int = 3
    ) -> str:
        """
        Build a Claude-ready structured reply with an opening prompt,
        music recommendations, and recommendation reasonings.
        """
        return to_text(
            adapter.structured_recommendation_reply(
                user_id=user_id, intent=intent, genre=genre, limit=limit
            )
        )

    @mcp.tool()
    def listening_timeline(user_id: str, days: int = 30) -> str:
        """Return a timeline of the user's listening history."""
        return to_text(adapter.listening_timeline(user_id, days=days))

    @mcp.tool()
    def get_user_preferences(user_id: str) -> str:
        """Get a user's derived preferences (genre/artist/mood affinities)."""
        return to_text(adapter.get_preferences(user_id))
