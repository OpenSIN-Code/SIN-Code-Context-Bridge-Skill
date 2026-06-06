# lib/sources/sin_brain.py

Adapter for the `sin_brain` package (persistent cross-session memory).
Optional dependency — missing means `is_available() = False`.

## Behavior

- `is_available()` — pure import probe.
- `query(q, max_results)` — calls `sin_brain.recall(q, scope="recall",
  k=max_results)`, maps each result to a `ContextChunk`.
- Missing `confidence` field falls back to `_DEFAULT_CONFIDENCE = 0.6`
  (the empirical "useful" midpoint from local brain runs).
- Swallows backend errors and returns `[]`.

## Why `scope="recall"` is pinned

`sin_brain` exposes multiple scopes (`recall`, `decision`, …). The
bridge is general-purpose; `recall` is the cross-cutting scope that
returns the broadest set. Per-scope filtering is a v0.2 feature.

## Touched by

- `lib/sources/__init__.py:ALL` — registered as `"sin_brain"`.
- `lib/bridge.py` — no per-source config needed.
- `tests/test_sin_brain_source.py` — covers happy / sad paths.

## Caveat

sin-brain is evolving fast; the `recall(query, scope, k)` signature
hasn't changed in 2026, but the bridge's test suite pins the call so a
silent signature change will be caught by CI.
