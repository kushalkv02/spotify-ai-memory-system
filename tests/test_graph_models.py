"""
Tests for graph models (User, Track, Artist, Memory, Playback, Preference, etc.).
"""
from __future__ import annotations

from datetime import datetime, timezone
from graph.models.album import Album
from graph.models.artist import Artist
from graph.models.memory import Memory
from graph.models.playback import Playback
from graph.models.preference import Preference
from graph.models.track import Track
from graph.models.user import User


class TestGraphModels:
    def test_user_model(self, sample_user_node):
        user = User.from_node(sample_user_node)
        assert user.user_id == "user_123"
        assert user.display_name == "Test User"
        assert user.email == "test@example.com"
        assert user.consent_given is True

        user_dict = user.to_dict()
        assert user_dict["user_id"] == "user_123"
        assert "created_at" in user_dict

    def test_track_model(self, sample_track_node):
        track = Track.from_node(sample_track_node)
        assert track.track_id == "track_456"
        assert track.title == "Starboy"
        assert track.duration_ms == 230000
        assert track.genre == "pop"

        track_dict = track.to_dict()
        assert track_dict["title"] == "Starboy"

    def test_artist_model(self):
        artist_node = {"artist_id": "art_1", "name": "The Weeknd", "genres": ["pop", "r&b"]}
        artist = Artist.from_node(artist_node)
        assert artist.artist_id == "art_1"
        assert artist.name == "The Weeknd"
        assert artist.genres == ["pop", "r&b"]
        assert artist.to_dict()["name"] == "The Weeknd"

    def test_album_model(self):
        album_node = {"album_id": "alb_1", "title": "Starboy", "release_year": 2016}
        album = Album.from_node(album_node)
        assert album.album_id == "alb_1"
        assert album.title == "Starboy"
        assert album.to_dict()["release_year"] == 2016

    def test_memory_model(self, sample_memory_node):
        mem = Memory.from_node(sample_memory_node)
        assert mem.memory_id == "mem_789"
        assert mem.user_id == "user_123"
        assert mem.summary == "User loves synthwave pop"
        assert mem.importance == 0.8
        assert mem.confidence == 0.95
        assert mem.status == "active"

        mem_dict = mem.to_dict()
        assert mem_dict["memory_id"] == "mem_789"
        assert "created_at" in mem_dict
        assert "valid_from" in mem_dict

    def test_playback_event_model(self):
        played_at = datetime.now(timezone.utc)
        event = Playback(
            user_id="u1",
            track_id="t1",
            played_at=played_at,
            ms_played=120000,
            context="playlist:top_50",
            session_id="sess_100",
        )
        data = event.to_dict()
        assert data["user_id"] == "u1"
        assert data["ms_played"] == 120000
        assert "played_at" in data

    def test_preference_model(self):
        pref = Preference(
            preference_id="pref_001",
            user_id="u1",
            kind="genre",
            value="synthwave",
            strength=0.85,
            sentiment="like",
        )
        assert pref.user_id == "u1"
        assert pref.strength == 0.85
        pref_dict = pref.to_dict()
        assert pref_dict["value"] == "synthwave"
