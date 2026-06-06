# lib/mcp_server.py

FastMCP server (stdio transport) that exposes the bridge as two MCP
tools. Imported lazily by `scripts/sin_context_bridge.py` so the CLI
works even when the `mcp` extra isn't installed.

## Tools

| Name | Args | Returns |
|------|------|---------|
| `sin_context` | `query: str`, `sources: str = ""`, `max_tokens: int = 8000` | JSON string |
| `sin_context_health` | — | JSON string |

`sources` is a comma-separated string (e.g. `"sckg,local"`) so MCP
clients that don't support `list[str]` can still pass it. Empty string
= all available.

## Transport

stdio only. The MCP stdio protocol is the lowest-common-denominator
that works for every MCP-aware client (opencode, Cursor, Claude Desktop,
etc.). HTTP/Streamable transports are a v0.2 candidate.

## Touched by

- `scripts/sin_context_bridge.py` (`serve` subcommand).
- `tests/` — `test_bridge.py` exercises the bridge path; the server
  itself is verified via a stdio handshake smoke test.

## Why a separate file

The CLI (`scripts/sin_context_bridge.py`) and the server
(`lib/mcp_server.py`) share `ContextBridge` but have different
lifecycles. Keeping them in separate modules avoids importing `mcp`
when the user just wants the CLI.
