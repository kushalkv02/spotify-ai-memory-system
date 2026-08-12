"""
Orchestration layer used by the API routes. Ties together:
validation -> raw-event persistence -> deterministic memory extraction
-> graph writeback.

The extractor is intentionally separate from raw-event retention. A future
structured-model adapter can enrich its validated output without deciding
whether an event may enter the retrievable memory graph.
"""
from .models.event import EventEnvelope, RawEventRecord
from .models.event_types import EventCategory
from .validation.event_validator import EventValidator
from .db.event_repository import EventRepository
from .db.memory_decision_repository import MemoryDecisionRepository
from .services.memory_extractor import MemoryExtractor
from .integrations.graph_client import GraphClient
from .utils.logger import get_logger
from .utils.exceptions import GraphWritebackError

logger = get_logger(__name__)

class InteractionOrchestrator:
    def __init__(
        self,
        validator: EventValidator,
        event_repository: EventRepository,
        memory_extractor: MemoryExtractor,
        memory_decision_repository: MemoryDecisionRepository,
        graph_client: GraphClient,
    ):
        self.validator = validator
        self.event_repository = event_repository
        self.memory_extractor = memory_extractor
        self.memory_decision_repository = memory_decision_repository
        self.graph_client = graph_client

    async def ingest(self, envelope: EventEnvelope, *, require_graph_writeback: bool = False) -> RawEventRecord:
        """
        Full ingest path for a single incoming event:
          1. validate (schema version + payload shape + consent)
          2. persist to Postgres (raw, immutable)
          3. classify into a separately retained memory-decision record
          4. graph writeback (record_interaction always; create_memory / update_preferences
             only when important)
          5. return the stored record
        """
        validated = await self.validator.validate(envelope)
        record = await self.event_repository.insert(validated)

        decision = self.memory_extractor.extract(record)
        is_new_memory = await self.memory_decision_repository.record(decision)
        await self.event_repository.mark_processed(record.event_id, decision.retain_as_memory, decision.confidence)
        record.is_important = decision.retain_as_memory
        record.importance_score = decision.confidence

        try:
            await self.graph_client.record_interaction(record)
            action = record.payload.get("action") or record.payload.get("action_type")
            if action in {"unlike", "unfollow_artist"}:
                await self.graph_client.remove_state_memories(record)
            if decision.memory_class.value in {"explicit_preference", "exclusion", "correction"}:
                await self.graph_client.update_preferences_from_event(record)
            if decision.retain_as_memory and is_new_memory and decision.summary:
                await self.graph_client.create_memory(record, decision.summary, tags=[decision.memory_class.value])
        except Exception as exc:
            # Graph writeback failures should not fail the API request — the
            # event is already safely persisted in Postgres.
            logger.error("Graph writeback failed for event_id=%s: %s", record.event_id, exc)
            if require_graph_writeback:
                raise GraphWritebackError(str(exc)) from exc

        return record
