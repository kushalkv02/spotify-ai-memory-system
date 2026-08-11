"""FastAPI dependency providers — wires concrete implementations into routes."""
from functools import lru_cache

from ..db.postgres_client import postgres_client, PostgresClient
from ..db.event_repository import EventRepository
from ..db.memory_decision_repository import MemoryDecisionRepository
from ..db.user_repository import UserRepository
from ..validation.event_versioning import EventSchemaRegistry
from ..validation.consent_checker import ConsentChecker
from ..validation.event_validator import EventValidator
from ..integrations.graph_client import graph_client, GraphClient
from ..orchestrator import InteractionOrchestrator
from ..services.memory_extractor import MemoryExtractor


def get_postgres_client() -> PostgresClient:
    return postgres_client


def get_event_repository() -> EventRepository:
    return EventRepository(get_postgres_client())


def get_memory_decision_repository() -> MemoryDecisionRepository:
    return MemoryDecisionRepository(get_postgres_client())


def get_user_repository() -> UserRepository:
    return UserRepository(get_postgres_client())


@lru_cache
def get_schema_registry() -> EventSchemaRegistry:
    return EventSchemaRegistry()


@lru_cache
def get_consent_checker() -> ConsentChecker:
    return ConsentChecker()


def get_event_validator() -> EventValidator:
    return EventValidator(get_schema_registry(), get_consent_checker())


def get_graph_client() -> GraphClient:
    return graph_client


def get_orchestrator() -> InteractionOrchestrator:
    return InteractionOrchestrator(
        validator=get_event_validator(),
        event_repository=get_event_repository(),
        memory_extractor=MemoryExtractor(),
        memory_decision_repository=get_memory_decision_repository(),
        graph_client=get_graph_client(),
    )
