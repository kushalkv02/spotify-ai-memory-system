"""Small client-facing catalog and session state used by the Vue demo.

The event pipeline remains the source of truth for durable interactions.  The
catalog data in this module deliberately lives behind one service so it can be
replaced by Spotify/Neo4j reads without changing any HTTP contracts.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any


class ClientStateService:
    def __init__(self) -> None:
        self.tracks = [
            {"id": "track-midnight", "title": "Midnight Circuit", "artistId": "artist-nova", "artistName": "Nova Lane", "albumId": "album-afterglow", "albumName": "Afterglow", "durationSeconds": 224, "genre": "Electronic", "coverUrl": ""},
            {"id": "track-tide", "title": "Slow Tide", "artistId": "artist-harbor", "artistName": "Harbor Days", "albumId": "album-blue-hour", "albumName": "Blue Hour", "durationSeconds": 201, "genre": "Indie", "coverUrl": ""},
            {"id": "track-velvet", "title": "Velvet Morning", "artistId": "artist-nova", "artistName": "Nova Lane", "albumId": "album-afterglow", "albumName": "Afterglow", "durationSeconds": 242, "genre": "Electronic", "coverUrl": ""},
            {"id": "track-sunroom", "title": "Sunroom", "artistId": "artist-amber", "artistName": "Amber Field", "albumId": "album-daylight", "albumName": "Daylight", "durationSeconds": 187, "genre": "Pop", "coverUrl": ""},
            {"id": "track-pines", "title": "Pines in Rain", "artistId": "artist-harbor", "artistName": "Harbor Days", "albumId": "album-blue-hour", "albumName": "Blue Hour", "durationSeconds": 258, "genre": "Indie", "coverUrl": ""},
            {"id": "track-lowlight", "title": "Low Light", "artistId": "artist-amber", "artistName": "Amber Field", "albumId": "album-daylight", "albumName": "Daylight", "durationSeconds": 214, "genre": "Pop", "coverUrl": ""},
            {"id": "track-constellations", "title": "Constellations", "artistId": "artist-cosmic", "artistName": "Cosmic Kind", "albumId": "album-orbits", "albumName": "Small Orbits", "durationSeconds": 236, "genre": "Electronic", "coverUrl": ""},
            {"id": "track-paper-moon", "title": "Paper Moon", "artistId": "artist-lanterns", "artistName": "Paper Lanterns", "albumId": "album-soft-glow", "albumName": "Soft Glow", "durationSeconds": 218, "genre": "Indie", "coverUrl": ""},
            {"id": "track-solar-wind", "title": "Solar Wind", "artistId": "artist-solra", "artistName": "Solra", "albumId": "album-horizon", "albumName": "Horizon Lines", "durationSeconds": 205, "genre": "Pop", "coverUrl": ""},
            {"id": "track-neon-rain", "title": "Neon Rain", "artistId": "artist-nova", "artistName": "Nova Lane", "albumId": "album-afterglow", "albumName": "Afterglow", "durationSeconds": 231, "genre": "Electronic", "coverUrl": ""},
            {"id": "track-coastline", "title": "Coastline", "artistId": "artist-harbor", "artistName": "Harbor Days", "albumId": "album-blue-hour", "albumName": "Blue Hour", "durationSeconds": 226, "genre": "Indie", "coverUrl": ""},
            {"id": "track-golden-hour", "title": "Golden Hour", "artistId": "artist-amber", "artistName": "Amber Field", "albumId": "album-daylight", "albumName": "Daylight", "durationSeconds": 198, "genre": "Pop", "coverUrl": ""},
            {"id": "track-cinder", "title": "Cinder", "artistId": "artist-cinder", "artistName": "Cinder Bloom", "albumId": "album-embers", "albumName": "Embers", "durationSeconds": 249, "genre": "Alternative", "coverUrl": ""},
            {"id": "track-wildfire", "title": "Wildfire", "artistId": "artist-cinder", "artistName": "Cinder Bloom", "albumId": "album-embers", "albumName": "Embers", "durationSeconds": 217, "genre": "Alternative", "coverUrl": ""},
            {"id": "track-citylights", "title": "Citylights", "artistId": "artist-echo", "artistName": "Echo Theory", "albumId": "album-night-drive", "albumName": "Night Drive", "durationSeconds": 222, "genre": "Synthwave", "coverUrl": ""},
            {"id": "track-afterimage", "title": "Afterimage", "artistId": "artist-echo", "artistName": "Echo Theory", "albumId": "album-night-drive", "albumName": "Night Drive", "durationSeconds": 244, "genre": "Synthwave", "coverUrl": ""},
            {"id": "track-open-sky", "title": "Open Sky", "artistId": "artist-juniper", "artistName": "Juniper Vale", "albumId": "album-meadowline", "albumName": "Meadowline", "durationSeconds": 229, "genre": "Folk", "coverUrl": ""},
            {"id": "track-still-water", "title": "Still Water", "artistId": "artist-juniper", "artistName": "Juniper Vale", "albumId": "album-meadowline", "albumName": "Meadowline", "durationSeconds": 263, "genre": "Folk", "coverUrl": ""},
        ]
        self.artists = [
            {"id": "artist-nova", "name": "Nova Lane", "imageUrl": "", "monthlyListeners": 128400},
            {"id": "artist-harbor", "name": "Harbor Days", "imageUrl": "", "monthlyListeners": 84300},
            {"id": "artist-amber", "name": "Amber Field", "imageUrl": "", "monthlyListeners": 61200},
            {"id": "artist-cosmic", "name": "Cosmic Kind", "imageUrl": "", "monthlyListeners": 45900},
            {"id": "artist-lanterns", "name": "Paper Lanterns", "imageUrl": "", "monthlyListeners": 37600},
            {"id": "artist-solra", "name": "Solra", "imageUrl": "", "monthlyListeners": 28400},
            {"id": "artist-cinder", "name": "Cinder Bloom", "imageUrl": "", "monthlyListeners": 51900},
            {"id": "artist-echo", "name": "Echo Theory", "imageUrl": "", "monthlyListeners": 42600},
            {"id": "artist-juniper", "name": "Juniper Vale", "imageUrl": "", "monthlyListeners": 33400},
        ]
        self.albums = [
            {"id": "album-afterglow", "title": "Afterglow", "artistId": "artist-nova", "artistName": "Nova Lane", "releaseYear": 2025, "coverUrl": ""},
            {"id": "album-blue-hour", "title": "Blue Hour", "artistId": "artist-harbor", "artistName": "Harbor Days", "releaseYear": 2024, "coverUrl": ""},
            {"id": "album-daylight", "title": "Daylight", "artistId": "artist-amber", "artistName": "Amber Field", "releaseYear": 2025, "coverUrl": ""},
            {"id": "album-orbits", "title": "Small Orbits", "artistId": "artist-cosmic", "artistName": "Cosmic Kind", "releaseYear": 2026, "coverUrl": ""},
            {"id": "album-soft-glow", "title": "Soft Glow", "artistId": "artist-lanterns", "artistName": "Paper Lanterns", "releaseYear": 2026, "coverUrl": ""},
            {"id": "album-horizon", "title": "Horizon Lines", "artistId": "artist-solra", "artistName": "Solra", "releaseYear": 2026, "coverUrl": ""},
            {"id": "album-embers", "title": "Embers", "artistId": "artist-cinder", "artistName": "Cinder Bloom", "releaseYear": 2026, "coverUrl": ""},
            {"id": "album-night-drive", "title": "Night Drive", "artistId": "artist-echo", "artistName": "Echo Theory", "releaseYear": 2026, "coverUrl": ""},
            {"id": "album-meadowline", "title": "Meadowline", "artistId": "artist-juniper", "artistName": "Juniper Vale", "releaseYear": 2026, "coverUrl": ""},
        ]
        self.playlists = [
            {"id": "playlist-focus", "name": "Focus flow", "description": "Calm tracks for deep work.", "coverUrl": "", "trackIds": ["track-midnight", "track-tide", "track-pines", "track-still-water"]},
            {"id": "playlist-night-drive", "name": "Night drive", "description": "Synths and electric energy for after dark.", "coverUrl": "", "trackIds": ["track-citylights", "track-afterimage", "track-constellations", "track-neon-rain"]},
            {"id": "playlist-fresh-air", "name": "Fresh air", "description": "Open-road indie and folk for a reset.", "coverUrl": "", "trackIds": ["track-open-sky", "track-coastline", "track-paper-moon", "track-wildfire"]},
            {"id": "playlist-new-favorites", "name": "New favorites", "description": "A bright mix from the newest voices in the catalog.", "coverUrl": "", "trackIds": ["track-golden-hour", "track-cinder", "track-citylights", "track-open-sky"]},
        ]
        self.likes: dict[str, set[str]] = defaultdict(set)
        self.follows: dict[str, set[str]] = defaultdict(set)
        self.recent: dict[str, list[str]] = defaultdict(list)
        self.messages: dict[str, list[dict[str, Any]]] = defaultdict(list)
        # This is the immediate UI projection of durable chat preferences.
        # Neo4j remains the long-lived cross-session source when enabled.
        self.chat_preferences: dict[str, dict[tuple[str, str], dict[str, Any]]] = defaultdict(dict)

    def _copy(self, value: Any) -> Any:
        return deepcopy(value)

    def track(self, track_id: str) -> dict[str, Any] | None:
        return next((self._copy(track) for track in self.tracks if track["id"] == track_id), None)

    def tracks_for_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        return [track for track_id in ids if (track := self.track(track_id))]

    def feed(self, user_id: str, graph_track_ids: list[str] | None = None) -> dict[str, Any]:
        recent = self.tracks_for_ids(self.recent[user_id])
        recommended = self.recommend(user_id, graph_track_ids=graph_track_ids)
        genre_order = self._preferred_genres(user_id)
        return {
            "recommended": recommended,
            "recentlyPlayed": recent,
            "forYouGenres": [
                {"genre": f"{genre_order[0]} for you", "tracks": self._copy([track for track in self.tracks if track["genre"] == genre_order[0]])},
                {"genre": f"{genre_order[1]} for you", "tracks": self._copy([track for track in self.tracks if track["genre"] == genre_order[1]])},
                {"genre": "New sounds for you", "tracks": self._copy([track for track in self.tracks if track["genre"] in {"Alternative", "Synthwave", "Folk"}])},
            ],
        }

    def apply_chat_preferences(self, user_id: str, preferences: list[dict[str, Any]]) -> None:
        for preference in preferences:
            kind = str(preference.get("kind", "")).strip().casefold()
            value = str(preference.get("value", "")).strip()
            sentiment = str(preference.get("sentiment", "like")).casefold()
            if kind and value and sentiment in {"like", "dislike"}:
                self.chat_preferences[user_id][(kind, value.casefold())] = {
                    "kind": kind, "value": value, "sentiment": sentiment,
                    "strength": float(preference.get("strength") or 1.0),
                }

    def recommend(self, user_id: str, limit: int = 20, graph_track_ids: list[str] | None = None) -> list[dict[str, Any]]:
        """Blend current chat signals with IDs returned by graph recommenders."""
        preferences = list(self.chat_preferences[user_id].values())
        graph_boost = set(graph_track_ids or [])

        def score(track: dict[str, Any]) -> float:
            value = 0.6 if track["id"] in graph_boost else 0.0
            for pref in preferences:
                matches = (
                    (pref["kind"] == "track" and pref["value"].casefold() == track["title"].casefold())
                    or (pref["kind"] == "artist" and pref["value"].casefold() == track["artistName"].casefold())
                    or (pref["kind"] == "genre" and pref["value"].casefold() == track["genre"].casefold())
                )
                if matches:
                    weight = 3.0 if pref["kind"] == "track" else 1.5
                    value += weight * pref["strength"] * (1 if pref["sentiment"] == "like" else -1)
            if track["id"] in self.likes[user_id]:
                value += 1.0
            return value

        # A direct negative track signal is an exclusion, not merely a lower rank.
        excluded = {
            pref["value"].casefold() for pref in preferences
            if pref["kind"] == "track" and pref["sentiment"] == "dislike"
        }
        ranked = [track for track in self.tracks if track["title"].casefold() not in excluded]
        ranked.sort(key=score, reverse=True)
        return self._copy(ranked[:limit])

    def _preferred_genres(self, user_id: str) -> list[str]:
        scores: dict[str, float] = defaultdict(float)
        for pref in self.chat_preferences[user_id].values():
            if pref["kind"] == "genre":
                scores[pref["value"]] += pref["strength"] * (1 if pref["sentiment"] == "like" else -1)
        defaults = ["Electronic", "Indie"]
        ordered = [genre for genre, score in sorted(scores.items(), key=lambda item: item[1], reverse=True) if score > 0]
        return (ordered + [genre for genre in defaults if genre not in ordered])[:2]

    def search(self, query: str) -> dict[str, list[dict[str, Any]]]:
        needle = query.casefold().strip()
        return {
            "tracks": self._copy([t for t in self.tracks if needle in f"{t['title']} {t['artistName']} {t['albumName']} {t['genre']}".casefold()]),
            "artists": self._copy([a for a in self.artists if needle in a["name"].casefold()]),
            "albums": self._copy([a for a in self.albums if needle in f"{a['title']} {a['artistName']}".casefold()]),
        }

    def featured_artists(self) -> list[dict[str, Any]]:
        return self._copy(self.artists)

    def library(self, user_id: str) -> dict[str, Any]:
        playlists = [{k: v for k, v in p.items() if k != "trackIds"} | {"trackCount": len(p["trackIds"])} for p in self.playlists]
        return {"displayName": "Listener", "avatarUrl": "", "playlists": self._copy(playlists), "likedTracks": self.tracks_for_ids(list(self.likes[user_id])), "followedArtists": self._copy([a for a in self.artists if a["id"] in self.follows[user_id]])}

    def playlist(self, playlist_id: str) -> dict[str, Any] | None:
        playlist = next((p for p in self.playlists if p["id"] == playlist_id), None)
        if not playlist:
            return None
        result = {k: v for k, v in playlist.items() if k != "trackIds"}
        result["tracks"] = self.tracks_for_ids(playlist["trackIds"])
        return result

    def album(self, album_id: str) -> dict[str, Any] | None:
        album = next((a for a in self.albums if a["id"] == album_id), None)
        if not album:
            return None
        result = self._copy(album)
        result["tracks"] = self._copy([t for t in self.tracks if t["albumId"] == album_id])
        return result

    def artist(self, artist_id: str) -> dict[str, Any] | None:
        artist = next((a for a in self.artists if a["id"] == artist_id), None)
        if not artist:
            return None
        result = self._copy(artist)
        result["topTracks"] = self._copy([t for t in self.tracks if t["artistId"] == artist_id])
        result["albums"] = self._copy([a for a in self.albums if a["artistId"] == artist_id])
        return result

    def record_play(self, user_id: str, track_id: str) -> None:
        if not self.track(track_id):
            return
        self.recent[user_id] = [track_id] + [item for item in self.recent[user_id] if item != track_id]
        self.recent[user_id] = self.recent[user_id][:20]

    def toggle_like(self, user_id: str, track_id: str) -> bool:
        liked = self.likes[user_id]
        if track_id in liked:
            liked.remove(track_id)
            return False
        liked.add(track_id)
        return True

    def toggle_follow(self, user_id: str, artist_id: str) -> bool:
        followed = self.follows[user_id]
        if artist_id in followed:
            followed.remove(artist_id)
            return False
        followed.add(artist_id)
        return True


client_state = ClientStateService()
