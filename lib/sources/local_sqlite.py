"""Purpose: Local SQLite context source (per-project memory).

A small SQLite database at `.sin/context.db` that the bridge can always use,
even when no other backend is installed. Auto-created on first run. The agent
can call `put()` to record project conventions, ADRs, user preferences, etc.

Docs: local_sqlite.doc.md
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from .base import Source, ContextChunk


# Local chunks are background memory, not primary evidence. We pin a low
# score (0.3) so the merger ranks them below real code/memory chunks but
# still surfaces them when the budget allows. The agent can override by
# putting high-confidence chunks (e.g. a pinned ADR) — those should
# overwrite the default via the score field on a future iteration.
_LOCAL_BASE_SCORE = 0.3

# Default DB path is a module-level constant so tests can monkeypatch
# `_DEFAULT_DB_PATH` without re-implementing the constructor (which would
# risk infinite recursion in older fixture designs).
_DEFAULT_DB_PATH = ".sin/context.db"


class LocalSQLiteSource(Source):
    """SQLite-backed context store scoped to the current project.

    Schema is intentionally minimal (single table, FTS-free) so the bridge
    has zero external runtime deps. The agent writes via `put()`; reads are
    a LIKE-based scan which is fine for the expected size (hundreds of rows,
    not millions).
    """

    name = "local"

    def __init__(self, db_path: str = _DEFAULT_DB_PATH) -> None:
        # Create parent dir eagerly — projects that never write to `.sin/`
        # still need the dir to exist so the first query doesn't 500.
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        # Two statements, no FTS5 yet — keeps the bridge install-trivial.
        # Adding FTS5 is a v0.2 candidate (see CHANGELOG).
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    created_at REAL DEFAULT (julianday('now'))
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_key ON chunks(key)"
            )

    def is_available(self) -> bool:
        # The local source is ALWAYS available — that's its whole purpose.
        # We still return a bool (not a constant) so the interface stays
        # uniform with the other sources.
        return True

    def query(self, query: str, max_results: int = 5) -> List[ContextChunk]:
        # LIKE-based search. SQLite's default case-insensitive LIKE for ASCII
        # is good enough for short project-scoped notes; FTS5 is a future
        # enhancement (see lib/merger.py for ranking rationale).
        try:
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute(
                    """
                    SELECT key, content, tags
                    FROM chunks
                    WHERE key LIKE ? OR content LIKE ?
                    LIMIT ?
                    """,
                    (f"%{query}%", f"%{query}%", int(max_results)),
                ).fetchall()
        except sqlite3.OperationalError as exc:
            # Most likely: the table doesn't exist yet (race on a brand-new
            # project). Re-init and return empty — the next query will
            # succeed.
            self._init_db()
            return []

        return [
            ContextChunk(
                source=self.name,
                content=row[1] or "",
                score=_LOCAL_BASE_SCORE,
                metadata={"key": row[0], "tags": row[2]},
            )
            for row in rows
        ]

    def put(self, key: str, content: str, tags: str = "") -> Optional[int]:
        """Insert or replace a chunk; returns the row id.

        Public helper so the agent can `put()` project conventions, ADRs,
        and user preferences. `key` is unique — re-`put()`ing the same key
        updates in place.
        """
        if not key or not content:
            return None
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT OR REPLACE INTO chunks (key, content, tags) VALUES (?, ?, ?)",
                (key, content, tags),
            )
            return int(cur.lastrowid or 0)
