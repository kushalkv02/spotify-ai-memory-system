"""
Builds a Memory from a batch of recent playback events. This is a
deterministic placeholder for the "Memory Generator (LLM Summary)"
step in your architecture diagram — swap `_summarize` for an actual
LLM call once that's wired up; everything downstream (embedding,
graph write) stays the same.
"""
from __future__ import annotations

from typing import Any

from ..services.memory_service import MemoryService


def _summarize(user_id: str, plays: list[dict[str, Any]]) -> str:
    if not plays:
        return f"No recent activity for {user_id}."
    titles = ", ".join(p.get("title", p.get("track_id", "?")) for p in plays[:5])
    return f"User recently played: {titles}."


def build_memory_from_recent_plays(user_id: str, plays: list[dict[str, Any]]) -> dict[str, Any]:
    summary = _summarize(user_id, plays)
    track_ids = [p["track_id"] for p in plays if "track_id" in p]
    service = MemoryService()
    return service.store_memory(user_id=user_id, summary=summary, track_ids=track_ids)
