"""Purpose: ContextBridge orchestrator — query all sources, merge, return.

Glue layer between the four `Source` adapters and the outside world (CLI +
MCP). Owns no state besides the source list; safe to instantiate per
request.

Docs: bridge.doc.md
"""
from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any

from .merger import merge_and_budget
from .sources import ALL as SOURCE_REGISTRY
from .sources.base import ContextChunk, Source

log = logging.getLogger(__name__)


class ContextBridge:
    """Aggregate multiple context backends behind one `query()` call.

    Construction is cheap — sources are instantiated but not "opened". Each
    source decides in `is_available()` / `query()` whether it can answer
    right now, and the bridge never blocks on a broken backend.
    """

    def __init__(
        self,
        sources: Optional[List[str]] = None,
        sckg_storage_path: str = "./.sin/knowledge.graph",
        local_db_path: str = ".sin/context.db",
    ) -> None:
        # Default: all known sources. The bridge will skip any whose
        # `is_available()` returns False at query time.
        if sources is None:
            sources = list(SOURCE_REGISTRY.keys())

        # Per-source config injection — keeps the bridge ctor the only
        # place that knows how to pass paths to a specific backend.
        self.sources: List[Source] = []
        for name in sources:
            cls = SOURCE_REGISTRY.get(name)
            if cls is None:
                log.warning("unknown source: %s", name)
                continue
            if name == "sckg":
                self.sources.append(cls(storage_path=sckg_storage_path))
            elif name in ("local", "sin_brain"):
                # Both backends use a SQLite file. Reuse the same path so
                # --db applies uniformly to every persistent store.
                self.sources.append(cls(db_path=local_db_path))
            else:
                self.sources.append(cls())

    def query(
        self,
        q: str,
        max_tokens: int = 8000,
        per_source_max: int = 5,
    ) -> Dict[str, Any]:
        """Fan out to every available source, then merge.

        Returns a JSON-serializable dict. `chunks` is the merged, ranked,
        budget-fitted list. `chunks_per_source` reports per-backend hit
        count (or "error: …" string) so the agent can debug a silent
        backend.
        """
        chunks: List[ContextChunk] = []
        per_source: Dict[str, Any] = {}

        for src in self.sources:
            if not src.is_available():
                per_source[src.name] = "unavailable"
                continue
            try:
                src_chunks = src.query(q, max_results=per_source_max)
            except Exception as exc:
                # Defensive: source contracts say they don't raise, but
                # third-party backends (sin_code_sckg, sin_brain) may have
                # bugs. We never let one bad source kill the whole query.
                log.warning("source %s raised: %s", src.name, exc)
                per_source[src.name] = f"error: {exc}"
                continue
            chunks.extend(src_chunks)
            per_source[src.name] = len(src_chunks)

        merged = merge_and_budget(chunks, max_tokens)

        return {
            "query": q,
            "chunks": [c.to_dict() for c in merged],
            "sources_queried": [s.name for s in self.sources if s.is_available()],
            "chunks_per_source": per_source,
            "total_chars": sum(len(c["content"]) for c in [c.to_dict() for c in merged]),
            "truncated": len(merged) < len(chunks),
        }

    def health(self) -> Dict[str, Any]:
        """Return availability summary for `/health` and the MCP `sin_context_health` tool."""
        reports = [s.health_check() for s in self.sources]
        return {
            "sources": reports,
            "available_count": sum(1 for r in reports if r.get("available")),
            "total_count": len(reports),
        }
