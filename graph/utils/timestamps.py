from __future__ import annotations

from datetime import datetime, timezone


def now_iso() -> str:
    """Current UTC time as an ISO-8601 string — the format we store on nodes/edges."""
    return datetime.now(timezone.utc).isoformat()


def to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)
