"""
Entry point for the Spotify Memory MCP server.

CALL FLOW
=========

  MCP client / host                 (Claude Desktop, Claude.ai, any
        |                            MCP-compatible GPT/Gemini client)
        |  MCP protocol (stdio, or sse/streamable-http if configured)
        v
  spotify_mcp/server.py             (this file — builds the FastMCP app,
        |                            registers every tool/resource module)
        v
  spotify_mcp/tools/*.py            (validates input via schemas/,
  spotify_mcp/resources/*.py         formats output via utils/formatting.py)
        |
        v
  spotify_mcp/adapters/graph_adapter.py   <-- the ONLY file that imports `graph`
        |
        v
  graph/services/*.py               (GraphService, MemoryService,
        |                            RecommendationService, ...)
        v
  graph/repositories/*.py           (Cypher lives here, nowhere else)
        |
        v
  graph/neo4j_client.py  -->  Neo4j Desktop database

Run directly:
    python -m spotify_mcp

Or point an MCP host (e.g. Claude Desktop's claude_desktop_config.json)
at this file — see README.md for the exact config snippet.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .adapters.graph_adapter import get_graph_adapter
from .config import mcp_config
from .resources import user_resources
from .tools import (
    engagement_tools,
    memory_tools,
    playback_tools,
    reasoning_tools,
    recommendation_tools,
    track_tools,
    user_tools,
)

mcp = FastMCP(
    mcp_config.server_name,
    host=mcp_config.host,
    port=mcp_config.port,
    streamable_http_path=mcp_config.streamable_http_path,
    sse_path=mcp_config.sse_path,
    message_path=mcp_config.message_path,
    stateless_http=mcp_config.stateless_http,
)
adapter = get_graph_adapter()

# -- register every tool/resource module against the shared mcp + adapter --
playback_tools.register(mcp, adapter)
engagement_tools.register(mcp, adapter)
user_tools.register(mcp, adapter)
track_tools.register(mcp, adapter)
memory_tools.register(mcp, adapter)
recommendation_tools.register(mcp, adapter)
reasoning_tools.register(mcp, adapter)
user_resources.register(mcp, adapter)


def main() -> None:
    """Run for either a local stdio host or a URL-based external host.

    ``streamable-http`` exposes the MCP endpoint at ``/mcp`` by default and
    is the preferred transport for Claude and other remote MCP clients.
    ``stdio`` remains unchanged for a local subprocess configuration.
    """
    mcp.run(transport=mcp_config.transport)


if __name__ == "__main__":
    print("Starting FastMCP server...")
    main()
