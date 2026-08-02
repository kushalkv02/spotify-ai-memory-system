from __future__ import annotations


def require_non_empty(value: str, field_name: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"'{field_name}' must be a non-empty string")
    return value


def require_id(value: str, field_name: str = "id") -> str:
    require_non_empty(value, field_name)
    if any(ch.isspace() for ch in value):
        raise ValueError(f"'{field_name}' must not contain whitespace: {value!r}")
    return value
