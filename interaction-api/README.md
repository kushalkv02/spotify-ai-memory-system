# interaction-api

Implements this slice of the overall architecture:

```
Vue.js Client
     │
     ▼ (Playback Events / Chat / UI Actions)
Interaction API (FastAPI)
     │
     ▼ (Validate + Authenticate + Consent Check)
Event Validation Layer
     │
     ▼ (Valid Versioned Event Contract)
PostgreSQL (Raw Immutable Events)
     │
     ▼
Memory Decision Engine  (naive inline placeholder — see orchestrator.py)
     │
     └─→ writes through to the `graph` package (Neo4j), which `spotify_mcp`
         already reads from via its own graph_adapter/tools.
```

## How this connects to `graph/` and `spotify_mcp/`

- `interaction-api` does **not** call `spotify_mcp` directly, and shouldn't.
  `spotify_mcp`'s tools (`memory_tools.py`, `recommendation_tools.py`, etc.)
  already read from Neo4j via `graph/repositories` + `graph/services`.
- Instead, `interaction-api/integrations/graph_client.py` imports your
  existing `graph.services.*` classes directly and calls into them after
  every event is persisted to Postgres. Once an event is written, it's
  visible to `spotify_mcp` on its next query — no new network hop needed.
- **You will need to adjust `integrations/graph_client.py`**: the method
  names called there (`record_interaction`, `create_memory`,
  `update_preferences_from_event`) are best-guesses based on your file
  names. Open that file and match them to your actual
  `graph/services/interaction_service.py` / `memory_service.py` /
  `preference_service.py` signatures.
- A real `memory-decision-engine` service will eventually replace
  `orchestrator.py`'s `_naive_importance()` heuristic — everything else
  (validation, Postgres insert, graph writeback) stays the same when you
  swap that in.

## Folders

- `api/` — FastAPI app, routes, auth/consent middleware, DI wiring
- `validation/` — schema versioning, payload validation, consent check
- `models/` — event contract, consent, and raw-record pydantic models
- `db/` — Postgres client + append-only `event_repository.py` (added beyond
  the original tree — needed for the "PostgreSQL" box to actually work)
- `integrations/` — bridge into the `graph` package (added beyond the
  original tree — this is the "connects with graph/mcp" piece)
- `orchestrator.py` — ties validation → Postgres → graph writeback together
  (added at the package root, used by `interaction_routes.py`)
- `utils/` — logging, timestamps, exceptions

---

## Testing steps

### 1. Install dependencies

```bash
cd spotify-mem-sys/interaction-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Postgres and create the table

Easiest with Docker:

```bash
docker run --name spotify-postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=spotify_interactions -p 5432:5432 -d postgres:16
```

Apply the migration:

```bash
docker exec -i spotify-postgres psql -U postgres -d spotify_interactions \
  < db/migrations/001_create_events_table.sql
```

### 3. Make sure Neo4j (via your existing `graph` package) is reachable

Your Neo4j Desktop instance should already be running per your existing
setup. Confirm `graph/config.py` points at the same URI/credentials
`interaction-api` will end up using through `graph.neo4j_client.Neo4jClient`.

### 4. Make the `graph` package importable

Run uvicorn from the **spotify-mem-sys root** (one level above
`interaction-api/`) so `graph` resolves as a top-level import:

```bash
cd spotify-mem-sys
export PYTHONPATH=$(pwd):$PYTHONPATH
uvicorn interaction-api.api.main:app --reload --port 8000
```

If `graph` fails to import, the app still starts — `graph_client.py` logs a
warning and disables writeback so you can test the API/Postgres path in
isolation first.

### 5. Check health

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```
`readiness` should report `"postgres": "ok"` and whether graph writeback is enabled.

### 6. Submit a test event (dev auth bypass via `X-User-Id`)

`settings.debug=True` + `allow_dev_auth_header=True` by default, so you can
skip minting a JWT while testing:

```bash
curl -X POST http://localhost:8000/interactions/events \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user_123" \
  -d '{
        "user_id": "user_123",
        "category": "playback",
        "payload": {"track_id": "track_abc", "action": "like"}
      }'
```

Expected: `201 Created` with the stored `RawEventRecord`, including
`is_important` and `importance_score` from the naive heuristic
(`like` → important).

Try a chat event:

```bash
curl -X POST http://localhost:8000/interactions/events \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user_123" \
  -d '{
        "user_id": "user_123",
        "category": "chat",
        "payload": {"message": "play something upbeat for a workout"}
      }'
```

### 7. Verify idempotency

Resend the exact same JSON body (same generated `event_id` won't repeat
automatically since it's a UUID default — pass an explicit `event_id` to
test the duplicate path):

```bash
curl -X POST http://localhost:8000/interactions/events \
  -H "Content-Type: application/json" -H "X-User-Id: user_123" \
  -d '{"event_id": "11111111-1111-1111-1111-111111111111",
       "user_id": "user_123", "category": "chat",
       "payload": {"message": "test dup"}}'
# repeat the exact same curl -> expect 409 Conflict
```

### 8. Verify consent enforcement

Turn off the bypass in `config.py` (`allow_dev_consent_bypass: bool = False`)
and resend an event for a user with no granted scopes — expect `403` with
`{"error": "consent_required", "missing_scopes": [...]}`.

### 9. Verify it reaches Postgres

```bash
docker exec -it spotify-postgres psql -U postgres -d spotify_interactions \
  -c "SELECT event_id, category, is_important, importance_score FROM raw_events ORDER BY id DESC LIMIT 5;"
```

### 10. Verify it reaches the graph (once `integrations/graph_client.py` is wired to your real method names)

Open Neo4j Browser / Desktop and check that the interaction/memory nodes
created by your `graph.services` calls show up, then confirm `spotify_mcp`'s
tools (e.g. `memory_tools.py`) can see the same data by running an MCP tool
call against it (or via your MCP client/inspector).

### 11. Automated smoke test (optional)

```bash
pip install pytest pytest-asyncio
```
Write a quick `test_health.py` hitting `/health/live` and `/health/ready`
with `httpx.AsyncClient(app=app, base_url="http://test")` — good first CI check
before wiring real Postgres/Neo4j into a test container.
