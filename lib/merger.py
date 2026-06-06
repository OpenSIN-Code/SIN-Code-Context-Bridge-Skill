"""Purpose: Merge + dedup + budget-fit for context chunks.

Pure function (`merge_and_budget`) — no I/O, easy to unit-test. Sorts by
relevance score descending, drops near-duplicates via a content fingerprint,
and walks the sorted list packing chunks into a conservative char budget.

Docs: merger.doc.md
"""
from __future__ import annotations

import hashlib
from typing import List

from .sources.base import ContextChunk


# ~4 chars per token is a conservative English-text estimate (real ratio is
# 3.5–4.5). Using the upper bound means we under-fill the budget slightly
# rather than overflow the LLM context window.
CHARS_PER_TOKEN = 4

# Fingerprint window: first 200 chars is enough to catch paraphrased
# duplicates ("Auth module: JWT-based…" vs "Auth module: JWT-based auth
# flow…") while ignoring later divergence. Hashing the window keeps the
# dedup map small even with 10k+ chunks.
_FINGERPRINT_CHARS = 200


def _fingerprint(content: str) -> str:
    """Stable hash of the leading window of `content` for dedup.

    SHA-1 (truncated to 16 hex chars) is fine — this is a collision-check
    for "same first-200-chars", not a security primitive. SHA-1 is faster
    than SHA-256 and the dedup map never grows large enough for collisions
    to matter.
    """
    return hashlib.sha1(content.strip()[:_FINGERPRINT_CHARS].encode("utf-8")).hexdigest()[:16]


def merge_and_budget(
    chunks: List[ContextChunk],
    max_tokens: int,
) -> List[ContextChunk]:
    """Sort by score desc, dedup by fingerprint, fit into char budget.

    Order of operations matters:
      1. Sort first so dedup keeps the highest-scored copy of any duplicate.
      2. Dedup second so the budget walker never wastes slots on chunks
         that will be discarded.
      3. Pack last — walks the deduped, sorted list and stops when adding
         the next chunk would overflow the budget.

    `max_tokens <= 0` returns `[]` (degenerate but explicit).
    """
    if max_tokens <= 0:
        return []

    char_budget = max_tokens * CHARS_PER_TOKEN
    seen: set[str] = set()
    unique: List[ContextChunk] = []

    # 1. Sort + 2. Dedup in a single pass to avoid materializing the sorted
    #    list twice (matters when a backend returns thousands of chunks).
    for chunk in sorted(chunks, key=lambda c: c.score, reverse=True):
        fp = _fingerprint(chunk.content)
        if fp in seen:
            continue
        seen.add(fp)
        unique.append(chunk)

    # 3. Pack into budget. We always include at least one chunk if the
    #    input is non-empty, even if it overflows — a 200k-char SCKG
    #    docstring is still more useful to the LLM than nothing.
    result: List[ContextChunk] = []
    used = 0
    for chunk in unique:
        size = len(chunk.content)
        if result and used + size > char_budget:
            break
        result.append(chunk)
        used += size

    return result
