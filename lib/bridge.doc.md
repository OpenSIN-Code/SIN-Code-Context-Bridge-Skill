# lib/bridge.py

`ContextBridge` — the orchestrator. The only class external callers need
to instantiate.

## What it does

1. Builds a list of `Source` adapters from a name list (default: all 4).
2. On `query(q, max_tokens)`, fans out to every available source.
3. Concatenates chunks, hands them to `merge_and_budget()`.
4. Returns a JSON-serializable dict with:
   - `chunks` — ranked, deduped, budget-fitted.
   - `sources_queried` — names of backends that actually ran.
   - `chunks_per_source` — hit count or `"error: …"` per backend.
   - `truncated` — `True` if the merger dropped chunks to fit the budget.

## Touched by

- `scripts/sin_context_bridge.py` — wraps the methods as CLI subcommands.
- `lib/mcp_server.py` — instantiates one per MCP session.
- `tests/test_bridge.py` — full coverage of the happy paths and the
  "source raises" failure mode.

## Why a class, not a function

Per-source configuration (SCKG storage path, local DB path) needs to be
threaded through; a class is the simplest way to keep that state without
arguments-on-every-call boilerplate.
