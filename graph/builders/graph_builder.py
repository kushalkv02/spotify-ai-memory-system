"""
Orchestrates schema setup and seed loading, and doubles as a runnable
demo script.

Usage (from the project root, so `graph` is importable):

    python -m graph.builders.graph_builder --schema --seed --demo
    python -m graph.builders.graph_builder --drop        # reset schema
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ..config import config
from ..neo4j_client import get_client

CYPHER_DIR: Path = config.cypher_dir


def _run_file(relative_path: str) -> None:
    path = CYPHER_DIR / relative_path
    client = get_client()
    client.run_script(path.read_text(encoding="utf-8"))
    print(f"  ✓ executed {relative_path}")


def apply_schema() -> None:
    print("Applying schema...")
    _run_file("schema/create_constraints.cypher")
    _run_file("schema/create_indexes.cypher")


def drop_schema() -> None:
    print("Dropping schema...")
    _run_file("schema/drop_schema.cypher")


def apply_seed() -> None:
    print("Loading seed data...")
    _run_file("seed/user_seed.cypher")
    _run_file("seed/music_seed.cypher")
    _run_file("seed/interactions_seed.cypher")
    _run_file("seed/sample_memories.cypher")


def run_demo_event() -> None:
    """
    Records one live event of each interaction type using the exact
    same GraphService the future Interaction API will call. Open
    Neo4j Desktop / Browser and re-run:
        MATCH (u:User)-[r]->(x) WHERE type(r) IN ['PLAYED','LIKED','SKIPPED','FOLLOWED']
        RETURN u, r, x
    to watch them appear.
    """
    from ..services.graph_service import get_graph_service

    service = get_graph_service()

    print("Recording a demo play event...")
    print(f"  ✓ {service.record_play_event(user_id='user_001', track_id='track_001', ms_played=180000, context='demo_script')}")

    print("Recording a demo like event...")
    print(f"  ✓ {service.like_track(user_id='user_001', track_id='track_003')}")

    print("Recording a demo skip event...")
    print(f"  ✓ {service.record_skip_event(user_id='user_001', track_id='track_004', ms_played=5000, context='demo_script')}")

    print("Recording a demo follow event...")
    print(f"  ✓ {service.follow_artist(user_id='user_001', artist_id='artist_002')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Graph schema/seed builder")
    parser.add_argument("--schema", action="store_true", help="Create constraints & indexes")
    parser.add_argument("--seed", action="store_true", help="Load seed data (users, music, memories)")
    parser.add_argument("--drop", action="store_true", help="Drop all constraints & indexes")
    parser.add_argument("--demo", action="store_true", help="Record one demo PLAYED event")
    args = parser.parse_args()

    client = get_client()
    if not client.verify_connectivity():
        raise SystemExit(
            "Could not connect to Neo4j. Check graph/.env (NEO4J_URI / NEO4J_USER / "
            "NEO4J_PASSWORD) and make sure the database is started in Neo4j Desktop."
        )

    if args.drop:
        drop_schema()
    if args.schema:
        apply_schema()
    if args.seed:
        apply_seed()
    if args.demo:
        run_demo_event()

    if not any([args.drop, args.schema, args.seed, args.demo]):
        parser.print_help()


if __name__ == "__main__":
    main()
