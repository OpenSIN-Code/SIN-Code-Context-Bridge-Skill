# lib/sources/

One adapter per context backend. Each module implements the `Source`
interface from `base.py` and is registered in `__init__.py:ALL` so the
bridge can instantiate it by name.

## Files

- `base.py` — `Source` ABC + `ContextChunk` dataclass. The contract.
- `sckg.py` — wraps the `sin_code_sckg` KnowledgeGraph (optional).
- `sin_brain.py` — wraps `sin_brain.recall()` (optional).
- `gitnexus.py` — shells out to the `gitnexus` CLI (external binary).
- `local_sqlite.py` — per-project `.sin/context.db` (always available).

## Contract (from base.py)

- `is_available()` — must NEVER raise. Cheap. No I/O where possible.
- `query(q, max_results)` — must NEVER raise. Return `[]` on any failure.
- `health_check()` — informational, used by the `/health` CLI.

A backend that violates the contract still won't crash the bridge
(`bridge.py` wraps every source in try/except), but the breakage will
show up as `"error: …"` in `chunks_per_source` rather than an empty list.

## Adding a new source

1. Subclass `Source` in `lib/sources/<name>.py`.
2. Register in `lib/sources/__init__.py:ALL`.
3. Add `is_available()` / `query()` (and any per-source config to
   `ContextBridge.__init__`).
4. Add a test in `tests/test_<name>_source.py`.
5. Add a `.doc.md` companion.
