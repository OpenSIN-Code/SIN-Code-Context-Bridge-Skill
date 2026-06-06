"""Purpose: Tests for the SCKG context source adapter.

SCKG is an optional dependency; the tests exercise both the installed path
(monkeypatching the import) and the not-installed path (real `is_available`).

Docs: test_sckg_source.doc.md
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))


def test_sckg_is_available_returns_bool():
    from lib.sources.sckg import SCKGSource
    # Must never raise; contract.
    available = SCKGSource().is_available()
    assert isinstance(available, bool)


def test_sckg_query_returns_list_when_unavailable(monkeypatch):
    from lib.sources import sckg
    # Force "not available" regardless of whether the package is installed.
    monkeypatch.setattr(sckg.SCKGSource, "is_available", lambda self: False)
    out = sckg.SCKGSource().query("anything")
    assert out == []


def test_sckg_query_handles_import_failure(monkeypatch):
    """If the SCKG import or KG call blows up, the source must return []."""
    from lib.sources import sckg

    class _BoomKG:
        def __init__(self, storage_path):
            pass

        def query(self, query, limit):
            raise RuntimeError("simulated SCKG failure")

    # Inject a fake `sin_code_sckg.graph` module so the in-method import
    # succeeds but the constructed KG then raises. This is the realistic
    # failure mode (package installed but graph broken).
    fake_pkg = types.ModuleType("sin_code_sckg")
    fake_graph = types.ModuleType("sin_code_sckg.graph")
    fake_graph.KnowledgeGraph = _BoomKG
    monkeypatch.setitem(sys.modules, "sin_code_sckg", fake_pkg)
    monkeypatch.setitem(sys.modules, "sin_code_sckg.graph", fake_graph)

    monkeypatch.setattr(sckg.SCKGSource, "is_available", lambda self: True)
    out = sckg.SCKGSource().query("test")
    assert out == []


def test_sckg_truncates_oversized_chunks(monkeypatch):
    """Chunks larger than the cap must be truncated with a marker."""
    from lib.sources import sckg

    huge = "x" * 10_000  # exceeds 4000-char cap

    class _FakeKG:
        def __init__(self, storage_path):
            pass

        def query(self, query, limit):
            return [{"symbol": "BigSymbol", "docstring": huge,
                     "relevance": 0.9, "file": "big.py", "line": 1}]

    # Inject the fake package so the in-method import resolves to _FakeKG.
    fake_pkg = types.ModuleType("sin_code_sckg")
    fake_graph = types.ModuleType("sin_code_sckg.graph")
    fake_graph.KnowledgeGraph = _FakeKG
    monkeypatch.setitem(sys.modules, "sin_code_sckg", fake_pkg)
    monkeypatch.setitem(sys.modules, "sin_code_sckg.graph", fake_graph)

    monkeypatch.setattr(sckg.SCKGSource, "is_available", lambda self: True)
    out = sckg.SCKGSource().query("test")
    assert len(out) == 1
    assert "truncated" in out[0].content
    assert out[0].source == "sckg"
    assert out[0].metadata["file"] == "big.py"


def test_sckg_maps_results_correctly(monkeypatch):
    """Happy path: KG returns hits, source maps them to ContextChunks."""
    from lib.sources import sckg

    class _FakeKG:
        def __init__(self, storage_path):
            pass

        def query(self, query, limit):
            return [
                {"symbol": "auth.login", "docstring": "JWT flow",
                 "relevance": 0.92, "file": "src/auth.py", "line": 14},
                {"symbol": "auth.logout", "docstring": "clear session",
                 "relevance": 0.5, "file": "src/auth.py", "line": 30},
            ]

    fake_pkg = types.ModuleType("sin_code_sckg")
    fake_graph = types.ModuleType("sin_code_sckg.graph")
    fake_graph.KnowledgeGraph = _FakeKG
    monkeypatch.setitem(sys.modules, "sin_code_sckg", fake_pkg)
    monkeypatch.setitem(sys.modules, "sin_code_sckg.graph", fake_graph)

    monkeypatch.setattr(sckg.SCKGSource, "is_available", lambda self: True)
    out = sckg.SCKGSource().query("test", max_results=5)
    assert len(out) == 2
    assert out[0].source == "sckg"
    assert out[0].score == 0.92
    assert out[0].content.startswith("auth.login:")
    assert out[0].metadata == {"file": "src/auth.py", "line": 14}
