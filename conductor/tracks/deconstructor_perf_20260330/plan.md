# Implementation Plan: Deconstructor Performance Optimization

## Phase 1: Worker Pool, Lock Mitigation, and Baseline
- [~] Task: Create a baseline test script to measure current overall execution time and compute SHA256 hashes of the generated output files (matches, unmatched, JSON, stats).
- [ ] Task: Write Tests - Add basic unit tests for the worker pool logic, asserting proper channel handling and worker termination.
- [ ] Task: Implement - Refactor `go_modules/deconstructor/main.go` to use a bounded worker pool (using channels and `runtime.NumCPU()`) instead of launching an unbounded `go deconstruct(w)` for every word.
- [ ] Task: Implement - Explicitly address the global mutex (`Mu`) contention in `MatchData` (e.g., implement sharded mutexes, use `sync.Map`, or aggregate matches locally per worker).
- [ ] Task: Implement - Evaluate importer loading time; parallelize data loading in `importer.go` if the time is measurable and significant.
- [ ] Task: Verify - Run the deconstructor, record the new execution time, and assert that the output file SHA256 hashes match the baseline perfectly.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Worker Pool, Lock Mitigation, and Baseline' (Protocol in workflow.md)

## Phase 2: O(k) Indexed Sandhi Rule Lookup
- [ ] Task: Write Tests - Add unit tests for the parsing and lookup logic of the new `SandhiRuleIndex`.
- [ ] Task: Implement - Create a 2D map `SandhiRuleIndex` keyed by `runeA` and `runeB` during initialization in the `importer` or `data` package.
- [ ] Task: Implement - Refactor all splitters (e.g., `split_2words.go`, `split_3words.go`, `split_lwff.go`) to look up rules via the O(k) index instead of iterating the entire `data.G.SandhiRules` slice.
- [ ] Task: Verify - Run the deconstructor, record the execution time delta, and assert that the output file SHA256 hashes still match the baseline perfectly.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: O(k) Indexed Sandhi Rule Lookup' (Protocol in workflow.md)

## Phase 3: Zero-Allocation Lookups (Optional)
- [ ] Task: Write Tests - Create performance benchmarks validating the speedup of avoiding string allocations on `[]rune` lookups.
- [ ] Task: Implement - Refactor the `IsInInflections`, `IsInInflectionNoFirst`, and `IsInInflectionNoLast` functions in `data/globaldata.go`. Replace the standard string-keyed maps with a structure that avoids `string([]rune)` allocations (e.g., a Rune Trie, or zero-allocation byte slice hacks if applicable to UTF-8 encoded Pāḷi).
- [ ] Task: Verify - Run the deconstructor, record the final execution time delta, and assert that the output file SHA256 hashes match the baseline perfectly.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Zero-Allocation Lookups (Optional)' (Protocol in workflow.md)
