from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RecordPlayInput(BaseModel):
    """Input for the `record_play` tool."""

    user_id: str = Field(..., description="Stable id of the listener")
    track_id: str = Field(..., description="Stable id of the track")
    user_display_name: Optional[str] = Field(
        None, description="If given, creates the User node when it doesn't exist yet"
    )
    track_title: Optional[str] = Field(
        None, description="If given, creates the Track node when it doesn't exist yet"
    )
    ms_played: Optional[int] = Field(None, description="Milliseconds of the track actually played")
    context: Optional[str] = Field(
        None, description="Where the play happened, e.g. 'playlist:abc' or 'search'"
    )
    session_id: Optional[str] = Field(None, description="Groups plays within one listening session")


class SkipTrackInput(BaseModel):
    """Input for the `skip_track` tool."""

    user_id: str = Field(..., description="Stable id of the listener")
    track_id: str = Field(..., description="Stable id of the track")
    user_display_name: Optional[str] = Field(
        None, description="If given, creates the User node when it doesn't exist yet"
    )
    track_title: Optional[str] = Field(
        None, description="If given, creates the Track node when it doesn't exist yet"
    )
    ms_played: Optional[int] = Field(None, description="Milliseconds played before the skip happened")
    context: Optional[str] = Field(
        None, description="Where the skip happened, e.g. 'playlist:abc' or 'radio'"
    )
    session_id: Optional[str] = Field(None, description="Groups events within one listening session")


class StoreMemoryInput(BaseModel):
    """Input for the `store_memory` tool."""

    user_id: str = Field(..., description="User this memory is about")
    summary: str = Field(..., description="Short natural-language memory summary")
    importance: float = Field(0.5, ge=0.0, le=1.0, description="0 (trivial) to 1 (critical)")
    track_ids: list[str] = Field(default_factory=list, description="Tracks this memory references")
