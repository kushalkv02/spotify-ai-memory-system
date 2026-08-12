"""Deterministic first-pass extraction for the memory decision boundary.

Model output can be merged here later, but it must be structured and may only
refine this result; policy and retention stay deterministic at this boundary.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from uuid import UUID

from ..models.event import ExtractedMemory, RawEventRecord, StructuredMemoryOutput
from ..models.event_types import MemoryClass, PlaybackAction
from ..config import settings


class MemoryExtractor:
    """Classify events and resolve payload identifiers into canonical entities."""

    _EXPLICIT = re.compile(r"\b(i\s+(?:love|like|prefer|hate|dislike)|never\s+play|don't\s+play)\b", re.I)
    _CORRECTION = re.compile(r"\b(not |instead|actually|rather than|don't)\b", re.I)

    def extract(
        self, event: RawEventRecord, model_output: StructuredMemoryOutput | None = None
    ) -> ExtractedMemory:
        print(f"Extracting memory from event {event.event_id} (user: {event.user_id}, category: {event.category})")
        entities = self._resolve_entities(event.payload)
        memory_class, summary = self._classify(event, entities)
        strength, factors = self._strength(event, memory_class, entities)
        retain = strength >= settings.memory_retention_threshold
        confidence = strength
        policy_class = f"{memory_class.value}:{'|'.join(factors)}"
        # The model contributes only validated confidence/wording. Deterministic
        # classification and policy remain the enforcement authority.
        if model_output and retain:
            confidence = round((confidence * 0.7) + (model_output.confidence * 0.3), 3)
            policy_class = f"{policy_class}+{model_output.policy_class}"
            summary = model_output.summary or summary
        semantic_key = self._semantic_key(event, memory_class, entities, summary) if retain else None
        return ExtractedMemory(
            event_id=event.event_id,
            memory_class=memory_class,
            retain_as_memory=retain,
            confidence=confidence,
            policy_class=policy_class,
            summary=summary,
            entities=entities,
            semantic_key=semantic_key,
            source_event_ids=[event.event_id],
        )

    @staticmethod
    def _resolve_entities(payload: dict[str, Any]) -> dict[str, list[str]]:
        # Values supplied by catalog/playback surfaces are already canonical.
        mapping = {
            "artist_id": "artists", "track_id": "tracks", "album_id": "albums",
            "playlist_id": "playlists", "show_id": "shows", "episode_id": "episodes",
            "topic_id": "topics", "activity_id": "activities", "context_id": "contexts",
        }
        return {entity: [str(payload[key])] for key, entity in mapping.items() if payload.get(key)}

    def _classify(self, event: RawEventRecord, entities: dict[str, list[str]]) -> tuple[MemoryClass, str | None]:
        payload = event.payload
        action = payload.get("action") or payload.get("action_type")
        message = str(payload.get("message") or payload.get("statement") or "").strip()
        subject = self._subject(entities, payload)

        # These reverse a stateful preference; they are not negative
        # preferences.  The orchestrator expires the corresponding retained
        # like/follow memory instead of creating a new exclusion memory.
        if action in {"unlike", "unfollow_artist"}:
            return MemoryClass.NON_MEMORY, None
        if payload.get("sentiment") == "dislike" or action in {PlaybackAction.DISLIKE.value, "unfollow_artist"} or re.search(r"\b(never|avoid|don't play)\b", message, re.I):
            return MemoryClass.EXCLUSION, f"User excludes {subject}."
        if self._CORRECTION.search(message) and message:
            return MemoryClass.CORRECTION, f"User corrected a preference: {message}"
        if payload.get("explicit_preference") or action in {PlaybackAction.LIKE.value, PlaybackAction.ADD_TO_PLAYLIST.value, "follow_artist"} or self._EXPLICIT.search(message):
            text = message or f"User explicitly prefers {subject}."
            return MemoryClass.EXPLICIT_PREFERENCE, text
        if action in {PlaybackAction.SKIP.value, PlaybackAction.COMPLETE.value}:
            # A single passive signal is useful history but deliberately not a
            # retrievable preference until repeated evidence promotes it.
            return MemoryClass.EPISODE, None
        if event.category == "chat" and message:
            return MemoryClass.CANDIDATE_PREFERENCE, message
        return MemoryClass.NON_MEMORY, None

    @staticmethod
    def _strength(event: RawEventRecord, memory_class: MemoryClass, entities: dict[str, list[str]]) -> tuple[float, list[str]]:
        """Score memory value deterministically; model output cannot retain data by itself.

        The score reflects how safe and useful the statement is for future
        music recommendations, rather than how fluent an LLM summary sounds.
        """
        payload = event.payload
        message = str(payload.get("message") or payload.get("statement") or "").casefold()
        action = payload.get("action") or payload.get("action_type")
        base = {
            MemoryClass.EXCLUSION: .64,
            MemoryClass.CORRECTION: .62,
            MemoryClass.EXPLICIT_PREFERENCE: .56,
            MemoryClass.CANDIDATE_PREFERENCE: .24,
            MemoryClass.EPISODE: .10,
            MemoryClass.NON_MEMORY: .0,
        }[memory_class]
        score, factors = base, [f"base_{memory_class.value}"]

        extracted = payload.get("extracted_preferences") or []
        if extracted:
            score += min(.15, .06 * len(extracted))
            factors.append(f"{min(len(extracted), 3)}_structured_signal")
        entity_count = sum(len(values) for values in entities.values())
        if entity_count:
            score += min(.10, .05 * entity_count)
            factors.append("canonical_entity")
        if any(word in message for word in ("love", "hate", "never", "always", "favorite", "favourite")):
            score += .08
            factors.append("strong_language")
        if any(word in message for word in ("but", "however", "instead", "rather than")):
            score += .06
            factors.append("contrast_or_correction")
        if action in {PlaybackAction.LIKE.value, PlaybackAction.ADD_TO_PLAYLIST.value, "follow_artist"}:
            score += .10
            factors.append("high_intent_action")
        if action in {PlaybackAction.SKIP.value, PlaybackAction.COMPLETE.value}:
            score += .06
            factors.append("passive_listening_signal")
        if event.category == "chat" and len(message.split()) >= 5:
            score += .03
            factors.append("specific_statement")

        score = round(min(1.0, score), 3)
        return score, factors

    @staticmethod
    def _subject(entities: dict[str, list[str]], payload: dict[str, Any]) -> str:
        for values in entities.values():
            if values:
                return values[0]
        return str(payload.get("value") or payload.get("track_title") or "this item")

    @staticmethod
    def _semantic_key(event: RawEventRecord, memory_class: MemoryClass, entities: dict[str, list[str]], summary: str | None) -> str:
        normalized = re.sub(r"\s+", " ", (summary or "").lower()).strip()
        material = {"user": event.user_id, "class": memory_class.value, "entities": entities, "summary": normalized}
        return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()
