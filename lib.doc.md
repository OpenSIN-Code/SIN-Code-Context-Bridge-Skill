# lib/

The core Python package for `sin-context-bridge`. Pure stdlib + optional
deps; safe to import on any Python 3.11+ install.

## Layout

- `bridge.py` — `ContextBridge` orchestrator; the only class callers need.
- `merger.py` — `merge_and_budget()`: sort + dedup + budget fit.
- `mcp_server.py` — FastMCP server exposing `sin_context` and
  `sin_context_health` over stdio.
- `sources/` — one adapter per backend (SCKG, sin-brain, GitNexus, local
  SQLite). Each implements the `Source` interface from `sources/base.py`.

## Touched by

- `scripts/sin_context_bridge.py` (CLI + MCP entrypoint).
- `tests/test_*.py` (full coverage).

## Design

- All backends are *soft* — any one can be missing and the bridge still
  works, as long as `local` (always available) is in the source list.
- The `Source` ABC enforces a `no-raise` contract: backends swallow their
  own errors and return `[]`. The bridge wraps even that in try/except as
  a second line of defense.
- `ContextBridge` owns no state besides the source list. Safe to
  instantiate per request.

## Imports

```python
from lib.bridge import ContextBridge
from lib.merger import merge_and_budget
from lib.sources import ALL  # full backend registry
```
