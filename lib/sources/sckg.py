"""Purpose: SCKG (Semantic Codebase Knowledge Graph) context source.

Bridges the standalone `sin_code_sckg` package — when present, queries its
in-process KnowledgeGraph for semantically related symbols. Gracefully no-ops
when the package is not installed (the bridge still works with the other
sources).

Docs: sckg.doc.md
"""
from __future__ import annotations

import logging
from typing import List

from .base import Source, ContextChunk

log = logging.getLogger(__name__)


# Conservative upper bound on individual chunk size in chars; SCKG can return
# very long docstrings, and the merger truncates anyway, so we cap early to
# avoid blowing memory before dedup.
_MAX_CHUNK_CHARS = 4_000


class SCKGSource(Source):
    """Adapter for the `sin_code_sckg` package (optional dependency)."""

    name = "sckg"

    def __init__(self, storage_path: str = "./.sin/knowledge.graph") -> None:
        # Path is stored so the user can override per-project via the bridge
        # config. We deliberately do NOT open the graph in __init__ — the
        # import is expensive and we want a fast `is_available()` check.
        self.storage_path = storage_path

    def is_available(self) -> bool:
        # Pure import probe — never raises by contract.
        try:
            import sin_code_sckg  # noqa: F401
            return True
        except Exception:
            return False

    def query(self, query: str, max_results: int = 5) -> List[ContextChunk]:
        if not self.is_available():
            return []
        try:
            # Local import keeps the module importable even when the package
            # is missing — `is_available()` is the only contract users see.
            from sin_code_sckg.graph import KnowledgeGraph

            kg = KnowledgeGraph(storage_path=self.storage_path)
            raw = kg.query(query, limit=max_results)
        except Exception as exc:
            # Backend failure = soft no-op. The bridge surfaces "error: …" via
            # `chunks_per_source`, but we must not let a SCKG crash kill the
            # whole query.
            log.warning("sckg source failed: %s", exc)
            return []

        chunks: List[ContextChunk] = []
        for r in raw or []:
            content = f"{r.get('symbol', '?')}: {r.get('docstring', '')}"
            if len(content) > _MAX_CHUNK_CHARS:
                # Truncate with explicit marker so the LLM can detect it.
                content = content[: _MAX_CHUNK_CHARS - 20] + "\n…[truncated]"
            chunks.append(
                ContextChunk(
                    source=self.name,
                    content=content,
                    score=float(r.get("relevance", 0.5)),
                    metadata={
                        "file": r.get("file"),
                        "line": r.get("line"),
                    },
                )
            )
        return chunks
