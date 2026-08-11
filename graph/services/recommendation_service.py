"""
Simple, graph-native recommendation strategies. These use the raw
Cypher in graph/cypher/queries/recommendations.cypher (mirrored here
as Python strings in graph/queries/recommendation_queries.py) rather
than an LLM — good enough as a baseline before the MCP/LLM layer in
your architecture diagram is wired up.
"""
from __future__ import annotations

from typing import Any

from ..neo4j_client import get_client
from ..queries.recommendation_queries import (
    ARTIST_AFFINITY_QUERY,
    COLLABORATIVE_FILTER_QUERY,
    GENRE_AFFINITY_QUERY,
    MOOD_AFFINITY_QUERY,
    RECENT_PLAY_TIMELINE_QUERY,
)


class RecommendationService:
    def __init__(self) -> None:
        self.client = get_client()

    def collaborative(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self.client.execute_read(
            COLLABORATIVE_FILTER_QUERY, {"user_id": user_id, "limit": limit}
        )

    def by_artist_affinity(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self.client.execute_read(
            ARTIST_AFFINITY_QUERY, {"user_id": user_id, "limit": limit}
        )

    def by_genre_affinity(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Recommend unplayed tracks from genres present in the user's history."""
        return self.client.execute_read(
            GENRE_AFFINITY_QUERY, {"user_id": user_id, "limit": limit}
        )

    def by_mood(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Recommend tracks by mood."""
        # Placeholder implementation; replace with actual mood-based recommendation logic
        return self.client.execute_read(
            MOOD_AFFINITY_QUERY, {"user_id": user_id, "limit": limit}
        )

    def listening_timeline(self, user_id: str, days: int = 30) -> list[dict[str, Any]]:
        """Return a timeline of the user's listening history."""
        return self.client.execute_read(
            RECENT_PLAY_TIMELINE_QUERY, {"user_id": user_id, "days": days}
        )
