# lib/sources/sckg.py

Adapter for the `sin_code_sckg` package (Semantic Codebase Knowledge
Graph). Optional dependency — if `sin_code_sckg` is not importable, the
source reports `is_available() = False` and the bridge skips it.

## Behavior

- `is_available()` — pure import probe, no I/O.
- `query(q, max_results)` — opens the KnowledgeGraph at
  `storage_path` (default `./.sin/knowledge.graph`), calls
  `kg.search(q, limit=max_results)`, maps each hit to a `ContextChunk`.
- Truncates chunks larger than 4000 chars (with a `…[truncated]`
  marker) so a runaway docstring can't blow the merger budget on its
  own.
- Swallows any backend error and returns `[]` (per the `Source`
  contract).

## Config

- `storage_path` — passed via `ContextBridge.__init__` /
  `templates/config.yaml`. Default is the project-local path used by
  the upstream CLI.

## Touched by

- `lib/sources/__init__.py:ALL` — registered as `"sckg"`.
- `lib/bridge.py` — instantiated with a per-project storage path.
- `tests/test_sckg_source.py` — covers available / unavailable /
  truncated paths.

## Caveat

The `KnowledgeGraph` API (`search`, `storage_path`) is the one used by
the upstream `sin-code-sckg` package as of 2026-06. If the upstream
changes its public surface, this adapter needs a corresponding bump.
