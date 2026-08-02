"""
One module per entity/concern, each exposing a `register(mcp, adapter)`
function. server.py imports and calls every `register` — no tool module
imports another, and none of them import `graph` directly (they only
ever go through `adapter`, an instance of GraphAdapter).
"""
