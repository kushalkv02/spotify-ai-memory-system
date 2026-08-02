"""Timestamp helpers."""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Current UTC timestamp (timezone-aware)."""
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    """Serialize a datetime to ISO-8601 string for event payloads / API responses."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 string back into a timezone-aware datetime."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
