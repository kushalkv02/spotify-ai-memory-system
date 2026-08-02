"""
graph
=====
Graph persistence layer for the Spotify AI Memory System.

This package owns everything related to Neo4j: connection management,
schema (constraints/indexes), seed data, node/edge models, repositories
(one per entity), higher-level services, reusable query strings, and
one-off builders/scripts.

Typical entry point for other parts of the app (e.g. the future FastAPI
Interaction API) is `graph.services.graph_service.get_graph_service()`.
"""
from .config import config
from .neo4j_client import get_client, Neo4jClient

__all__ = ["config", "get_client", "Neo4jClient"]
