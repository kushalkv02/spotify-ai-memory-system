"""Enumerations shared across the event contract."""
from enum import Enum


class EventCategory(str, Enum):
    PLAYBACK = "playback"
    CHAT = "chat"
    UI_ACTION = "ui_action"


class PlaybackAction(str, Enum):
    PLAY = "play"
    PAUSE = "pause"
    SKIP = "skip"
    SEEK = "seek"
    LIKE = "like"
    UNLIKE = "unlike"
    DISLIKE = "dislike"
    ADD_TO_PLAYLIST = "add_to_playlist"
    COMPLETE = "complete"


class UIActionType(str, Enum):
    SEARCH = "search"
    OPEN_ARTIST_PAGE = "open_artist_page"
    OPEN_PLAYLIST = "open_playlist"
    FOLLOW_ARTIST = "follow_artist"
    UNFOLLOW_ARTIST = "unfollow_artist"


class ImportanceLabel(str, Enum):
    NOT_IMPORTANT = "not_important"
    IMPORTANT = "important"
