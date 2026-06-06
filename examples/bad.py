#!/usr/bin/env python3
"""Purpose: Bad example — what NOT to do with the bridge.

Run from the skill root: `python examples/bad.py`
Docs: bad.doc.md
"""
from __future__ import annotations

import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SKILL_ROOT))

from lib.bridge import ContextBridge  # noqa: E402


def main() -> None:
    # ❌ BAD 1: No max_tokens → result could be megabytes, blows the LLM
    #          context window. Always set a budget.
    # bridge = ContextBridge()
    # bridge.query("auth")  # DON'T DO THIS

    # ❌ BAD 2: Bypassing the bridge and calling sources directly.
    #          You lose dedup, ranking, and budget fitting.
    # from lib.sources.sckg import SCKGSource
    # raw = SCKGSource().query("auth", max_results=999)  # DON'T DO THIS

    # ❌ BAD 3: Instantiating per-call and ignoring health. If GitNexus is
    #          missing, the bridge silently skips it — but the agent should
    #          see `chunks_per_source` and adjust its prompt.
    bridge = ContextBridge()
    result = bridge.query("auth", max_tokens=2000)  # budget set ✓
    # BAD: ignoring `truncated=True` and assuming the result is exhaustive.
    print(f"got {len(result['chunks'])} chunks")  # DO NOT assume this is "all" of them

    # ❌ BAD 4: Trying to use SCKG as a "codebase search engine" for
    #          unrelated text. SCKG is symbol-aware; pass function/class
    #          names, not prose.
    # bridge.query("please write me a hello world in python")  # DON'T DO THIS

    # ❌ BAD 5: Treating the bridge as a write API. Use the local source's
    #          `put()` directly (or call `LocalSQLiteSource().put(...)`).
    # bridge.put(...)  # DOES NOT EXIST ON THE BRIDGE

    print("This script intentionally shows anti-patterns. See good.py instead.")


if __name__ == "__main__":
    main()
