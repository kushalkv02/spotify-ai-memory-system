"""Catalog, library, and recommendation endpoints consumed by the Vue client."""
from fastapi import APIRouter, Depends, HTTPException, Query

from ...services.client_state_service import client_state
from ...integrations.graph_client import GraphClient
from ..dependencies import get_graph_client
from ..middleware.auth_middleware import authenticate_request

router = APIRouter(tags=["catalog"])


@router.get("/tracks/feed")
async def get_feed(
    user_id: str = Depends(authenticate_request), graph_client: GraphClient = Depends(get_graph_client)
):
    graph_recommendations = await graph_client.recommendations_for_user(user_id, limit=20)
    return client_state.feed(user_id, [item["track_id"] for item in graph_recommendations if item.get("track_id")])


@router.get("/tracks/search")
async def search_tracks(q: str = Query(min_length=1, max_length=200), user_id: str = Depends(authenticate_request)):
    return client_state.search(q)


@router.get("/library")
async def get_library(user_id: str = Depends(authenticate_request)):
    return client_state.library(user_id)


@router.get("/recommendations")
async def get_recommendations(
    limit: int = Query(default=20, ge=1, le=50), user_id: str = Depends(authenticate_request),
    graph_client: GraphClient = Depends(get_graph_client),
):
    graph_recommendations = await graph_client.recommendations_for_user(user_id, limit=limit)
    return {"tracks": client_state.recommend(
        user_id, limit=limit,
        graph_track_ids=[item["track_id"] for item in graph_recommendations if item.get("track_id")],
    )}


@router.get("/artists")
async def get_artists(user_id: str = Depends(authenticate_request)):
    """Starter artists available to browse and follow."""
    return {"artists": client_state.featured_artists()}


@router.get("/playlists/{playlist_id}")
async def get_playlist(playlist_id: str, user_id: str = Depends(authenticate_request)):
    playlist = client_state.playlist(playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist


@router.get("/albums/{album_id}")
async def get_album(album_id: str, user_id: str = Depends(authenticate_request)):
    album = client_state.album(album_id)
    if not album:
        raise HTTPException(status_code=404, detail="Album not found")
    return album


@router.get("/artists/{artist_id}")
async def get_artist(artist_id: str, user_id: str = Depends(authenticate_request)):
    artist = client_state.artist(artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")
    return artist
