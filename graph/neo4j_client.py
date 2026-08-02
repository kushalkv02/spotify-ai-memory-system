"""
Neo4j connection management.

A single, process-wide driver (singleton) is created from `graph.config`
and reused by every repository. All writes go through `execute_write`,
which uses the driver's managed transaction functions so they are safe
to retry and show up immediately in Neo4j Desktop / Neo4j Browser.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator, Optional

from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import AuthError, ServiceUnavailable

from .config import config

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Thin, singleton wrapper around the official neo4j Python driver."""

    _instance: Optional["Neo4jClient"] = None

    def __init__(self) -> None:
        self._driver: Driver = GraphDatabase.driver(
            config.uri,
            auth=(config.user, config.password),
            max_connection_lifetime=config.max_connection_lifetime,
            max_connection_pool_size=config.max_connection_pool_size,
            connection_acquisition_timeout=config.connection_acquisition_timeout,
        )

    # -- singleton -----------------------------------------------------
    @classmethod
    def get_instance(cls) -> "Neo4jClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -- connectivity ----------------------------------------------------
    def verify_connectivity(self) -> bool:
        try:
            self._driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s (db=%s)", config.uri, config.database)
            return True
        except (ServiceUnavailable, AuthError) as exc:
            logger.error("Neo4j connectivity check failed: %s", exc)
            return False

    # -- sessions / execution --------------------------------------------
    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._driver.session(database=config.database)
        try:
            yield session
        finally:
            session.close()

    def execute_read(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        with self.session() as session:
            result = session.execute_read(lambda tx: list(tx.run(query, parameters or {})))
            return [record.data() for record in result]

    def execute_write(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        with self.session() as session:
            result = session.execute_write(lambda tx: list(tx.run(query, parameters or {})))
            return [record.data() for record in result]

    def run_script(self, cypher_text: str) -> None:
        """
        Execute a multi-statement .cypher file. Statements are split on
        `;` at end-of-line and blank / comment-only (`//`) lines are
        skipped. Good enough for our schema/seed scripts; not a general
        Cypher parser.
        """
        statements = []
        for raw in cypher_text.split(";"):
            stmt = "\n".join(
                line for line in raw.splitlines() if not line.strip().startswith("//")
            ).strip()
            if stmt:
                statements.append(stmt)

        with self.session() as session:
            for statement in statements:
                session.execute_write(lambda tx, stmt=statement: tx.run(stmt))
                logger.debug("Executed statement: %s", statement.splitlines()[0][:80])

    def close(self) -> None:
        self._driver.close()
        Neo4jClient._instance = None


def get_client() -> Neo4jClient:
    return Neo4jClient.get_instance()
