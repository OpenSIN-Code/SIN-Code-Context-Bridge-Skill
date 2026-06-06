"""Purpose: Tests for the local SQLite context source.

Focus:
  - The DB is auto-created on construction.
  - put() / query() round-trip works.
  - LIKE search matches both the key and content columns.
  - put() with empty key/content is a no-op (returns None).

Docs: test_local_sqlite.doc.md
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
import sys

import pytest

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))


def test_local_creates_db_on_init(tmp_path):
    from lib.sources.local_sqlite import LocalSQLiteSource
    db = tmp_path / "ctx.db"
    LocalSQLiteSource(db_path=str(db))
    assert db.exists()
    # Schema is in place.
    with sqlite3.connect(db) as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(chunks)")}
    assert {"id", "key", "content", "tags", "created_at"}.issubset(cols)


def test_local_put_then_query(tmp_path):
    from lib.sources.local_sqlite import LocalSQLiteSource
    db = tmp_path / "ctx.db"
    src = LocalSQLiteSource(db_path=str(db))
    src.put("k1", "JWT auth flow", tags="auth")
    src.put("k2", "Postgres connection pool", tags="db")

    out = src.query("JWT")
    assert len(out) == 1
    assert out[0].content == "JWT auth flow"
    assert out[0].metadata["key"] == "k1"
    assert out[0].source == "local"


def test_local_query_matches_content_and_key(tmp_path):
    from lib.sources.local_sqlite import LocalSQLiteSource
    db = tmp_path / "ctx.db"
    src = LocalSQLiteSource(db_path=str(db))
    src.put("auth.flow", "uses JWT")
    src.put("db.pool", "uses asyncpg")

    # Match by content
    assert len(src.query("asyncpg")) == 1
    # Match by key
    assert len(src.query("auth")) == 1
    # No match
    assert src.query("nothing") == []


def test_local_is_available_always_true(tmp_path):
    from lib.sources.local_sqlite import LocalSQLiteSource
    src = LocalSQLiteSource(db_path=str(tmp_path / "x.db"))
    assert src.is_available() is True


def test_local_put_rejects_empty(tmp_path):
    from lib.sources.local_sqlite import LocalSQLiteSource
    src = LocalSQLiteSource(db_path=str(tmp_path / "x.db"))
    assert src.put("", "content") is None
    assert src.put("key", "") is None
    # Neither row should exist.
    assert src.query("content") == []


def test_local_put_replaces_existing(tmp_path):
    """Re-put on the same key overwrites (used for hot-updating project facts)."""
    from lib.sources.local_sqlite import LocalSQLiteSource
    db = tmp_path / "ctx.db"
    src = LocalSQLiteSource(db_path=str(db))
    src.put("rule.typing", "use mypy strict", tags="lint")
    src.put("rule.typing", "use basedpyright strict", tags="lint")

    rows = src.query("strict")
    assert len(rows) == 1
    assert "basedpyright" in rows[0].content
