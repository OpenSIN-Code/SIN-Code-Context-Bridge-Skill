#!/usr/bin/env python3
"""Purpose: Good example — single MCP call, all 4 sources, budget-aware.

Run from the skill root: `python examples/good.py`
Docs: good.doc.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Make the skill importable when running this script directly.
_SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SKILL_ROOT))

from lib.bridge import ContextBridge  # noqa: E402


def main() -> None:
    # 1) Build the bridge — auto-discovers which sources are available.
    bridge = ContextBridge()

    # 2) Check what's reachable before issuing the query.
    health = bridge.health()
    print(f"[health] {health['available_count']}/{health['total_count']} sources available")
    for s in health["sources"]:
        print(f"  - {s['name']}: {'✓' if s['available'] else '✗'}")

    # 3) One unified query — sources, merge, dedup, budget all handled server-side.
    result = bridge.query(
        q="where is the auth middleware and what does the user prefer for it?",
        max_tokens=4000,
        per_source_max=5,
    )

    # 4) Print the merged, ranked chunks. `truncated` tells the caller whether
    #    some results were dropped to fit the budget.
    print(f"\n[query] '{result['query']}' → {len(result['chunks'])} chunks (truncated={result['truncated']})")
    for c in result["chunks"]:
        meta = c.get("metadata", {})
        loc = meta.get("file") or meta.get("key") or "?"
        print(f"  [{c['source']:<9} {c['score']:.2f}] {loc}: {c['content'][:80]}…")

    # 5) Per-source health — pinpoints which backend is silent.
    print(f"\n[chunks_per_source] {result['chunks_per_source']}")


if __name__ == "__main__":
    main()
