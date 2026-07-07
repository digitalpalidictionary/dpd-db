# Plan: Study go_modules/frequency for optimization (#157)

## Phase 1 — Baseline & harness

- [x] 1. Build sandbox (symlinked `shared_data`, `go_modules`;
  throwaway copy of `dpd.db`) and record full-run baseline
  of `go run go_modules/frequency/main.go`: wall time + peak RSS.
  → verified: wall 3:49, user CPU 2797s, peak RSS 6.65GB; db copy's
  freq_html sums byte-match the live db (685,553,525).
- [x] 2. Write `go_modules/frequency/study_test.go` benchmark harness
  (temporary study artifact). → compiles, runs from sandbox.

## Phase 2 — Prove/kill hypotheses

- [x] 3. H1 freqFinder: PROVEN. 12.5ms → 0.159ms per headword (79×).
  Aggregation identity verified for every word-section pair in all
  4 corpora + 2000-headword end-to-end sample identical.
  BONUS FINDING: SYA file map ∩ freq map = ∅ — all SYA freqs are 0
  in production; stale `sya_file_freq.json` (old `Canonical/` names),
  current resources match the file map; fix = re-run SYA setup.
- [x] 4. H2 template: PROVEN (modest). Clone+clean 381µs → shared
  pre-minified 277µs (1.4×), byte-identical HTML for 2000 samples.
- [x] 5. H3 JSON load: PROVEN (modest). Valid+Unmarshal 1.64s vs
  Unmarshal-only 1.35s on 71MB cst file (~18% of load stage).
- [x] 6. H4 db write: PROVEN. delete+CreateInBatches 57.4s vs prepared
  UPDATE 4.2s (13.7×). Full-row load 3.3s/+1.6GB heap vs
  selected-column load 0.6s/+~40MB.
- [x] 6b. (added) End-to-end prototype with all fixes combined:
  15.9s wall / 2.4GB RSS vs baseline 229s / 6.65GB; output md5 over
  all 89,144 (id, freq_html, freq_data) rows identical to live db.
  Also proves shared template safe under 44 concurrent workers.
- [x] 7. H5 memory: PROVEN. Heap 511MB (per-file maps) → 241MB
  (section maps only); process peak RSS 6.65GB is dominated by
  full-row load + stashes, addressed by task 6's column select.

## Phase 3 — Report

- [x] 8. Findings report written to `findings.md` (all 5 hypotheses
  proven, none killed; SYA data bug documented); presented for
  discussion. User approved implementing everything.

## Phase 4 — Implementation (user-approved)

- [x] 9. Rewrote `main.go`: corpus struct, section maps, column-select
  load, shared minified template, prepared UPDATE, unified path joins.
  `go build` + `go vet` clean. (Deviation: `study_test.go` was deleted
  at this step rather than at task 13 — its job was done for the
  research phase; a fresh temporary harness was written per task
  for the remaining equivalence checks.)
- [x] 10. Simplified `gradient.go` to a `bucket()` loop, exact old
  quirky semantics preserved (steps not offset by min). Brute-forced
  1,548,946 (min,max,value) combos + large-magnitude spot checks in a
  temporary `gradient_equiv_test.go` (deleted after passing) — zero
  mismatches.
- [x] 11. `tools/json.go`: dropped `json.Valid` pre-parse from all 5
  `ReadJson*` helpers; `Unmarshal`'s own error now drives the panic
  (same panic-on-invalid behavior). Also fixed pre-existing
  `interface{}`→`any` lint on `JsonMarshall` (file was touched, so
  owned per project convention).
- [x] 12. `setup/main.go`: added optional corpus arg
  (`go run ./go_modules/frequency/setup sya` runs one corpus; no arg
  runs all four, unchanged default). Removed dead `writeFileList` in
  `2SC.go` (and now-unused `os`/`slices` imports).
- [x] 13. Deleted the 3 stale `shared_data/frequency/*(copy).json`
  files (confirmed untracked in git beforehand). `study_test.go` and
  `gradient_equiv_test.go` both deleted (temporary study artifacts).
- [x] 14. Verified: `go build ./go_modules/...` + `go vet` clean.
  Fresh throwaway copy of live `dpd.db`, ran the rewritten binary:
  **15.9s wall / 2.73GB peak RSS** (baseline was 3m49s / 6.65GB).
  md5 of `(id, freq_html, freq_data)` over all 89,144 rows —
  **identical** to the live db. Sandbox cleaned up afterward.

## Status: implementation complete, verified, not yet committed

Remaining before this thread closes: user decision on committing, and
whether/when to run `go run ./go_modules/frequency/setup sya` to fix
the live SYA data (a separate, deliberate step — not part of this
verification, since it changes real output values).
