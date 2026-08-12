"""
Turns a reasoning path (from ReasoningService) into a short, human
readable explanation string — the thing that eventually gets handed
to GPT/Claude/Gemini in the MCP layer as grounding context, or shown
directly to the user ("recommended because you loved Currents").
"""
from __future__ import annotations

from typing import Any


class ExplanationService:
    def explain_recommendations(
        self, *, recommendations: list[dict[str, Any]], preferences: list[dict[str, Any]],
        recent_plays: list[dict[str, Any]], recent_skips: list[dict[str, Any]],
    ) -> str:
        """Compose explanations from all available graph evidence.

        Recommendation rows may come from collaborative, artist, or genre
        strategies. Each strategy is allowed to contribute one explanation;
        the preference/recent-history text is used only when those graph
        relationships do not provide a more specific reason.
        """
        explanations: list[str] = []
        seed_by_artist = {
            str(item.get("artist_id") or item.get("artist")): item
            for item in recent_plays
            if item.get("artist_id") or item.get("artist")
        }
        for recommendation in recommendations:
            artist = recommendation.get("artist") or recommendation.get("artist_name")
            shared = recommendation.get("shared_listeners")
            if shared:
                explanations.append(self.explain_collaborative(int(shared)))
                continue
            if artist and artist in seed_by_artist:
                seed = seed_by_artist[artist].get("title") or seed_by_artist[artist].get("track_id")
                if seed:
                    explanations.append(self.explain_shared_artist(str(artist), str(seed)))
            elif artist:
                # Artist-affinity queries return the artist but not a seed;
                # use the listener's latest played title as the seed context.
                seed = next((item.get("title") for item in recent_plays if item.get("title")), None)
                if seed:
                    explanations.append(self.explain_shared_artist(str(artist), str(seed)))
            if len(explanations) >= 2:
                break
        if explanations:
            return " ".join(dict.fromkeys(explanations))
        liked = next((item for item in preferences if item.get("sentiment") == "like" and item.get("value")), None)
        if liked:
            return f"Recommended using your saved preference for {liked['value']}."
        if recent_plays:
            title = recent_plays[0].get("title") or recent_plays[0].get("track_id")
            if title:
                return f"Recommended from your recent listening, including {title}."
        if recent_skips:
            title = recent_skips[0].get("title") or recent_skips[0].get("track_id")
            if title:
                return f"Recommended while avoiding patterns from recent skips, including {title}."
        return "Recommended from the highest-ranked available tracks." if recommendations else "No recommendation evidence is available yet."

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
