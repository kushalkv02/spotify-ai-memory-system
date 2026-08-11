"""
Tests for interaction-api models (EventEnvelope, ExplicitPreferenceInput, ValidatedEvent).
"""
from __future__ import annotations

import tests  # noqa: F401

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from interaction_api.models.event import (
    EventEnvelope,
    ExplicitPreferenceInput,
    RawEventRecord,
    StructuredMemoryOutput,
    ValidatedEvent,
)
from interaction_api.models.event_types import ConsentState, EventCategory, EventSurface


class TestInteractionModels:
    def test_event_envelope_defaults(self):
        env = EventEnvelope(
            user_id="user_123",
            category=EventCategory.PLAYBACK,
            payload={"track_id": "track_456"},
        )
        assert env.schema_version == "1.1.0"
        assert env.user_id == "user_123"
        assert env.category == EventCategory.PLAYBACK
        assert env.subject_scope == "user"
        assert env.surface == EventSurface.UNKNOWN
        assert env.consent_state == ConsentState.PENDING
        assert env.source_event_id == env.event_id
        assert env.payload["track_id"] == "track_456"

    def test_event_envelope_naive_datetime_auto_utc(self):
        naive_dt = datetime(2026, 8, 11, 12, 0, 0)
        env = EventEnvelope(
            user_id="user_123",
            category=EventCategory.PLAYBACK,
            occurred_at=naive_dt,
        )
        assert env.occurred_at.tzinfo == timezone.utc

    def test_explicit_preference_input_valid(self):
        pref = ExplicitPreferenceInput(
            user_id="user_123",
            kind="genre",
            value="synthwave",
            sentiment="like",
            strength=0.9,
        )
        assert pref.kind == "genre"
        assert pref.value == "synthwave"
        assert pref.strength == 0.9

    def test_explicit_preference_input_invalid_kind(self):
        with pytest.raises(ValidationError):
            ExplicitPreferenceInput(
                user_id="user_123",
                kind="invalid_kind",
                value="rock",
            )

    def test_validated_event(self):
        now = datetime.now(timezone.utc)
        val_event = ValidatedEvent(
            user_id="user_123",
            category=EventCategory.UI_ACTION,
            received_at=now,
            consent_scopes_checked=["playback_history"],
        )
        assert val_event.user_id == "user_123"
        assert val_event.consent_scopes_checked == ["playback_history"]

    def test_structured_memory_output(self):
        out = StructuredMemoryOutput(
            confidence=0.85,
            policy_class="user_preference",
            summary="User prefers electronic synthwave music",
        )
        assert out.confidence == 0.85
        assert out.policy_class == "user_preference"
