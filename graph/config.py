"""
Graph configuration.

Loads Neo4j connection settings from environment variables (a `.env`
file is picked up automatically if `python-dotenv` is installed).
See `.env.example` for the variables this expects.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is optional; env vars can also be set directly.
    pass


@dataclass(frozen=True)
class GraphConfig:
    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user: str = os.getenv("NEO4J_USER", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "password")
    database: str = os.getenv("NEO4J_DATABASE", "neo4j")

    max_connection_lifetime: int = int(os.getenv("NEO4J_MAX_CONN_LIFETIME", "3600"))
    max_connection_pool_size: int = int(os.getenv("NEO4J_MAX_POOL_SIZE", "50"))
    connection_acquisition_timeout: int = int(os.getenv("NEO4J_CONN_TIMEOUT", "60"))

    # Root of the cypher/ folder, used by builders to locate .cypher scripts.
    cypher_dir: Path = field(default_factory=lambda: Path(__file__).parent / "cypher")


config = GraphConfig()
