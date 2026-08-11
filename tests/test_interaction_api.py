"""
FastAPI TestClient tests for interaction-api routes (health, catalog, auth).
"""
from __future__ import annotations

import tests  # noqa: F401

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from interaction_api.api.dependencies import get_graph_client, get_postgres_client
from interaction_api.api.main import app


@pytest.fixture
def mock_pg():
    mock = AsyncMock()
    mock.ping.return_value = True
    return mock


@pytest.fixture
def mock_graph():
    mock = AsyncMock()
    mock.enabled = False
    mock.recommendations_for_user.return_value = []
    return mock


@pytest.fixture
def test_client(mock_pg, mock_graph):
    app.dependency_overrides[get_postgres_client] = lambda: mock_pg
    app.dependency_overrides[get_graph_client] = lambda: mock_graph
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


class TestHealthRoutes:
    def test_liveness(self, test_client):
        resp = test_client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_readiness(self, test_client):
        resp = test_client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["postgres"] == "ok"
        assert "graph_writeback_enabled" in data


class TestCatalogRoutes:
    def test_search_tracks_unauthenticated(self, test_client):
        resp = test_client.get("/tracks/search?q=blinding")
        assert resp.status_code in (401, 403)

    def test_search_tracks_with_dev_auth(self, test_client):
        resp = test_client.get("/tracks/search?q=blinding", headers={"X-User-Id": "user_001"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert "tracks" in data

    def test_get_artists(self, test_client):
        resp = test_client.get("/artists", headers={"X-User-Id": "user_001"})
        assert resp.status_code == 200
        data = resp.json()
        assert "artists" in data
        assert isinstance(data["artists"], list)

    def test_get_playlist_not_found(self, test_client):
        resp = test_client.get("/playlists/non_existent_id", headers={"X-User-Id": "user_001"})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Playlist not found"


class TestAuthRoutes:
    def test_auth_me_unauthenticated(self, test_client):
        resp = test_client.get("/auth/me")
        assert resp.status_code in (401, 403)
