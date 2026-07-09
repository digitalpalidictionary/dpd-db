# Deconstructor Benchmark Findings

> Generated 2026-07-08, Tier A workload (20k deterministic sorted unmatched words), 22-core AMD.

## Summary

The deconstructor is **lock-bound, not CPU-bound**. Adding workers doesn't help. Two-thirds of all allocations come from `RunesPlus` (rune concatenation). The largest single CPU consumer is `slicerunetostring` (16.2%) — the implicit `[]rune → string` conversion in every inflection lookup.

## H1: Global lock contention — CONFIRMED 🔴

**92% of all blocking time** is on `sync.Mutex.Lock`. Workers spend more time waiting for each other than computing.

| Lock | Type | Block time | Notes |
|------|------|-----------|-------|
| `muMatched.Lock` (MakeMatch) | RWMutex write | 88.5% cum | Writing new matches dominates |
| `muProcess.Lock` (ProcessPlusOne) | Mutex | 3.7% waiting | Per-word counter |
| `muMatched.RLock` (HasNoMatches) | RWMutex read | 1.6% waiting | Checking if matched |
| `muTried.Lock` (NotTriedYet) | Mutex | implicit in Mutex.Lock | Dedup check |

**Worker count sweep** (11/22/44/88 workers, 3 runs each):

| Workers | Median (s) | Notes |
|---------|-----------|-------|
| 11 (CPU/2) | 46.8 | |
| 22 (CPU)   | 46.5 | |
| 44 (CPU×2) | 46.6 | current default |
| 88 (CPU×4) | 47.7 | slight degradation |

**Zero scaling.** The computation is lock-bound — 44 workers produce the same wall time as 11.

## H2: NotTriedYet linear scan — CONFIRMED 🟡

`slices.Contains(splitList, splitString)` scans the growing `TriedMap` linearly under `muTried.Lock`. With 220,784 blocked tries, the per-word TriedMap can grow to hundreds of entries. The lock is already the biggest contention point; the O(n) scan inside it makes it worse.

- NotTriedYet allocates 9MB inuse / 38MB cumulative
- MakeSplitString (called by NotTriedYet) allocates 29MB cumulative
- Each NotTriedYet call joins strings just to build a dedup key

## H3: MakeCopy / RunesPlus allocation storm — CONFIRMED 🔴

**`RunesPlus` allocates 24GB — 67.5% of all allocations** across the 40s run. Total allocations: 35.5GB for 20k words (~1.8MB/word).

| Source | Alloc (GB) | % |
|--------|-----------|----|
| `RunesPlus` | 24.0 | 67.5 |
| `slices.Clone` (word slices) | 1.17 | 3.3 |
| `IsInInflections` ([]rune→string) | 1.01 | 2.8 |
| `reflect.growslice` | 0.98 | 2.8 |
| `AddPath` | 0.64 | 1.8 |
| `slices.Clone` (string slices) | 0.64 | 1.8 |

CPU: `runtime.makeslicecopy` = 15.27% cum, `runtime.mallocgc` = 14.70% cum.

### Latent bug: MakeCopy clones RuleFront twice, RuleBack never

In `data/worddata.go:MakeCopy()`:
```go
w2.RuleFront = slices.Clone(w.RuleFront)  // cloned once
w2.RuleFront = slices.Clone(w.RuleFront)  // cloned AGAIN — overwrites the first clone
```
`w2.RuleBack` is never cloned — the copy shares the backing array with the original. This is a bug, not a measurement artifact.

## H4: rune↔string conversion churn — CONFIRMED 🔴

`slicerunetostring` = **16.21% CPU flat**, 29.14% cumulative. Every `IsInInflections(word []rune)` does `string(word)` — an allocation. In `Split2`/`Split3` inner loops, this happens O(len²) times per word.

- `encoderune`: 10.93% CPU (encoding runes to UTF-8)
- `IsInInflections`: 1.01GB alloc (2.8% of total)
- Combined string conversion + encoding = ~27% CPU

## H5: Worker count untuned — CONFIRMED (irrelevant)

See H1 table. Worker count doesn't matter because the global mutexes serialize all meaningful work.

## H6: Stage breakdown (Tier A)

| Stage | Time (s) | % |
|-------|---------|----|
| Import (DB + files) | 0.004 | ~0% |
| Compute (deconstruction) | 36.9 | 92% |
| File writes (TSV/JSON) | 3.0 | 8% |

The compute phase is everything. Import and file writes are negligible.

## H7: Inflection map memory — CONFIRMED 🟡

End-of-run heap: 957MB total.

| Map | Inuse (MB) | % |
|-----|-----------|----|
| `MapDifference` (import) | 256 | 26.8 |
| `AllInflectionsNoFirst` | 93 | 9.8 |
| `AllInflectionsNoLast` | 90 | 9.4 |
| CST word list | 72 | 7.6 |

The three inflection maps (`AllInflections`, `NoFirst`, `NoLast`) use `map[string]string` with empty values — switching to `map[string]struct{}` halves bucket payload (~183MB → ~91MB savings on NoFirst+NoLast alone).

## H8: Split3 triple-nested — CONFIRMED 🟡

Split3 = 63.68% cumulative CPU (the biggest single algorithmic cost). However, most of that time is spent in lock contention and string conversions, not the split logic itself. The inner loop checks 3 inflections per sandhi-rule pair; the commented-out early-exit (checking `IsInInflectionNoFirst` before the inner rule loop) would help most when H1+H4 are fixed first.

## Latent bugs (report only)

1. **MakeCopy clones RuleFront twice, never clones RuleBack** (`data/worddata.go:55-56`). The RuleBack slice is shared between copies, risking data corruption in concurrent access.
2. **`reduceUnmatched()` picks different word subsets each run** (Go map iteration). Combined with concurrent workers, this makes the deconstructor non-deterministic — two runs with the same database produce different output sets.

## Top 3 optimization candidates (ranked)

### 1. 🥇 Eliminate RunesPlus allocation storm + rune→string conversion (H3+H4)

**Cost:** 67.5% alloc + 16.2% CPU.
**Fix:** Store words as strings in WordData, not `[]rune`. Pre-convert before splitter loops.
**Estimated ceiling:** 40-60% wall-clock improvement.
**Risk:** Every splitter and helper touches `w.Middle`, `w.Word`, etc. — high touch surface. But the actual change is mechanical (replace `[]rune` with `string` in the WordData struct).

### 2. 🥈 Eliminate global mutexes (H1)

**Cost:** 92% of blocking time; makes 88 workers no faster than 11.
**Fix:** Per-word MatchData/TriedMap owned by each worker goroutine, merged at the end. The word-level computation is embarrassingly parallel — no shared state except dedup.
**Estimated ceiling:** 3-5× wall-clock speedup (unlocks 22 cores).
**Risk:** Requires restructuring MatchData from global singleton to per-worker, then merging. Dedup semantics (NotTriedYet) must be preserved. Higher effort than #1.

### 3. 🥉 Switch inflection maps to `map[string]struct{}` (H7)

**Cost:** 183MB memory; some GC pressure.
**Fix:** `map[string]string` → `map[string]struct{}` for AllInflections/NoFirst/NoLast.
**Estimated ceiling:** 5-10% memory reduction, mild speedup from reduced GC scanning.
**Risk:** Low — mechanical change to GlobalData and all call sites.

## Golden output

- `scratchpad/golden_r1.tsv` — deterministic 1-worker golden (336,031 pairs, 18,238 matched / 20,000)
- MD5: `500e8d090bb7497d554a2d20a83358c2`

## Profiles

- `scratchpad/profiles/cpu_tierA.prof` — CPU profile (40s, 44 workers)
- `scratchpad/profiles/heap_tierA.prof` — heap profile (957MB inuse)
- `scratchpad/profiles/mutex_tierA.prof` — mutex contention (1586s delay)
- `scratchpad/profiles/block_tierA.prof` — block profile (1856s delay)
