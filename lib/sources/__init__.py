"""Purpose: Context source adapters (SCKG, sin-brain, GitNexus, local SQLite).

Each module implements the `Source` interface from `base.py` and is loaded
lazily by the bridge so missing optional deps don't crash the import chain.

Docs: sources.doc.md
"""
from __future__ import annotations

from .base import Source, ContextChunk  # noqa: F401
from .sckg import SCKGSource  # noqa: F401
from .sin_brain import SinBrainSource  # noqa: F401
from .gitnexus import GitNexusSource  # noqa: F401
from .local_sqlite import LocalSQLiteSource  # noqa: F401


# Registry used by the bridge to instantiate sources by name. Keeping it in
# one place means new backends are a one-line addition.
ALL: dict[str, type[Source]] = {
    "sckg": SCKGSource,
    "sin_brain": SinBrainSource,
    "gitnexus": GitNexusSource,
    "local": LocalSQLiteSource,
}


def available_names() -> list[str]:
    """Names of backends whose import is currently resolvable.

    The bridge uses this to build the default `sources` list — only those
    that would actually return chunks are queried.
    """
    return [name for name, cls in ALL.items() if cls().is_available()]
