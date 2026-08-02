"""Tools for storing/reading Memory nodes (the LLM-facing memory system)."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..adapters.graph_adapter import GraphAdapter
from ..schemas.tool_schemas import StoreMemoryInput
from ..utils.formatting import to_text


def register(mcp: FastMCP, adapter: GraphAdapter) -> None:
    @mcp.tool()
    def store_memory(payload: StoreMemoryInput) -> str:
        """
        Persist a memory about a user (already summarized/judged
        important upstream) and link it to the tracks it references.
        """
        result = adapter.store_memory(
            user_id=payload.user_id,
            summary=payload.summary,
            importance=payload.importance,
            track_ids=payload.track_ids,
        )
        return to_text(result)

    @mcp.tool()
    def get_recent_memories(user_id: str, limit: int = 20) -> str:
        """Get a user's most recent memories, most recent first."""
        return to_text(adapter.recent_memories(user_id, limit=limit))

    @mcp.tool()
    def get_memory(memory_id: str) -> str:
        """Get one memory by its stable memory ID."""
        return to_text(adapter.get_memory(memory_id))

    @mcp.tool()
    def get_memories_referencing_track(track_id: str, limit: int = 20) -> str:
        """Get memories that explicitly reference a track."""
        return to_text(adapter.memories_referencing_track(track_id, limit=limit))

    @mcp.tool()
    def delete_memory(memory_id: str) -> str:
        """Permanently delete a memory and its graph relationships."""
        return to_text(adapter.delete_memory(memory_id))
