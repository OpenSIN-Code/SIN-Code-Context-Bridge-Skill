# examples/good.py

The "this is how you should call the bridge" example. Run from the
skill root:

```bash
python examples/good.py
```

## What it shows

1. Build the bridge (auto-discovers which sources are available).
2. Run `health()` first so the output shows the agent *what* it's
   working with.
3. Make a single `query()` call with a realistic budget.
4. Print the merged, ranked chunks with file/key context.
5. Print per-source hit counts so the agent can see which backend
   was silent.

## Anti-patterns this example *avoids*

- Setting `max_tokens` (the LLM context window is finite).
- Calling sources directly (loses dedup / ranking / budget fit).
- Ignoring `chunks_per_source` (the agent should know which backend
  answered).
- Assuming `chunks` is exhaustive (it may be `truncated`).
