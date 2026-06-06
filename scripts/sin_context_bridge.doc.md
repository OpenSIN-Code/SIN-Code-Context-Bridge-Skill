# scripts/sin_context_bridge.py

CLI + MCP entry point. Three subcommands:

- `query <Q>` — one-shot unified query, prints JSON to stdout.
- `health` — list which backends are reachable, prints JSON.
- `serve` — start the FastMCP server on stdio.

## Console script

Defined in `pyproject.toml`:

```toml
[project.scripts]
sin-context-bridge = "scripts.sin_context_bridge:app"
```

After `pip install -e .`, the `sin-context-bridge` binary lands on PATH
and can be invoked from any shell or wired into `opencode.json` as an
MCP server.

## Touched by

- `pyproject.toml` — entry point registration.
- `lib/bridge.py` — every subcommand builds a `ContextBridge` and
  delegates to `query()` / `health()`.
- `lib/mcp_server.py` — `serve` builds the FastMCP server lazily so
  the CLI works without the `[mcp]` extra.

## Why `typer`

`typer` gives us a real CLI parser, type-hint-driven args, and `--help`
text for free. The CLI surface is small enough that `argparse` would
also work, but `typer`'s `--sources` multi-value support is what makes
`sources="sckg,local"` ergonomically correct.
