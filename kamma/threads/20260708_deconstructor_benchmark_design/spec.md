# Spec: Deconstructor Benchmark Suite (design only — to be executed by another agent)

## Context

`go_modules/deconstructor/` deconstructs ~1M unmatched Pāḷi compound words using a
bounded worker pool (`runtime.NumCPU() × 2` workers), an O(k) sandhi-rule index,
and a family of splitters (`Split2`, `Split3`, `SplitLwff`, `SplitLwfb`,
`SplitRecursive` + ~14 heuristic splitters). It was already optimized once
(bounded pool, rule index → 3-5× speedup). This thread designs the **next round
of measurement**: a benchmark/profiling suite another agent runs to find where
the remaining time and memory go. **No production code changes.** Temporary,
uncommitted scaffolding (`*_test.go` benchmark files, pprof flags in a throwaway
copy of `main.go`) is allowed; the deconstructor's logic must not change.

## Goal

Produce a ranked, evidence-backed list of optimization candidates, each with:
measured cost (% of CPU time, allocations, or lock-wait), a hypothesis for the
fix, and estimated ceiling of improvement. Output: a findings report in this
thread directory (`findings.md`), plus saved pprof profiles.

## Ground rules for the executing agent

1. **Never benchmark against the live db.** Copy `dpd.db` to scratchpad if any
   test touches it. Skip `SaveToDb()` entirely (guard already exists via
   `L.WordLimit != 0` / `testSet`).
2. **Correctness baseline first.** Before any experiment, run the current code
   once on the chosen workload and save `output/matches.tsv` sorted — this is
   the golden output. Any later experimental variant must produce identical
   matches (the point is measurement, but a broken measurement harness produces
   false conclusions).
3. **Fresh process per measurement** (per CLAUDE.md benchmarking rules). Check
   system load before trusting wall-clock; prefer ratios.
4. **Two workload tiers:**
   - **Tier A (fast iteration):** a fixed deterministic sample of ~20k words
     from `Unmatched` (sorted keys, first 20k — map iteration is random, so
     sort first). Use `L.WordLimit` or a filtered map. Target: < 1 min runs.
   - **Tier B (validation):** the full corpus, run only to confirm the top 2-3
     findings from Tier A scale.
5. All scaffolding lives in scratchpad or is deleted before finishing; nothing
   is committed.

## Benchmark hypotheses to test (ranked by expected payoff)

### H1. Global lock contention throttles the worker pool
`matchdata.go` guards everything with four **global** mutexes. Every single
`SplitRecursive` call takes `muTried` (in `NotTriedYet`), `muProcess`
(`ProcessPlusOne` — also taken in every splitter), and `muMatched` twice
(`HasNoMatches`). With `NumCPU×2` workers hammering four global locks, workers
may spend more time waiting than splitting.
**Measure:** run with `runtime.SetMutexProfileFraction(1)` and block profiling;
capture `pprof` mutex + block profiles on Tier A. Report % of worker time
blocked, per-lock breakdown.

### H2. `NotTriedYet` does an O(n) linear scan under a global lock
`slices.Contains(splitList, splitString)` scans a growing string slice while
holding `muTried`, and `MakeSplitString()` (a join + conversions) runs on every
call just to build the probe key. For words with thousands of tried splits this
is quadratic under a global mutex.
**Measure:** CPU profile — % time in `NotTriedYet` + `MakeSplitString`;
histogram of `TriedMap` value lengths at end of run (max, p99). A
`map[string]struct{}` per word would make this O(1) — measure the ceiling.

### H3. `MakeCopy` allocation storm / GC pressure
Every candidate split calls `w.MakeCopy()` which clones 6 slices — inside
`Split3`'s O(n²) inner loops and every lwff/lwfb candidate. This is the classic
alloc-heavy hot path.
**Measure:** heap/alloc profile (`pprof -alloc_space`, `-alloc_objects`);
`GODEBUG=gctrace=1` to get GC % of wall time; report allocations per word
processed. Also note (report only, don't fix): `MakeCopy` clones `RuleFront`
twice and never clones `RuleBack` — flag as a latent-bug finding.

### H4. rune↔string conversion churn in map lookups
`IsInInflections(word []rune)` does `string(word)` — an allocation — on every
lookup, and lookups happen O(len²) per word in `Split2`/`Split3`. Similarly
`string(w.Word)` is re-converted in every `MatchData` method.
**Measure:** alloc profile attribution to `runtime.slicerunetostring`; CPU % in
map access vs conversion. Micro-benchmark (`testing.B`): current lookup vs a
pre-converted-string design on real inflection data.

### H5. Worker count is untuned
`NumCPU×2` was a guess. If H1 shows contention, more workers = more contention;
if work is CPU-bound, ×2 oversubscribes.
**Measure:** Tier A wall-clock sweep over workers ∈ {NumCPU/2, NumCPU, ×2, ×4},
fresh process each, 3 runs each, report median + spread.

### H6. Stage breakdown — where does end-to-end time actually go?
Import (3 parallel loaders), compute, TSV/JSON writes, `SaveToDb` (GORM
`CreateInBatches` 2000 after full `DELETE FROM lookup`).
**Measure:** timestamps around each stage on a full Tier B run (SaveToDb against
a scratchpad db copy). If import or db-write dominates, splitter micro-tuning is
pointless — this frames all other findings (per CLAUDE.md: state what fraction
of the user-facing command each candidate represents).

### H7. Memory footprint of the three inflection maps
`AllInflections`, `NoFirst`, `NoLast` are `map[string]string` with empty values
— `map[string]struct{}` halves bucket payload; `NoFirst`/`NoLast` triple the
key storage of the same corpus.
**Measure:** heap profile after import; `runtime.ReadMemStats` HeapInuse before
vs after import. Report MB and whether it matters (footprint, not speed —
unless GC scanning of huge maps shows up in gctrace).

### H8. `Split3` triple-nested explosion
O(len²) split positions × sandhi-rule pairs, with `MakeCopy` in the innermost
loop, and a commented-out early-exit (`deconstructor.md` TODO: "eliminate
possibilities upfront with noLastLetter and noFirstLetter checks").
**Measure:** CPU self+cumulative % of `Split3` vs `Split2` vs lwff/lwfb;
counter of inner-loop iterations per word length; test the ceiling of the
early-exit pre-check idea by counting how often `IsInInflectionNoFirst(word1)`
would prune the inner rule loop.

## Deliverables (executing agent)

1. `findings.md` in this thread dir: per-hypothesis verdict
   (confirmed/rejected + numbers), ranked top-3 optimization candidates with
   estimated ceilings, latent bugs observed (report only).
2. Saved profiles (cpu, heap, mutex, block) in scratchpad, paths referenced.
3. Golden-output equivalence statement for any variant measured.
4. No diffs to production code; scaffolding removed.

## Out of scope

- Implementing any optimization (separate follow-up thread).
- Changing output formats, limits defaults, or db logic.
- Benchmarking `exporter/deconstructor/` (already optimized separately).

## Independent verification (Agent 2, 2026-07-08)

A second agent ran the benchmark suite independently from a separately-authored
harness (`go_modules/deconstructor/cmd/bench2/`, `cmd/lookupbench/`), without
reading or building on the first agent's conclusions. Results are in
`findings_agent2.md`.

Key independent findings:
- **Golden output is deterministic** across 1-worker and 44-worker runs (same
  MD5 × 5 runs). The spec's H9 concern about output varying with parallel
  workers does not hold for the sorted (word, split) pair set — dedup ensures
  the same matches are found regardless of worker interleaving.
- **Worker scaling is partial, not zero**: 4× workers (11→44) gives 1.27×
  speedup, plateauing at 2×CPU. (First agent reported "zero scaling".)
- **H2 (NotTriedYet linear scan) is rejected as a bottleneck**: only 0.029%
  of block time. The real lock bottleneck is `muMatched` (MakeMatch), not
  `muTried`.
- **RunesPlus is 82.6% of all allocation *objects*** (not just bytes) — 621M
  objects across 20k words.
- **Micro-benchmark confirms 3.03× speedup** for pre-converted string keys vs
  `[]rune → string` lookup.
- **MakeCopy bug clarified**: RuleBack is not shared (as first agent reported) —
  it is *nil* in the copy (never assigned). RuleFront is cloned twice from the
  original (redundant, not harmful). Both lines use `w.RuleFront`.

Top-3 ranked candidates agree with first agent's ranking (allocations+string
conversion #1, lock elimination #2, map[string]struct{} #3) but the magnitude
and mechanisms differ in detail — see `findings_agent2.md`.

## Non-goals / risks

- Wall-clock numbers on a loaded machine are noise — use profiles and ratios.
- Map iteration order randomness: any word sample must be sorted-then-sliced or
  results aren't reproducible.
- `TriedMap`/dedup behavior means run-to-run match *counts* are stable but
  per-word routes can vary with worker interleaving; golden comparison must be
  on the sorted set of (word, split) pairs, not routes/times.
