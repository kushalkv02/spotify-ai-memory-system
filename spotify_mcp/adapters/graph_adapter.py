"""
GraphAdapter is the ONLY place in spotify_mcp that imports from `graph`.

Why this boundary exists:
  - tools/*.py stay MCP-shaped (input schema in, text content out) and
    never see a graph Node, a Cypher string, or a repository.
  - If the graph package's internals change, only this file changes.
  - It's the one place to add cross-cutting concerns later (caching,
    consent checks, rate limiting) without touching every tool.

Call flow through this file:
  tools/*.py  -->  GraphAdapter method  -->  graph/services/*.py
                                          --> graph/repositories/*.py
                                          --> graph/neo4j_client.py --> Neo4j
"""
from __future__ import annotations

from typing import Any, Optional

from graph.repositories.engagement_repository import EngagementRepository
from graph.repositories.playback_repository import PlaybackRepository
from graph.repositories.track_repository import TrackRepository
from graph.repositories.user_repository import UserRepository
from graph.services.explanation_service import ExplanationService
from graph.services.graph_service import get_graph_service
from graph.services.memory_service import MemoryService
from graph.services.preference_service import PreferenceService
from graph.services.reasoning_service import ReasoningService
from graph.services.recommendation_service import RecommendationService


class GraphAdapter:
    """Facade over every graph service/repository the MCP tools need."""

    def __init__(self) -> None:
        self.graph = get_graph_service()
        self.memory = MemoryService()
        self.preference = PreferenceService()
        self.recommendation = RecommendationService()
        self.reasoning = ReasoningService()
        self.explanation = ExplanationService()

        self.users = UserRepository()
        self.tracks = TrackRepository()
        self.playback = PlaybackRepository()
        self.engagement = EngagementRepository()

    # -- playback -----------------------------------------------------------
    def record_play(
        self,
        user_id: str,
        track_id: str,
        user_display_name: Optional[str] = None,
        track_title: Optional[str] = None,
        ms_played: Optional[int] = None,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        return self.graph.record_play_event(
            user_id=user_id,
            track_id=track_id,
            user_display_name=user_display_name,
            track_title=track_title,
            ms_played=ms_played,
            context=context,
            session_id=session_id,
        )

    def recent_plays(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.playback.get_recent_plays(user_id, limit=limit)

    # -- users / tracks -----------------------------------------------------
    def get_user(self, user_id: str) -> Optional[dict[str, Any]]:
        return self.users.get_user(user_id)

    def ensure_user(self, user_id: str, display_name: str) -> dict[str, Any]:
        return self.graph.ensure_user(user_id, display_name)

    def search_tracks(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return self.tracks.search_by_title(query, limit=limit)

    def ensure_track(self, track_id: str, title: str) -> dict[str, Any]:
        return self.graph.ensure_track(track_id, title)

    # -- memory ---------------------------------------------------------
    def store_memory(
        self,
        user_id: str,
        summary: str,
        importance: float = 0.5,
        track_ids: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        return self.memory.store_memory(user_id, summary, importance, track_ids)

    def recent_memories(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.memory.recent_memories(user_id, limit=limit)

    def get_memory(self, user_id: str, version_id: str) -> Optional[dict[str, Any]]:
        return self.memory.get_memory(user_id, version_id)

    def memories_referencing_track(
        self, user_id: str, track_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        return self.memory.memories_referencing_track(user_id, track_id, limit=limit)

    def expire_memory(self, user_id: str, version_id: str) -> dict[str, Any]:
        return {"version_id": version_id, "expired": self.memory.expire_memory(user_id, version_id)}

    def correct_memory(
        self, user_id: str, previous_version_id: str, summary: str, contradiction: bool = False
    ) -> dict[str, Any]:
        return self.memory.correct_memory(
            user_id, previous_version_id, summary, contradiction=contradiction
        )

    def retrieve_memories(
        self, user_id: str, intent: str = "", related_track_ids: Optional[list[str]] = None,
        limit: int = 8, context_budget: int = 1800,
    ) -> list[dict[str, Any]]:
        return self.memory.retrieve(
            user_id, intent=intent, related_track_ids=related_track_ids,
            limit=limit, context_budget=context_budget,
        )

    # -- preferences -----------------------------------------------------
    def get_preferences(self, user_id: str) -> list[dict[str, Any]]:
        return self.preference.get_preferences(user_id)

    # -- recommendations -----------------------------------------------------
    def recommend_collaborative(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self.recommendation.collaborative(user_id, limit=limit)

    def recommend_by_artist(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self.recommendation.by_artist_affinity(user_id, limit=limit)

    def recommend_by_genre(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self.recommendation.by_genre_affinity(user_id, limit=limit)

    def recommend_by_mood(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self.recommendation.by_mood(user_id, limit=limit)

    # -- reasoning / explanation --------------------------------------------
    def listening_timeline(self, user_id: str, days: int = 30) -> list[dict[str, Any]]:
        return self.reasoning.listening_timeline(user_id, days=days)

    def get_genre_affinity(self, user_id: str) -> list[dict[str, Any]]:
        return self.reasoning.genre_affinity(user_id)

    def get_mood_affinity(self, user_id: str) -> list[dict[str, Any]]:
        return self.reasoning.mood_affinity(user_id)

    # -- likes -----------------------------------------------------------
    def like_track(
        self,
        user_id: str,
        track_id: str,
        user_display_name: Optional[str] = None,
        track_title: Optional[str] = None,
    ) -> dict[str, Any]:
        return self.graph.like_track(
            user_id=user_id,
            track_id=track_id,
            user_display_name=user_display_name,
            track_title=track_title,
        )

    def unlike_track(self, user_id: str, track_id: str) -> dict[str, Any]:
        self.graph.unlike_track(user_id=user_id, track_id=track_id)
        return {"user_id": user_id, "track_id": track_id, "liked": False}

    def get_liked_tracks(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return self.engagement.get_liked_tracks(user_id, limit=limit)

    # -- skips -----------------------------------------------------------
    def record_skip(
        self,
        user_id: str,
        track_id: str,
        user_display_name: Optional[str] = None,
        track_title: Optional[str] = None,
        ms_played: Optional[int] = None,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        return self.graph.record_skip_event(
            user_id=user_id,
            track_id=track_id,
            user_display_name=user_display_name,
            track_title=track_title,
            ms_played=ms_played,
            context=context,
            session_id=session_id,
        )

    def get_recent_skips(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.engagement.get_recent_skips(user_id, limit=limit)

    # -- follows -----------------------------------------------------------
    def follow_artist(
        self,
        user_id: str,
        artist_id: str,
        user_display_name: Optional[str] = None,
        artist_name: Optional[str] = None,
    ) -> dict[str, Any]:
        return self.graph.follow_artist(
            user_id=user_id,
            artist_id=artist_id,
            user_display_name=user_display_name,
            artist_name=artist_name,
        )

    def unfollow_artist(self, user_id: str, artist_id: str) -> dict[str, Any]:
        self.graph.unfollow_artist(user_id=user_id, artist_id=artist_id)
        return {"user_id": user_id, "artist_id": artist_id, "followed": False}

    def get_followed_artists(self, user_id: str) -> list[dict[str, Any]]:
        return self.engagement.get_followed_artists(user_id)


_adapter: Optional[GraphAdapter] = None


def get_graph_adapter() -> GraphAdapter:
    """Process-wide singleton, same pattern as get_graph_service()."""
    global _adapter
    if _adapter is None:
        _adapter = GraphAdapter()
    return _adapter
