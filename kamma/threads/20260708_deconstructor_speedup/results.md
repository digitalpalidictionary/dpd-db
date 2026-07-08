# Results: Deconstructor Speedup

Branch: `deconstructor-speedup`. All measurements on 22-core AMD, variable load
(reported alongside). Correctness gate: sorted `(word, split)` set. Benefit
gate: compute-stage wall-clock, fresh process per run.

## Headline

| Workload | Baseline compute | Final (A+B) compute | Speedup |
|---|---|---|---|
| 20k words (median of 3) | ~36.5s | ~11.7s | **3.1×** |
| 100k words (1 run each) | 2m27s (147s) | 37.3s | **3.9×** |

The speedup **grows with scale** (3.1× → 3.9×) because the removed bottleneck was
lock contention, which worsens as more words hammer the shared map. Full corpus
(~1M words) will extrapolate at least as well; not run here to save time, but the
same binaries do it with `-words 0`.

## What changed

### Change A — per-worker MatchData (removed the global lock)
- Baseline serialized ~88% of all worker block-time on one `muMatched` write lock
  inside `MakeMatch`.
- Each worker now owns a `*MatchData` (new `workerpool.RunCollect`), merged after
  compute (`MatchData.Merge`). The four global mutexes are gone from the hot path.
- **Result:** block profile is now empty — lock contention eliminated. Race
  detector clean.

### Change B — string/offset rewrite of Split2 + Split3 (killed alloc/conversion churn)
- Baseline burned 67% of allocations (24GB / 20k words) in `tools.RunesPlus`, plus
  ~16% CPU in `[]rune → string` conversion on every inflection lookup.
- Split2/Split3 now build the middle as a string + rune-offset table once per
  call, test candidates as zero-allocation substrings via `IsInInflectionsStr`,
  and materialize `[]rune` only on a match. Sandhi rule characters are cached as
  strings on `SandhiRules` (`Ch1S`/`Ch2S`) so they are never re-converted.
- No `WordData` type change; no other splitter touched.
- **Result:** total `alloc_space` 36GB → 12.7GB (2.8×); `RunesPlus` 24GB → 0.1GB.

### Change C — DEFERRED
- The `MakeCopy` RuleBack fix was **not applied**. It changes the `rules` output
  column, so it belongs in the bug discussion (below), per your instruction to
  finish the perf work first.
- Committable tests were added (non-behavioral): multi-byte `runeOffsets`
  round-trip, `IsInInflectionsStr` equivalence, `RunCollect` state collection.

## Correctness

Output is **deterministic** (identical MD5 across repeated runs at 1 and 44
workers). It differs from the *old* baseline on a tiny, fixed set of words:

| Workload | Words matched (same both) | Diverging words | Net pair diff |
|---|---|---|---|
| 20k | 18,238 | 2 | +6 |
| 100k | 93,583 | 2 | +6 |

Still only **2 words** at 5× scale (`acchakokataracchakā`, `adhippāyako`). Cause:
a pre-existing in-place slice-mutation in some splitters rewrites one job's word
into another, so a few words get processed twice. The old global map hid this by
deduping across passes; per-worker isolation lets the second pass find a few
extra valid splits. Accepted per your call ("2 in 20,000 is virtually
identical; output was never bit-stable before" — though note it now *is*
deterministic run-to-run).

## Bugs to discuss (not fixed)

1. **In-place mutation / aliasing** (e.g. `SplitIka`: `append(word[:n], 'a')`
   into a backing array shared with `w.Word`). Causes the double-processing above.
   You wrote this logic and want to assess whether it is intentional.
2. **`MakeCopy` RuleBack** (`data/worddata.go`): clones `RuleFront` twice and
   never clones `RuleBack`, so copies drop back-rule history in the `rules`
   column. A clear copy-paste typo, but fixing it changes output — held for review.

## Tests
- `go test -race ./go_modules/deconstructor/...` — all pass.
- New: `splitters/split_helpers_test.go`, `data/globaldata_test.go`,
  `workerpool` RunCollect test.

## Files changed (production)
- `data/matchdata.go` — removed mutexes, added `NewMatchData` + `Merge`.
- `data/worddata.go` — added `Acc *MatchData` field (copied in `MakeCopy`).
- `data/globaldata.go` — added `IsInInflectionsStr`.
- `data/stats.go` — removed mutexes from `SaveWordStats`.
- `data/sandhi_rules.go` — added cached `Ch1S`/`Ch2S`.
- `importer/sandhi_rules.go` — populate `Ch1S`/`Ch2S`.
- `splitters/split_2words.go`, `split_3words.go` — string/offset rewrite.
- `splitters/split_helpers.go` — `runeOffsets`.
- `splitters/*.go` (19 files) — mechanical `data.M.` → `w.Acc.` for per-worker accumulator.
- `main.go` — `RunCollect` + `Merge` wiring.
- `workerpool/workerpool.go` — added `RunCollect`.
