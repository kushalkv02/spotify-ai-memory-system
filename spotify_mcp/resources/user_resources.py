from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..adapters.graph_adapter import GraphAdapter
from ..utils.formatting import to_text


def register(mcp: FastMCP, adapter: GraphAdapter) -> None:
    @mcp.resource("spotify://user/{user_id}/profile")
    def user_profile(user_id: str) -> str:
        """A user's profile plus their derived preferences, as context."""
        return to_text(
            {
                "user": adapter.get_user(user_id),
                "preferences": adapter.get_preferences(user_id),
            }
        )

    @mcp.resource("spotify://user/{user_id}/recent-memories")
    def user_recent_memories(user_id: str) -> str:
        """A user's most recent memories, as context."""
        return to_text(adapter.recent_memories(user_id, limit=10))
