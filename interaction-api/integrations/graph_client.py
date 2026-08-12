"""
Bridge between interaction-api and the already-built `graph` package.

`graph/` and `spotify_mcp/` are sibling folders under spotify-mem-sys/, not
nested inside interaction-api/. For `from graph...` imports to resolve at
runtime you need ONE of:

  1. Run uvicorn from the spotify-mem-sys/ repo root (so it's on sys.path), e.g.:
         cd spotify-mem-sys && uvicorn interaction-api.api.main:app --reload
  2. Add the repo root to PYTHONPATH:
         export PYTHONPATH=/path/to/spotify-mem-sys:$PYTHONPATH
  3. Package `graph` (add a pyproject.toml/setup.py to it) and
         pip install -e ../graph

Why this exists at all: interaction-api doesn't call spotify_mcp directly.
spotify_mcp reads from Neo4j via graph.repositories / graph.services already.
So the way interaction-api "connects" to the MCP server is indirect and
correct: interaction-api writes through the SAME graph package into the
SAME Neo4j database that spotify_mcp's tools read from. Once an event is
written here, it should be visible to `spotify_mcp` tools (e.g.
memory_tools.py, recommendation_tools.py) on their next query — no direct
network call between the two services is needed.

The adapter calls the public graph-service APIs directly.  It intentionally
keeps the interaction API independent of Neo4j repositories and Cypher.
"""
import asyncio
from typing import Any, Optional
from datetime import datetime, timezone
from uuid import uuid4

from ..models.event import RawEventRecord
from ..utils.exceptions import GraphWritebackError
from ..utils.logger import get_logger
from ..config import settings
import traceback
logger = get_logger(__name__)

_graph_available = False
try:
    # These imports assume spotify-mem-sys/ root is on sys.path (see docstring above).
    from graph.services.interaction_service import InteractionService as GraphInteractionService
    from graph.services.memory_service import MemoryService as GraphMemoryService
    from graph.services.preference_service import PreferenceService as GraphPreferenceService
    from graph.services.recommendation_service import RecommendationService as GraphRecommendationService
    from graph.services.reasoning_service import ReasoningService as GraphReasoningService
    from graph.services.explanation_service import ExplanationService as GraphExplanationService
    from graph.neo4j_client import Neo4jClient

    _graph_available = True
except ImportError as exc:  # pragma: no cover
    logger.warning(
        "Could not import `graph` package (%s). Graph writeback is disabled; "
        "events will still persist to Postgres. See integrations/graph_client.py "
        "docstring to fix import paths.",
        exc,
    )


class GraphClient:
    """Thin adapter interaction-api uses to push data into the graph package.

    Kept separate from the raw graph.services classes so routes/services in
    interaction-api don't need to know graph's internal API shape directly.
    """

    def __init__(self):
        self.enabled = settings.enable_graph_writeback and _graph_available
        if self.enabled:
            # TODO: confirm these constructors match your actual Neo4jClient /
            # service classes (e.g. some may need a shared driver instance
            # passed in rather than constructing their own).
            self._neo4j_client = Neo4jClient()
            self._interaction_service = GraphInteractionService()
            self._memory_service = GraphMemoryService()
            self._preference_service = GraphPreferenceService()
            self._recommendation_service = GraphRecommendationService()
            self._reasoning_service = GraphReasoningService()
            self._explanation_service = GraphExplanationService()

    async def record_interaction(self, event: RawEventRecord) -> None:
        """Write a raw interaction into the graph (e.g. (:User)-[:PERFORMED]->(:Interaction)).

        Called for every event regardless of importance, mirroring how
        graph/cypher/seed/interactions_seed.cypher models interaction nodes.
        """
        if not self.enabled:
            return
        try:
            await self._interaction_service.handle_event(
                user_id=event.user_id,
                category=event.category,
                payload=event.payload,
                occurred_at=event.occurred_at,
            )
        except Exception as exc:
            # Non-fatal: the event is already safely in Postgres.
            logger.exception("Graph writeback (record_interaction) failed")
            print(traceback.format_exc())
            raise

    async def create_memory(self, event: RawEventRecord, summary_text: str, tags: Optional[list[str]] = None) -> None:
        """Write an LLM-generated memory node + link it to the source interaction.

        Called only for events the (future) Memory Decision Engine marks
        'important'. Today, interaction_routes.py calls this with a naive
        placeholder summary until memory-decision-engine/memory_generator
        is wired in for real.
        """
        if not self.enabled:
            return
        try:
            self._memory_service.store_memory(
                user_id=event.user_id,
                summary=summary_text,
                importance=event.importance_score or 0.5,
                track_ids=[event.payload["track_id"]] if event.payload.get("track_id") else [],
                source_event_id=str(event.event_id),
                source=f"event:{event.category}",
                confidence=event.importance_score or 0.5,
                explicitness=1.0 if event.payload.get("explicit_preference") else 0.0,
                subject_scope=event.subject_scope,
                source_action=event.payload.get("action") or event.payload.get("action_type"),
                entity_type=("track" if event.payload.get("track_id") else "artist" if event.payload.get("artist_id") else None),
                entity_id=event.payload.get("track_id") or event.payload.get("artist_id"),
            )
        except Exception as exc:
            logger.error("Graph writeback (create_memory) failed: %s", exc)
            raise GraphWritebackError(str(exc)) from exc

    async def remove_state_memories(self, event: RawEventRecord) -> int:
        """Expire retrievable memories created by a reversed state action."""
        if not self.enabled:
            return 0
        action = event.payload.get("action") or event.payload.get("action_type")
        entity_type = "track" if action == "unlike" else "artist" if action == "unfollow_artist" else None
        entity_id = event.payload.get("track_id") or event.payload.get("artist_id")
        if not entity_type or not entity_id:
            return 0
        try:
            return await asyncio.to_thread(
                self._memory_service.expire_state_memories,
                event.user_id, entity_type=entity_type, entity_id=str(entity_id),
            )
        except Exception as exc:
            logger.error("Graph writeback (remove_state_memories) failed: %s", exc)
            raise GraphWritebackError(str(exc)) from exc

    async def fallback_explanation(
        self, *, recommendations: list[dict[str, Any]], preferences: list[dict[str, Any]],
        reasoning: list[dict[str, Any]], user_id: str,
    ) -> str:
        """Use deterministic graph explanations when Gemini cannot respond."""
        recent_plays = reasoning
        recent_skips: list[dict[str, Any]] = []
        if not self.enabled:
            return "Recommended from the highest-ranked available tracks."
        try:
            recent_plays, recent_skips = await asyncio.gather(
                asyncio.to_thread(self._reasoning_service.get_recent_plays, user_id, 20),
                asyncio.to_thread(self._reasoning_service.get_recent_skips, user_id, 20),
            )
        except Exception as exc:
            logger.warning("Detailed reasoning evidence unavailable for fallback: %s", exc)
        
        return self._explanation_service.explain_recommendations(
            recommendations=recommendations, preferences=preferences,
            recent_plays=recent_plays, recent_skips=recent_skips,
        )

    async def update_preferences_from_event(self, event: RawEventRecord) -> None:
        """Update (:User)-[:PREFERS]->(:Artist|:Genre) style edges from
        explicit signals (like/dislike/add_to_playlist) in the event payload.
        """
        if not self.enabled:
            return
        try:
            self._preference_service.recompute_genre_preferences(event.user_id)
        except Exception as exc:
            logger.error("Graph writeback (update_preferences_from_event) failed: %s", exc)
            raise GraphWritebackError(str(exc)) from exc

    async def set_explicit_preference(
        self,
        *,
        user_id: str,
        kind: str,
        value: str,
        sentiment: str,
        strength: float | None,
    ) -> dict[str, Any]:
        """Upsert a preference explicitly declared by the user."""
        if not self.enabled:
            return {
                "user_id": user_id,
                "kind": kind,
                "value": value,
                "sentiment": sentiment,
                "strength": strength if strength is not None else (1.0 if sentiment == "like" else 0.0),
            }
        try:
            return self._preference_service.set_explicit_preference(
                user_id=user_id,
                kind=kind,
                value=value,
                sentiment=sentiment,
                strength=strength,
            )
        except Exception as exc:
            logger.error("Graph writeback (set_explicit_preference) failed: %s", exc)
            raise GraphWritebackError(str(exc)) from exc

    async def recommendations_for_user(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Collect graph-native strategies without making recommendations unavailable.

        The client-state ranker blends these with the fresh chat preference
        projection, so chat changes are visible immediately even if Neo4j is
        temporarily offline.
        """
        if not self.enabled:
            return []
        try:
            results: list[dict[str, Any]] = []
            for strategy in (
                self._recommendation_service.collaborative,
                self._recommendation_service.by_artist_affinity,
                self._recommendation_service.by_genre_affinity,
            ):
                results.extend(strategy(user_id, limit=limit))
            unique: dict[str, dict[str, Any]] = {}
            for item in results:
                if item.get("track_id"):
                    unique.setdefault(item["track_id"], item)
            return list(unique.values())[:limit]
        except Exception as exc:
            logger.warning("Graph recommendations unavailable: %s", exc)
            return []

    async def recommendation_evidence_for_user(
        self, user_id: str, intent: str, *, recommendation_limit: int = 12,
        memory_limit: int = 6, preference_limit: int = 12, reasoning_days: int = 30,
        reasoning_limit: int = 12,
    ) -> dict[str, Any]:
        """Read all Neo4j evidence required for a Gemini recommendation turn.

        Unlike the individual best-effort helpers, this is deliberately
        fail-closed: Gemini must not be described as graph-grounded when the
        graph integration is disabled or one of its required reads fails.
        Empty lists are valid for a new listener; an unavailable graph is not.
        """
        if not self.enabled:
            raise GraphWritebackError(
                "Neo4j graph integration is disabled or the graph package could not be loaded"
            )
        try:
            return await asyncio.to_thread(
                self._recommendation_evidence_for_user,
                user_id,
                intent,
                recommendation_limit,
                memory_limit,
                preference_limit,
                reasoning_days,
                reasoning_limit,
            )
        except Exception as exc:
            logger.error("Required Neo4j recommendation evidence is unavailable: %s", exc)
            raise GraphWritebackError("Required Neo4j recommendation evidence is unavailable") from exc

    def _recommendation_evidence_for_user(
        self, user_id: str, intent: str, recommendation_limit: int,
        memory_limit: int, preference_limit: int, reasoning_days: int,
        reasoning_limit: int,
    ) -> dict[str, Any]:
        recommendation_results: list[dict[str, Any]] = []
        for strategy in (
            self._recommendation_service.collaborative,
            self._recommendation_service.by_artist_affinity,
            self._recommendation_service.by_genre_affinity,
        ):
            recommendation_results.extend(strategy(user_id, limit=recommendation_limit))
        unique_recommendations: dict[str, dict[str, Any]] = {}
        for item in recommendation_results:
            if item.get("track_id"):
                unique_recommendations.setdefault(item["track_id"], item)

        memories = self._memory_service.retrieve(
            user_id, intent=intent, surface="chat", limit=memory_limit, context_budget=1200,
        )
        preferences = self._preference_service.get_preferences(user_id)
        reasoning = self._reasoning_service.listening_timeline(user_id, days=reasoning_days)
        explanation = self._explanation_service.explain_recommendations(
            recommendations=list(unique_recommendations.values())[:recommendation_limit],
            preferences=[item for item in preferences[:preference_limit] if item.get("value")],
            recent_plays=reasoning[:reasoning_limit], recent_skips=[],
        )
        return {
            "graph_recommendations": list(unique_recommendations.values())[:recommendation_limit],
            "memory_context": [
                {
                    "summary": item.get("summary", ""),
                    "strength": round(float(item.get("importance", .5)) * float(item.get("confidence", 1)), 3),
                    "memory_class": item.get("source", "memory"),
                }
                for item in memories
            ],
            "preference_context": [
                {
                    "kind": item.get("kind", "preference"),
                    "value": item.get("value", ""),
                    "sentiment": item.get("sentiment", "like"),
                    "strength": round(float(item.get("strength", 0.0)), 3),
                }
                for item in preferences[:preference_limit]
                if item.get("value")
            ],
            "reasoning_context": reasoning[:reasoning_limit],
            "explanation_context": explanation,
        }

    async def memory_context_for_recommendations(self, user_id: str, intent: str, limit: int = 6) -> list[dict[str, Any]]:
        """Return only scored memory summaries approved for recommendation use."""
        if not self.enabled:
            return []
        try:
            memories = self._memory_service.retrieve(
                user_id, intent=intent, surface="chat", limit=limit, context_budget=1200,
            )
            return [
                {
                    "summary": item.get("summary", ""),
                    "strength": round(float(item.get("importance", .5)) * float(item.get("confidence", 1)), 3),
                    "memory_class": item.get("source", "memory"),
                }
                for item in memories
            ]
        except Exception as exc:
            logger.warning("Recommendation memory retrieval unavailable: %s", exc)
            return []

    async def preference_context_for_recommendations(self, user_id: str, limit: int = 12) -> list[dict[str, Any]]:
        """Return persisted Neo4j preferences as bounded recommendation evidence."""
        if not self.enabled:
            return []
        try:
            preferences = self._preference_service.get_preferences(user_id)
            return [
                {
                    "kind": item.get("kind", "preference"),
                    "value": item.get("value", ""),
                    "sentiment": item.get("sentiment", "like"),
                    "strength": round(float(item.get("strength", 0.0)), 3),
                }
                for item in preferences[:limit]
                if item.get("value")
            ]
        except Exception as exc:
            logger.warning("Recommendation preference retrieval unavailable: %s", exc)
            return []

    async def reasoning_context_for_recommendations(self, user_id: str, days: int = 30, limit: int = 12) -> list[dict[str, Any]]:
        """Return recent listening reasoning facts from the Neo4j graph."""
        if not self.enabled:
            return []
        try:
            return self._reasoning_service.listening_timeline(user_id, days=days)[:limit]
        except Exception as exc:
            logger.warning("Recommendation reasoning retrieval unavailable: %s", exc)
            return []

    async def upsert_account(self, *, user_id: str, login: str, email: str, display_name: str) -> None:
        """Create the account's user node and its initial graph relationships."""
        if not self.enabled:
            return
        now = datetime.now(timezone.utc).isoformat()
        session_id = f"auth-{uuid4()}"
        conversation_id = f"welcome-{user_id}"
        query = """
        MERGE (u:User {user_id: $user_id})
        ON CREATE SET u.created_at = $now, u.consent_given = false
        SET u.login = $login, u.email = $email, u.display_name = $display_name, u.last_login_at = $now
        MERGE (s:Session {session_id: $session_id})
        SET s.user_id = $user_id, s.started_at = $now, s.device = 'web'
        MERGE (u)-[:HAS_SESSION]->(s)
        MERGE (c:Conversation {conversation_id: $conversation_id})
        ON CREATE SET c.user_id = $user_id, c.started_at = $now
        MERGE (u)-[:STARTED]->(c)
        """
        try:
            self._neo4j_client.execute_write(query, {
                "user_id": user_id, "login": login, "email": email,
                "display_name": display_name, "session_id": session_id,
                "conversation_id": conversation_id, "now": now,
            })
        except Exception as exc:
            logger.error("Graph writeback (upsert_account) failed: %s", exc)
            raise GraphWritebackError(str(exc)) from exc

    async def seed_artists(self, artists: list[dict[str, Any]], tracks: list[dict[str, Any]]) -> None:
        """Idempotently mirror starter artists, tracks, and authorship into Neo4j."""
        if not self.enabled:
            return
        try:
            self._neo4j_client.execute_write("""
                UNWIND $artists AS artist
                MERGE (a:Artist {artist_id: artist.id})
                SET a.name = artist.name,
                    a.monthly_listeners = artist.monthlyListeners,
                    a.seeded = true
            """, {"artists": artists})
            self._neo4j_client.execute_write("""
                UNWIND $tracks AS track
                MERGE (t:Track {track_id: track.id})
                SET t.title = track.title,
                    t.genre = track.genre,
                    t.seeded = true
                MERGE (a:Artist {artist_id: track.artistId})
                ON CREATE SET a.name = track.artistName, a.seeded = true
                MERGE (t)-[:BY]->(a)
            """, {"tracks": tracks})
        except Exception as exc:
            logger.error("Graph writeback (seed_artists) failed: %s", exc)
            # Catalog browsing remains available when Neo4j Desktop is not
            # running; the next API restart will retry this idempotent seed.
            return


graph_client = GraphClient()
