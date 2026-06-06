# tests/

Pytest suite for `sin-context-bridge`. Each file targets one module:

- `test_bridge.py` — `ContextBridge` happy + failure paths.
- `test_sckg_source.py` — SCKG adapter (uses monkeypatch, no real SCKG).
- `test_sin_brain_source.py` — sin-brain adapter.
- `test_gitnexus_source.py` — GitNexus CLI subprocess adapter.
- `test_local_sqlite.py` — local SQLite store (real DB, tmp_path).
- `test_merger.py` — pure-function merger logic.

## Conventions

- All tests use `tmp_path` for filesystem isolation; nothing in the
  working dir is mutated.
- The `local` source tests are the only ones that touch real I/O; the
  other adapters are mocked via `monkeypatch`.
- The CLI/MCP server is exercised in `hooks/post_install.sh` and via
  the `sin-context-bridge serve` smoke test, not in pytest (MCP stdio
  is awkward to test in-process).

## Running

```bash
cd ~/.config/opencode/skills/sin-context-bridge
pytest -q
```

or, with coverage:

```bash
pytest --cov=lib --cov=scripts
```
