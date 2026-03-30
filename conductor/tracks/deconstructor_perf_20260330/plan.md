# Implementation Plan: Deconstructor Performance Optimization

## Phase 1: Worker Pool, Lock Mitigation, and Baseline
- [x] Task: Create a baseline test script to measure current overall execution time and compute SHA256 hashes of the generated output files (matches, unmatched, JSON, stats).
- [x] Task: Write Tests - Add basic unit tests for the worker pool logic, asserting proper channel handling and worker termination.
- [x] Task: Implement - Refactor `go_modules/deconstructor/main.go` to use a bounded worker pool (using channels and `runtime.NumCPU()`) instead of launching an unbounded `go deconstruct(w)` for every word.
- [x] Task: Implement - Explicitly address the global mutex (`Mu`) contention in `MatchData` (e.g., implement sharded mutexes, use `sync.Map`, or aggregate matches locally per worker).
- [x] Task: Implement - Evaluate importer loading time; parallelize data loading in `importer.go` if the time is measurable and significant.
- [x] Task: Verify - Run the deconstructor, record the new execution time, and assert that the output file SHA256 hashes match the baseline perfectly.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Worker Pool, Lock Mitigation, and Baseline' (Protocol in workflow.md)

### Phase 1 Implementation Notes (do not lose on context clear)
- `HasNoMatches`, `matchCount`, `ProcessCounter` changed from value receivers `(m MatchData)` to pointer receivers `(m *MatchData)` — value receivers caused an unsynchronized full-struct copy before the mutex was acquired, causing data races detected by `-race`.
- `BlockedTries` and `MaxedOut` in `data/matchdata.go` changed from bare `int` to `sync/atomic.Int64`; `split_recursive.go` updated to use `.Add(1)`. This was a pre-existing data race.
- Worker count settled on `runtime.NumCPU() * 2` (benchmarked 1x/4x/8x on 22-core machine; marginal differences, 2x chosen).
- SHA256 hash verification dropped from Verify tasks — word set is non-deterministic (Go map iteration), so hashes differ each run. Verification approach is: timing + matched% (should be ~90%).
- **`data.L.WordLimit` is currently set to `500` in `limits.go` for fast testing. Must be reset to `0` before final commit.**
- Worker pool extracted to `go_modules/deconstructor/workerpool/` sub-package (generic `Run[T any]`) rather than inlined in `main.go` — needed to avoid `package main` `init()` side-effects preventing unit tests.

## Phase 2: O(k) Indexed Sandhi Rule Lookup

### Phase 2 Pre-work (verify before implementing)
- `SandhiRules.ChA` and `ChA.ChB` are `[]rune` slices loaded from TSV. The splitters compare them against single-rune slices (`wordA[len(wordA)-1:]`, `wordB[:1]`). Before building `map[rune]map[rune][]SandhiRules`, **confirm ChA and ChB are always exactly 1 rune** by inspecting the TSV (path: `tools.Pth.SandhiRules`). If multi-rune, the index key needs to be a string, not a rune.
- Splitters that iterate `data.G.SandhiRules` — ALL of these need refactoring:
  - `split_2words.go` — 1 loop
  - `split_3words.go` — 2 nested loops (`srA` and `srB` — both keyed on ChA/ChB)
  - `split_lwff.go` — 1 loop
  - `split_lwfb.go` — 1 loop
  - `split_pīti.go` — 1 loop
  - `split_ādi.go` — 1 loop
  - `split_apicaevaiti.go` — 1 loop
- `SandhiRuleIndex` should be added as a new field on `GlobalData` in `data/globaldata.go`, populated during import (after `makeSandhiRules()` completes).
- `GlobalData` methods (`IsInInflections` etc.) have value receivers — this is safe because `G` is read-only during the worker phase (written only in `init()` before any workers start).

- [x] Task: Write Tests - Add unit tests for the parsing and lookup logic of the new `SandhiRuleIndex`.
- [x] Task: Implement - Create a 2D map `SandhiRuleIndex` keyed by `runeA` and `runeB` during initialization in the `importer` or `data` package.
- [x] Task: Implement - Refactor all splitters (e.g., `split_2words.go`, `split_3words.go`, `split_lwff.go`) to look up rules via the O(k) index instead of iterating the entire `data.G.SandhiRules` slice.
- [x] Task: Verify - Run the deconstructor, record the execution time delta, and assert that the output file SHA256 hashes still match the baseline perfectly.
- [x] Task: Conductor - User Manual Verification 'Phase 2: O(k) Indexed Sandhi Rule Lookup' (Protocol in workflow.md)

### Phase 2 Implementation Notes (do not lose on context clear)
- ChA and ChB in sandhi_rules.tsv are confirmed always exactly 1 rune — index key is `rune`, not `string`.
- `BuildSandhiRuleIndex(rules []SandhiRules) map[rune]map[rune][]SandhiRules` added to `data/sandhi_rules.go`.
- `SandhiRuleIndex` field added to `GlobalData` in `data/globaldata.go`; populated in `importer/importer.go` after `makeSandhiRules()` and assigned to `data.G.SandhiRuleIndex` in `main.go`.
- All 7 splitters refactored: `split_2words.go`, `split_3words.go`, `split_lwff.go`, `split_lwfb.go`, `split_pīti.go`, `split_ādi.go`, `split_apicaevaiti.go`. In `split_ādi.go` and `split_apicaevaiti.go`, the `t.IsConsonant(sr.ChA[0])` guard moved to `t.IsConsonant(wordALastRune)` before the index lookup (equivalent, since the index key IS wordALastRune).
- Phase 2 verify run (WordLimit=500): matched% 87%, total 9.6s (Phase 1 baseline ~10.2s). Marginal at 500 words — full-dataset benefit will be proportional to sandhi rule count × word positions evaluated.
- **`data.L.WordLimit` is still `500` in `limits.go`. Must be reset to `0` before final commit.**

## Phase 3: Zero-Allocation Lookups (Optional)
- [x] Task: Write Tests - Create performance benchmarks validating the speedup of avoiding string allocations on `[]rune` lookups.
- [x] Task: Implement - Refactor the `IsInInflections`, `IsInInflectionNoFirst`, and `IsInInflectionNoLast` functions in `data/globaldata.go`. Replace the standard string-keyed maps with a structure that avoids `string([]rune)` allocations (e.g., a Rune Trie, or zero-allocation byte slice hacks if applicable to UTF-8 encoded Pāḷi).
- [x] Task: Verify - Run the deconstructor, record the final execution time delta, and assert that the output file SHA256 hashes match the baseline perfectly.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Zero-Allocation Lookups (Optional)' (Protocol in workflow.md)

### Phase 3 Implementation Notes (do not lose on context clear)
- `RuneTrie` implemented in `data/rune_trie.go`; micro-benchmark showed ~2x speedup vs `string([]rune)+map` in isolation (10k fixture, ~106ns vs ~210ns per 5 lookups, 0 allocs both).
- **Reverted from hot path:** full-run with `WordLimit=500` showed 15.9s (vs Phase 2 baseline 9.6s) — trie was slower due to pointer-chasing and cache misses at production inflection-set scale. Go compiler already optimizes `string([]rune)` map lookups to avoid allocation, so Phase 3 solved a non-problem.
- `data/rune_trie.go` and `data/rune_trie_test.go` retained for reference and correctness tests; trie is NOT wired into `GlobalData` or the splitter hot path.
- **`data.L.WordLimit` is still `500` in `limits.go`. Must be reset to `0` before final commit.**
