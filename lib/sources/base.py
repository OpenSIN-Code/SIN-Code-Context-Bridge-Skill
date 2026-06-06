"""Purpose: Abstract base for context sources.

Every context backend (SCKG, sin-brain, GitNexus, local SQLite, …) implements
the same `Source` interface so the bridge can plug them in/out at runtime and
gracefully degrade when a backend is missing.

Docs: base.doc.md
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any


@dataclass
class ContextChunk:
    """Single unit of context returned by a Source.

    Fields:
        source:  short identifier of the backend (e.g. "sckg", "local").
        content: the actual context text (markdown/plain — rendered as-is).
        score:   0.0–1.0 relevance; the merger sorts desc by this.
        metadata: free-form dict the source can attach (file path, kind, etc.).
    """

    source: str
    content: str
    score: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """JSON-safe serialization for the bridge output."""
        return asdict(self)


class Source(ABC):
    """Base class every context backend must implement.

    Contract:
        - `is_available()` must NOT raise (use try/except internally).
        - `query()` must return a list (possibly empty) and must NOT raise —
          the bridge treats any backend failure as "no chunks from this source".
        - `health_check()` is purely informational; the bridge never blocks on it.
    """

    name: str = ""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the backend can be queried right now.

        Should be cheap (no I/O) so the bridge can call it on every query.
        Implementations typically check for an importable module or a binary
        on PATH.
        """

    @abstractmethod
    def query(self, query: str, max_results: int = 5) -> List[ContextChunk]:
        """Return up to `max_results` chunks relevant to `query`.

        Implementations MUST swallow backend errors and return [] on failure —
        the bridge deliberately treats individual source failures as soft
        rather than hard errors (graceful degradation).
        """

    def health_check(self) -> Dict[str, Any]:
        """Standard health dict for the `/health` CLI subcommand.

        Subclasses may override to add backend-specific fields (e.g. db path
        for the local SQLite source).
        """
        return {"name": self.name, "available": self.is_available()}
