"""
MCP tools return text content back to the LLM host. Graph services
return Python dicts/lists (or None) — this is the one place that
turns those into the JSON strings every tool hands back, so formatting
stays consistent across all of them.
"""
from __future__ import annotations

import json
from typing import Any


def to_text(data: Any) -> str:
    if data is None:
        return json.dumps({"result": None, "note": "not found"})
    return json.dumps(data, indent=2, default=str)
