# lib/sources/gitnexus.py

Adapter for the `gitnexus` CLI (`@abhigyanpatwari/gitnexus`). The CLI
is an external Node binary, so this adapter shells out via
`subprocess.run`.

## Behavior

- `is_available()` — `shutil.which("gitnexus") is not None`. No I/O
  beyond the cached PATH lookup.
- `query(q, max_results)` — runs `gitnexus query <q> --json --limit
  <n>`, parses the JSON envelope, maps each result to a `ContextChunk`.
- 30s timeout. Anything slower usually means an un-indexed monorepo
  and the bridge should fall back to other sources.
- Non-zero exit, missing `--json` support, timeout, JSON-parse error:
  all return `[]` (no raise).

## Why subprocess, not the Python SDK

The gitnexus Python SDK lags behind the CLI by a few weeks. Going
through the CLI keeps the bridge decoupled from npm-version drift.

## Touched by

- `lib/sources/__init__.py:ALL` — registered as `"gitnexus"`.
- `lib/bridge.py` — no per-source config.
- `tests/test_gitnexus_source.py` — stubs `shutil.which` and
  `subprocess.run` to cover the four failure modes without spawning a
  real process.

## Caveat

The CLI output schema (`{"results": [{"symbol", "context", "score",
"file"}]}`) is the one from gitnexus v0.x. Schema changes will surface
as zero chunks with no error — a v0.2 fix is to validate the shape and
log a warning.
