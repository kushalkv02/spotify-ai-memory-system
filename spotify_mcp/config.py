"""
MCP server configuration — separate from graph/config.py (which holds
Neo4j connection settings). This only configures the MCP server itself.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


@dataclass(frozen=True)
class MCPConfig:
    server_name: str = os.getenv("MCP_SERVER_NAME", "spotify-memory")
    server_version: str = os.getenv("MCP_SERVER_VERSION", "0.1.0")
    # "stdio" is what Claude Desktop / most local MCP hosts expect.
    # Use "sse" or "streamable-http" if you're exposing this server over the network.
    transport: str = os.getenv("MCP_TRANSPORT", "stdio")


mcp_config = MCPConfig()
