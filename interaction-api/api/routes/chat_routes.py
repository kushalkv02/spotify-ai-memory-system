"""Conversation endpoints used by the Listening memory widget."""
from datetime import datetime, timezone
from uuid import uuid4

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ...orchestrator import InteractionOrchestrator
from ...utils.exceptions import GraphWritebackError, PersistenceError
from ...services.client_state_service import client_state
from ...services.chat_workflow import ChatRecommendationWorkflow
from ..dependencies import get_graph_client, get_orchestrator
from ...integrations.graph_client import GraphClient
from ..middleware.auth_middleware import authenticate_request

router = APIRouter(prefix="/chat", tags=["chat"])

_QUICK_REPLIES = [
    {"id": "genre-electronic", "label": "I like electronic"},
    {"id": "artist-nova", "label": "I like Nova Lane"},
    {"id": "song-contrast", "label": "I like Midnight Circuit but not Neon Rain"},
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
    try:
        workflow = ChatRecommendationWorkflow(orchestrator, graph_client)
        result = await workflow.run(
            user_id=user_id, content=user_message["content"], context=message.context,
            legacy_preference=message.preference.model_dump() if message.preference else None,
        )
    except PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not persist chat event to Postgres") from exc
    except GraphWritebackError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Chat was stored in Postgres, but Neo4j writeback failed") from exc

    assistant_message = _message("assistant", result["reply_content"])
    client_state.messages[user_id].extend([user_message, assistant_message])
    return assistant_message | {
        "quickReplies": _QUICK_REPLIES,
        "eventId": str(result["event"].event_id),
        "trackRefs": result["recommended"],
        "preferencesSaved": [signal.model_dump() for signal in result["signals"]],
        "memoryStrength": result["event"].importance_score,
        "memoryRetained": result["event"].is_important,
        "llmProvider": "gemini" if result["gemini_recommendation_used"] else "deterministic-fallback",
        "graphEvidenceUsed": result["graph_evidence_used"],
    }


@router.delete("/messages", status_code=204)
async def clear_messages(user_id: str = Depends(authenticate_request)):
    client_state.messages[user_id].clear()


@router.get("/quick-replies")
async def quick_replies(user_id: str = Depends(authenticate_request)):
    return {"suggestions": _QUICK_REPLIES}
