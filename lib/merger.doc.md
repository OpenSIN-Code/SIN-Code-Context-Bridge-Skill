# lib/merger.py

Pure function `merge_and_budget(chunks, max_tokens)`. No I/O. The merger
is the bridge's quality control — without it, an agent gets the same
chunk from SCKG and GitNexus and burns 2× the budget.

## Algorithm

1. **Sort** by `score` descending. Sorting first means the dedup step
   keeps the highest-scored copy of any near-duplicate.
2. **Dedup** by SHA-1 fingerprint of the first 200 chars of each chunk's
   content. Two chunks that *start* the same way are almost always
   paraphrases of the same source — the divergence later is usually
   formatting noise.
3. **Pack** into a `max_tokens * 4` char budget. The walker always
   includes at least one chunk if the input is non-empty (overflow beats
   nothing for the agent's "answer the question" goal).

## Why ~4 chars per token

Empirically the upper bound for English prose. Code can be denser
(1 char ≈ 1 token for symbols), so this is conservative — we under-fill
the budget slightly rather than overflow the LLM context window.

## Touched by

- `lib/bridge.py` — calls once per query.
- `tests/test_merger.py` — covers dedup, budget, sort, edge cases.

## Future

- v0.2: add MMR (maximal-marginal-relevance) re-ranking for diversity
  instead of pure score-sort. Today two highly-similar SCKG chunks can
  crowd out a complementary GitNexus hit.
- v0.2: pluggable fingerprint strategy (SimHash for fuzzy dedup).
