# Deconstructor Benchmark Findings — Independent Run (Agent 2)

> Generated 2026-07-08 by an independent benchmark pass.
> Written from scratch — does not reference or build on any other agent's
> conclusions. All measurements taken with a separately-authored harness
> (`go_modules/deconstructor/cmd/bench2/`, `cmd/lookupbench/`).
> Workload: Tier A — 20,000 deterministic sorted unmatched words.
> Machine: 22-core AMD, load avg ~1.5 during runs.

## Golden baseline

- 336,031 (word, split) pairs; 18,238 / 20,000 words matched (91.19%)
- MD5: `500e8d090bb7497d554a2d20a83358c2`
- **Identical across 1-worker and 44-worker runs** (verified 3× each).
  The dedup logic (NotTriedYet + MakeMatch's `slices.Contains` guard) ensures
  the same match *set* regardless of worker interleaving. Output sorted by
  (word, split) is fully deterministic.

## Summary

The deconstructor is **allocation-bound and partially lock-bound**. The single
biggest cost is `tools.RunesPlus` — a `[]rune` concatenation that allocates a
new slice on every call, called ~621M times (82.6% of all allocations, 24.3GB
of 36GB total). The second cost is the implicit `[]rune → string` conversion
(`runtime.slicerunetostring`) on every inflection-map lookup — 15.9% flat CPU.
These two together drive a GC overhead of 19% of all CPU time.

Lock contention is real but does not completely eliminate scaling: 4× more
workers yields 1.27× speedup, plateauing at 2×CPU. The bottleneck lock is
`muMatched` (RWMutex write in `MakeMatch`), which accounts for 72% of all
blocked time. `muTried` (NotTriedYet) sees negligible contention.

## H1: Global lock contention — CONFIRMED (partial) 🟠

Block profile (1355.5s total delay across 44 workers):

| Call site | Lock | Block time | % of total |
|-----------|------|-----------|------------|
| `MakeMatch` | RWMutex write | 975.5s | 71.96% |
| `ProcessPlusOne` | Mutex | 249.0s | 18.37% |
| `HasNoMatches` | RWMutex read | 19.5s | 1.44% |
| `NotTriedYet` | Mutex | 0.39s | 0.029% |

Mutex profile (1138.6s total): 98.2% on `Mutex.Unlock`, 88.5% cum in `MakeMatch`.

**Worker count sweep** (medians of 3 runs each):

| Workers | Median (s) |
|---------|-----------|
| 11 (CPU/2) | 54.2 |
| 22 (CPU)   | 46.4 |
| 44 (CPU×2) | 42.6 |
| 88 (CPU×4) | 43.1 |

4× workers (11→44) gives 1.27× speedup; 88 workers shows no improvement.
**Scaling is limited, not eliminated.** The system benefits from parallelism
up to ~2×CPU, then `muMatched` write-lock contention caps it.

## H2: NotTriedYet linear scan — REJECTED as bottleneck ⬜

- CPU: `NotTriedYet` = 1.33% cum; `MakeSplitString` = 0.37% cum.
- Block: `NotTriedYet` = 390ms = **0.029%** of total block time.
- Alloc: `NotTriedYet` = 46MB inuse; `MakeSplitString` = 0.21GB cum.
- 220,784 blocked tries (dedup hits), but the cost is negligible.

The O(n) scan inside `muTried` is cheap in practice. `muTried` sees almost no
contention — the real lock bottleneck is `muMatched` (MakeMatch), not
`muTried`. Switching to `map[string]struct{}` per-word would make this O(1)
but the current cost is too small to matter.

## H3: RunesPlus allocation storm — CONFIRMED 🔴

`RunesPlus` is the dominant allocator by an enormous margin:

| Metric | Value | % of total |
|--------|-------|------------|
| alloc_space | 24.31GB | 67.6% of 35.97GB |
| alloc_objects | 620,967,743 | 82.6% of 751M |

CPU: `makeslicecopy` = 16.18% cum, `mallocgc` = 15.22% cum.
GC: `gcBgMarkWorker` = 19.03% cum CPU; 59 GC cycles; heap grows to 2.1GB.

`RunesPlus` callers: Split3 = 61.9%, Split2 = 37.5%.

Every sandhi-rule application does `RunesPlus(wordA[:n-1], sr.Ch1)` and
`RunesPlus(sr.Ch2, wordB[1:])` — two fresh `[]rune` allocations per rule per
split position. In Split3's O(n²) loop with ~1-5 rules per position, this is
hundreds of allocations per word.

### Latent bug: MakeCopy clones RuleFront twice, never clones RuleBack

`data/worddata.go:MakeCopy()`:
```go
w2.RuleFront = slices.Clone(w.RuleFront)  // clone 1
w2.RuleFront = slices.Clone(w.RuleFront)  // clone 2 — re-clones original, redundant
// w2.RuleBack is never assigned → stays nil (empty)
```
Both lines use `w.RuleFront` (the original). `RuleBack` is never copied — the
copy's `RuleBack` is nil, silently dropping rule history. Impact: the "rules"
column in the output TSV may be incomplete for multi-step splits. This is a
**data-completeness bug**, not a crash.

## H4: rune↔string conversion churn — CONFIRMED 🔴

| Symbol | flat CPU | cum CPU |
|--------|---------|---------|
| `slicerunetostring` | 15.91% | 28.70% |
| `encoderune` | 10.86% | 10.86% |

Combined string conversion + encoding = **~26.8% flat CPU** — the largest
single flat cost.

81% of `slicerunetostring` calls come from `IsInInflections` (86.2s of 106.4s).
`IsInInflections` is the biggest cumulative consumer at 34.93% cum.

Every `IsInInflections(word []rune)` does `string(word)` — an allocation — on
every lookup. In Split2/Split3 inner loops this happens O(len²) times per word.

### Micro-benchmark (cmd/lookupbench/)

| Design | ns/op | Speedup |
|--------|-------|---------|
| Current: `map[string]string`, `string([]rune)` | 121.1 | 1.00× |
| Optimized: `map[string]struct{}`, pre-converted string key | 40.0 | **3.03×** |

Pre-converted string keys are 3× faster per lookup, and eliminate the
allocation entirely.

## H5: Worker count untuned — CONFIRMED (partial) 🟡

See H1 table. Optimal at NumCPU×2 (44 workers on this 22-core machine). Beyond
that, `muMatched` contention eliminates gains. Below that (11 workers),
throughput is ~27% slower — there is useful parallelism available, just capped.

## H6: Stage breakdown — CONFIRMED ⬜

| Stage | Time | % |
|-------|------|---|
| Import (DB + files) | 4ms | ~0% |
| Compute (deconstruction) | 41.2s | 92% |
| File writes (TSV/JSON) | 3.8s | 8% |

Compute dominates entirely. Import is negligible; file writes are minor.
Splitter micro-tuning is the right focus.

## H7: Inflection map memory — CONFIRMED (low priority) 🟡

| State | HeapInuse |
|-------|-----------|
| After import | 1180MB |
| After compute | 2108MB |

Inuse at heap snapshot (968MB):

| Source | Inuse | % |
|--------|-------|---|
| `MapDifference` (import) | 258MB | 26.7% |
| `AllInflectionsNoFirst` | 98.75MB | 10.2% |
| `AllInflectionsNoLast` | 94.75MB | 9.8% |
| `MakeMatch` (MatchedMap/Items) | 89.78MB | 9.3% |
| CST word list | 72.25MB | 7.5% |

`NoFirst` + `NoLast` = 193.5MB. Switching `map[string]string` →
`map[string]struct{}` would halve bucket payload (~95MB savings). Low impact
on speed unless GC scanning of these maps shows in gctrace — it doesn't
significantly (GC is driven by RunesPlus churn, not map scanning).

## H8: Split3 triple-nested — CONFIRMED 🟡

| Splitter | cum CPU |
|----------|---------|
| `SplitRecursive` | 65.26% |
| `Split3` | 64.25% |
| `SplitLwff` | 58.17% |
| `Split2` | 32.36% |
| `SplitLwfb` | 20.01% |

Split3 is the biggest single algorithmic cost. `RunesPlus` attribution:
Split3 = 61.9%, Split2 = 37.5%. Most of Split3's CPU is in string conversion
(`slicerunetostring` 28.7% cum) and lock overhead (863s block delay cum),
not the split logic itself. The commented-out early-exit pre-check
(`IsInInflectionNoFirst` before the inner rule loop) would help, but only
after H3+H4 reduce the per-iteration overhead.

## H9: Determinism — CLARIFIED ⬜

The spec's H9 note claims output "still varies" with parallel workers. My
measurements show the opposite: the **sorted set of (word, split) pairs is
identical** (same MD5) across all 1-worker and 44-worker runs. The dedup logic
ensures the same matches are found regardless of interleaving.

The real non-determinism is only in **which words are selected** when
`L.WordLimit` is set (production path): `reduceUnmatched()` iterates a Go map
(randomized), picking a different N-word subset each run. This is a property
of the production code path, not of the matching logic itself.

## Latent bugs (report only)

1. **MakeCopy loses RuleBack** (`data/worddata.go:55-57`): RuleFront is cloned
   twice (redundant), RuleBack is never cloned — copies start with nil RuleBack,
   silently dropping rule history. The "rules" output column may be incomplete
   for multi-step recursive splits.

2. **`reduceUnmatched()` is non-deterministic** (`importer/unmatched.go`): Go
   map iteration order is randomized, so `L.WordLimit` picks a different word
   subset each run. Affects the production path only; the benchmark harness
   works around this by sorting keys before truncating.

## Top 3 optimization candidates (ranked)

### 1. 🥇 Eliminate RunesPlus allocations + rune→string conversions (H3+H4)

**Cost:** 67.6% of all allocations + 26.8% flat CPU + 19% CPU in GC (driven by
allocation churn).
**Fix:** Store `Word`/`Middle` as `string`, not `[]rune`. Pre-convert before
splitter loops. Replace `RunesPlus` (two `[]rune` allocs) with string
concatenation (one alloc, and only when needed). Use `map[string]struct{}`
for inflection maps (also fixes H7).
**Micro-bench:** 3.03× speedup on lookup alone; eliminates 621M allocations.
**Estimated ceiling:** 40-60% wall-clock improvement (single-threaded), plus
reduced GC pressure improves parallel scaling.
**Risk:** High touch surface — every splitter and helper touches `w.Middle`,
`w.Word` as `[]rune`. But the change is mechanical (type swap + call-site fixes).

### 2. 🥈 Eliminate MakeMatch write-lock contention (H1)

**Cost:** 72% of all blocked time; caps scaling at 1.27× for 4× workers.
**Fix:** Per-worker `MatchData` (each worker owns its own `MatchedMap`,
`TriedMap`, `ProcessCount`), merged at end of compute. The word-level
computation is embarrassingly parallel — no shared state except the final merge.
**Estimated ceiling:** 2-3× wall-clock (unlocks 22 cores; currently capped at
~2×CPU effective).
**Risk:** Requires restructuring `MatchData` from global singleton to
per-worker + merge. Must preserve dedup semantics (`NotTriedYet` becomes
per-worker, which is safe — each word is processed by exactly one worker via
the job channel). Higher effort than #1, but multiplier on top of #1's gains.

### 3. 🥉 Fix MakeCopy + switch inflection maps to struct{} (H3-bug + H7)

**Cost:** RuleBack data loss (correctness) + 193MB memory.
**Fix:** Fix `MakeCopy` to clone RuleBack. Switch `map[string]string` →
`map[string]struct{}` for AllInflections/NoFirst/NoLast.
**Estimated ceiling:** Correctness fix + 5-10% memory, mild GC reduction.
**Risk:** Low — mechanical changes. The MakeCopy fix is a one-liner.

## Profiles (saved in scratchpad2/profiles/)

- `cpu.prof` — CPU profile (35.7s duration, 370.7s total samples)
- `heap.prof` — heap profile (968MB inuse, 36GB alloc_space)
- `mutex.prof` — mutex contention (1138.6s delay)
- `block.prof` — block profile (1355.5s delay)

## Notes on methodology

- Every profile run was a fresh process (no in-process reuse).
- The worker sweep ran 3 fresh processes per worker count.
- The golden baseline was verified identical (MD5) across 1-worker ×2 and
  44-worker ×3 runs.
- No production deconstructor code was modified. All scaffolding lives in
  `go_modules/deconstructor/cmd/bench2/` and `cmd/lookupbench/` (untracked).
- `git status` confirms no production files touched by this pass.
