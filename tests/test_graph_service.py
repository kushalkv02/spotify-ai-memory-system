"""
Tests for GraphService and repository interactions.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from graph.services.graph_service import GraphService, get_graph_service


class TestGraphService:
    @pytest.fixture
    def service(self, mock_neo4j_driver):
        with patch.object(GraphService, "__init__", lambda self: None):
            srv = GraphService()
            srv.users = MagicMock()
            srv.tracks = MagicMock()
            srv.artists = MagicMock()
            srv.playback = MagicMock()
            srv.engagement = MagicMock()
            return srv

    def test_ensure_user(self, service):
        service.users.create_user.return_value = {"user_id": "u123", "display_name": "Alice"}
        res = service.ensure_user("u123", "Alice")
        assert res["user_id"] == "u123"
        service.users.create_user.assert_called_once()

    def test_ensure_track(self, service):
        service.tracks.create_track.return_value = {"track_id": "t456", "title": "Song"}
        res = service.ensure_track("t456", "Song")
        assert res["track_id"] == "t456"
        service.tracks.create_track.assert_called_once()

    def test_record_play_event(self, service):
        service.playback.record_play.return_value = {
            "user_id": "u1",
            "track_id": "t1",
            "played_at": "2026-01-01T00:00:00+00:00",
        }
        res = service.record_play_event(
            user_id="u1",
            track_id="t1",
            user_display_name="User 1",
            track_title="Track 1",
            ms_played=180000,
        )
        assert res["user_id"] == "u1"
        service.users.create_user.assert_called_once()
        service.tracks.create_track.assert_called_once()
        service.playback.record_play.assert_called_once()

    def test_like_track(self, service):
        service.engagement.like_track.return_value = {
            "user_id": "u1",
            "track_id": "t1",
            "liked_at": "2026-01-01T00:00:00+00:00",
        }
        res = service.like_track("u1", "t1")
        assert res["user_id"] == "u1"
        service.engagement.like_track.assert_called_once_with(user_id="u1", track_id="t1", liked_at=None)

    def test_unlike_track(self, service):
        service.unlike_track("u1", "t1")
        service.engagement.unlike_track.assert_called_once_with(user_id="u1", track_id="t1")

    def test_record_skip_event(self, service):
        service.engagement.record_skip.return_value = {
            "user_id": "u1",
            "track_id": "t1",
            "skipped_at": "2026-01-01T00:00:00+00:00",
        }
        res = service.record_skip_event("u1", "t1", ms_played=5000)
        assert res["user_id"] == "u1"
        service.engagement.record_skip.assert_called_once()

    def test_follow_artist(self, service):
        service.engagement.follow_artist.return_value = {
            "user_id": "u1",
            "artist_id": "a1",
            "followed_at": "2026-01-01T00:00:00+00:00",
        }
        res = service.follow_artist("u1", "a1", artist_name="Artist 1")
        assert res["artist_id"] == "a1"
        service.artists.create_artist.assert_called_once()
        service.engagement.follow_artist.assert_called_once()

    def test_unfollow_artist(self, service):
        service.unfollow_artist("u1", "a1")
        service.engagement.unfollow_artist.assert_called_once_with(user_id="u1", artist_id="a1")

    def test_get_graph_service_singleton(self, mock_neo4j_driver):
        srv1 = get_graph_service()
        srv2 = get_graph_service()
        assert srv1 is srv2
