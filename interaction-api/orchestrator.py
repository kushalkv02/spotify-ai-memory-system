"""
Orchestration layer used by the API routes. Ties together:
validation -> Postgres persistence -> (naive, inline) importance decision
-> graph writeback.

This inline importance check is a stand-in for the real
`memory-decision-engine` service (see spotify-mem-sys/memory-decision-engine/).
Swap `_naive_importance` for a call to that service once it's built —
everything else in this file should stay the same.
"""
from .models.event import EventEnvelope, RawEventRecord
from .models.event_types import EventCategory, PlaybackAction
from .validation.event_validator import EventValidator
from .db.event_repository import EventRepository
from .integrations.graph_client import GraphClient
from .utils.logger import get_logger
from .config import settings
from .utils.exceptions import GraphWritebackError

logger = get_logger(__name__)

_EXPLICIT_SIGNAL_ACTIONS = {
    PlaybackAction.LIKE.value,
    PlaybackAction.DISLIKE.value,
    PlaybackAction.ADD_TO_PLAYLIST.value,
}


class InteractionOrchestrator:
    def __init__(
        self,
        validator: EventValidator,
        event_repository: EventRepository,
        graph_client: GraphClient,
    ):
        self.validator = validator
        self.event_repository = event_repository
        self.graph_client = graph_client

    async def ingest(self, envelope: EventEnvelope, *, require_graph_writeback: bool = False) -> RawEventRecord:
        """
        Full ingest path for a single incoming event:
          1. validate (schema version + payload shape + consent)
          2. persist to Postgres (raw, immutable)
          3. naive importance scoring (placeholder for memory-decision-engine)
          4. graph writeback (record_interaction always; create_memory / update_preferences
             only when important)
          5. return the stored record
        """
        validated = await self.validator.validate(envelope)
        record = await self.event_repository.insert(validated)

        is_important, score = self._naive_importance(record)
        await self.event_repository.mark_processed(record.event_id, is_important, score)
        record.is_important = is_important
        record.importance_score = score

        try:
            await self.graph_client.record_interaction(record)
            if record.category == EventCategory.PLAYBACK.value and record.payload.get("action") in _EXPLICIT_SIGNAL_ACTIONS:
                await self.graph_client.update_preferences_from_event(record)
            if is_important:
                # TODO: replace this lightweight summary with the real memory
                # generator once that service exists.
                summary = (
                    f"User stated a listening preference: {record.payload['message']}"
                    if record.category == EventCategory.CHAT.value
                    else f"{record.category} event: {record.payload}"
                )
                await self.graph_client.create_memory(record, summary)
        except Exception as exc:
            # Graph writeback failures should not fail the API request — the
            # event is already safely persisted in Postgres.
            logger.error("Graph writeback failed for event_id=%s: %s", record.event_id, exc)
            if require_graph_writeback:
                raise GraphWritebackError(str(exc)) from exc

        return record

    def _naive_importance(self, record: RawEventRecord) -> tuple[bool, float]:
        """Placeholder importance heuristic — replace with
        memory-decision-engine's ImportanceScorer once that service exists.
        """
        score = 0.0
        if record.category == EventCategory.CHAT.value:
            score = 0.7
        elif record.category == EventCategory.PLAYBACK.value:
            score = 0.8 if record.payload.get("action") in _EXPLICIT_SIGNAL_ACTIONS else 0.2
        elif record.category == EventCategory.UI_ACTION.value:
            score = 0.3
        return score >= settings.importance_threshold, score
