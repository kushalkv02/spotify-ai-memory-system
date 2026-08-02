"""Conversation endpoints used by the Listening memory widget."""
from datetime import datetime, timezone
from uuid import uuid4

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ...models.event import EventEnvelope
from ...models.event_types import EventCategory
from ...orchestrator import InteractionOrchestrator
from ...utils.exceptions import GraphWritebackError, PersistenceError
from ...services.client_state_service import client_state
from ..dependencies import get_graph_client, get_orchestrator
from ...integrations.graph_client import GraphClient
from ..middleware.auth_middleware import authenticate_request

router = APIRouter(prefix="/chat", tags=["chat"])

_QUICK_REPLIES = [
    {"id": "more-like-this", "label": "More like this"},
    {"id": "change-mood", "label": "Change the mood"},
    {"id": "less-of-genre", "label": "Less of this genre"},
]


class PreferenceInput(BaseModel):
    kind: Literal["genre", "artist", "mood"]
    value: str = Field(min_length=1, max_length=256)
    sentiment: Literal["like", "dislike"] = "like"
    strength: float | None = Field(default=None, ge=0, le=1)


class ChatMessageInput(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    context: list[dict[str, str]] = Field(default_factory=list)
    preference: PreferenceInput | None = None


def _message(role: str, content: str) -> dict[str, str]:
    return {"id": str(uuid4()), "role": role, "content": content, "createdAt": datetime.now(timezone.utc).isoformat()}


def _reply(content: str) -> str:
    normalized = content.casefold()
    if any(word in normalized for word in ("chill", "calm", "focus", "work")):
        return "I’ll lean into calm electronic and indie tracks for this session. Try Midnight Circuit or Slow Tide."
    if any(word in normalized for word in ("less", "skip", "don’t like", "dislike")):
        return "Got it — I’ll use that as a negative signal and reduce similar recommendations."
    return "I’ve saved that preference for this session. Keep playing or skipping tracks and I’ll tune the next recommendations."


def _infer_preference(content: str) -> PreferenceInput | None:
    """Turn common chat preference phrasing into a structured graph preference."""
    normalized = content.casefold()
    sentiment = "dislike" if any(phrase in normalized for phrase in ("don't like", "don’t like", "dislike", "avoid", "less ", "skip ")) else "like"
    for genre in ("electronic", "indie", "pop", "rock", "jazz", "classical", "hip hop", "hip-hop"):
        if genre in normalized:
            return PreferenceInput(kind="genre", value=genre, sentiment=sentiment)
    for mood in ("chill", "calm", "focus", "upbeat", "energetic", "relaxed", "workout", "sleep"):
        if mood in normalized:
            return PreferenceInput(kind="mood", value=mood, sentiment=sentiment)
    if any(phrase in normalized for phrase in ("i like", "i love", "more like", "less of", "prefer", "don't want", "don’t want")):
        return PreferenceInput(kind="mood", value=content.strip()[:256], sentiment=sentiment)
    return None


@router.get("/messages")
async def get_messages(limit: int = Query(default=50, ge=1, le=200), user_id: str = Depends(authenticate_request)):
    return {"messages": client_state.messages[user_id][-limit:]}


@router.post("/messages")
async def send_message(
    message: ChatMessageInput,
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
    graph_client: GraphClient = Depends(get_graph_client),
):
    user_message = _message("user", message.content.strip())
    assistant_message = _message("assistant", _reply(user_message["content"]))

    try:
        event = await orchestrator.ingest(
            EventEnvelope(
                user_id=user_id,
                category=EventCategory.CHAT,
                payload={
                    "message": user_message["content"],
                    "user_display_name": "Listener",
                    "context": message.context[-10:],
                },
            ),
            require_graph_writeback=True,
        )
        preference = message.preference or _infer_preference(user_message["content"])
        if preference:
            await graph_client.set_explicit_preference(
                user_id=user_id,
                kind=preference.kind,
                value=preference.value,
                sentiment=preference.sentiment,
                strength=preference.strength,
            )
    except PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not persist chat event to Postgres") from exc
    except GraphWritebackError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Chat was stored in Postgres, but Neo4j writeback failed") from exc

    client_state.messages[user_id].extend([user_message, assistant_message])
    return assistant_message | {"quickReplies": _QUICK_REPLIES, "eventId": str(event.event_id)}


@router.delete("/messages", status_code=204)
async def clear_messages(user_id: str = Depends(authenticate_request)):
    client_state.messages[user_id].clear()


@router.get("/quick-replies")
async def quick_replies(user_id: str = Depends(authenticate_request)):
    return {"suggestions": _QUICK_REPLIES}
