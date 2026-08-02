"""Tools for reading/creating User nodes."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..adapters.graph_adapter import GraphAdapter
from ..utils.formatting import to_text


def register(mcp: FastMCP, adapter: GraphAdapter) -> None:
    @mcp.tool()
    def get_user(user_id: str) -> str:
        """Fetch a user's profile node by id."""
        return to_text(adapter.get_user(user_id))

    @mcp.tool()
    def create_user(user_id: str, display_name: str) -> str:
        """Create (or update) a User node. Idempotent — safe to call repeatedly."""
        return to_text(adapter.ensure_user(user_id, display_name))
