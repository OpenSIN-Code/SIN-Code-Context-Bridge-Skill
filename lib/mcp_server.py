"""Purpose: FastMCP server exposing sin_context + sin_context_health.

Standalone MCP server (stdio transport) so any MCP-aware client can call
the bridge. Kept separate from `scripts/sin_context_bridge.py` so the
import graph stays clean — the script wraps this for `serve` while the
CLI commands (`query`, `health`) live in the script.

Docs: mcp_server.doc.md
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Optional, List

from .bridge import ContextBridge

log = logging.getLogger(__name__)


# Tools exposed via MCP. Add new tools by appending to this list AND
# registering them with @mcp.tool() below — keep both in sync.
MCP_TOOL_NAMES = ["sin_context", "sin_context_health"]


def build_server() -> object:
    """Construct the FastMCP server and register all tools.

    Imported lazily by `scripts/sin_context_bridge.py` so that installing
    the skill without the `[mcp]` extra still gives a working CLI.
    """
    # Imported here, not at module top — the bridge must remain importable
    # on systems without the `mcp` package installed.
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("sin-context-bridge")
    bridge = ContextBridge()

    @mcp.tool()
    def sin_context(
        query: str,
        sources: str = "",
        max_tokens: int = 8000,
    ) -> str:
        """Unified context query across SCKG, sin-brain, GitNexus, local SQLite.

        Args:
            query: Natural-language or keyword search.
            sources: Comma-separated source names (default: all available).
                Valid: "sckg", "sin_brain", "gitnexus", "local".
            max_tokens: Token budget for the merged response (default 8000).
        """
        src_list: Optional[List[str]] = (
            [s.strip() for s in sources.split(",") if s.strip()] if sources else None
        )
        # Re-instantiate with the requested source subset so a `local`-only
        # call skips the SCKG import probe (faster, fewer log lines).
        scoped = ContextBridge(src_list)
        result = scoped.query(query, max_tokens)
        return json.dumps(result, indent=2, ensure_ascii=False)

    @mcp.tool()
    def sin_context_health() -> str:
        """Report which context sources are currently available."""
        return json.dumps(bridge.health(), indent=2, ensure_ascii=False)

    return mcp


def run() -> None:
    """Entry point for `python -m lib.mcp_server` (used by tests + script)."""
    sys.stderr.write(
        "[sin-context-bridge] MCP server starting (stdio). "
        f"Tools: {', '.join(MCP_TOOL_NAMES)}\n"
    )
    server = build_server()
    server.run()
