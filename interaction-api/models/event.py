"""Pydantic models for the Versioned Event Contract."""
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import UUID

from .event_types import ConsentState, EventCategory, EventSurface, MemoryClass


class EventEnvelope(BaseModel):
    """Shape the Vue.js client POSTs to /interactions/events."""
    schema_version: str = Field(default="1.1.0")
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: Optional[str] = None
    category: EventCategory
    # These are contract fields, not untrusted client metadata.  The validator
    # stamps consent_state after checking the authenticated user's consent.
    subject_scope: str = Field(default="user", min_length=1, max_length=128)
    surface: EventSurface = EventSurface.UNKNOWN
    locale: str = Field(default="und", min_length=2, max_length=35)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    consent_state: ConsentState = ConsentState.PENDING
    source_event_id: Optional[str] = Field(default=None, max_length=128)
    idempotency_key: str = Field(default_factory=lambda: str(uuid.uuid4()), min_length=1, max_length=255)
    payload: dict[str, Any] = Field(default_factory=dict)
    client_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def ensure_tz_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def attach_source_event_identifier(self) -> "EventEnvelope":
        # Standalone client events originate from themselves; derived events
        # provide the upstream source identifier explicitly.
        if not self.source_event_id:
            self.source_event_id = self.event_id
        return self


class ExplicitPreferenceInput(BaseModel):
    """A user-declared preference submitted by the chat/UI client."""

    user_id: str
    session_id: Optional[str] = None
    kind: Literal["genre", "artist", "mood"]
    value: str = Field(min_length=1, max_length=256)
    sentiment: Literal["like", "dislike"] = "like"
    strength: Optional[float] = Field(default=None, ge=0, le=1)
    source_message: Optional[str] = None


class ValidatedEvent(EventEnvelope):
    """An EventEnvelope that has passed schema + consent validation."""
    received_at: datetime
    consent_scopes_checked: list[str] = Field(default_factory=list)


class RawEventRecord(BaseModel):
    """Row-level representation of an event as stored in Postgres."""
    id: Optional[int] = None
    event_id: UUID
    user_id: str
    session_id: Optional[str] = None
    category: str
    schema_version: str
    subject_scope: str
    surface: str
    locale: str
    occurred_at: datetime
    received_at: datetime
    consent_state: str
    source_event_id: Optional[str] = None
    idempotency_key: str
    payload: dict[str, Any]
    client_metadata: dict[str, Any]
    is_important: Optional[bool] = None
    importance_score: Optional[float] = None
    processed_at: Optional[datetime] = None


class ExtractedMemory(BaseModel):
    """A decision artifact; raw event retention never depends on this model."""
    event_id: UUID
    memory_class: MemoryClass
    retain_as_memory: bool
    confidence: float = Field(ge=0, le=1)
    policy_class: str
    summary: Optional[str] = None
    entities: dict[str, list[str]] = Field(default_factory=dict)
    semantic_key: Optional[str] = None
    source_event_ids: list[UUID] = Field(default_factory=list)


class StructuredMemoryOutput(BaseModel):
    """Validated output accepted from a trusted extraction model adapter."""
    confidence: float = Field(ge=0, le=1)
    policy_class: str = Field(min_length=1, max_length=128)
    summary: Optional[str] = Field(default=None, max_length=2000)
