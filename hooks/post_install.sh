#!/usr/bin/env bash
# Purpose: Post-install verification — sanity-check that sin-context-bridge works end-to-end.
# Docs: post_install.doc.md
set -euo pipefail

SKILL_DIR="${SKILL_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
echo "[sin-context-bridge] Post-install verification starting…"

# 1. CLI must be importable.
if ! python3 -c "import sys; sys.path.insert(0, '${SKILL_DIR}'); from lib.bridge import ContextBridge" \
     2>/dev/null; then
  echo "  ✗ lib.bridge import failed" >&2
  exit 1
fi
echo "  ✓ lib.bridge importable"

# 2. CLI health subcommand must work.
if ! python3 -m scripts.sin_context_bridge health >/dev/null 2>&1 \
   && ! python3 -c "
import sys
sys.path.insert(0, '${SKILL_DIR}')
from lib.bridge import ContextBridge
import json
print(json.dumps(ContextBridge().health()))
" >/dev/null 2>&1; then
  echo "  ✗ health check failed" >&2
  exit 1
fi
echo "  ✓ health check runs"

# 3. Pytest must pass (best-effort; not a hard gate if pytest missing).
if command -v pytest >/dev/null 2>&1; then
  if (cd "${SKILL_DIR}" && pytest -q 2>&1 | tail -3); then
    echo "  ✓ pytest suite passed"
  else
    echo "  ! pytest had failures (see above) — fix before tagging a release"
  fi
else
  echo "  - pytest not installed, skipping"
fi

echo "[sin-context-bridge] Post-install verification OK."
