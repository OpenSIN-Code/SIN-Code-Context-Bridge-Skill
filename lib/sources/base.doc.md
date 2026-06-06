# lib/sources/base.py

The `Source` abstract base class and the `ContextChunk` dataclass. The
single contract every backend adapter implements.

## What it defines

- **`ContextChunk`** — one unit of context. Fields:
  - `source` — short name (e.g. `"sckg"`).
  - `content` — text the LLM will read.
  - `score` — 0.0–1.0 relevance; merger sorts desc.
  - `metadata` — free-form dict (`file`, `line`, `kind`, `tags`…).
- **`Source`** — ABC with two abstract methods:
  - `is_available() -> bool` — must never raise.
  - `query(q, max_results=5) -> list[ContextChunk]` — must never raise.
- **`health_check() -> dict`** — concrete default; subclasses can override.

## Why a no-raise contract

A single broken backend should not break the whole bridge. The merger
can only rank what it gets, and `[]` from a backend is far more useful
to the agent than an exception that crashes the MCP server.

## Touched by

- `lib/sources/{sckg,sin_brain,gitnexus,local_sqlite}.py` — implement
  this interface.
- `lib/bridge.py` — iterates a list of `Source` instances.
- `tests/test_*.py` — every adapter test imports from here.
