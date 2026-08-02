"""Tools for reading/creating Track nodes."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..adapters.graph_adapter import GraphAdapter
from ..utils.formatting import to_text


def register(mcp: FastMCP, adapter: GraphAdapter) -> None:
    @mcp.tool()
    def search_tracks(query: str, limit: int = 10) -> str:
        """Search tracks by (partial, case-insensitive) title."""
        return to_text(adapter.search_tracks(query, limit=limit))

    @mcp.tool()
    def create_track(track_id: str, title: str) -> str:
        """Create (or update) a Track node. Idempotent — safe to call repeatedly."""
        return to_text(adapter.ensure_track(track_id, title))
