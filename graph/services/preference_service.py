"""
Derives/updates Preference nodes from listening history. The scoring
here is intentionally simple (play-count based) — swap it out once
the Memory Decision Engine can weigh in with richer signals.
"""
from __future__ import annotations

import uuid
from collections import Counter
from typing import Any

from ..models.preference import Preference
from ..repositories.playback_repository import PlaybackRepository
from ..repositories.preference_repository import PreferenceRepository


class PreferenceService:
    def __init__(self) -> None:
        self.playback = PlaybackRepository()
        self.preferences = PreferenceRepository()

    def recompute_genre_preferences(self, user_id: str, limit: int = 200) -> list[dict[str, Any]]:
        plays = self.playback.get_recent_plays(user_id, limit=limit)
        # NOTE: get_recent_plays doesn't return genre today — this is a
        # starting point to extend once Track.genre is fetched alongside.
        genre_counts: Counter[str] = Counter()
        total = len(plays) or 1

        results = []
        for genre, count in genre_counts.most_common(10):
            pref = Preference(
                preference_id=f"pref_{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                kind="genre",
                value=genre,
                strength=round(count / total, 3),
            )
            results.append(self.preferences.upsert_preference(pref))
        return results

    def get_preferences(self, user_id: str) -> list[dict[str, Any]]:
        return self.preferences.get_for_user(user_id)

    def set_explicit_preference(
        self,
        user_id: str,
        kind: str,
        value: str,
        sentiment: str = "like",
        strength: float | None = None,
        ) -> dict:
        """Directly upsert a Preference node from an explicit, user-stated
        signal (e.g. a chatbot message or a quick-reply button), bypassing
        the play-count based recompute_genre_preferences heuristic.

        - `kind`: "genre" | "artist" | "mood"
        - `sentiment`: "like" | "dislike" — used to derive a default strength
        if `strength` isn't explicitly provided.
        - `strength`: optional explicit override in [0, 1]."""
        resolved_strength = strength if strength is not None else (1.0 if sentiment == "like" else 0.0)

        pref = Preference(
            preference_id=f"pref_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            kind=kind,
            value=value,
            strength=resolved_strength,
            sentiment=sentiment,
        )
        return self.preferences.upsert_preference(pref)