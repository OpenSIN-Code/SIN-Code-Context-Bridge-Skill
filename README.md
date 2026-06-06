# sin-context-bridge

> Unified context bridge — query SCKG + sin-brain + GitNexus + local SQLite in **1 MCP call**.

## TL;DR

```python
# In an MCP-aware agent
sin_context("auth module structure", sources="sckg,gitnexus,local", max_tokens=4000)
```

Returns a single ranked JSON payload drawn from up to 4 context backends,
deduplicated, and budget-fitted to your token window.

## Why

Gathering context today means 4+ MCP round-trips with different shapes,
different ordering, different error semantics. This skill unifies them.

| Before | After |
|--------|-------|
| `recall_tool(...)` + `gitnexus_context(...)` + `local_db.query(...)` | `sin_context(query)` |
| Agent ranks/merges in its own context | Server returns ranked, deduped, budget-fitted |
| Any one failure breaks the call | Soft-fail per source, partial results returned |

## The 4 sources

| Source | What it provides | Install |
|--------|------------------|---------|
| **sckg** | Semantic Codebase Knowledge Graph (symbols + docstrings) | `pip install sin-context-bridge[sckg]` |
| **sin_brain** | Persistent memory (decisions, preferences, ADR history) | `pip install sin-context-bridge[brain]` |
| **gitnexus** | Graph relationships (callers, callees, blast radius) | `npm i -g @abhigyanpatwari/gitnexus` |
| **local** | Per-project `.sin/context.db` (auto-created) | none (always available) |

## Install

```bash
cd ~/.config/opencode/skills/sin-context-bridge

# Minimal (just the local source)
pip install -e .

# With all 4 sources
pip install -e .[sckg,brain,mcp]
```

## Usage

### CLI

```bash
sin-context-bridge query "auth module"
sin-context-bridge query "user prefs" --sources "sin_brain,local" --max-tokens 4000
sin-context-bridge health
sin-context-bridge serve   # start MCP server (stdio)
```

### MCP

Wire into `~/.config/opencode/opencode.json` under `mcp`:

```json
"sin-context-bridge": {
  "type": "local",
  "command": ["sin-context-bridge", "serve"],
  "enabled": true
}
```

Then in any agent / opencode call:

```python
mcp("sin-context-bridge", "sin_context",
    query="where is the auth middleware?",
    sources="sckg,gitnexus,local",
    max_tokens=4000)
```

## Output shape

```json
{
  "query": "auth module",
  "chunks": [
    {
      "source": "sckg",
      "content": "auth.login: JWT-based login flow with refresh tokens",
      "score": 0.92,
      "metadata": {"file": "src/auth/login.py", "line": 14}
    },
    {
      "source": "gitnexus",
      "content": "auth.login: callers=8, callees=2",
      "score": 0.81,
      "metadata": {"file": "src/auth/login.py"}
    }
  ],
  "sources_queried": ["sckg", "gitnexus", "local"],
  "chunks_per_source": {"sckg": 3, "gitnexus": 5, "local": 0},
  "total_chars": 8741,
  "truncated": true
}
```

## Graceful degradation

| Missing | Effect |
|---------|--------|
| `sin_code_sckg` not installed | `sckg` reports `"unavailable"`, other sources run |
| `sin_brain` not installed | `sin_brain` reports `"unavailable"` |
| `gitnexus` binary missing | `gitnexus` reports `"unavailable"` |
| **all of the above** | Only `local` runs; `.sin/context.db` is created on first call |
| Source raises mid-query | Soft error in `chunks_per_source`, others continue |

## Project layout

```
sin-context-bridge/
├── SKILL.md                      # skill entry point (opencode metadata)
├── README.md                     # you are here
├── CHANGELOG.md                  # v0.1.0 release notes
├── pyproject.toml                # install + console script
├── scripts/
│   └── sin_context_bridge.py     # CLI: query / health / serve
├── lib/
│   ├── bridge.py                 # orchestrator
│   ├── merger.py                 # dedup + budget fit
│   ├── mcp_server.py             # FastMCP server
│   └── sources/
│       ├── base.py               # Source abstract base
│       ├── sckg.py               # sin_code_sckg adapter
│       ├── sin_brain.py          # sin_brain adapter
│       ├── gitnexus.py           # gitnexus CLI subprocess adapter
│       └── local_sqlite.py       # per-project .sin/context.db
├── tests/                        # pytest suite
├── examples/                     # good.py + bad.py
├── templates/
│   └── config.yaml               # per-project config
├── hooks/
│   └── post_install.sh           # post-install hook
└── docs/                         # CoDocs companions
```

## License

MIT
