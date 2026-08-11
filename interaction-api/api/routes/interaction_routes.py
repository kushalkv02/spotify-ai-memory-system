"""
Interaction API routes.

Vue.js Client -> (Playback Events / Chat / UI Actions) -> here.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ...models.event import EventEnvelope, ExplicitPreferenceInput, RawEventRecord
from ...models.event_types import EventCategory
from ...utils.exceptions import ConsentDeniedError, EventValidationError, DuplicateEventError
from ...orchestrator import InteractionOrchestrator
from ..dependencies import get_orchestrator
from ..middleware.auth_middleware import authenticate_request
from ...services.client_state_service import client_state
from ...utils.exceptions import GraphWritebackError, PersistenceError

router = APIRouter(prefix="/interactions", tags=["interactions"])


class TrackInteractionInput(BaseModel):
    trackId: str = Field(min_length=1)
    source: str | None = None
    atSeconds: float | None = Field(default=None, ge=0)


class ArtistInteractionInput(BaseModel):
    artistId: str = Field(min_length=1)


async def _persist_client_event(
    *,
    user_id: str,
    category: EventCategory,
    payload: dict,
    orchestrator: InteractionOrchestrator,
) -> RawEventRecord:
    """Send client shorthand routes through the durable event pipeline."""
    try:
        return await orchestrator.ingest(
            EventEnvelope(user_id=user_id, category=category, payload=payload),
            require_graph_writeback=True,
        )
    except (ConsentDeniedError, EventValidationError, DuplicateEventError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not persist interaction event to Postgres",
        ) from exc
    except GraphWritebackError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Interaction was stored in Postgres, but Neo4j writeback failed",
        ) from exc


@router.post("/play")
async def log_play(
    payload: TrackInteractionInput,
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
):
    track = client_state.track(payload.trackId)
    record = await _persist_client_event(
        user_id=user_id,
        category=EventCategory.PLAYBACK,
        payload={
            "action": "play",
            "track_id": payload.trackId,
            "track_title": track["title"] if track else payload.trackId,
            "user_display_name": "Listener",
            "context": payload.source,
        },
        orchestrator=orchestrator,
    )
    client_state.record_play(user_id, payload.trackId)
    return {"trackId": payload.trackId, "recorded": True, "eventId": str(record.event_id)}


@router.post("/skip")
async def log_skip(
    payload: TrackInteractionInput,
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
):
    track = client_state.track(payload.trackId)
    record = await _persist_client_event(
        user_id=user_id,
        category=EventCategory.PLAYBACK,
        payload={
            "action": "skip",
            "track_id": payload.trackId,
            "track_title": track["title"] if track else payload.trackId,
            "user_display_name": "Listener",
            "ms_played": int((payload.atSeconds or 0) * 1000),
            "context": payload.source,
        },
        orchestrator=orchestrator,
    )
    return {"trackId": payload.trackId, "recorded": True, "atSeconds": payload.atSeconds, "eventId": str(record.event_id)}


@router.post("/like")
async def toggle_like(
    payload: TrackInteractionInput,
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
):
    is_liked = payload.trackId in client_state.likes[user_id]
    track = client_state.track(payload.trackId)
    record = await _persist_client_event(
        user_id=user_id,
        category=EventCategory.PLAYBACK,
        payload={
            "action": "unlike" if is_liked else "like",
            "track_id": payload.trackId,
            "track_title": track["title"] if track else payload.trackId,
            "artist_id": track.get("artistId") if track else None,
            "artist_name": track.get("artistName") if track else None,
            "user_display_name": "Listener",
        },
        orchestrator=orchestrator,
    )
    return {"trackId": payload.trackId, "liked": client_state.toggle_like(user_id, payload.trackId), "eventId": str(record.event_id)}


@router.post("/likes")
async def like_song(
    payload: TrackInteractionInput,
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
):
    track = client_state.track(payload.trackId)
    record = await _persist_client_event(
        user_id=user_id,
        category=EventCategory.PLAYBACK,
        payload={
            "action": "like", "track_id": payload.trackId,
            "track_title": track["title"] if track else payload.trackId,
            "artist_id": track.get("artistId") if track else None,
            "artist_name": track.get("artistName") if track else None,
            "user_display_name": "Listener",
        },
        orchestrator=orchestrator,
    )
    client_state.likes[user_id].add(payload.trackId)
    return {"trackId": payload.trackId, "liked": True, "eventId": str(record.event_id)}


@router.delete("/likes/{track_id}")
async def unlike_song(
    track_id: str,
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
):
    track = client_state.track(track_id)
    record = await _persist_client_event(
        user_id=user_id,
        category=EventCategory.PLAYBACK,
        payload={
            "action": "unlike", "track_id": track_id,
            "track_title": track["title"] if track else track_id,
            "artist_id": track.get("artistId") if track else None,
            "artist_name": track.get("artistName") if track else None,
            "user_display_name": "Listener",
        },
        orchestrator=orchestrator,
    )
    client_state.likes[user_id].discard(track_id)
    return {"trackId": track_id, "liked": False, "eventId": str(record.event_id)}


@router.post("/follow")
async def toggle_follow(
    payload: ArtistInteractionInput,
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
):
    artist = next((artist for artist in client_state.artists if artist["id"] == payload.artistId), None)
    is_following = payload.artistId in client_state.follows[user_id]
    action = "unfollow_artist" if is_following else "follow_artist"
    record = await _persist_client_event(
        user_id=user_id,
        category=EventCategory.UI_ACTION,
        payload={
            "action_type": action,
            "artist_id": payload.artistId,
            "artist_name": artist["name"] if artist else payload.artistId,
            "user_display_name": "Listener",
        },
        orchestrator=orchestrator,
    )
    return {"artistId": payload.artistId, "following": client_state.toggle_follow(user_id, payload.artistId), "eventId": str(record.event_id)}


@router.post("/follows")
async def follow_artist(
    payload: ArtistInteractionInput,
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
):
    artist = next((item for item in client_state.artists if item["id"] == payload.artistId), None)
    record = await _persist_client_event(
        user_id=user_id,
        category=EventCategory.UI_ACTION,
        payload={"action_type": "follow_artist", "artist_id": payload.artistId, "artist_name": artist["name"] if artist else payload.artistId, "user_display_name": "Listener"},
        orchestrator=orchestrator,
    )
    client_state.follows[user_id].add(payload.artistId)
    return {"artistId": payload.artistId, "following": True, "eventId": str(record.event_id)}


@router.delete("/follows/{artist_id}")
async def unfollow_artist(
    artist_id: str,
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
):
    artist = next((item for item in client_state.artists if item["id"] == artist_id), None)
    record = await _persist_client_event(
        user_id=user_id,
        category=EventCategory.UI_ACTION,
        payload={"action_type": "unfollow_artist", "artist_id": artist_id, "artist_name": artist["name"] if artist else artist_id, "user_display_name": "Listener"},
        orchestrator=orchestrator,
    )
    client_state.follows[user_id].discard(artist_id)
    return {"artistId": artist_id, "following": False, "eventId": str(record.event_id)}


@router.post("/preferences")
async def submit_explicit_preference(
    preference: ExplicitPreferenceInput,
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
):
    """Capture a declared preference through the same versioned event contract."""
    if preference.user_id != user_id:
        raise HTTPException(status_code=403, detail="user_id in body must match authenticated user")

    record = await _persist_client_event(
        user_id=user_id,
        category=EventCategory.CHAT,
        payload={
            "message": preference.source_message or f"I {preference.sentiment} {preference.value}",
            "explicit_preference": True,
            "kind": preference.kind,
            "value": preference.value,
            "sentiment": preference.sentiment,
            "strength": preference.strength,
        },
        orchestrator=orchestrator,
    )
    return {"recorded": True, "eventId": str(record.event_id)}


@router.post("/events", response_model=RawEventRecord, status_code=status.HTTP_201_CREATED)
async def submit_event(
    envelope: EventEnvelope,
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
):
    """Accept a single interaction event (playback / chat / ui_action)."""
    if envelope.user_id != user_id:
        raise HTTPException(status_code=403, detail="user_id in body must match authenticated user")

    try:
        return await orchestrator.ingest(envelope)
    except ConsentDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "consent_required", "missing_scopes": exc.missing_scopes},
        )
    except DuplicateEventError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except EventValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/events/batch", response_model=list[RawEventRecord], status_code=status.HTTP_201_CREATED)
async def submit_events_batch(
    envelopes: list[EventEnvelope],
    user_id: str = Depends(authenticate_request),
    orchestrator: InteractionOrchestrator = Depends(get_orchestrator),
):
    """Batch variant — e.g. for client-side buffered playback events."""
    results = []
    for envelope in envelopes:
        if envelope.user_id != user_id:
            raise HTTPException(status_code=403, detail="user_id in body must match authenticated user")
        try:
            results.append(await orchestrator.ingest(envelope))
        except ConsentDeniedError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "consent_required", "missing_scopes": exc.missing_scopes},
            )
        except DuplicateEventError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
        except EventValidationError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return results
