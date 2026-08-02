"""
spotify_mcp
===========
The MCP Server from the architecture diagram — sits between the graph
layer (`graph/`) and whatever LLM/host is calling it (Claude Desktop,
Claude.ai, GPT, Gemini — anything speaking the Model Context Protocol).

It does not talk to Neo4j directly. Every tool/resource goes through
`adapters.graph_adapter.GraphAdapter`, which is the single import
boundary into the `graph` package. See README.md for the full call flow.
"""
