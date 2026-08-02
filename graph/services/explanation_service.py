"""
Turns a reasoning path (from ReasoningService) into a short, human
readable explanation string — the thing that eventually gets handed
to GPT/Claude/Gemini in the MCP layer as grounding context, or shown
directly to the user ("recommended because you loved Currents").
"""
from __future__ import annotations


class ExplanationService:
    def explain_shared_artist(self, artist_name: str, seed_track_title: str) -> str:
        return (
            f"Recommended because you've been listening to \"{seed_track_title}\", "
            f"and this track is also by {artist_name}."
        )

    def explain_collaborative(self, shared_listeners: int) -> str:
        return (
            f"Recommended because {shared_listeners} listener(s) with similar taste "
            "to yours also played this track."
        )
