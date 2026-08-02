"""
Walks the graph to find WHY a track is connected to a user — the
connective tissue between a recommendation and its explanation.
"""
from __future__ import annotations

from typing import Any

from ..neo4j_client import get_client
from ..queries.temporal_queries import RECENT_PLAY_TIMELINE_QUERY


class ReasoningService:
    def __init__(self) -> None:
        self.client = get_client()

    def listening_timeline(self, user_id: str, days: int = 30) -> list[dict[str, Any]]:
        return self.client.execute_read(
            RECENT_PLAY_TIMELINE_QUERY, {"user_id": user_id, "days": days}
        )
