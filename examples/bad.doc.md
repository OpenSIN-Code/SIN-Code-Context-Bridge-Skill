# examples/bad.py

The "please don't do this" example. Each call is commented out with a
`# DON'T DO THIS` marker and a one-line reason.

## Anti-patterns catalogued

1. **No `max_tokens`** → result can be megabytes, blows the LLM context.
2. **Calling sources directly** → loses dedup, ranking, budget fit.
3. **Ignoring `truncated=True`** → agent assumes the result is exhaustive
   when it isn't.
4. **Passing prose to SCKG** → SCKG is symbol-aware; pass
   function/class names, not English questions.
5. **Treating the bridge as a write API** → use
   `LocalSQLiteSource().put(...)` instead.

The script prints a one-line summary and exits 0 — it exists for
humans to read, not to assert behavior.
