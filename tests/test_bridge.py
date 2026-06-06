"""Purpose: Tests for the ContextBridge orchestrator.

Focus areas:
  - Empty / missing source list returns the right shape.
  - At least the always-available `local` source is queried by default.
  - Backend exceptions are caught and surfaced as "error: …" rather than
    crashing the whole query.

Docs: test_bridge.doc.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow `from lib.bridge import ...` in `pytest` invocations from the
# skill root or the repo root.
_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))


@pytest.fixture
def local_db(tmp_path, monkeypatch):
    """Patch LocalSQLiteSource to point every instance at a per-test DB.

    Returns the path to the temp DB so individual tests can `put()` rows
    before exercising the bridge. We patch the __init__ DEFAULT rather
    than re-implementing the constructor — the original __init__ is the
    one we want to run, just with a different path.
    """
    from lib.sources import local_sqlite
    db = tmp_path / "context.db"
    # `_DEFAULT_DB_PATH` is read inside the original __init__. Patching it
    # here means the constructor's real logic runs (no recursion), and
    # every instance created during the test uses the temp DB.
    monkeypatch.setattr(local_sqlite, "_DEFAULT_DB_PATH", str(db))
    return db


def test_bridge_with_no_sources_returns_empty():
    from lib.bridge import ContextBridge
    bridge = ContextBridge([])
    result = bridge.query("test")
    assert result["chunks"] == []
    assert result["sources_queried"] == []


def test_bridge_calls_only_available_sources(local_db):
    from lib.bridge import ContextBridge
    # `local` is always available; the others may or may not be installed.
    bridge = ContextBridge(["local"])
    result = bridge.query("hello world")
    assert "local" in result["sources_queried"]
    assert "chunks_per_source" in result
    assert "local" in result["chunks_per_source"]


def test_bridge_health_reports_per_source(local_db):
    from lib.bridge import ContextBridge
    bridge = ContextBridge(["local"])
    h = bridge.health()
    assert "sources" in h
    assert h["total_count"] == 1
    assert h["available_count"] >= 1  # local is always available
    assert h["sources"][0]["name"] == "local"


def test_bridge_handles_source_exception(local_db):
    """A raising source must not crash the whole query."""
    from lib.bridge import ContextBridge
    from lib.sources.base import Source

    class BoomSource(Source):
        name = "boom"

        def is_available(self) -> bool:
            return True

        def query(self, query, max_results=5):
            raise RuntimeError("intentional test failure")

    bridge = ContextBridge.__new__(ContextBridge)
    bridge.sources = [BoomSource()]
    result = bridge.query("anything")
    assert result["chunks"] == []
    assert "error:" in result["chunks_per_source"]["boom"]


def test_bridge_unknown_source_warns_and_skips(caplog, local_db):
    from lib.bridge import ContextBridge
    # An unknown name should be dropped, not raised.
    bridge = ContextBridge(["nope", "local"])
    assert any(s.name == "local" for s in bridge.sources)
    assert not any(s.name == "nope" for s in bridge.sources)


def test_bridge_query_returns_expected_keys(local_db):
    from lib.bridge import ContextBridge
    bridge = ContextBridge(["local"])
    result = bridge.query("test")
    for key in ("query", "chunks", "sources_queried", "chunks_per_source",
                "total_chars", "truncated"):
        assert key in result, f"missing key: {key}"


def test_bridge_local_put_then_query(local_db):
    """End-to-end: put a chunk via the local source, query it via the bridge."""
    from lib.sources.local_sqlite import LocalSQLiteSource
    from lib.bridge import ContextBridge

    # put() through a directly-instantiated source (uses the patched DB).
    LocalSQLiteSource().put("auth.preference", "Use JWT-based auth flow", tags="convention")

    bridge = ContextBridge(["local"])
    result = bridge.query("auth")
    assert any("JWT" in c["content"] for c in result["chunks"])
    assert result["chunks_per_source"]["local"] >= 1
