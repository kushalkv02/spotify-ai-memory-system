"""
Walks the graph to find WHY a track is connected to a user — the
connective tissue between a recommendation and its explanation.
"""
from __future__ import annotations

from typing import Any

from ..neo4j_client import get_client
from ..queries.temporal_queries import RECENT_PLAY_TIMELINE_QUERY
from ..queries.reasoning_queries import (GENRE_AFFINITY_REASONING_QUERY, MOOD_AFFINITY_REASONING_QUERY)
from ..repositories.engagement_repository import EngagementRepository
from ..repositories.playback_repository import PlaybackRepository


class ReasoningService:
    def __init__(self) -> None:
        self.client = get_client()
        self.playback = PlaybackRepository()
        self.engagement = EngagementRepository()

    def get_recent_plays(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent play evidence through the reasoning boundary."""
        return self.playback.get_recent_plays(user_id, limit=limit)

    def get_recent_skips(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent skip evidence through the reasoning boundary."""
        return self.engagement.get_recent_skips(user_id, limit=limit)

    def listening_timeline(self, user_id: str, days: int = 30) -> list[dict[str, Any]]:
        return self.client.execute_read(
            RECENT_PLAY_TIMELINE_QUERY, {"user_id": user_id, "days": days}
        )

    def genre_affinity(self, user_id: str) -> list[dict[str, Any]]:
        """Aggregate play-count by genre so the LLM can explain genre biases."""
        return self.client.execute_read(
            GENRE_AFFINITY_REASONING_QUERY, {"user_id": user_id}
        )

    def mood_affinity(self, user_id: str) -> list[dict[str, Any]]:
        """Aggregate play-count by mood so the LLM can explain mood biases."""
        return self.client.execute_read(
            MOOD_AFFINITY_REASONING_QUERY, {"user_id": user_id}
        )
