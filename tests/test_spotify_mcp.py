"""
Tests for spotify_mcp package (schemas, formatting utils, GraphAdapter facade).
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from spotify_mcp.adapters.graph_adapter import GraphAdapter, get_graph_adapter
from spotify_mcp.schemas.tool_schemas import (
    RecordPlayInput,
    SkipTrackInput,
    StoreMemoryInput,
)
from spotify_mcp.utils.formatting import to_text


class TestFormattingUtils:
    def test_to_text_with_none(self):
        result = to_text(None)
        parsed = json.loads(result)
        assert parsed["result"] is None
        assert parsed["note"] == "not found"

    def test_to_text_with_dict(self):
        data = {"user_id": "u1", "tracks": ["t1", "t2"]}
        result = to_text(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_to_text_with_list(self):
        data = [{"id": 1}, {"id": 2}]
        result = to_text(data)
        parsed = json.loads(result)
        assert parsed == data


class TestToolSchemas:
    def test_record_play_input_valid(self):
        inp = RecordPlayInput(
            user_id="user_123",
            track_id="track_456",
            user_display_name="Alice",
            ms_played=150000,
        )
        assert inp.user_id == "user_123"
        assert inp.track_id == "track_456"
        assert inp.ms_played == 150000

    def test_skip_track_input_valid(self):
        inp = SkipTrackInput(
            user_id="user_123",
            track_id="track_456",
            ms_played=5000,
        )
        assert inp.user_id == "user_123"
        assert inp.ms_played == 5000

    def test_store_memory_input_valid(self):
        inp = StoreMemoryInput(
            user_id="user_123",
            summary="User loves indie rock",
            importance=0.8,
            track_ids=["t1", "t2"],
        )
        assert inp.user_id == "user_123"
        assert inp.importance == 0.8
        assert inp.track_ids == ["t1", "t2"]


class TestGraphAdapter:
    @pytest.fixture
    def adapter(self, mock_neo4j_driver):
        with patch.object(GraphAdapter, "__init__", lambda self: None):
            ad = GraphAdapter()
            ad.graph = MagicMock()
            ad.memory = MagicMock()
            ad.preference = MagicMock()
            ad.recommendation = MagicMock()
            ad.reasoning = MagicMock()
            ad.explanation = MagicMock()
            ad.users = MagicMock()
            ad.tracks = MagicMock()
            ad.playback = MagicMock()
            ad.engagement = MagicMock()
            return ad

    def test_record_play(self, adapter):
        adapter.graph.record_play_event.return_value = {"status": "ok"}
        res = adapter.record_play("u1", "t1", user_display_name="User 1")
        assert res == {"status": "ok"}
        adapter.graph.record_play_event.assert_called_once_with(
            user_id="u1",
            track_id="t1",
            user_display_name="User 1",
            track_title=None,
            ms_played=None,
            context=None,
            session_id=None,
        )

    def test_like_track(self, adapter):
        adapter.graph.like_track.return_value = {"status": "liked"}
        res = adapter.like_track("u1", "t1")
        assert res == {"status": "liked"}
        adapter.graph.like_track.assert_called_once_with(
            user_id="u1",
            track_id="t1",
            user_display_name=None,
            track_title=None,
        )

    def test_unlike_track(self, adapter):
        res = adapter.unlike_track("u1", "t1")
        assert res == {"user_id": "u1", "track_id": "t1", "liked": False}
        adapter.graph.unlike_track.assert_called_once_with(user_id="u1", track_id="t1")

    def test_structured_recommendation_reply(self, adapter):
        adapter.preference.get_preferences.return_value = [
            {"kind": "genre", "sentiment": "like", "value": "indie"}
        ]
        adapter.reasoning.get_recent_plays.return_value = [
            {"track_id": "played_1", "title": "Recent Song", "genre": "indie"}
        ]
        adapter.reasoning.get_recent_skips.return_value = []
        adapter.memory.retrieve.return_value = [
            {"summary": "User likes indie music", "strength": 0.8}
        ]
        adapter.recommendation.by_genre_affinity.return_value = [
            {"track_id": "t1", "title": "Song One", "artist": "Artist One", "genre": "indie"}
        ]
        adapter.recommendation.by_artist_affinity.return_value = [
            {"track_id": "t2", "title": "Song Two", "artist": "Artist Two"}
        ]
        adapter.recommendation.collaborative.return_value = [
            {"track_id": "t1", "title": "Song One", "artist": "Artist One"}
        ]
        adapter.recommendation.by_mood.return_value = []
        adapter.explanation.explain_recommendations.return_value = "Recommended using your saved indie preference."

        result = adapter.structured_recommendation_reply("u1", intent="recommend indie", limit=3)

        assert result["reply_framework"]["music_recommendations_heading"] == "music recommendations -"
        assert result["reply_framework"]["reasonings_heading"] == "reasonings -"
        assert "I've got indie saved!" in result["reply_markdown"]
        assert "music recommendations -" in result["reply_markdown"]
        assert "reasonings -" in result["reply_markdown"]
        assert result["music_recommendations"] == [
            {
                "track_id": "t1",
                "title": "Song One",
                "artist": "Artist One",
                "genre": "indie",
                "mood": None,
            },
            {
                "track_id": "t2",
                "title": "Song Two",
                "artist": "Artist Two",
                "genre": None,
                "mood": None,
            },
        ]
        assert result["reasonings"] == ["Recommended using your saved indie preference."]

    def test_get_graph_adapter_singleton(self, mock_neo4j_driver):
        a1 = get_graph_adapter()
        a2 = get_graph_adapter()
        assert a1 is a2
