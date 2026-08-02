"""Pydantic models for the Versioned Event Contract."""
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from .event_types import EventCategory


class EventEnvelope(BaseModel):
    """Shape the Vue.js client POSTs to /interactions/events."""
    schema_version: str = Field(default="1.0.0")
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: Optional[str] = None
    category: EventCategory
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(default_factory=dict)
    client_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def ensure_tz_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


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
    occurred_at: datetime
    received_at: datetime
    payload: dict[str, Any]
    client_metadata: dict[str, Any]
    is_important: Optional[bool] = None
    importance_score: Optional[float] = None
    processed_at: Optional[datetime] = None
