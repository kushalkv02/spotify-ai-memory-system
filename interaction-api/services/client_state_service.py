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
        ]
        self.artists = [
            {"id": "artist-nova", "name": "Nova Lane", "imageUrl": "", "monthlyListeners": 128400},
            {"id": "artist-harbor", "name": "Harbor Days", "imageUrl": "", "monthlyListeners": 84300},
            {"id": "artist-amber", "name": "Amber Field", "imageUrl": "", "monthlyListeners": 61200},
            {"id": "artist-cosmic", "name": "Cosmic Kind", "imageUrl": "", "monthlyListeners": 45900},
            {"id": "artist-lanterns", "name": "Paper Lanterns", "imageUrl": "", "monthlyListeners": 37600},
            {"id": "artist-solra", "name": "Solra", "imageUrl": "", "monthlyListeners": 28400},
        ]
        self.albums = [
            {"id": "album-afterglow", "title": "Afterglow", "artistId": "artist-nova", "artistName": "Nova Lane", "releaseYear": 2025, "coverUrl": ""},
            {"id": "album-blue-hour", "title": "Blue Hour", "artistId": "artist-harbor", "artistName": "Harbor Days", "releaseYear": 2024, "coverUrl": ""},
            {"id": "album-daylight", "title": "Daylight", "artistId": "artist-amber", "artistName": "Amber Field", "releaseYear": 2025, "coverUrl": ""},
            {"id": "album-orbits", "title": "Small Orbits", "artistId": "artist-cosmic", "artistName": "Cosmic Kind", "releaseYear": 2026, "coverUrl": ""},
            {"id": "album-soft-glow", "title": "Soft Glow", "artistId": "artist-lanterns", "artistName": "Paper Lanterns", "releaseYear": 2026, "coverUrl": ""},
            {"id": "album-horizon", "title": "Horizon Lines", "artistId": "artist-solra", "artistName": "Solra", "releaseYear": 2026, "coverUrl": ""},
        ]
        self.playlists = [{"id": "playlist-focus", "name": "Focus flow", "description": "Calm tracks for deep work.", "coverUrl": "", "trackIds": ["track-midnight", "track-tide", "track-pines"]}]
        self.likes: dict[str, set[str]] = defaultdict(set)
        self.follows: dict[str, set[str]] = defaultdict(set)
        self.recent: dict[str, list[str]] = defaultdict(list)
        self.messages: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def _copy(self, value: Any) -> Any:
        return deepcopy(value)

    def track(self, track_id: str) -> dict[str, Any] | None:
        return next((self._copy(track) for track in self.tracks if track["id"] == track_id), None)

    def tracks_for_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        return [track for track_id in ids if (track := self.track(track_id))]

    def feed(self, user_id: str) -> dict[str, Any]:
        recent = self.tracks_for_ids(self.recent[user_id])
        return {
            "recommended": self._copy(self.tracks[:4]),
            "recentlyPlayed": recent,
            "forYouGenres": [
                {"genre": "Electronic for you", "tracks": self._copy([track for track in self.tracks if track["genre"] == "Electronic"])},
                {"genre": "Indie for you", "tracks": self._copy([track for track in self.tracks if track["genre"] == "Indie"])},
            ],
        }

    def search(self, query: str) -> dict[str, list[dict[str, Any]]]:
        needle = query.casefold().strip()
        return {
            "tracks": self._copy([t for t in self.tracks if needle in f"{t['title']} {t['artistName']} {t['albumName']}".casefold()]),
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
