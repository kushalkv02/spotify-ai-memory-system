"""
Tests for graph.utils (validators, timestamps, serializers).
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest

from graph.utils.serializers import node_to_dict, records_to_dicts
from graph.utils.timestamps import now_iso, parse_iso, to_iso
from graph.utils.validators import require_id, require_non_empty


class TestGraphValidators:
    def test_require_non_empty_valid(self):
        result = require_non_empty("hello", "field")
        assert result == "hello"

    def test_require_non_empty_raises_on_empty(self):
        with pytest.raises(ValueError, match="'field' must be a non-empty string"):
            require_non_empty("", "field")

    def test_require_non_empty_raises_on_whitespace(self):
        with pytest.raises(ValueError, match="'field' must be a non-empty string"):
            require_non_empty("   ", "field")

    def test_require_id_valid(self):
        result = require_id("user_001", "user_id")
        assert result == "user_001"

    def test_require_id_raises_on_whitespace_content(self):
        with pytest.raises(ValueError, match="must not contain whitespace"):
            require_id("user 001", "user_id")


class TestGraphTimestamps:
    def test_now_iso_returns_valid_iso_string(self):
        iso_str = now_iso()
        assert isinstance(iso_str, str)
        dt = datetime.fromisoformat(iso_str)
        assert dt.tzinfo is not None

    def test_to_iso_naive_and_aware(self):
        naive_dt = datetime(2026, 8, 11, 12, 0, 0)
        aware_iso = to_iso(naive_dt)
        assert aware_iso.startswith("2026-08-11T12:00:00+00:00") or aware_iso.startswith("2026-08-11T12:00:00+00")

        aware_dt = datetime(2026, 8, 11, 12, 0, 0, tzinfo=timezone.utc)
        assert to_iso(aware_dt) == aware_dt.isoformat()

    def test_parse_iso(self):
        iso_str = "2026-08-11T12:30:00+00:00"
        dt = parse_iso(iso_str)
        assert dt.year == 2026
        assert dt.month == 8
        assert dt.day == 11
        assert dt.hour == 12
        assert dt.minute == 30


class TestGraphSerializers:
    def test_node_to_dict_with_dict_input(self):
        input_dict = {"name": "Test Node", "val": 42}
        result = node_to_dict(input_dict)
        assert result == input_dict
        assert result is not input_dict

    def test_node_to_dict_with_neo4j_like_node(self):
        mock_node = MagicMock()
        mock_node.items.return_value = [("user_id", "u1"), ("name", "Alice")]
        result = node_to_dict(mock_node)
        assert result == {"user_id": "u1", "name": "Alice"}

    def test_records_to_dicts(self):
        records = [
            {"id": "1", "name": "Item 1"},
            {"id": "2", "name": "Item 2"},
        ]
        results = records_to_dicts(records)
        assert len(results) == 2
        assert results[0] == records[0]
        assert results[1] == records[1]
