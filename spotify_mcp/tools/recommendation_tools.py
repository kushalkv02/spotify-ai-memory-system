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

    