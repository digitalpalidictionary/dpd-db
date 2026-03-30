# Specification: Deconstructor Performance Optimization

## Overview
The `go_modules/deconstructor` program has several severe performance bottlenecks preventing it from running efficiently. It currently creates unbounded goroutines causing scheduler thrashing, experiences extreme lock contention on a global mutex, redundantly iterates over all sandhi rules, and unnecessarily allocates strings from rune slices millions of times. 

The objective of this track is to implement a targeted set of performance optimizations to drastically reduce execution time while preserving exact output fidelity, verified through automated hash comparison.

## Functional Requirements
1. **Worker Pool & Lock Mitigation:** Replace the unbounded `go deconstruct(w)` loop in `main.go` with a bounded worker pool pattern using channels. Explicitly address global mutex contention (e.g., via sharded mutexes or `sync.Map` for `MatchedMap` and `TriedMap`).
2. **O(k) Indexed Sandhi Rule Lookup:** Parse `data.G.SandhiRules` at initialization into an indexed map (e.g., `map[rune]map[rune][]SandhiRule`) and refactor splitters to look up matching rules in O(k) time (where k is the typical 1-5 matching rules) instead of iterating the entire list.
3. **Zero-Allocation Inflection Lookups (Phase 3):** Refactor the `IsInInflections`, `IsInInflectionNoFirst`, and `IsInInflectionNoLast` lookup functions to eliminate the expensive `string([]rune)` memory allocations in the hot path.
4. **Automated Verification:** Implement SHA256 hashing of baseline outputs to automatically verify output fidelity after every phase. Explicitly measure and report execution timing before and after each phase.

## Non-Functional Requirements
- **Fidelity:** The exact same matches and splits must be produced. The output TSV and JSON files must be identical to historical runs (verified via SHA256 hash).
- **Performance:** Execution time should be significantly reduced (targeting a 10x-20x speedup), with timing clearly logged.
- **Concurrency:** Memory footprint and thread contention should be minimized by relying on a stable worker pool and reduced locking.

## Acceptance Criteria
- [ ] Deconstructor compiles successfully after modifications.
- [ ] Baseline outputs are hashed, and post-phase outputs match the baseline SHA256 hashes perfectly.
- [ ] Concurrency is bounded; no more than `runtime.NumCPU()` goroutines process words simultaneously.
- [ ] Global mutex contention is mitigated.
- [ ] Sandhi rules are indexed and looked up in O(k) time.
- [ ] Execution time per phase is explicitly recorded and printed to the summary.

## Out of Scope
- Modifying the underlying logic or grammatical rules of the splits themselves.
- Adding new sandhi rules or new morphological logic.
