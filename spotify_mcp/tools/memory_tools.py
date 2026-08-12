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
        print(f"Retrieving {limit} recent memories for user {user_id}")
        return to_text(adapter.recent_memories(user_id, limit=limit))

    @mcp.tool()
    def get_memory(user_id: str, version_id: str) -> str:
        """Get one memory assertion inside the requesting user's identity scope."""
        return to_text(adapter.get_memory(user_id, version_id))

    @mcp.tool()
    def get_memories_referencing_track(user_id: str, track_id: str, limit: int = 20) -> str:
        """Get current memories for one user that explicitly reference a track."""
        return to_text(adapter.memories_referencing_track(user_id, track_id, limit=limit))

    @mcp.tool()
    def expire_memory(user_id: str, version_id: str) -> str:
        """Expire a memory assertion without erasing its audit history."""
        return to_text(adapter.expire_memory(user_id, version_id))

    @mcp.tool()
    def correct_memory(user_id: str, previous_version_id: str, summary: str, contradiction: bool = False) -> str:
        """Append a correction (or contradiction) while retaining the prior assertion."""
        return to_text(adapter.correct_memory(user_id, previous_version_id, summary, contradiction))

    @mcp.tool()
    def retrieve_memories(
        user_id: str, intent: str = "", related_track_ids: list[str] | None = None,
        limit: int = 8, context_budget: int = 1800,
    ) -> str:
        """Build a scoped, diverse hybrid-retrieval memory context pack."""
        return to_text(adapter.retrieve_memories(user_id, intent, related_track_ids, limit, context_budget))
