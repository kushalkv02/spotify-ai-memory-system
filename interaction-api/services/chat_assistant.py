"""Gemini-backed, structured preference extraction for the chat surface.

The model is used to understand conversational language; persistence and
recommendation decisions remain in the application.  This keeps a malformed
model response (or an unavailable API key) from bypassing the event/memory
pipeline.
"""
from __future__ import annotations

import asyncio
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..config import settings


class PreferenceSignal(BaseModel):
    kind: Literal["genre", "artist", "track", "mood"]
    value: str = Field(min_length=1, max_length=256)
    sentiment: Literal["like", "dislike"]
    strength: float = Field(default=1.0, ge=0, le=1)


class ChatTurn(BaseModel):
    reply: str = Field(min_length=1, max_length=1000)
    preferences: list[PreferenceSignal] = Field(default_factory=list, max_length=12)


class RecommendationPlan(BaseModel):
    track_ids: list[str] = Field(default_factory=list, max_length=3)
    rationale: str = Field(min_length=1, max_length=400)
    # Application-owned provenance; Gemini never controls this field.
    used_gemini: bool = False


class ChatAssistant:
    """Creates a conversational reply and independently usable preference signals."""

    def __init__(self) -> None:
        self._client: Any | None = None

    @property
    def enabled(self) -> bool:
        return bool(settings.gemini_api_key)

    async def respond(
        self, *, content: str, context: list[dict[str, str]], catalog: list[dict[str, Any]]
    ) -> ChatTurn:
        if self.enabled:
            try:
                return await asyncio.to_thread(self._respond_with_gemini, content, context, catalog)
            except Exception:
                # The deterministic parser below is intentionally the safe
                # fallback for quota, network, and malformed-model failures.
                pass
        return self._fallback(content, context, catalog)

    def _respond_with_gemini(
        self, content: str, context: list[dict[str, str]], catalog: list[dict[str, Any]]
    ) -> ChatTurn:
        from google import genai
        from google.genai import types

        if self._client is None:
            self._client = genai.Client(api_key=settings.gemini_api_key)
        catalog_text = "; ".join(
            f"{track['title']} by {track['artistName']} ({track['genre']})" for track in catalog
        )
        recent = "\n".join(f"{turn.get('role', 'user')}: {turn.get('content', '')}" for turn in context[-8:])
        prompt = f"""You are the music-preference assistant inside a listening app.
Ask a short, friendly follow-up when useful, especially first ask which genre the listener likes and then which artist they like. Extract every explicit preference independently. A statement such as 'I like Artist's Song A but not Song B' MUST create one liked track and one disliked track. Only extract values the listener states; do not invent artists or tracks. Use catalog spelling when a match is clear.

Catalog: {catalog_text}
Recent conversation:\n{recent}
Latest listener message: {content}
"""
        response = self._client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=ChatTurn,
                temperature=0.2,
            ),
        )
        parsed = response.parsed
        return parsed if isinstance(parsed, ChatTurn) else ChatTurn.model_validate_json(response.text)

    async def recommend_tracks(
        self,
        *,
        candidates: list[dict[str, Any]],
        memories: list[dict[str, Any]],
        preferences: list[dict[str, Any]],
        graph_recommendations: list[dict[str, Any]],
        reasoning: list[dict[str, Any]],
        intent: str,
        explanation_context: str = "",
    ) -> RecommendationPlan:
        """Let Gemini select only from candidates ranked by the deterministic engine.

        Memory strengths are supplied as evidence, never as model-controlled
        scores. If Gemini is unavailable, deterministic candidate order wins.
        """
        fallback = RecommendationPlan(
            track_ids=[track["id"] for track in candidates[:3]],
            rationale="Ranked by the saved memory-strength signals.",
        )
        if not self.enabled or not candidates:
            return fallback
        try:
            return await asyncio.to_thread(
                self._recommend_with_gemini,
                candidates,
                memories,
                preferences,
                graph_recommendations,
                reasoning,
                intent,
                explanation_context,
            )
        except Exception:
            return fallback

    def _recommend_with_gemini(
        self,
        candidates: list[dict[str, Any]],
        memories: list[dict[str, Any]],
        preferences: list[dict[str, Any]],
        graph_recommendations: list[dict[str, Any]],
        reasoning: list[dict[str, Any]],
        intent: str,
        explanation_context: str = "",
    ) -> RecommendationPlan:
        from google.genai import types

        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=settings.gemini_api_key)
        candidate_text = "\n".join(
            f"{track['id']} | {track['title']} | {track['artistName']} | {track['genre']}" for track in candidates
        )
        memory_text = "\n".join(
            f"strength={memory['strength']:.3f}: {memory['summary']}" for memory in memories
        ) or "No retained memory available."
        preference_text = "\n".join(
            f"{item['sentiment']} {item['kind']}={item['value']} (strength={item['strength']:.3f})"
            for item in preferences
        ) or "No persisted graph preferences available."
        graph_recommendation_text = "\n".join(
            f"{item.get('track_id', '')}: {item.get('title', '')}"
            for item in graph_recommendations
            if item.get("track_id")
        ) or "No graph-native recommendation results available."
        reasoning_text = "\n".join(
            f"recently played: {item.get('title', item.get('track_id', 'unknown track'))}"
            for item in reasoning
        ) or "No graph listening-timeline facts available."
        response = self._client.models.generate_content(
            model=settings.gemini_model,
            contents=f"""Choose up to three music recommendations only from the candidate IDs below.
Treat higher-strength memories as stronger evidence. Never recommend an explicitly disliked or excluded item; the deterministic candidate list has already applied hard exclusions. Return IDs in best-first order and a short user-facing rationale.

Use all graph evidence below: retained memories, persisted preferences,
graph-native recommendation results, and the listening timeline. Graph data is
evidence only; select exclusively from the candidate IDs.

Listener request: {intent}
Retained memories (strength is 0 to 1):
{memory_text}
Persisted graph preferences:
{preference_text}
Graph-native recommendation results:
{graph_recommendation_text}
Graph listening timeline:
{reasoning_text}
Deterministic explanation evidence:
{explanation_context or "No specific explanation evidence available."}
Candidates:
{candidate_text}
""",
            config=types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=RecommendationPlan,
                temperature=0.1,
            ),
        )
        parsed = response.parsed
        plan = parsed if isinstance(parsed, RecommendationPlan) else RecommendationPlan.model_validate_json(response.text)
        allowed = {track["id"] for track in candidates}
        plan.track_ids = [track_id for track_id in plan.track_ids if track_id in allowed][:3]
        if not plan.track_ids:
            return RecommendationPlan(
                track_ids=[track["id"] for track in candidates[:3]],
                rationale="Ranked by the saved memory-strength signals.",
            )
        return plan.model_copy(update={"used_gemini": True})

    def _fallback(self, content: str, context: list[dict[str, str]], catalog: list[dict[str, Any]]) -> ChatTurn:
        """Catalog-aware fallback for local development without Gemini credentials."""
        normalized = content.casefold()
        signals: list[PreferenceSignal] = []
        seen: set[tuple[str, str]] = set()

        def sentiment_at(position: int) -> Literal["like", "dislike"]:
            # Preference language is usually scoped by a contrast word. This
            # correctly handles "I like Song A but not Song B".
            start = max(normalized.rfind(" but ", 0, position), normalized.rfind(" however ", 0, position))
            segment = normalized[start + 1:position]
            if re.search(r"\b(don't|don’t|not|dislike|hate|avoid|skip|less)\b", segment):
                return "dislike"
            return "like"

        def add(kind: Literal["genre", "artist", "track", "mood"], value: str, position: int) -> None:
            key = (kind, value.casefold())
            if key not in seen:
                seen.add(key)
                signals.append(PreferenceSignal(kind=kind, value=value, sentiment=sentiment_at(position)))

        for track in catalog:
            title = track["title"]
            index = normalized.find(title.casefold())
            if index >= 0:
                add("track", title, index)
        for artist in {track["artistName"] for track in catalog}:
            index = normalized.find(artist.casefold())
            if index >= 0:
                add("artist", artist, index)
        for genre in {track["genre"] for track in catalog}:
            index = normalized.find(genre.casefold())
            if index >= 0:
                add("genre", genre, index)

        if signals:
            liked = [s.value for s in signals if s.sentiment == "like"]
            disliked = [s.value for s in signals if s.sentiment == "dislike"]
            parts = []
            if liked:
                parts.append(f"I saved your preference for {', '.join(liked)}")
            if disliked:
                parts.append(f"I’ll avoid {', '.join(disliked)}")
            reply = ". ".join(parts) + ". I’ll use that in your next recommendations."
            if any(signal.kind == "genre" for signal in signals) and not any(signal.kind == "artist" for signal in signals):
                reply += " Which artist do you like?"
            return ChatTurn(reply=reply, preferences=signals)

        previous_assistant = " ".join(turn.get("content", "").casefold() for turn in context if turn.get("role") == "assistant")
        if "which genre" not in previous_assistant:
            reply = "Which genre do you like most right now — for example electronic, indie, pop, folk, or something else?"
        elif "which artist" not in previous_assistant:
            reply = "Nice. Which artist do you like? You can also tell me a song you love or one you want me to avoid."
        else:
            reply = "Tell me an artist, genre, or a song you like and one you do not — I’ll save both signals separately."
        return ChatTurn(reply=reply)


chat_assistant = ChatAssistant()
