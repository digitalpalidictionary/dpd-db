# Plan: Deconstructor Speedup

Read `spec.md` first. Two changes (A: per-worker MatchData; B: confined
string/offset in Split2+Split3) + one bug fix (C: MakeCopy RuleBack), each
behind a measured before/after gate. **All work happens on a dedicated git
branch and is committed there** (see 0.1). Every measurement = median of 3
fresh processes on a quiet machine (`uptime` first), reported with spread.

Binding gates (from spec): golden `(word,split)` MD5 must never change
(Tier A `500e8d09…`); a change is kept only if Tier B wall-clock median
improves beyond noise AND its targeted profile metric moves.

## Phase 0 — branch + baseline

- [ ] 0.1 Create and switch to branch `deconstructor-speedup` off `main`.
      Commit the two kamma thread dirs (benchmark-design + this) as the first
      commit if not already on the branch.
- [ ] 0.2 `go vet ./go_modules/...` clean (never `go build` a single main pkg —
      project CLAUDE.md).
- [ ] 0.3 Copy `dpd.db` to scratchpad for any run that reaches `SaveToDb`;
      otherwise keep `WordLimit != 0` / testSet so SaveToDb is skipped.
- [ ] 0.4 Capture baselines (fresh processes):
      - Tier A golden `(word,split)` → confirm `md5 = 500e8d09…`.
      - Tier B (full corpus) golden `(word,split)` → save md5 as `golden_tierB`.
      - Tier B wall-clock: 3 fresh runs, record median + spread → `baseline.txt`.
      - Capture baseline cpu+heap+mutex+block profiles (Tier A is fine for
        mechanism attribution) → `profiles/baseline/`.
      → verify: two Tier B runs give identical `(word,split)` md5 (determinism
        holds at full scale, as it did at 20k).

## Phase A — per-worker MatchData (Change A)

- [ ] A.1 Add `RunCollect` to `deconstructor/workerpool` (keep `Run`). Unit-test
      it (workerpool already has a test file).
- [ ] A.2 Refactor `MatchData` accumulation to per-worker instances + a `Merge`;
      thread the accumulator explicitly through `deconstruct`/`SplitRecursive`/
      sub-splitters (record the threading choice in a note here). Remove the
      four global mutexes from the hot path; keep `BlockedTries`/`MaxedOut`
      atomics. Preserve `NotTriedYet` dedup exactly.
- [ ] A.3 Lint/build: `go vet ./go_modules/...`, `gofmt`.
- [ ] A.4 Correctness gate: Tier A + Tier B golden `(word,split)` md5 unchanged.
      STOP if changed.
- [ ] A.5 Benefit measurement (fresh processes):
      - Tier B wall-clock median vs baseline.
      - Block profile: `muMatched` share of block time (target: 72% → small).
      - Worker sweep {11,22,44} — scaling vs baseline 1.27×.
      → decision: keep if Tier B median beats noise; else diagnose/revert.
- [ ] A.6 Commit Change A to the branch with the measured numbers in the commit
      body (before/after median, muMatched block %).

## Phase B — confined string/offset in Split2+Split3 (Change B)

- [ ] B.1 Add `runeOffsets(s string) []int` helper + `IsInInflectionsStr`.
      Unit-test both (multi-byte round-trip per spec tests #2, #3).
- [ ] B.2 Rewrite Split2 inner loop: one `string`+offset build per call,
      substring candidates, `IsInInflectionsStr`, string-concat sandhi,
      materialize `[]rune` only on match. Do NOT touch other splitters or the
      `WordData` struct type.
- [ ] B.3 Rewrite Split3 inner loops the same way (this is the big one — 61.9%).
- [ ] B.4 Lint/build clean; `gofmt`.
- [ ] B.5 Correctness gate: Tier A + Tier B golden `(word,split)` md5 unchanged.
      Extra scrutiny on multi-byte words. STOP if changed.
- [ ] B.6 Benefit measurement (fresh processes, on top of A):
      - Tier B wall-clock median vs post-A.
      - Alloc profile: `RunesPlus` share → ~0; total alloc_space drop;
        `slicerunetostring`/`encoderune` CPU drop; `gcBgMarkWorker` from ~19%.
      → decision: keep if Tier B median beats noise; else diagnose/revert.
- [ ] B.7 Commit Change B to the branch with measured numbers in the body.

## Phase C — MakeCopy RuleBack fix

- [ ] C.1 Fix `MakeCopy`: clone `RuleFront` once + `RuleBack` once
      (`data/worddata.go`). Add `worddata_test.go` (spec test #1).
- [ ] C.2 Gate: `(word,split)` md5 unchanged (only `rules` column changes).
- [ ] C.3 Commit to the branch.

## Phase D — validate & report

- [ ] D.1 Full smoke: `go vet ./go_modules/...`, run the Go test suite for the
      deconstructor packages. If the broader pipeline has a cheap smoke, run it.
- [ ] D.2 Final combined measurement: Tier B wall-clock baseline vs final
      (A+B+C), median of 3 fresh runs. Report the **combined measured speedup**
      and what fraction of the standalone deconstructor command it represents
      (and note deconstructor is one stage of `makedict`).
- [ ] D.3 Write `results.md` in this thread: per-change before/after numbers,
      profile confirmations, golden-equivalence statements, combined speedup.
      Honest verdict — if a change delivered only imaginary benefit, say so and
      note it was reverted.
- [ ] D.4 Ensure scaffolding (bench harnesses, pprof-instrumented main copies)
      lives only in scratchpad; production code carries only the real changes +
      the committable unit tests. Final commit on the branch.
      → verify: `git status` clean; branch contains all commits; `git diff
        main...branch` shows only intended files.

## Notes
- No optimization is accepted on a single run or micro-bench alone (spec gate).
- If Change A underdelivers, the alternative sequencing (B before A) is testable —
  but only pursue it if A's Tier B result is within noise.
- Do not sweep unrelated pre-existing dirty files into any commit.
