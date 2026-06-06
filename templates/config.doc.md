# templates/config.yaml

Per-project config template. Copy to `.sin/context-bridge.yaml` in the
project root to override defaults.

## What it controls

- **`sources`** — ordered list of backend names. The bridge skips any
  whose `is_available()` is False, so listing a missing dep is
  harmless. Removing a name entirely avoids even the import probe.
- **`sckg.storage_path`** — path to the KnowledgeGraph file. Default
  is the project-local `.sin/knowledge.graph`.
- **`local.db_path`** — path to the local SQLite store. Default
  `.sin/context.db`.
- **`defaults.max_tokens`** — budget applied when the caller doesn't
  specify one. 8000 is a reasonable LLM-2 context window.
- **`defaults.per_source_max`** — chunks fetched per backend before
  merging. Higher = more candidates, more dedup work.
- **`logging.level`** — `info` or `warning`. v0.1 doesn't read this
  field yet; the placeholder exists for the v0.2 logger config.

## Touched by

- The bridge will read this in v0.2 (currently the constructor takes
  args directly). For v0.1, copy values into a `ContextBridge(sources=
  [...], sckg_storage_path=..., local_db_path=...)` call.
