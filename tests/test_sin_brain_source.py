"""Purpose: Tests for the sin-brain context source adapter.

Docs: test_sin_brain_source.doc.md
"""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))


def test_sin_brain_is_available_returns_bool():
    from lib.sources.sin_brain import SinBrainSource
    assert isinstance(SinBrainSource().is_available(), bool)


def test_sin_brain_query_returns_list_when_unavailable(monkeypatch):
    from lib.sources import sin_brain
    monkeypatch.setattr(sin_brain.SinBrainSource, "is_available", lambda self: False)
    assert sin_brain.SinBrainSource().query("anything") == []


def test_sin_brain_query_handles_recall_failure(monkeypatch):
    from lib.sources import sin_brain

    def _explode(*_args, **_kwargs):
        raise RuntimeError("simulated sin-brain outage")

    monkeypatch.setattr(sin_brain.SinBrainSource, "is_available", lambda self: True)
    # Patch the import site used by sin_brain.query.
    monkeypatch.setitem(sys.modules, "sin_brain",
                         type(sys)("sin_brain"))
    sys.modules["sin_brain"].recall = _explode
    assert sin_brain.SinBrainSource().query("test") == []


def test_sin_brain_query_maps_results(monkeypatch):
    from lib.sources import sin_brain
    import types

    def _fake_recall(query, limit=5):
        return [
            {"id": "1", "kind": "decision", "content": "Use bcrypt", "confidence": 0.88},
            {"id": "2", "kind": "preference", "content": "User likes strict types"},
        ]

    class _FakeBrainCortex:
        def __init__(self, storage_path):
            pass

        def recall(self, query, limit=5):
            return _fake_recall(query, limit)

        def close(self):
            pass

    # Inject a fake sin_brain.cortex module so the in-method import succeeds.
    fake_cortex = types.ModuleType("sin_brain.cortex")
    fake_cortex.BrainCortex = _FakeBrainCortex
    sys.modules["sin_brain"] = types.ModuleType("sin_brain")
    sys.modules["sin_brain.cortex"] = fake_cortex

    monkeypatch.setattr(sin_brain.SinBrainSource, "is_available", lambda self: True)

    out = sin_brain.SinBrainSource().query("test")
    assert len(out) == 2
    assert out[0].source == "sin_brain"
    assert out[0].score == 0.88
    # Missing confidence should fall back to the default (0.6).
    assert out[1].score == sin_brain._DEFAULT_CONFIDENCE
