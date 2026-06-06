# Changelog

All notable changes to `sin-context-bridge` are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-06-04

### Added

- Initial release.
- `ContextBridge` orchestrator that fans out to 4 context sources.
- Source adapters:
  - `SCKGSource` — wraps the `sin_code_sckg` KnowledgeGraph.
  - `SinBrainSource` — wraps `sin_brain.recall()`.
  - `GitNexusSource` — shells out to the `gitnexus` CLI (30s timeout).
  - `LocalSQLiteSource` — per-project `.sin/context.db` with `put()` helper.
- `merge_and_budget()` merger:
  - Sorts by score descending.
  - Dedups by SHA-1 fingerprint of the first 200 chars.
  - Fits into a conservative char budget (4 chars/token).
- CLI: `sin-context-bridge {query,health,serve}`.
- FastMCP server exposing two tools:
  - `sin_context(query, sources="", max_tokens=8000)`
  - `sin_context_health()`
- Graceful degradation: any source can be missing and the bridge still works.
- Pytest suite covering the bridge, all 4 sources, and the merger.
- CoDocs companions for every source file.
- Per-project config template at `templates/config.yaml`.
- Post-install hook at `hooks/post_install.sh`.

### Notes

- Local SQLite uses `LIKE` search (no FTS5 yet). FTS5 is a v0.2 candidate.
- `sin_code_sckg` and `sin_brain` are pulled from `file://` URLs in the
  optional-dependency groups; PyPI publication will swap to real versions
  once those packages ship.
- GitNexus is invoked via `subprocess.run` (not the Python SDK) to keep
  the bridge decoupled from npm-version drift.
