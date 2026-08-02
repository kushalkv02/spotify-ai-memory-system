# graph/ — Neo4j layer for the Spotify AI Memory System

This is the graph persistence layer described in your architecture diagram
(everything from `Memory Decision Engine` down through `Neo4j Graph`).
It's usable standalone right now — no FastAPI / frontend required — via
the seed scripts and `GraphService`.

## 1. Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # then fill in your Neo4j Desktop credentials
```

Make sure the database is **started** in Neo4j Desktop first (the driver
will fail to connect otherwise).

## 2. Create schema + load seed data

Run from the folder that contains `graph/` (so it's importable as a package):

```bash
python -m graph.builders.graph_builder --schema --seed
```

This will:
- Apply all constraints/indexes in `graph/cypher/schema/`
- Load sample data from `graph/cypher/seed/`: 4 users, 4 artists / 5 albums /
  12 tracks, a spread of `PLAYED`/`LIKED`/`SKIPPED`/`FOLLOWED` interactions
  across those users (enough overlap for collaborative filtering to return
  real results — `user_001` and `user_002` share several plays), and a
  sample memory

Open **Neo4j Browser** (or the Desktop graph view) and run:

```cypher
MATCH (n) RETURN n LIMIT 50
```

to see everything.

## 3. Record interaction events dynamically (the core feature)

`GraphService` exposes one method per interaction signal. All of them
create the User/Track/Artist nodes if they don't exist yet (pass the
optional name/title args), then write the relationship with a timestamp.

| Method | Relationship | Type |
|---|---|---|
| `record_play_event(user_id, track_id, ...)` | `(User)-[:PLAYED]->(Track)` | event — new edge every call, full history kept |
| `like_track(user_id, track_id, ...)` | `(User)-[:LIKED]->(Track)` | state — idempotent, re-liking refreshes the timestamp |
| `unlike_track(user_id, track_id)` | deletes `LIKED` | state |
| `record_skip_event(user_id, track_id, ...)` | `(User)-[:SKIPPED]->(Track)` | event — mirrors PLAYED |
| `follow_artist(user_id, artist_id, ...)` | `(User)-[:FOLLOWED]->(Artist)` | state — idempotent |
| `unfollow_artist(user_id, artist_id)` | deletes `FOLLOWED` | state |

```python
from graph.services.graph_service import get_graph_service

service = get_graph_service()

service.record_play_event(
    user_id="user_001",
    track_id="track_001",
    user_display_name="Kushal",   # optional — creates the User if new
    track_title="The Less I Know the Better",  # optional — creates the Track if new
    ms_played=180000,
    context="manual_test",
)

service.like_track(user_id="user_001", track_id="track_001")
service.record_skip_event(user_id="user_001", track_id="track_004", ms_played=5000)
service.follow_artist(user_id="user_001", artist_id="artist_002")
```

Or via the built-in demo (records one play, like, skip, and follow for `user_001`):

```bash
python -m graph.builders.graph_builder --demo
```

Then in Neo4j Browser:

```cypher
MATCH (u:User)-[r]->(x)
WHERE type(r) IN ['PLAYED', 'LIKED', 'SKIPPED', 'FOLLOWED']
RETURN u, r, x
```

You'll see the relationships appear immediately — every call is a direct,
synchronous write, no queue in between.

**Why PLAYED/SKIPPED use `CREATE` but LIKED/FOLLOWED use `MERGE`:** plays
and skips are events — a user can play or skip the same track many times,
and each one is meaningful history, so a new edge is created every call.
Likes and follows are state — a user either likes a track or doesn't, so
the relationship is merged (one edge, timestamp refreshes) and removed
explicitly via `unlike_track`/`unfollow_artist` rather than piling up.

## 4. Reset schema while iterating

```bash
python -m graph.builders.graph_builder --drop
```

## 5. Get recommendations

After loading data, use the dedicated command-line runner:

```bash
python -m graph.builders.recommendation_cli user_001 --strategy all --limit 5
```

See [RECOMMENDATIONS.md](RECOMMENDATIONS.md) for direct Python and MCP usage,
the available strategies, and the expected result fields.

## Layout

- `neo4j_client.py` — singleton driver + read/write helpers, used by every repository
- `config.py` — reads connection settings from `.env`
- `cypher/` — raw `.cypher` files: `schema/` (constraints/indexes), `seed/` (sample data:
  `user_seed.cypher`, `music_seed.cypher`, `interactions_seed.cypher`, `sample_memories.cypher`
  — run in that order, each one MATCHes nodes the previous file created),
  `queries/` (reference queries, mirrored as Python strings in `queries/*.py`)
- `models/` — plain dataclasses, one per node label (`User`, `Track`, `Memory`, ...)
- `repositories/` — the only layer that writes Cypher; one file per entity plus
  `base_repository.py` for the common MERGE/GET/DELETE pattern.
  `playback_repository.py` and `engagement_repository.py` are the odd ones out —
  they manage *relationships* (`PLAYED`/`LIKED`/`SKIPPED`/`FOLLOWED`), not nodes,
  so neither subclasses `BaseRepository`.
- `services/` — orchestration on top of repositories. **`graph_service.py` is the
  main entry point** — `record_play_event()` is what the future Interaction API
  will call for every playback event.
- `queries/` — parametrized Cypher strings as Python constants, used by services
  that don't need a full repository (recommendations, reasoning, analytics).
- `utils/` — timestamps, dict/node serialization, id validation.
- `builders/` — runnable orchestration: `graph_builder.py` (schema + seed + demo),
  `memory_builder.py` / `preference_builder.py` (placeholders for the
  LLM-summary and preference-aggregation steps upstream in your diagram).

## Next steps (not built yet, on purpose)

- `interaction_service.handle_event()` already accepts the same event shape your
  FastAPI Interaction API will eventually send — point that endpoint at it directly.
- `recommendation_service.py` / `reasoning_service.py` use plain Cypher heuristics
  today (collaborative filtering, artist affinity) — swap in the MCP/LLM layer
  from your diagram once that exists; the graph queries underneath don't need to change.
- `preference_service.recompute_genre_preferences()` has a TODO: `get_recent_plays`
  doesn't return `genre` yet — extend that query to join `Track.genre` before this
  will produce real numbers.
