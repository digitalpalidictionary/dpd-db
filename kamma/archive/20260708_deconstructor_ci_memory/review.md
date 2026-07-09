# Review: Deconstructor CI Memory Fit

## Verdict: PASSED — mergeable, no blocking issues

Reviewed via two independent subagents (per user request), not `/kamma:3-review`:
an Opus code review of the committed branch and a CodeRabbit CLI review. Both
agree the streaming refactor preserves the golden output.

## Objective
Cut the Go deconstructor's peak RSS from ~24 GB (holds all 14.5M match candidates
in RAM + ~10M-entry TriedMap) to single-digit GB so it fits GitHub's 16 GB CI
runner, then regenerate it in CI and retire the manual premade-artifact upload —
without changing `deconstructor_output.json` (byte-identical gate).

## Result
- **Local full corpus:** peak RSS 3.41 GB (was 23.9 GB, ~7×), output byte-identical
  (20k MD5 `82a9e465`, full MD5 `77f9b2ae`), deterministic, race-clean.
- **CI full corpus** (run 29016342450, 16 GB runner): peak RSS ~5.3 GB flat,
  934,196 words → 847,307 matched, 14,494,461 match items, compute ~12.3 min,
  finish-word dupes 0 — memory fit PROVEN on the target runner.

## Files changed (branch vs main)
- `go_modules/deconstructor/data/matchdata.go` — streaming core; `SaveToDb`/`shouldDelete` removed
- `go_modules/deconstructor/main.go` — temp-dir lifecycle, no db write
- `go_modules/deconstructor/data/matchdata_test.go` — new unit tests
- `tools/configger.py` — `generate.deconstructor: yes` in github_release profile
- `scripts/build/deconstructor_output_add_to_db.py` — positive gate
- `scripts/bash/generate_components.py`, `justfile` — local build order (go run → add_to_db)
- `.github/workflows/draft_release.yml`, `mobile_release.yml` — Generate Deconstructor → Add to db
- `.github/workflows/deconstructor_ci_test.yml` — proof workflow

## Findings

### CodeRabbit (2) — both rejected
1. `selectTopEntries` `extraCounter` never advances — INTENTIONAL. Faithfully
   mirrors the original `SaveTopEntriesJson` rule (dead branch included); that is
   what makes the output byte-identical. Opus confirmed independently. "Fixing" it
   would change the dictionary output — the forbidden thing.
2. `test_pdf.yml` doesn't assert PDF outputs — out of scope (pre-existing
   test-workflow gap, unrelated to the deconstructor).

### Opus — no blocking
- SHOULD-FIX: temp dir orphaned on a mid-run panic (`main.go`). **FIXED** —
  `defer os.RemoveAll(tempDir)` after `MkdirTemp`; redundant success-path cleanup
  removed. gofmt/vet/build clean; generation untouched so golden preserved.
- NITs (accepted, not fixed — debug-artifact / defensive, no golden impact):
  manual-correction rows no longer in `matches.tsv` and its printed row count
  overstates by ~4k; `FinishWordDupes` is observability-only; `matches.tsv` now
  csv-quotes special chars; `os.Remove` errors best-effort.

## Equivalence argument (verified by Opus)
Each word is a unique map key → exactly one job → one worker; `w.Word` is never
reassigned (split_ika aliasing bug already fixed), so all of a word's candidates
live in one worker's buffer in one `deconstruct` call. Per-word sort+select over
that buffer equals the old global sort+select (`compareMatchItems` is a total
order). Manual corrections are disjoint from worker words (excluded from input),
overlaid first in `Merge`. `TopFive` is built from in-RAM `topDict`, never
round-tripped through the streamed files — so disk streaming cannot affect the
golden JSON.

## Test evidence
- `go test -race ./go_modules/deconstructor/...` pass (+5 new unit tests)
- `go vet ./go_modules/...`, gofmt clean
- 20k + full-corpus golden MD5 identical local; CI full run green (memory)
