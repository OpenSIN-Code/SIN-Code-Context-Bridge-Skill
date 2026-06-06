"""Purpose: Tests for the merger (dedup + budget fit).

Docs: test_merger.doc.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(_SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILL_ROOT))


def _chunk(source: str, content: str, score: float = 0.5):
    from lib.sources.base import ContextChunk
    return ContextChunk(source=source, content=content, score=score)


def test_merger_dedupes_by_content():
    from lib.merger import merge_and_budget
    chunks = [
        _chunk("a", "hello world", 0.9),
        _chunk("b", "hello world", 0.8),     # duplicate of 'a' by fingerprint
        _chunk("c", "unique content", 0.7),
    ]
    out = merge_and_budget(chunks, max_tokens=100)
    assert len(out) == 2
    # Higher-scored copy wins; 'a' must come first.
    assert out[0].source == "a"
    assert out[1].source == "c"


def test_merger_respects_budget():
    from lib.merger import merge_and_budget
    chunks = [
        _chunk("a", "x" * 1000, 0.9),
        _chunk("b", "y" * 1000, 0.8),
        _chunk("c", "z" * 100, 0.7),
    ]
    # 50 tokens = 200 chars. The walker always includes the first
    # (highest-scored) chunk even if it overflows — that chunk is the
    # most relevant result and is more useful than returning nothing.
    # Subsequent chunks must be dropped to stay within budget.
    out = merge_and_budget(chunks, max_tokens=50)
    assert len(out) == 1
    assert out[0].source == "a"  # highest score, kept despite overflow


def test_merger_fits_smaller_chunks_when_first_fits():
    """When the top chunk fits, later chunks are included up to the budget."""
    from lib.merger import merge_and_budget
    chunks = [
        _chunk("a", "x" * 100, 0.9),
        _chunk("b", "y" * 50, 0.8),
        _chunk("c", "z" * 200, 0.7),  # would push over 200-char budget
    ]
    out = merge_and_budget(chunks, max_tokens=50)  # 200 char budget
    # 'a' (100) + 'b' (50) = 150, fits. 'c' (200) would push to 350 > 200.
    assert [c.source for c in out] == ["a", "b"]


def test_merger_sorts_by_score_desc():
    from lib.merger import merge_and_budget
    chunks = [
        _chunk("low", "low score", 0.1),
        _chunk("hi", "high score", 0.9),
        _chunk("mid", "mid score", 0.5),
    ]
    out = merge_and_budget(chunks, max_tokens=10_000)
    assert [c.source for c in out] == ["hi", "mid", "low"]


def test_merger_zero_tokens_returns_empty():
    from lib.merger import merge_and_budget
    out = merge_and_budget([_chunk("a", "x")], max_tokens=0)
    assert out == []


def test_merger_handles_empty_input():
    from lib.merger import merge_and_budget
    assert merge_and_budget([], max_tokens=100) == []


def test_merger_dedup_is_strict_leading_window():
    """Two chunks whose first 200 chars match are duplicates even if they diverge later."""
    from lib.merger import merge_and_budget
    prefix = "A" * 250
    chunks = [
        _chunk("a", prefix + " end1", 0.9),
        _chunk("b", prefix + " end2", 0.8),
    ]
    out = merge_and_budget(chunks, max_tokens=10_000)
    assert len(out) == 1
    assert out[0].source == "a"
