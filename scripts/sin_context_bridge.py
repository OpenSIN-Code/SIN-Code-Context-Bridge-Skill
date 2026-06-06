"""Purpose: CLI + MCP entry point for sin-context-bridge.

Three subcommands:
  - query:  one-shot unified context query (prints JSON to stdout)
  - health: list which backends are reachable (prints JSON to stdout)
  - serve:  start the FastMCP server on stdio (for MCP-aware clients)

Docs: sin_context_bridge.doc.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, List

import typer

# Make the skill root importable when the script is run directly
# (e.g. `python scripts/sin_context_bridge.py`). Without this, the script
# can only be invoked as a module from the project root.
_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))

from lib.bridge import ContextBridge  # noqa: E402

app = typer.Typer(
    add_completion=False,
    help="Unified context bridge — query SCKG, sin-brain, GitNexus, local SQLite in one call.",
    no_args_is_help=True,
)


def _parse_sources(sources: str) -> Optional[List[str]]:
    """Parse a comma-separated source string into a list.

    Empty string = "use all available" (the bridge default). Whitespace is
    tolerated because humans fat-finger spaces.
    """
    if not sources or not sources.strip():
        return None
    return [s.strip() for s in sources.split(",") if s.strip()]


@app.command()
def query(
    q: str = typer.Argument(..., help="Natural-language or keyword search."),
    sources: str = typer.Option(
        "",
        "--sources",
        "-s",
        help='Comma-separated source names. E.g. "sckg,gitnexus". Default: all available.',
    ),
    max_tokens: int = typer.Option(
        8000, "--max-tokens", "-m", help="Token budget for the merged response."
    ),
    per_source_max: int = typer.Option(
        5, "--per-source-max", help="Max results to fetch from each source."
    ),
    db: str = typer.Option(
        "sin-brain.db", "--db", help="Path to sin-brain SQLite DB (and local SQLite).",
    ),
) -> None:
    """Query unified context and print JSON to stdout."""
    bridge = ContextBridge(_parse_sources(sources), local_db_path=db)
    result = bridge.query(q, max_tokens=max_tokens, per_source_max=per_source_max)
    # indent=2 keeps the output human-greppable; default ensure_ascii=True
    # would escape non-ASCII chars in user content (e.g. comments).
    # default=str handles non-serializable objects (datetime, Memory, etc.)
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False, default=str))


@app.command()
def health() -> None:
    """Show source availability summary (JSON)."""
    bridge = ContextBridge()
    typer.echo(json.dumps(bridge.health(), indent=2, ensure_ascii=False))


@app.command()
def serve() -> None:
    """Start the FastMCP server on stdio."""
    try:
        from lib.mcp_server import build_server  # noqa: WPS433 — late import
    except ImportError as exc:
        typer.echo(
            "MCP extras not installed. Run: pip install 'sin-context-bridge[mcp]'",
            err=True,
        )
        typer.echo(f"Import error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    server = build_server()
    # MCP is stdio-only by design; we write a single banner line to stderr
    # so the user can confirm the server is up without polluting the
    # JSON-RPC stream on stdout.
    typer.echo(
        "[sin-context-bridge] MCP server starting (stdio). "
        "Tools: sin_context, sin_context_health",
        err=True,
    )
    server.run()


if __name__ == "__main__":
    app()
