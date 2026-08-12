# spotify_mcp/ — MCP Server for the Spotify AI Memory System

This is the **MCP Server** box in your architecture diagram (the layer
between the Neo4j graph and GPT/Claude/Gemini). It exposes graph
capabilities — recording plays, storing/reading memories, recommendations,
reasoning — as MCP tools and resources any MCP-compatible client can call.

It never talks to Neo4j directly; it calls `graph/` for everything.

## Call flow

```
MCP client/host                 (Claude Desktop, Claude.ai, any
     |                           MCP-compatible GPT/Gemini client)
     |  MCP protocol (stdio by default)
     v
spotify_mcp/server.py           builds the FastMCP app, registers
     |                          every tools/*.py + resources/*.py module
     v
spotify_mcp/tools/*.py          validates input (schemas/tool_schemas.py),
spotify_mcp/resources/*.py      formats output (utils/formatting.py)
     |
     v
spotify_mcp/adapters/graph_adapter.py   <- the ONLY file that imports `graph`
     |
     v
graph/services/*.py             GraphService, MemoryService,
     |                          RecommendationService, ReasoningService...
     v
graph/repositories/*.py         Cypher lives here, nowhere else
     |
     v
graph/neo4j_client.py  -->  Neo4j Desktop database
```

The single-boundary rule: **only `adapters/graph_adapter.py` imports from
`graph`.** Every tool module imports `GraphAdapter`, never `graph`
directly — so if the graph package's internals change, this is the one
file you touch.

## Layout

```
spotify_mcp/
├── server.py              # entry point: builds FastMCP app, registers everything
├── config.py               # MCP_SERVER_NAME / MCP_TRANSPORT env vars
├── adapters/
│   └── graph_adapter.py    # the single boundary into graph/
├── tools/                  # one module per concern; each exposes register(mcp, adapter)
│   ├── playback_tools.py   # record_play, get_recent_plays
│   ├── engagement_tools.py # like_track, unlike_track, get_liked_tracks,
│   │                       # skip_track, get_recent_skips,
│   │                       # follow_artist, unfollow_artist, get_followed_artists
│   ├── user_tools.py       # get_user, create_user
│   ├── track_tools.py      # search_tracks, create_track
│   ├── memory_tools.py     # store_memory, get_recent_memories
│   ├── recommendation_tools.py  # recommend_collaborative, recommend_by_artist_affinity
│   └── reasoning_tools.py  # get_listening_timeline, get_user_preferences
├── resources/
│   └── user_resources.py   # spotify://user/{id}/profile, .../recent-memories
├── schemas/
│   └── tool_schemas.py     # pydantic input models for multi-field tools
└── utils/
    └── formatting.py       # dict/list -> JSON text sent back to the LLM
```

## Setup

From the project root (so both `graph` and `spotify_mcp` are importable):

```bash
pip install -r requirements.txt
cp .env.example .env        # Neo4j Desktop credentials (shared with graph/)
python -m graph.builders.graph_builder --schema --seed   # if you haven't already
```

## Run the server directly (for testing)

```bash
python -m spotify_mcp
```

It starts on stdio and waits for an MCP client to connect — it won't
print anything on its own; that's normal for stdio transport.

## Connect an external MCP host over HTTP

The server supports both local stdio and URL-based external hosts. Use
Streamable HTTP for new integrations:

```bash
MCP_TRANSPORT=streamable-http \
MCP_HOST=127.0.0.1 \
MCP_PORT=8000 \
python -m spotify_mcp
```

The MCP endpoint is then:

```text
http://127.0.0.1:8000/mcp
```

For a host running on another machine, bind to an appropriate interface and
put the server behind TLS/authentication at the network boundary:

```bash
MCP_TRANSPORT=streamable-http MCP_HOST=0.0.0.0 MCP_PORT=8000 python -m spotify_mcp
```

Do not expose an unauthenticated Neo4j-backed MCP endpoint directly to the
public internet. Use a reverse proxy, VPN, or an authenticated private
network. The server's existing tools and resources are available on both
stdio and HTTP; transport selection does not change graph behavior.

## Quick sanity check without a real MCP client

```bash
python3 -c "
import asyncio
from spotify_mcp.server import mcp

async def main():
    for t in await mcp.list_tools():
        print(t.name)

asyncio.run(main())
"
```

## Connect it to Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "spotify-memory": {
      "command": "python",
      "args": ["-m", "spotify_mcp"],
      "cwd": "/absolute/path/to/your/project/root"
    }
  }
}
```

Restart Claude Desktop and it will discover the complete tool set, including
the explanation tool:

- **Playback**: `record_play`, `get_recent_plays`
- **Engagement**: `like_track`, `unlike_track`, `get_liked_tracks`,
  `skip_track`, `get_recent_skips`, `follow_artist`, `unfollow_artist`,
  `get_followed_artists`
- **Users / tracks**: `get_user`, `create_user`, `search_tracks`, `create_track`
- **Memory**: `store_memory`, `get_recent_memories`
- **Recommendations**: `recommend_collaborative`, `recommend_by_artist_affinity`,
  `structured_recommendation_reply`
- **Reasoning**: `get_listening_timeline`, `get_user_preferences`,
  `explain_recommendations`

### Claude Desktop using the HTTP endpoint

Start the HTTP server first, then configure Claude Desktop with the MCP URL
(the exact UI/config syntax depends on the Claude Desktop version):

```json
{
  "mcpServers": {
    "spotify-memory": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

If the host expects SSE instead, start with `MCP_TRANSPORT=sse`; the SSE URL
is `http://127.0.0.1:8000/sse`. Keep the stdio configuration above when Claude
Desktop launches the server itself as a local subprocess.

### Other external hosts

Any MCP-compatible host should be configured with the same Streamable HTTP
URL. After connecting, it discovers the registered tools automatically. The
host can then call playback, engagement, memory, recommendation, reasoning,
user, and track tools against the same Neo4j database used by the FastAPI app.

## Adding a new tool

1. Add the method to `adapters/graph_adapter.py` if it doesn't already wrap
   what you need from a `graph` service/repository.
2. Add a `@mcp.tool()` function in the relevant `tools/*.py` file (or a new
   file, following the `register(mcp, adapter)` pattern).
3. Register it in `server.py` if it's a new file.

Nothing else needs to change — the adapter boundary means new tools never
need to know about Cypher, `neo4j_client`, or repositories.
