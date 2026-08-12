"""Tools that give the LLM the 'why' behind a recommendation/pattern."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..adapters.graph_adapter import GraphAdapter
from ..utils.formatting import to_text


def register(mcp: FastMCP, adapter: GraphAdapter) -> None:

    @mcp.tool()
    def get_genre_affinity(user_id: str) -> str:
        """Get a user's derived genre affinities."""
        return to_text(adapter.get_genre_affinity(user_id))
    @mcp.tool()
    def get_mood_affinity(user_id: str) -> str:
        """Get a user's derived mood affinities."""
        return to_text(adapter.get_mood_affinity(user_id))

    @mcp.tool()
    def get_listening_timeline(user_id: str, days: int = 30) -> str:
        """Get a user's play history over the last N days, most recent first."""
        return to_text(adapter.listening_timeline(user_id, days=days))

    @mcp.tool()
    def get_user_preferences(user_id: str) -> str:
        """Get a user's derived preferences (genre/artist/mood affinities)."""
        return to_text(adapter.get_preferences(user_id))

    @mcp.tool()
    def explain_recommendations(user_id: str, limit: int = 10) -> str:
        """Explain graph-native recommendations using shared listeners and artist history."""
        return to_text(adapter.explain_recommendations(user_id, limit=limit))
