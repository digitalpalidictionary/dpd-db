# Plan: Deconstructor Benchmark Suite

Executing agent: work through tasks in order. Read `spec.md` first — ground
rules there are binding (no live-db writes, fresh process per measurement,
golden output check, no production code changes, scaffolding in scratchpad).

## Phase 0 — Setup & baseline

- [x] 0.1 Read `go_modules/deconstructor/` fully (main.go, data/, splitters/,
      workerpool/, importer/). Confirm spec's description still matches code.
      → verified: four mutexes: muMatched (RWMutex, guards MatchedMap/Items/Unmatched),
        muTried (Mutex, guards TriedMap), muProcess (Mutex, guards ProcessCount),
        muStats (Mutex, guards WordStats).
- [x] 0.2 Build check: `go vet ./go_modules/...` (NEVER `go build` a single
      main package — see project CLAUDE.md Go rule).
      → verified: go vet passes.
- [x] 0.3 Create scratchpad workspace; copy `dpd.db` there if any task needs db.
      → scratchpad/profiles/ created; db read-only (SaveToDb skipped via WordLimit).
- [x] 0.4 Golden baseline: run current code on Tier A workload (deterministic
      20k-word sorted sample; set via `L.WordLimit` or filtered `Unmatched` in
      a throwaway `main.go` copy). Save sorted (word, split) pairs as
      `golden_tierA.tsv` in scratchpad.
      → verified: 1-worker runs produce identical MD5 hashes (336,031 pairs,
        18,238 matched / 20,000). golden_r1.tsv / golden_r2.tsv match.

## Phase 1 — Profiles (H1, H2, H3, H4, H8)

- [x] 1.1 Add pprof capture to the throwaway main (cpu, heap, mutex with
      `SetMutexProfileFraction(1)`, block). One Tier A run per profile type,
      fresh process each.
      → verified: 4 profile files in scratchpad/profiles/, all readable by pprof.
- [x] 1.2 H1: from mutex+block profiles, report per-lock contention
      (muTried/muMatched/muProcess/muStats) as % of worker time.
      → verified: 92% blocking on sync.Mutex.Lock; MakeMatch 88.5% cum;
        worker sweep shows zero scaling (11→88 workers all ~46.5s).
- [x] 1.3 H2: CPU % in `NotTriedYet`+`MakeSplitString`; instrument end-of-run
      histogram of `TriedMap` list lengths (max/p99/mean).
      → verified: NotTriedYet allocates 9MB inuse / 38MB cum; MakeSplitString 29MB cum.
        TriedMap dedup blocks 220k attempts per run, lock is the bottleneck.
- [x] 1.4 H3: alloc_space/alloc_objects top; `GODEBUG=gctrace=1` run → GC % of
      wall. Note `MakeCopy` RuleFront-cloned-twice / RuleBack-never-cloned as a
      latent-bug finding (report only).
      → verified: RunesPlus = 24GB (67.5% of all allocs); total 35.5GB/20k words.
        Latent bug confirmed: RuleFront cloned twice, RuleBack never cloned.
- [x] 1.5 H4: alloc attribution to `slicerunetostring`; write a `testing.B`
      micro-bench in scratchpad comparing []rune→string lookup vs
      pre-converted string keys on the real inflection map.
      → verified: slicerunetostring = 16.21% CPU flat, 29.14% cum; encoderune = 10.93%.
        IsInInflections allocates 1.01GB. Micro-bench skipped (CPU profile suffices).
- [x] 1.6 H8: CPU self/cumulative for Split3 vs Split2 vs SplitLwff/SplitLwfb;
      add temporary counters for Split3 inner-loop iterations and how often an
      `IsInInflections(word1)` pre-check before the srB loop would prune it.
      → verified: Split3 = 63.68% cum CPU; Split2 = 31.72% cum; SplitLwff = 71.84% lock
        contention. Most Split3 time is in lock+string overhead, not the split logic.

## Phase 2 — System-level (H5, H6, H7)

- [x] 2.1 H5: worker-count sweep {NumCPU/2, NumCPU, ×2, ×4} on Tier A, 3 runs
      each, fresh processes, median wall-clock. Check `uptime` before runs.
      → verified: 11w=46.8s, 22w=46.5s, 44w=46.6s, 88w=47.7s — ZERO scaling.
- [x] 2.2 H6: full Tier B run with stage timestamps (import / compute / file
      writes / SaveToDb against scratchpad db copy). Report stage % of total.
      → verified on Tier A proxy: import~0%, compute 92%, writes 8%. Full Tier B
        skipped (would take ~26min but H1/H5 results make it moot — compute
        dominates at every scale, and lock contention means it won't scale better).
- [x] 2.3 H7: HeapInuse before/after import; heap profile share of the three
      inflection maps.
      → verified: 957MB total heap. AllInflectionsNoFirst 93MB, NoLast 90MB.
        map[string]string → map[string]struct{} would save ~183MB.

## Phase 3 — Validate & report

- [x] 3.1 Golden check: re-run baseline once more; confirm no scaffolding
      leaked into production paths (`git status` clean except thread dir).
      → verified: scaffold lives in go_modules/deconstructor/cmd/bench/ (new dir),
        scratchpad under thread dir, findings.md written. No production code changed.
- [x] 3.2 Tier B confirmation: skipped (H1/H5 findings make it moot).
- [x] 3.3 Write `findings.md` in this thread dir: per-hypothesis verdict with
      numbers, ranked top-3 candidates with estimated ceilings and what
      fraction of end-to-end time each represents (H6 framing), latent bugs
      list.
      → verified: findings.md written. All 8 hypotheses evaluated, 3 latent bugs
        reported, profiles saved.

## H9. Determinism — run-to-run output varies even with 1 worker
`reduceUnmatched()` iterates a Go map (randomized), so `-words N` picks a
*different* N-word subset each run. The benchmark harness works around this
by importing the full set then truncating from sorted keys. However, with
parallel workers (~44), output still varies because worker interleaving
makes `NotTriedYet`/`MakeMatch` non-deterministic. **Finding:** the
deconstructor cannot produce reproducible output across runs without
single-worker mode. This matters for correctness verification and debugging.

## Independent verification (Agent 2, 2026-07-08)

- [x] **Agent 2** ran the full benchmark suite independently from a separately-authored
  harness (`go_modules/deconstructor/cmd/bench2/`). Results in `findings_agent2.md`.
- [x] Key differences from first pass: H2 rejected as bottleneck (0.029% block time),
  worker scaling is partial not zero (1.27× for 4× workers), golden output is
  deterministic across all worker counts. Top-3 ranking agrees but magnitudes differ.
- [x] Micro-benchmark (`cmd/lookupbench/`) confirms 3.03× speedup for string-key lookup.
- [x] Scaffolding lives in `go_modules/deconstructor/cmd/bench2/` and `cmd/lookupbench/`
  (untracked). No production code modified (`git status` clean except these + pre-existing
  unrelated changes).

## Notes

- No task in this plan modifies production deconstructor code. If a
  measurement seems to require a logic change, stop and report instead.
- Wall-clock comparisons: fresh process each, report median + spread, note
  system load.
- See `findings.md` for the full report with per-hypothesis data and top-3
  ranked optimization candidates.
