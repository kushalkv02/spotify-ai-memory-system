# Reverie — Spotify AI Memory System

Reverie is a Spotify-style music application that remembers a listener’s
preferences across playback and conversation. It combines a Vue 3 client, a
FastAPI interaction API, PostgreSQL for an immutable event/audit trail, Neo4j
for listener state and explainable relationships, and an MCP server that makes
the graph available to compatible AI hosts.

The project is intentionally designed so an LLM can help interpret or rank
music choices without becoming the source of truth: validation, consent,
memory-retention rules, event history, and recommendation exclusions remain
deterministic and persisted.

## Contents

- [What it does](#what-it-does)
- [Architecture](#architecture)
- [Repository layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Running the services](#running-the-services)
- [API overview](#api-overview)
<<<<<<< HEAD
- [Langgraph automation](#langgraph-automation)
=======
>>>>>>> 56e6d0d (readme commit)
- [Memory and recommendation behavior](#memory-and-recommendation-behavior)
- [MCP server](#mcp-server)
- [Development, tests, and troubleshooting](#development-tests-and-troubleshooting)

## What it does

- Provides a responsive Spotify-inspired browsing, library, player, and chat
  interface.
- Supports account signup/login with JWT bearer authentication, with a local
  `X-User-Id` development bypass enabled by default.
- Captures plays, skips, likes, follows, chat messages, and explicit
  preferences through a versioned event contract.
- Saves every accepted event in PostgreSQL before projecting it into Neo4j.
- Derives durable, versioned memories and preference evidence from explicit or
  high-confidence signals.
- Recommends music from graph-based collaborative/artist/genre affinity plus a
  deterministic client-side ranker that respects exclusions.
- Uses Gemini optionally for structured preference extraction and ordering a
  pre-approved candidate set; deterministic fallbacks keep chat useful without
  an API key or when Gemini is unavailable.
- Exposes playback, engagement, memory, recommendation, reasoning, user, and
  track capabilities through Model Context Protocol (MCP).

## Architecture

```mermaid
flowchart LR
  UI[Vue 3 + Vite client] --> API[FastAPI Interaction API]
  API --> AUTH[JWT auth, consent, validation]
  AUTH --> PG[(PostgreSQL\nusers · raw events · decisions)]
  AUTH --> ORCH[Memory extraction + orchestration]
  ORCH --> NEO[(Neo4j\nstate · history · memories · preferences)]
  API -. optional structured extraction/ranking .-> GEMINI[Gemini]
  MCPHost[MCP-compatible host] --> MCP[FastMCP server]
  MCP --> NEO
```

The main write path is:

1. The client sends an interaction or chat message to FastAPI.
2. Authentication, schema validation, and consent checks run first.
3. The raw event is appended to PostgreSQL with an idempotency key.
4. `MemoryExtractor` deterministically records a separate memory decision.
5. The graph client projects interaction state to Neo4j and, where retained,
   creates memory and preference evidence.
6. The chat workflow reads graph evidence, creates safe candidates, and uses
   Gemini only as an optional interpreter/ranker.

`ARCHITECTURE.md` contains the detailed workflow diagrams and data-model
semantics.

## Repository layout

```text
.
├── client/                 Vue 3/Vite single-page application
│   └── src/                views, Pinia stores, API services, components
├── interaction-api/        FastAPI HTTP API and chat workflow
│   ├── api/routes/         auth, health, interactions, catalog, and chat routes
│   ├── db/                 asyncpg repositories and SQL migrations
│   ├── services/           memory extraction, chat assistant, LangGraph flow
│   └── integrations/       the API boundary into graph/
├── graph/                  Neo4j models, repositories, services, Cypher, seeds
│   └── builders/           schema/seed/demo and recommendation CLI commands
├── spotify_mcp/            FastMCP server over graph capabilities
│   ├── tools/              tool groups by domain
│   └── resources/          Spotify URI resources for users and memories
├── tests/                  pytest unit and API tests
├── ARCHITECTURE.md         detailed component and workflow documentation
├── RECOMMENDATIONS.md      graph recommendation CLI and Python examples
└── requirements.txt        graph/MCP Python dependencies
```

## Prerequisites

- Python 3.11+ (Python 3.10 may work, but 3.11 is recommended)
- Node.js 18+ and npm
- PostgreSQL 16+ (Docker is the quickest local option)
- Neo4j 5.x (Neo4j Desktop or a local server)
- A Gemini API key only if Gemini-backed chat extraction/ranking is desired

## Quick start

These commands assume you are at the repository root.

### 1. Create and configure an environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r interaction-api/requirements.txt
cp .env.example .env
```

Edit `.env` with your Neo4j credentials. Add the Interaction API settings
shown in [Configuration](#configuration), particularly the PostgreSQL DSN.
Never commit `.env` or an API key.

### 2. Start PostgreSQL and apply migrations

The default API DSN uses port `5433`; this Docker command matches it:

```bash
docker run --name reverie-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=spotify_interactions \
  -p 5433:5432 -d postgres:16
```

Run all migrations in order:

```bash
for migration in interaction-api/db/migrations/*.sql; do
  docker exec -i reverie-postgres psql -U postgres -d spotify_interactions < "$migration"
done
```

If PostgreSQL already runs elsewhere, set `INTERACTION_API_POSTGRES_DSN`
instead and execute the same SQL files with your own `psql` connection.

### 3. Start Neo4j and initialize the graph

Start your Neo4j database, then apply constraints/indexes and load the bundled
catalog, users, interaction history, and sample memories:

```bash
python -m graph.builders.graph_builder --schema --seed
```

You can inspect it in Neo4j Browser with:

```cypher
MATCH (n) RETURN n LIMIT 50
```

### 4. Start the API

```bash
uvicorn interaction-api.api.main:app --reload --port 8000
```

Swagger UI is available at `http://127.0.0.1:8000/docs`; liveness is at
`http://127.0.0.1:8000/health/live`.

### 5. Start the web client in another terminal

```bash
cd client
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. By default Vite proxies `/api` calls to
`http://localhost:8000`.

## Configuration

All Python services load the root `.env`. The included `.env.example` covers
Neo4j and basic MCP variables; add the API values below when needed.

```dotenv
# Neo4j — required for graph setup, API graph writeback, and MCP
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=replace-with-your-password
NEO4J_DATABASE=neo4j

# Interaction API — values use the INTERACTION_API_ prefix
INTERACTION_API_POSTGRES_DSN=postgresql://postgres:postgres@localhost:5433/spotify_interactions
INTERACTION_API_JWT_SECRET=replace-this-in-production
INTERACTION_API_DEBUG=true
INTERACTION_API_ALLOW_DEV_AUTH_HEADER=true
INTERACTION_API_ALLOW_DEV_CONSENT_BYPASS=true
INTERACTION_API_MEMORY_RETENTION_THRESHOLD=0.55

# Optional Gemini integration; omitting the key enables deterministic fallback
INTERACTION_API_GEMINI_API_KEY=your-google-ai-studio-key
INTERACTION_API_GEMINI_MODEL=gemini-3.5-flash

# Optional MCP transport configuration
MCP_TRANSPORT=stdio
# MCP_HOST=127.0.0.1
# MCP_PORT=8000
```

Important production settings:

- Set a strong `INTERACTION_API_JWT_SECRET`, set `INTERACTION_API_DEBUG=false`,
  and disable `INTERACTION_API_ALLOW_DEV_AUTH_HEADER`.
- Configure `INTERACTION_API_CORS_ALLOWED_ORIGINS` to the deployed client
  origin(s).
- Do not expose an unauthenticated MCP HTTP endpoint. Put it behind TLS and
  authentication or a private network.

For a separately hosted frontend, create `client/.env`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

For local proxying, leave it unset. `VITE_API_PROXY_TARGET` can change Vite’s
development proxy target without changing browser-visible URLs.

## Running the services

### Frontend

```bash
cd client
npm run dev       # local development server
npm run build     # production build in client/dist
npm run preview   # preview the production build
```

### Interaction API

```bash
uvicorn interaction-api.api.main:app --reload --host 127.0.0.1 --port 8000
```

At startup the API connects to PostgreSQL and makes the starter catalog artists
available in Neo4j. It requires PostgreSQL to start. Interaction and chat
shortcuts also require graph writeback; a failed Neo4j projection produces a
`503` after the raw event has safely been saved in PostgreSQL.

The local development auth header lets you exercise protected endpoints before
creating an account:

```bash
curl 'http://127.0.0.1:8000/tracks/search?q=midnight' \
  -H 'X-User-Id: local-user'
```

### Graph tools

```bash
# Apply schema, seed data, or record a small demo interaction set
python -m graph.builders.graph_builder --schema --seed
python -m graph.builders.graph_builder --demo

# Print recommendations as JSON
python -m graph.builders.recommendation_cli user_001 --strategy all --limit 5
```

Use `--drop` only when you deliberately want to remove the graph schema while
iterating.

## API overview

All endpoints except health, signup, and login require either a bearer JWT or,
in the default local configuration, `X-User-Id`. The API’s interactive OpenAPI
specification at `/docs` is the authoritative request/response reference.

| Area | Endpoints | Purpose |
| --- | --- | --- |
| Health | `GET /health/live`, `GET /health/ready` | Liveness and Postgres/graph status |
| Auth | `POST /auth/signup`, `POST /auth/login`, `GET /auth/me` | Accounts and JWTs |
| Interaction shortcuts | `POST /interactions/play`, `/skip`, `/like`, `/follow` | Client-friendly playback and engagement writes |
| Explicit state | `POST/DELETE /interactions/likes`, `POST/DELETE /interactions/follows` | Set or reverse likes/follows |
| Event ingestion | `POST /interactions/events`, `POST /interactions/events/batch` | Versioned raw event contracts |
| Preferences | `POST /interactions/preferences` | Persist a structured explicit preference |
| Catalog | `GET /tracks/feed`, `/tracks/search`, `/recommendations`, `/library`, `/artists`, `/artists/{id}`, `/albums/{id}`, `/playlists/{id}` | Starter catalog and personalized views |
| Chat | `GET/POST/DELETE /chat/messages`, `GET /chat/quick-replies` | Conversational preference capture and recommendations |

Example event ingestion with development auth:

```bash
curl -X POST http://127.0.0.1:8000/interactions/events \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: user_123' \
  -d '{
    "user_id": "user_123",
    "category": "playback",
    "payload": {"track_id": "track_abc", "action": "like"}
  }'
```

Example chat request:

```bash
curl -X POST http://127.0.0.1:8000/chat/messages \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: user_123' \
  -d '{"content":"I like Nova Lane’s Midnight Circuit but not Neon Rain"}'
```

Chat responses include extracted `preferencesSaved`, `trackRefs`, whether the
memory was retained, and whether Gemini or the deterministic fallback ranked
the recommendations.

<<<<<<< HEAD
## Langgraph Automation

### LangGraph automation

LangGraph acts as the orchestration layer of the conversational recommendation system. The workflow maintains a shared state containing the user's identity, email, question, extracted entities, retrieved memories, Spotify data, and final answer.

The workflow first identifies the current user and extracts relevant entities and intent from the question. It then retrieves recent structured memories from Neo4j and performs semantic-memory retrieval from ChromaDB using Gemini embeddings.

Based on the retrieved context and the user's request, the workflow conditionally determines whether memory-based reasoning or Spotify catalog search is required. When catalog information is required, the workflow invokes the search_tracks capability through the Spotify MCP server.

Finally, the retrieved memory and Spotify context are passed to the Gemini LLM to generate the final response, which is returned through FastAPI to the Vue.js chat interface.

ChromaDB provides semantic memory retrieval. User memories are represented as embeddings, allowing the system to retrieve memories based on semantic similarity rather than requiring an exact keyword match. The retrieved semantic memories are combined with recent structured memories from Neo4j before recommendation generation.

`services/chat_workflow.py` is the orchestrator for every `POST /chat/messages`
request. It keeps the existing Postgres/Neo4j services as the systems of
record, while LangGraph controls the order and state passed between stages:

```mermaid
flowchart LR
  A[understand\nGemini + fallback] --> B[persist\nEvent + memory pipeline]
  B --> C[project_preferences\nNeo4j + UI projection]
  C --> D[recommend\nGraph + local ranker]
  D --> E[compose_reply]
```

This is deliberately a per-turn workflow without a LangGraph checkpoint:
conversation and memory durability remain in the project’s existing Postgres
and Neo4j data model. Add a LangGraph checkpointer later only if you need
interrupt/resume or human approval between these nodes.

                         ┌──────────────────────┐
                         │      Vue.js UI       │
                         │  Chat + Auth + Player│
                         └──────────┬───────────┘
                                    │
                                    │ POST /chat/messages
                                    ▼
                         ┌──────────────────────┐
                         │   FastAPI Backend    │
                         │ chat_workflow.py     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │        LangGraph             │
                    │       ChatRecommendation     |
                    |                Workflow      │
                    └──────────────┬───────────────┘
                                   │
             ┌─────────────────────┴─────────────────────┐
             │                                           │
             ▼                                           ▼
     ┌────────────────────┐                     ┌────────────────────┐
     │ Node 1             │                     │ Shared State       │
     │ User Identification│───────────────────▶️│ user_id            │
     │ by email           │                     │ email              │
     └─────────┬──────────┘                     │ question           │
               │                                │ entities           │
               ▼                                │ memories           │
     ┌────────────────────┐                     │ spotify_data       │
     │ Node 2             │                     │ answer             │
     │ Entity Extraction  │                     └────────────────────┘
     │ / Intent Analysis  │
     └─────────┬──────────┘
             │
             ▼
     ┌────────────────────┐
     │ Node 3             │
     │ Recent Memory      │
     │ Retrieval          │
     │                    │
     │ Neo4j              │
     └─────────┬──────────┘
               │
               ▼
     ┌────────────────────┐
     │ Node 4             │
     │ Semantic Memory    │
     │ Retrieval          │
     │                    │
     │ ChromaDB           │
     │ + Gemini Embedding │
     └─────────┬──────────┘
               │
               ▼
          ┌─────────────┐
          │ Conditional │
          │ Decision    │
          └──────┬──────┘
                 │
         ┌───────┴────────┐
         │                │
         ▼                ▼
     Memory-based       Catalog/
     recommendation     Spotify search
           │                │
           │                ▼
           │       ┌──────────────────┐
           │       │ Spotify MCP      │
           │       │ search_tracks    │
           │       └────────┬─────────┘
           │                │
           └────────┬───────┘
                    ▼
          ┌────────────────────┐
          │ Recommendation /   │
          │ Response Generation│
          │                    │
          │ Gemini LLM         │
          └──────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Final Answer     │
            │ state["answer"]  │
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ FastAPI Response │
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │ Vue Chat UI      │
            └──────────────────┘

=======
>>>>>>> 56e6d0d (readme commit)
## Memory and recommendation behavior

### Storage responsibilities

| Store | Holds | Why |
| --- | --- | --- |
| PostgreSQL | Accounts, append-only raw events, memory decisions | Auditability, retries, idempotency, and event truth |
| Neo4j | Music catalog, listener state, event relationships, preferences, versioned memories | Traversal, reasoning, personalized retrieval |
| In-memory client state | Small starter catalog, current UI projections, local ranking state | Responsive demo/client experience |

<<<<<<< HEAD
### Memory Architecture: 
                   USER QUESTION
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
          Neo4j                   ChromaDB
       Structured               Semantic
        Memory                  Memory
             │                       │
             │                       │
      recent memories        embedding similarity
             │                       │
             └───────────┬───────────┘
                         ▼
                  Combined Memories
                         │
                         ▼
                  Recommendation
                    Generation

=======
>>>>>>> 56e6d0d (readme commit)
### Event/state semantics

- Plays and skips create a new `PLAYED` or `SKIPPED` relationship every time,
  preserving listening history.
- Likes and follows are current state: Neo4j merges them; unlike/unfollow
  removes them.
- A retained memory has a stable `memory_id`, immutable `version_id`, strength,
  confidence, validity range, and source event. Expired state memories remain
  auditable but are not retrieved.
- The default memory retention threshold is `0.55`. Explicit preferences,
  corrections, exclusions, and strong language are more likely to cross it
  than passive plays, skips, or vague chats.
- Unliking or unfollowing reverses matching state memory; it does not create a
  new negative preference.

### Recommendation safety

Neo4j provides collaborative, artist-affinity, and genre-affinity candidates.
The client-state ranker de-duplicates candidates and applies active preference
and exclusion signals. Gemini, if configured, can only select IDs from that
already-safe candidate list and write a rationale. It cannot invent tracks,
change a memory score, or bypass exclusions.

## MCP server

The MCP server is separate from the HTTP API but reads the same Neo4j graph.
It never embeds Cypher in tools: `spotify_mcp/adapters/graph_adapter.py` is the
single boundary from MCP to `graph/` services.

Start a local stdio server for an MCP host that launches it as a subprocess:

```bash
python -m spotify_mcp
```

For a URL-based host, use Streamable HTTP:

```bash
MCP_TRANSPORT=streamable-http MCP_HOST=127.0.0.1 MCP_PORT=8001 \
  python -m spotify_mcp
```

The endpoint is then `http://127.0.0.1:8001/mcp`. Port `8001` is used above to
avoid clashing with the FastAPI service on `8000`.

Available capabilities include:

- Playback: record a play and retrieve recent plays
- Engagement: like/unlike/skip tracks and follow/unfollow artists
- Memories: store and retrieve recent memories
- Recommendations: collaborative, artist, and genre affinity; structured
  recommendation replies
- Reasoning: timelines, preferences, and recommendation explanations
- Users/tracks: get/create users, search/create tracks
- Resources: `spotify://user/{user_id}/profile` and recent memories

For a Claude Desktop-style local configuration:

```json
{
  "mcpServers": {
    "spotify-memory": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["-m", "spotify_mcp"],
      "cwd": "/absolute/path/to/spotify-mem-sys"
    }
  }
}
```

See [`spotify_mcp/README.md`](spotify_mcp/README.md) for a full tool list and
SSE/HTTP connection notes.

## Development, tests, and troubleshooting

### Tests

Run Python tests from the project root:

```bash
pytest
```

Run client service tests:

```bash
cd client
npm test
```

### Useful checks

```bash
# API health
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready

# Build the web client
(cd client && npm run build)

# List registered MCP tools without connecting a host
python -c 'import asyncio; from spotify_mcp.server import mcp; asyncio.run(mcp.list_tools())'
```

### Common issues

| Symptom | Likely cause and fix |
| --- | --- |
| API startup fails | PostgreSQL is unavailable or the DSN is wrong. Start the container and confirm `INTERACTION_API_POSTGRES_DSN`. |
| Neo4j connection error | Start the Neo4j database and verify `NEO4J_URI`, user, password, and database name. |
| `503` after a play/like/chat shortcut | The raw event was saved but mandatory graph writeback failed. Inspect Neo4j connectivity and server logs. |
| Browser gets `401` | Log in, or use `X-User-Id` only while debug/dev-header bypass remains enabled. |
| Chat says deterministic fallback | Expected when no Gemini key is configured or Gemini is unavailable; functionality and safety checks remain in place. |
| No recommendations for a new user | The graph strategies need listening evidence. Seed the graph or record plays/preferences first. |
| MCP server seems idle | Normal with `stdio`: it waits for an MCP client and does not serve a browser page. |

## Further reading

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — full architecture, decision pipeline,
  graph semantics, and deployment notes
- [`RECOMMENDATIONS.md`](RECOMMENDATIONS.md) — recommendation strategy details
- [`interaction-api/README.md`](interaction-api/README.md) — API-focused notes
- [`client/README.md`](client/README.md) — frontend-focused notes
- [`spotify_mcp/README.md`](spotify_mcp/README.md) — MCP tool/server reference
# spotify-ai-memory-system
