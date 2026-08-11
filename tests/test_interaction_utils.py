"""
Tests for interaction-api utils (exceptions, timestamps).
"""
from __future__ import annotations

import tests  # noqa: F401

from datetime import datetime, timezone
import pytest

from interaction_api.utils.exceptions import (
    AuthenticationError,
    ConsentDeniedError,
    DuplicateEventError,
    EventValidationError,
    GraphWritebackError,
    InteractionAPIError,
    PersistenceError,
    UnsupportedEventVersionError,
)
from interaction_api.utils.timestamps import parse_iso, to_iso, utc_now


class TestInteractionExceptions:
    def test_hierarchy(self):
        assert issubclass(AuthenticationError, InteractionAPIError)
        assert issubclass(ConsentDeniedError, InteractionAPIError)
        assert issubclass(EventValidationError, InteractionAPIError)
        assert issubclass(UnsupportedEventVersionError, EventValidationError)
        assert issubclass(PersistenceError, InteractionAPIError)
        assert issubclass(DuplicateEventError, PersistenceError)
        assert issubclass(GraphWritebackError, InteractionAPIError)

    def test_consent_denied_error_missing_scopes(self):
        err = ConsentDeniedError(["playback_history", "user_preferences"])
        assert err.missing_scopes == ["playback_history", "user_preferences"]
        assert "Missing consent scopes" in str(err)


class TestInteractionTimestamps:
    def test_utc_now(self):
        now = utc_now()
        assert isinstance(now, datetime)
        assert now.tzinfo is timezone.utc

    def test_to_iso(self):
        naive = datetime(2026, 8, 11, 10, 0, 0)
        iso = to_iso(naive)
        assert iso.startswith("2026-08-11T10:00:00+00:00")

    def test_parse_iso(self):
        iso_str = "2026-08-11T10:00:00+00:00"
        dt = parse_iso(iso_str)
        assert dt.year == 2026
        assert dt.tzinfo is not None
