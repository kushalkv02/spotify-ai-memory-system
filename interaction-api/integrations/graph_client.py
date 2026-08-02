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

IMPORTANT: The method names called below (`record_interaction`,
`create_memory`, `update_preferences_from_event`) are best-guess based on
your file names (graph/services/interaction_service.py, memory_service.py,
preference_service.py). Adjust them to match your actual method signatures.
"""
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

    async def record_interaction(self, event: RawEventRecord) -> None:
        """Write a raw interaction into the graph (e.g. (:User)-[:PERFORMED]->(:Interaction)).

        Called for every event regardless of importance, mirroring how
        graph/cypher/seed/interactions_seed.cypher models interaction nodes.
        """
        if not self.enabled:
            return
        try:
            # TODO: replace with your actual method, e.g.:
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
                track_ids=[event.payload["track_id"]] if event.payload.get("track_id") else [],
            )
        except Exception as exc:
            logger.error("Graph writeback (create_memory) failed: %s", exc)
            raise GraphWritebackError(str(exc)) from exc

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
