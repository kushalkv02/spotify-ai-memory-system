from __future__ import annotations

from typing import Any


def node_to_dict(node: Any) -> dict[str, Any]:
    """
    Normalize a neo4j Node (or a plain dict already returned by
    Neo4jClient, which calls .data() under the hood) into a plain dict.
    """
    if isinstance(node, dict):
        return dict(node)
    return dict(node.items())  # neo4j.graph.Node supports .items()


def records_to_dicts(records: list[Any]) -> list[dict[str, Any]]:
    return [node_to_dict(r) for r in records]
