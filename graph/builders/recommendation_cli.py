"""Run the graph-native recommendation service from the command line.

Usage (from the project root)::

    python -m graph.builders.recommendation_cli user_001 --strategy all
"""
from __future__ import annotations

import argparse
import json
from typing import Any

from ..neo4j_client import get_client
from ..services.recommendation_service import RecommendationService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Return track recommendations for a user from Neo4j."
    )
    parser.add_argument("user_id", help="The User.user_id to recommend for")
    parser.add_argument(
        "--strategy",
        choices=("collaborative", "artist", "genre", "all"),
        default="all",
        help="Recommendation strategy to run (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum recommendations per strategy (default: 10)",
    )
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be at least 1")
    return args


def get_recommendations(
    service: RecommendationService, strategy: str, user_id: str, limit: int
) -> dict[str, list[dict[str, Any]]]:
    methods = {
        "collaborative": service.collaborative,
        "artist": service.by_artist_affinity,
        "genre": service.by_genre_affinity,
    }
    selected = methods if strategy == "all" else {strategy: methods[strategy]}
    return {
        name: method(user_id, limit=limit)
        for name, method in selected.items()
    }


def main() -> None:
    args = parse_args()
    client = get_client()
    if not client.verify_connectivity():
        raise SystemExit(
            "Could not connect to Neo4j. Copy .env.example to .env, set the "
            "NEO4J_* values, and start the database."
        )

    results = get_recommendations(
        RecommendationService(), args.strategy, args.user_id, args.limit
    )
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
