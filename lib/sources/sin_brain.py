"""Purpose: sin-brain context source (persistent memory backend).

Bridges the standalone `sin_brain` package — when installed, queries its
`BrainCortex.recall()` API for prior decisions, user preferences, and
cross-session memory. Falls back to a silent no-op when sin-brain is not
on the path.

Docs: sin_brain.doc.md
"""
from __future__ import annotations

import logging
from typing import List

from .base import Source, ContextChunk

log = logging.getLogger(__name__)


# Default confidence for sin-brain chunks when the backend omits one. The
# brain ranks its own results, but its score field is not always a strict
# probability — 0.6 is the empirical "useful" midpoint from local tests.
_DEFAULT_CONFIDENCE = 0.6


class SinBrainSource(Source):
    """Adapter for the `sin_brain` package (optional dependency)."""

    name = "sin_brain"

    def __init__(self, db_path: str = "sin-brain.db") -> None:
        # Path to sin-brain's SqliteStore. Defaults to "sin-brain.db" in cwd.
        # BrainCortex(storage_path=...) creates + reads the DB at this path.
        self.db_path = db_path

    def is_available(self) -> bool:
        try:
            import sin_brain  # noqa: F401
            return True
        except Exception:
            return False

    def query(self, query: str, max_results: int = 5) -> List[ContextChunk]:
        if not self.is_available():
            return []
        try:
            # BrainCortex is the public high-level API. It accepts
            # storage_path and has built-in FTS5 + composite scoring.
            # recall(query, limit=N, scope=None) returns list[Memory].
            from sin_brain.cortex import BrainCortex
            cortex = BrainCortex(storage_path=self.db_path)
            raw = cortex.recall(query, limit=max_results)
            cortex.close()
        except Exception as exc:
            log.warning("sin_brain source failed: %s", exc)
            return []

        chunks: List[ContextChunk] = []
        for r in raw or []:
            # BrainCortex.recall returns Memory dataclass instances.
            if hasattr(r, "content"):
                content = r.content
                mid = getattr(r, "id", "")
                kind = getattr(r, "kind", "")
                score = float(getattr(r, "confidence", _DEFAULT_CONFIDENCE))
            else:
                content = r.get("content", "")
                mid = r.get("id", "")
                kind = r.get("kind", "")
                score = float(r.get("confidence", _DEFAULT_CONFIDENCE))
            chunks.append(
                ContextChunk(
                    source=self.name,
                    content=str(content)[:2000],
                    score=score,
                    metadata={"kind": kind, "id": mid},
                )
            )
        return chunks
