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


def _first_text(*values: Any) -> Optional[str]:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


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
        return self.reasoning.get_recent_plays(user_id, limit=limit)

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

    def structured_recommendation_reply(
        self, user_id: str, intent: str = "", genre: Optional[str] = None, limit: int = 3
    ) -> dict[str, Any]:
        """Build a Claude-ready recommendation response from graph evidence.

        The MCP host still owns the final wording, but this gives it a stable
        response framework with the same graph-backed ingredients every time.
        """
        safe_limit = max(1, min(limit, 10))
        preferences = self.preference.get_preferences(user_id)
        recent_plays = self.reasoning.get_recent_plays(user_id, limit=20)
        recent_skips = self.reasoning.get_recent_skips(user_id, limit=20)
        memories = self.memory.retrieve(user_id, intent=intent or genre or "", limit=5)

        recommendations: list[dict[str, Any]] = []
        strategies = (
            self.recommendation.by_genre_affinity,
            self.recommendation.by_artist_affinity,
            self.recommendation.collaborative,
            self.recommendation.by_mood,
        )
        for strategy in strategies:
            recommendations.extend(strategy(user_id, limit=safe_limit))

        unique_recommendations: list[dict[str, Any]] = []
        seen_track_ids: set[str] = set()
        for item in recommendations:
            track_id = _first_text(item.get("track_id"), item.get("id"))
            if track_id and track_id in seen_track_ids:
                continue
            if track_id:
                seen_track_ids.add(track_id)
            unique_recommendations.append(item)
            if len(unique_recommendations) >= safe_limit:
                break

        saved_genre = genre or self._saved_genre(preferences, recent_plays, unique_recommendations)
        example_songs = self._example_song_titles(unique_recommendations, recent_plays, limit=2)
        opening = self._structured_opening(saved_genre, example_songs)
        reasoning = self.explanation.explain_recommendations(
            recommendations=unique_recommendations,
            preferences=preferences,
            recent_plays=recent_plays,
            recent_skips=recent_skips,
        )
        music_recommendations = [
            {
                "track_id": item.get("track_id"),
                "title": item.get("title"),
                "artist": _first_text(item.get("artist"), item.get("artist_name"), item.get("artistName")),
                "genre": item.get("genre"),
                "mood": item.get("mood"),
            }
            for item in unique_recommendations
        ]
        memory_context = [
            {
                "summary": item.get("summary"),
                "strength": item.get("strength") or item.get("importance"),
            }
            for item in memories
            if item.get("summary")
        ]
        reply_markdown = self._structured_reply_markdown(
            opening=opening,
            recommendations=music_recommendations,
            reasoning=reasoning,
        )
        return {
            "reply_framework": {
                "opening": opening,
                "music_recommendations_heading": "music recommendations -",
                "reasonings_heading": "reasonings -",
            },
            "reply_markdown": reply_markdown,
            "music_recommendations": music_recommendations,
            "reasonings": [reasoning] if reasoning else [],
            "evidence": {
                "saved_genre": saved_genre,
                "example_songs": example_songs,
                "preferences": preferences,
                "memories": memory_context,
                "recent_plays": recent_plays[:5],
                "recent_skips": recent_skips[:5],
            },
            "instructions_for_host": (
                "Use reply_markdown as the default user-facing response. Keep the "
                "three sections in this order when rewriting: opening, music "
                "recommendations, reasonings."
            ),
        }

    # -- reasoning / explanation --------------------------------------------
    def listening_timeline(self, user_id: str, days: int = 30) -> list[dict[str, Any]]:
        return self.reasoning.listening_timeline(user_id, days=days)

    def get_genre_affinity(self, user_id: str) -> list[dict[str, Any]]:
        return self.reasoning.genre_affinity(user_id)

    def get_mood_affinity(self, user_id: str) -> list[dict[str, Any]]:
        return self.reasoning.mood_affinity(user_id)

    def explain_recommendations(self, user_id: str, limit: int = 10) -> str:
        """Explain graph-native recommendations for an MCP host."""
        recommendations: list[dict[str, Any]] = []
        for strategy in (
            self.recommendation.collaborative,
            self.recommendation.by_artist_affinity,
            self.recommendation.by_genre_affinity,
        ):
            recommendations.extend(strategy(user_id, limit=limit))
        unique = {item.get("track_id"): item for item in recommendations if item.get("track_id")}
        recent_plays = self.reasoning.get_recent_plays(user_id, limit=20)
        recent_skips = self.reasoning.get_recent_skips(user_id, limit=20)
        return self.explanation.explain_recommendations(
            recommendations=list(unique.values())[:limit],
            preferences=self.preference.get_preferences(user_id),
            recent_plays=recent_plays, recent_skips=recent_skips,
        )

    @staticmethod
    def _saved_genre(
        preferences: list[dict[str, Any]], recent_plays: list[dict[str, Any]],
        recommendations: list[dict[str, Any]],
    ) -> str:
        liked_genre = next(
            (
                item.get("value")
                for item in preferences
                if item.get("kind") == "genre"
                and item.get("sentiment") == "like"
                and item.get("value")
            ),
            None,
        )
        if liked_genre:
            return str(liked_genre)
        genre = next((item.get("genre") for item in recent_plays if item.get("genre")), None)
        if genre:
            return str(genre)
        genre = next((item.get("genre") for item in recommendations if item.get("genre")), None)
        return str(genre) if genre else "music"

    @staticmethod
    def _example_song_titles(
        recommendations: list[dict[str, Any]], recent_plays: list[dict[str, Any]], limit: int = 2
    ) -> list[str]:
        titles: list[str] = []
        for source in (recommendations, recent_plays):
            for item in source:
                title = _first_text(item.get("title"), item.get("track_title"))
                if title and title not in titles:
                    titles.append(title)
                if len(titles) >= limit:
                    return titles
        return titles

    @staticmethod
    def _structured_opening(saved_genre: str, example_songs: list[str]) -> str:
        if len(example_songs) >= 2:
            return (
                f"I've got {saved_genre} saved! Which {saved_genre} artists do you like? "
                f"For example, {example_songs[0]} or {example_songs[1]}?"
            )
        if example_songs:
            return (
                f"I've got {saved_genre} saved! Which {saved_genre} artists do you like? "
                f"For example, artists like the ones behind {example_songs[0]}?"
            )
        return f"I've got {saved_genre} saved! Which {saved_genre} artists do you like?"

    @staticmethod
    def _structured_reply_markdown(
        opening: str, recommendations: list[dict[str, Any]], reasoning: str
    ) -> str:
        if recommendations:
            rec_lines = [
                "- "
                + " - ".join(
                    part for part in (_first_text(item.get("title")), _first_text(item.get("artist"))) if part
                )
                for item in recommendations
            ]
        else:
            rec_lines = ["- No graph-backed recommendations are available yet."]
        reasoning_lines = [f"- {reasoning}"] if reasoning else ["- No recommendation reasoning is available yet."]
        return "\n\n".join(
            [
                opening,
                "music recommendations -\n" + "\n".join(rec_lines),
                "reasonings -\n" + "\n".join(reasoning_lines),
            ]
        )

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
        return self.reasoning.get_recent_skips(user_id, limit=limit)

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
