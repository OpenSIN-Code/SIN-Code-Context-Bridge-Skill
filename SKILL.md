---
name: sin-context-bridge
description: Unified context bridge — query SCKG + sin-brain + GitNexus + local SQLite in 1 MCP call. Use when agent needs cross-source context (e.g. "what's the auth module's structure AND what does the user prefer AND what was the last decision"). Auto-discovers which sources are available; gracefully degrades if any are missing.
license: MIT
---

# sin-context-bridge

## What it does

`sin_context(query, sources="sckg,sin_brain,gitnexus,local", max_tokens=8000)` returns a
single ranked JSON payload drawn from up to 4 context backends, deduplicated, and
budget-fitted to your token window.

## When to use

| Trigger | Use case |
|---------|----------|
| Agent needs cross-source context | One MCP call vs 4 |
| "what's the structure of X AND what does the user prefer AND what was the last decision" | All in one |
| Looking up symbols/memory/conventions together | Unified ranking |
| Working in a project with `.sin/context.db` | Hits local store + remote backends |

## When NOT to use

- You need raw graph traversal (use `gitnexus_cypher` directly).
- You need to write to sin-brain (use `remember_tool` directly).
- You need a single-source answer (cheaper to call the source directly).

## The 4 sources

| Source | What | Install |
|--------|------|---------|
| **sckg** | Semantic Codebase Knowledge Graph | `pip install sin-context-bridge[sckg]` |
| **sin_brain** | Persistent memory (4 tiers, SQLite+FTS5) | `pip install sin-context-bridge[brain]` |
| **gitnexus** | Upstream graph context (mandatory) | `npm install -g @abhigyanpatwari/gitnexus` |
| **local** | Per-project `.sin/context.db` (auto-created) | none (always available) |

## Install

```bash
cd ~/.config/opencode/skills/sin-context-bridge
pip install -e .           # local only
pip install -e .[sckg,brain,mcp]  # all sources + MCP server
```

## Usage

### MCP

Add to `~/.config/opencode/opencode.json` under `mcp`:

```json
"sin-context-bridge": {
  "type": "local",
  "command": ["sin-context-bridge", "serve"],
  "enabled": true
}
```

Then call from any agent:

```python
sin_context("auth module", sources="sckg,gitnexus", max_tokens=4000)
sin_context_health()
```

### CLI

```bash
sin-context-bridge query "auth module"
sin-context-bridge query "user prefs" --sources "sin_brain,local" --max-tokens 4000
sin-context-bridge health
sin-context-bridge serve   # stdio MCP server
```

## Output shape

```json
{
  "query": "auth module",
  "chunks": [
    {"source": "sckg", "content": "auth: JWT-based flow", "score": 0.92, "metadata": {"file": "src/auth.py"}},
    {"source": "gitnexus", "content": "auth.py: callers=12, callees=3", "score": 0.85, "metadata": {"file": "src/auth.py"}}
  ],
  "sources_queried": ["sckg", "gitnexus", "local"],
  "chunks_per_source": {"sckg": 3, "gitnexus": 5, "local": 0},
  "total_chars": 12340,
  "truncated": true
}
```

## Graceful degradation

- `sin-code-sckg` not installed → skips SCKG, uses rest.
- `gitnexus` binary missing → skips GitNexus.
- `sin-brain` not installed → uses local SQLite only.
- All missing → only `local` runs, `.sin/context.db` created on first use.
- Source raises mid-query → soft error in `chunks_per_source`, others continue.

## Files

- `SKILL.md` — this file
- `scripts/sin_context_bridge.py` — CLI + MCP entry
- `lib/bridge.py` — orchestrator
- `lib/merger.py` — dedup + budget fit
- `lib/sources/{sckg,sin_brain,gitnexus,local_sqlite}.py` — 4 adapters
- `lib/mcp_server.py` — FastMCP server
- `tests/test_*.py` — 6 test files
- `templates/config.yaml` — per-project config
- `hooks/post_install.sh` — post-install sanity check
- `docs/*.doc.md` — CoDocs companions

## Related skills

- `ceo-audit` — uses SCKG/sin-brain internally for SOTA audits
- `gitnexus-debugging` — uses GitNexus for impact analysis
- `sin-codocs` — produces the `.doc.md` companions in `docs/`
