# Implementation Plan: Deconstructor Performance Optimization

## Phase 1: Worker Pool, Lock Mitigation, and Baseline
- [x] Task: Create a baseline test script to measure current overall execution time and compute SHA256 hashes of the generated output files (matches, unmatched, JSON, stats).
- [x] Task: Write Tests - Add basic unit tests for the worker pool logic, asserting proper channel handling and worker termination.
- [x] Task: Implement - Refactor `go_modules/deconstructor/main.go` to use a bounded worker pool (using channels and `runtime.NumCPU()`) instead of launching an unbounded `go deconstruct(w)` for every word.
- [x] Task: Implement - Explicitly address the global mutex (`Mu`) contention in `MatchData` (e.g., implement sharded mutexes, use `sync.Map`, or aggregate matches locally per worker).
- [x] Task: Implement - Evaluate importer loading time; parallelize data loading in `importer.go` if the time is measurable and significant.
- [x] Task: Verify - Run the deconstructor, record the new execution time, and assert that the output file SHA256 hashes match the baseline perfectly.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Worker Pool, Lock Mitigation, and Baseline' (Protocol in workflow.md)

### Phase 1 Implementation Notes
- `HasNoMatches`, `matchCount`, `ProcessCounter` changed from value receivers `(m MatchData)` to pointer receivers `(m *MatchData)` — value receivers caused an unsynchronized full-struct copy before the mutex was acquired, causing data races detected by `-race`.
- `BlockedTries` and `MaxedOut` in `data/matchdata.go` changed from bare `int` to `sync/atomic.Int64`; `split_recursive.go` updated to use `.Add(1)`. This was a pre-existing data race.
- Worker count settled on `runtime.NumCPU() * 2` (benchmarked 1x/4x/8x on 22-core machine; marginal differences, 2x chosen).
- Worker pool extracted to `go_modules/deconstructor/workerpool/` sub-package (generic `Run[T any]`) rather than inlined in `main.go` — needed to avoid `package main` `init()` side-effects preventing unit tests.

## Phase 2: O(k) Indexed Sandhi Rule Lookup

- [x] Task: Write Tests - Add unit tests for the parsing and lookup logic of the new `SandhiRuleIndex`.
- [x] Task: Implement - Create a 2D map `SandhiRuleIndex` keyed by `runeA` and `runeB` during initialization in the `importer` or `data` package.
- [x] Task: Implement - Refactor all splitters (e.g., `split_2words.go`, `split_3words.go`, `split_lwff.go`) to look up rules via the O(k) index instead of iterating the entire `data.G.SandhiRules` slice.
- [x] Task: Verify - Run the deconstructor, record the execution time delta, and assert that the output file SHA256 hashes still match the baseline perfectly.
- [x] Task: Conductor - User Manual Verification 'Phase 2: O(k) Indexed Sandhi Rule Lookup' (Protocol in workflow.md)

### Phase 2 Implementation Notes
- ChA and ChB in sandhi_rules.tsv are confirmed always exactly 1 rune — index key is `rune`, not `string`.
- `BuildSandhiRuleIndex(rules []SandhiRules) map[rune]map[rune][]SandhiRules` added to `data/sandhi_rules.go`.
- `SandhiRuleIndex` field added to `GlobalData` in `data/globaldata.go`; populated in `importer/importer.go` after `makeSandhiRules()` and assigned to `data.G.SandhiRuleIndex` in `main.go`.
- All 7 splitters refactored. In `split_ādi.go` and `split_apicaevaiti.go`, the `t.IsConsonant(sr.ChA[0])` guard moved to `t.IsConsonant(wordALastRune)` before the index lookup.

## Phase 3: Zero-Allocation Lookups (Optional)
- [x] Task: Write Tests - Create performance benchmarks validating the speedup of avoiding string allocations on `[]rune` lookups.
- [x] Task: Implement - Refactor the `IsInInflections`, `IsInInflectionNoFirst`, and `IsInInflectionNoLast` functions in `data/globaldata.go`. Replace the standard string-keyed maps with a structure that avoids `string([]rune)` allocations (e.g., a Rune Trie, or zero-allocation byte slice hacks if applicable to UTF-8 encoded Pāḷi).
- [x] Task: Verify - Run the deconstructor, record the final execution time delta, and assert that the output file SHA256 hashes match the baseline perfectly.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Zero-Allocation Lookups (Optional)' (Protocol in workflow.md)

### Phase 3 Implementation Notes
- `RuneTrie` implemented in `data/rune_trie.go`; micro-benchmark showed ~2x speedup vs `string([]rune)+map` in isolation.
- **Reverted from hot path:** full-run showed trie was slower due to pointer-chasing and cache misses at production scale. Go compiler already optimizes `string([]rune)` map lookups to avoid allocation, so Phase 3 solved a non-problem.
