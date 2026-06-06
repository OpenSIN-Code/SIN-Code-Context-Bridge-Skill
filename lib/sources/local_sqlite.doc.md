# lib/sources/local_sqlite.py

Per-project SQLite context store at `.sin/context.db`. Always available
— this is the bridge's "at least one source works" guarantee.

## Behavior

- `is_available()` — always `True` (that's the whole point).
- `query(q, max_results)` — `LIKE %q%` against `key` and `content`,
  capped at `max_results`. Returns chunks with a fixed low score
  (0.3) — local notes are background, not primary evidence.
- `put(key, content, tags="")` — `INSERT OR REPLACE` on the unique
  `key` index. Public helper for the agent to record project
  conventions / user preferences.
- Auto-creates the DB and schema on construction. Recovers gracefully
  from a missing-table race by re-initializing.

## Schema

```sql
CREATE TABLE chunks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    key        TEXT UNIQUE NOT NULL,
    content    TEXT NOT NULL,
    tags       TEXT,
    created_at REAL DEFAULT (julianday('now'))
);
CREATE INDEX idx_chunks_key ON chunks(key);
```

## Why no FTS5 (yet)

Keeps the bridge install-trivial. LIKE on a few hundred rows is fast
enough. v0.2 will add FTS5 for projects that accumulate thousands of
chunks.

## Touched by

- `lib/sources/__init__.py:ALL` — registered as `"local"`.
- `lib/bridge.py` — receives a `db_path` config.
- `tests/test_local_sqlite.py` — covers schema, put/query round-trip,
  empty-input safety, replace-on-conflict.
