"""Purpose: GitNexus context source (graph relationships via subprocess).

GitNexus is an external Node CLI (`@abhigyanpatwari/gitnexus`) that we shell
out to with a 30s timeout. The bridge treats a non-zero exit, a missing
binary, or a JSON-parse error all as "no chunks from this source".

Docs: gitnexus.doc.md
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
from typing import List

from .base import Source, ContextChunk

log = logging.getLogger(__name__)


# 30s is enough for a local repo with a few thousand symbols; the graph is
# in-memory after `gitnexus analyze` so most queries finish in <2s. Anything
# beyond 30s usually means an un-indexed monorepo and the agent should
# fall back to other sources.
_SUBPROCESS_TIMEOUT_SECONDS = 30


class GitNexusSource(Source):
    """Adapter that calls the `gitnexus` CLI as a subprocess.

    The CLI lives in the user's global npm prefix; we never vendor it. This
    keeps the bridge lightweight but means the source is silently disabled
    on systems without Node/npm.
    """

    name = "gitnexus"

    def is_available(self) -> bool:
        # `which` is cached by the shell, but the call is so cheap that we
        # do it on every probe — the bridge only invokes this twice per
        # query (once for health, once for query).
        return shutil.which("gitnexus") is not None

    def query(self, query: str, max_results: int = 5) -> List[ContextChunk]:
        if not self.is_available():
            return []
        try:
            proc = subprocess.run(
                [
                    "gitnexus",
                    "query",
                    query,
                    "--json",
                    "--limit",
                    str(max_results),
                ],
                capture_output=True,
                text=True,
                timeout=_SUBPROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            log.warning("gitnexus source timed out after %ss", _SUBPROCESS_TIMEOUT_SECONDS)
            return []
        except Exception as exc:
            log.warning("gitnexus subprocess failed: %s", exc)
            return []

        if proc.returncode != 0:
            # The CLI writes the error to stderr; we log at debug to avoid
            # spamming the agent's transcript with benign "no results" cases.
            log.debug("gitnexus exit=%s stderr=%s", proc.returncode, proc.stderr[:200])
            return []

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            # The CLI version on PATH may not support `--json`; treat as
            # soft-fail rather than crash.
            log.debug("gitnexus output not JSON: %s", exc)
            return []

        chunks: List[ContextChunk] = []
        for r in data.get("results", []):
            chunks.append(
                ContextChunk(
                    source=self.name,
                    content=f"{r.get('symbol', '?')}: {r.get('context', '')}",
                    score=float(r.get("score", 0.5)),
                    metadata={"file": r.get("file")},
                )
            )
        return chunks
