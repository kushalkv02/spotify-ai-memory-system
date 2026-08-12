# Spotify AI Memory System Architecture

## Overview

The project is a music application with durable, explainable listener memory.
The Vue client submits interactions and chat messages to FastAPI. FastAPI
validates each event, writes the immutable record to PostgreSQL, then projects
approved state and memory into Neo4j. The graph is also exposed as an MCP
server so Gemini, Claude, GPT, or another compatible host can use tools.

```mermaid
flowchart TB
  UI[Vue client] --> API[FastAPI interaction-api]
  API --> AUTH[Authentication, consent, validation]
  AUTH --> ORCH[InteractionOrchestrator and MemoryExtractor]
  ORCH --> PG[(PostgreSQL: users, raw events, decisions)]
  ORCH --> GC[GraphClient integration]
  GC --> NEO[(Neo4j: graph state, memories, preferences)]
  UI -->|chat request| API
  API -. structured extraction and ranking .-> GEMINI[Gemini]
  HOST[MCP-compatible LLM host] --> MCP[spotify_mcp FastMCP server]
  MCP --> NEO
```

## Components and boundaries

| Component | Responsibility | Key files |
| --- | --- | --- |
| `client/` | Vue views/components, player and chat UI, API requests | `src/services/*`, `src/store/*` |
| `interaction-api/` | HTTP endpoints, auth, consent, event pipeline, chat workflow | `api/`, `orchestrator.py`, `services/chat_workflow.py` |
| PostgreSQL | Immutable event system of record and memory-decision audit | `db/event_repository.py`, `db/memory_decision_repository.py` |
| `graph/` | Domain models, Cypher repositories, graph behavior, reasoning and recommendations | `services/`, `repositories/` |
| Neo4j | Listener state, event history, versioned memories, preference evidence | `neo4j_client.py` |
| `spotify_mcp/` | FastMCP tool/resource interface for graph capabilities | `server.py`, `tools/`, `adapters/graph_adapter.py` |
| Gemini | Optional structured preference extraction and recommendation ranking | `services/chat_assistant.py` |

Rules that keep the system maintainable:

1. The client never writes directly to PostgreSQL or Neo4j.
2. Raw events are persisted to PostgreSQL before graph projection.
3. `GraphClient` is the `interaction-api` boundary into `graph/`.
4. `spotify_mcp/adapters/graph_adapter.py` is the MCP boundary into `graph/`.
5. Repositories own Cypher; services own domain behavior; routes/tools do not
   contain Cypher.
6. Gemini can extract or choose from safe candidates, but cannot override
   validation, memory-retention policy, or deterministic exclusions.

## Data model

PostgreSQL stores `users`, immutable `raw_events`, and `memory_decisions`.
Neo4j contains `User`, `Track`, `Artist`, `Album`, `Playlist`, `Session`,
`Conversation`, and versioned `Memory` nodes.

| Neo4j relationship | Meaning | Lifecycle |
| --- | --- | --- |
| `PLAYED` | Play with timestamp/context/duration | New edge for every event |
| `SKIPPED` | Skip with timestamp/context/duration | New edge for every event |
| `LIKED` | Current track-like state | Merged; deleted by unlike |
| `FOLLOWED` | Current artist/album-follow state | Merged; artist edge deleted by unfollow |
| `HAS_MEMORY` | User owns a memory version | Versioned link |
| `REFERENCES` | Memory refers to a track | Versioned link |
| `PREFERS` | Explicit/derived preference evidence | Updated or recomputed |
| `BY` | Track-to-artist catalog metadata | Catalog state |

A memory has a stable `memory_id` and immutable `version_id`, along with
importance, confidence, validity range, source event, and status. Like/follow
memories also retain canonical action/entity metadata so reversal targets only
the matching state memory. Expired memories remain auditable but are excluded
from retrieval and recommendations.

## Feature workflows

### Authentication and consent

```mermaid
flowchart LR
  A[Client request] --> B[Auth middleware]
  B -->|valid identity| C[Route receives authenticated user_id]
  B -->|invalid or missing| D[401 or 403]
  C --> E[Consent and event validation]
  E -->|approved| F[Continue]
  E -->|missing scope| G[ConsentDeniedError and 403]
```

The authenticated identity is authoritative; interaction routes reject a
payload `user_id` that does not match it.

### Play event

```mermaid
flowchart TD
  A[POST /interactions/play] --> B[Resolve catalog track metadata]
  B --> C[EventEnvelope action=play]
  C --> D[Validate auth, consent, schema]
  D --> E[Insert raw event in PostgreSQL]
  E --> F[MemoryExtractor classifies event]
  F --> G[Store decision and processed score]
  G --> H[GraphClient.record_interaction]
  H --> I[InteractionService then GraphService]
  I --> J[MERGE User/Track as needed]
  J --> K[CREATE User-PLAYED-Track]
  K --> L[Return event ID]
```

Play relationships are event history: replaying a track creates another
`PLAYED` edge and keeps the full listening timeline.

### Skip event and reasoning tools

```mermaid
flowchart TD
  A[POST /interactions/skip] --> B[Ingest action=skip]
  B --> C[PostgreSQL raw event and decision]
  C --> D[GraphService.record_skip_event]
  D --> E[CREATE User-SKIPPED-Track]
  E --> F[ReasoningService.get_recent_skips]
  F --> G[MCP get_recent_skips or explanation fallback]
```

`get_recent_plays` and `get_recent_skips` are both registered MCP tools.
They delegate through `GraphAdapter` and `ReasoningService`, making the same
evidence available to an MCP host and to the application fallback.

### Like and unlike

```mermaid
flowchart TD
  A[Like endpoint] --> B{Already liked?}
  B -->|no| C[Ingest action=like]
  B -->|yes on toggle route| D[Ingest action=unlike]
  C --> E[MERGE User-LIKED-Track]
  E --> F[Accepted explicit-preference memory]
  F --> G[Create active Memory tagged with track/action]
  D --> H[DELETE User-LIKED-Track]
  H --> I[Expire matching active like Memory]
  I --> J[No exclusion memory is created]
```

Unlike reverses a stateful preference; it is not interpreted as dislike. The
prior state memory becomes non-retrievable instead of affecting future ranking.

### Follow and unfollow artist

```mermaid
flowchart TD
  A[Follow endpoint] --> B{Already followed?}
  B -->|no| C[Ingest action_type=follow_artist]
  B -->|yes on toggle route| D[Ingest action_type=unfollow_artist]
  C --> E[MERGE User-FOLLOWED-Artist]
  E --> F[Create active Memory tagged with artist/action]
  D --> G[DELETE User-FOLLOWED-Artist]
  G --> H[Expire matching active follow Memory]
  H --> I[No replacement exclusion memory]
```

The expiry logic also recognizes legacy state memories that predate the
canonical action/entity metadata.

### Memory decision pipeline

```mermaid
flowchart TD
  A[Playback, UI, or chat event] --> B[EventValidator]
  B --> C[Persist immutable raw event]
  C --> D[MemoryExtractor]
  D --> E{Class and score meet threshold?}
  E -->|no| F[Persist decision only]
  E -->|yes| G[Create memory decision]
  G --> H[GraphClient.create_memory]
  H --> I[MemoryService.store_memory]
  I --> J[Create versioned Memory, HAS_MEMORY, REFERENCES]
```

Memory classification and retention are deterministic. It recognizes explicit
preferences, exclusions, corrections, candidate preferences, passive episodes,
and non-memory events. Strength is based on canonical entities, language,
contrast, and signal type; a model cannot make an otherwise rejected event
retrievable.

### Chat and recommendations

```mermaid
flowchart TD
  A[POST /chat/messages] --> B[LangGraph: understand]
  B --> C{Gemini structured extraction succeeds?}
  C -->|yes| D[Genre/artist/track/mood signals]
  C -->|no| E[Deterministic catalog-aware extractor]
  D --> F[LangGraph: persist]
  E --> F
  F --> G[Normal event and memory pipeline]
  G --> H[LangGraph: project_preferences]
  H --> I[Persist graph preferences and update client state]
  I --> J[Read graph memories/preferences/recommendations/reasoning]
  J --> K[LangGraph: recommend]
  K --> L[Deterministic candidate ranker applies exclusions]
  L --> M{Gemini ranking succeeds?}
  M -->|yes| N[Select only allowed candidate IDs]
  M -->|no| O[Use deterministic order]
  O --> P[ExplanationService creates rationale]
  N --> Q[LangGraph: compose_reply]
  P --> Q
  Q --> R[Reply with tracks, saved preferences, metadata]
```

Gemini never receives authority to invent a recommendation; it selects only
from candidate IDs produced after exclusions. If Gemini extraction or ranking
fails, the chat remains functional using deterministic behavior. The ranking
fallback passes persisted preferences, recent plays, and skips to
`ExplanationService` for the user-facing reason.

### Preferences and graph-native recommendations

```mermaid
flowchart LR
  A[Accepted explicit signal] --> B[PreferenceService]
  B --> C[Explicit preference or derived affinity]
  C --> D[(Neo4j PREFERS evidence)]
  D --> E[Collaborative, artist, genre strategies]
  E --> F[De-duplicate graph candidates]
  F --> G[ClientState deterministic ranking]
  G --> H[Safe candidates for Gemini/fallback]
```

Neo4j is the persisted cross-session preference view. `ClientStateService`
also projects fresh chat signals immediately so the UI can respond while graph
evidence is read or refreshed.

### MCP invocation

```mermaid
flowchart TD
  A[MCP host: Gemini, Claude, GPT] --> B[FastMCP server]
  B --> C[Tool module]
  C --> D[GraphAdapter]
  D --> E[Graph service/repository]
  E --> F[(Neo4j)]
  F --> G[Dict/list result]
  G --> H[JSON text formatter]
  H --> A
```

The server supports two deployment modes without changing any tool behavior:

```mermaid
flowchart LR
  A[Local Claude Desktop] -->|stdio subprocess| B[spotify_mcp]
  C[External Claude or MCP host] -->|Streamable HTTP /mcp or SSE /sse| B
  B --> D[GraphAdapter]
  D --> E[(Shared Neo4j)]
```

Use `MCP_TRANSPORT=stdio` for a host that launches the process and
`MCP_TRANSPORT=streamable-http` for a host configured with a URL such as
`http://127.0.0.1:8000/mcp`. The HTTP server is configurable with
`MCP_HOST`, `MCP_PORT`, `MCP_STREAMABLE_HTTP_PATH`, `MCP_SSE_PATH`, and
`MCP_STATELESS_HTTP`. Keep an HTTP deployment behind authentication/TLS or a
private network before exposing it beyond the local machine.

Tool modules are grouped by playback, engagement, users/tracks, memories,
recommendations, and reasoning. `server.py` registers every group. The adapter
boundary prevents MCP tools from depending on Cypher or graph internals.

## Failure behavior

| Situation | Result |
| --- | --- |
| Invalid event/auth mismatch/missing consent | Rejected before persistence. |
| PostgreSQL failure | Service-unavailable response; no successful ingest is claimed. |
| Required graph writeback fails | Raw event stays durable in PostgreSQL; caller receives graph-writeback failure. |
| Gemini extraction fails | Deterministic catalog-aware extraction continues the chat workflow. |
| Gemini ranking fails | Deterministic candidate order plus `ExplanationService` rationale. |
| Unlike/unfollow | Current graph edge is deleted and matching state memory is expired. |

## Extension points

- Add an interaction by extending validation, sending it through
  `InteractionOrchestrator.ingest`, and dispatching it in
  `graph/services/interaction_service.py`.
- Add graph behavior in a repository first, then expose it through a service.
- Add an MCP capability with an adapter method and a tool module; register a
  new module in `spotify_mcp/server.py` when necessary.
- Change retention policy in `MemoryExtractor`, never by letting an LLM write
  memories directly.
- Add recommendation strategies in `RecommendationService` and keep model
  output restricted to the resulting candidate set.
