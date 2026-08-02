"""
Thin wrapper around PreferenceService.recompute_genre_preferences —
kept as its own builder so it can be scheduled (cron / background job)
independently of the request/response path once that exists.
"""
from __future__ import annotations

from typing import Any

from ..services.preference_service import PreferenceService


def rebuild_preferences_for_user(user_id: str) -> list[dict[str, Any]]:
    service = PreferenceService()
    return service.recompute_genre_preferences(user_id)
