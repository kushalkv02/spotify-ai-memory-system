"""
Pytest configuration and shared fixtures for spotify-mem-sys tests.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any, Generator
from unittest.mock import MagicMock, patch
import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Map hyphenated directory 'interaction-api' to importable module name 'interaction_api'
INTERACTION_API_DIR = os.path.join(PROJECT_ROOT, "interaction-api")
if INTERACTION_API_DIR not in sys.path:
    sys.path.insert(0, INTERACTION_API_DIR)

if os.path.exists(INTERACTION_API_DIR) and "interaction_api" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "interaction_api",
        os.path.join(INTERACTION_API_DIR, "__init__.py"),
        submodule_search_locations=[INTERACTION_API_DIR],
    )
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        sys.modules["interaction_api"] = mod
        spec.loader.exec_module(mod)


@pytest.fixture
def mock_neo4j_session() -> MagicMock:
    """Fixture providing a mocked Neo4j session."""
    session = MagicMock()
    result_mock = MagicMock()
    result_mock.data.return_value = []
    result_mock.single.return_value = None
    session.run.return_value = result_mock
    session.execute_write.return_value = []
    session.execute_read.return_value = []
    return session


@pytest.fixture(autouse=True)
def mock_neo4j_driver(mock_neo4j_session: MagicMock) -> Generator[MagicMock, None, None]:
    """Fixture overriding the Neo4jClient singleton instance with a mock."""
    client_mock = MagicMock()
    client_mock.session.return_value.__enter__.return_value = mock_neo4j_session
    client_mock.session.return_value.__exit__.return_value = False
    client_mock.execute_read.return_value = []
    client_mock.execute_write.return_value = []

    with patch("neo4j.GraphDatabase.driver"), \
         patch("graph.neo4j_client.Neo4jClient.get_instance", return_value=client_mock), \
         patch("graph.neo4j_client.get_client", return_value=client_mock):
        yield client_mock


@pytest.fixture
def sample_user_node() -> dict[str, Any]:
    return {
        "user_id": "user_123",
        "display_name": "Test User",
        "email": "test@example.com",
        "consent_given": True,
        "created_at": "2026-01-01T00:00:00+00:00",
    }


@pytest.fixture
def sample_track_node() -> dict[str, Any]:
    return {
        "track_id": "track_456",
        "title": "Starboy",
        "duration_ms": 230000,
        "genre": "pop",
    }


@pytest.fixture
def sample_memory_node() -> dict[str, Any]:
    return {
        "memory_id": "mem_789",
        "version_id": "ver_789_v1",
        "user_id": "user_123",
        "summary": "User loves synthwave pop",
        "importance": 0.8,
        "confidence": 0.95,
        "source": "user",
        "status": "active",
        "subject_scope": "user",
        "recorded_at": "2026-01-01T12:00:00+00:00",
        "valid_from": "2026-01-01T12:00:00+00:00",
    }
