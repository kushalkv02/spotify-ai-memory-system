"""
Tools for the core interaction event: a user playing a track.
This is the MCP-facing entry point onto GraphService.record_play_event.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..adapters.graph_adapter import GraphAdapter
from ..schemas.tool_schemas import RecordPlayInput
from ..utils.formatting import to_text


def register(mcp: FastMCP, adapter: GraphAdapter) -> None:
    @mcp.tool()
    def record_play(payload: RecordPlayInput) -> str:
        """
        Record that a user played a track, writing a
        (User)-[:PLAYED]->(Track) event to the graph. Pass
        user_display_name / track_title the first time you see a new
        user_id / track_id so the nodes get created.
        """
        result = adapter.record_play(
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
    def get_recent_plays(user_id: str, limit: int = 20) -> str:
        """Get a user's most recent play events, most recent first."""
        return to_text(adapter.recent_plays(user_id, limit=limit))
