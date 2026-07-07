## Thread
- **ID:** 20260707_frequency_go_study
- **Objective:** Study and (on approval) implement speed/memory/readability
  optimizations for `go_modules/frequency/`, proving every claim with
  benchmarks and output-equivalence checks, referencing #157.

## Files Changed
- `go_modules/frequency/main.go` — corpus struct replacing 8 globals + init();
  section-aggregated freq maps (79x fewer lookups); column-select DB load;
  shared pre-minified template (no per-row Clone/CleanWhiteSpace); prepared
  `UPDATE` of the two freq columns instead of DELETE + full-row reinsert.
- `go_modules/frequency/gradient/gradient.go` — simplified 10-branch
  if/else + 11-field struct to a `bucket()` loop; exact old semantics
  preserved, including the "steps not offset by min" quirk.
- `go_modules/frequency/setup/main.go` — added optional corpus arg
  (`go run ./go_modules/frequency/setup sya`); no-arg path unchanged
  (runs all four in original order).
- `go_modules/frequency/setup/2SC.go` — removed dead `writeFileList` and
  its now-unused `os`/`slices` imports.
- `go_modules/tools/json.go` — dropped the `json.Valid` pre-parse from
  all 6 `ReadJson*` helpers (panic-on-invalid now driven by `Unmarshal`'s
  own error); fixed pre-existing `interface{}`→`any` lint on `JsonMarshall`
  since the file was touched.
- Deleted (untracked, gitignored data): 3 stale
  `shared_data/frequency/*(copy).json` fossils; regenerated all four
  corpora's frequency JSONs via the new `setup` arg, fixing a live data
  bug (see Findings).
- Deleted (temporary study artifacts, not part of the commit):
  `go_modules/frequency/study_test.go`, a transient
  `gradient_equiv_test.go` used only to brute-force-verify `bucket()`.

## Findings

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `go_modules/tools/html.go:6` (`CleanWhiteSpace`) | Now unused anywhere in `go_modules/` (repo-wide grep, confirmed by 2 independent reviewers) — orphaned by the template-minification rewrite. | `go build`/`go vet` won't flag it since it's exported; it will silently rot otherwise. | Delete it, or leave a one-line comment if intentionally kept as a general utility. Deferred — not blocking. |
| 2 | minor | `go_modules/dpdDb/db.go:44` (`GetDpdHeadword`) | Was `main.go`'s only caller before the column-select rewrite; no other callers found repo-wide. | Same rot risk as #1; low priority since it's a small reusable exported helper. | Leave as-is; flag for a future cross-package dead-code pass, not this thread. |
| 3 | nit | `go_modules/frequency/main.go:27-30, 66-72, 166-169` (`corpus` struct + `loadCorpora`) | `corpus.name`/`fileMapPath`/`freqMapPath` fields are populated but never read; `makeFreqTable` indexes `corpora[0..3]` positionally, relying on `loadCorpora()`'s literal slice order matching `templateData`'s field order — a future reorder would silently swap corpora with no compiler error. | Positional coupling is more fragile than the old named-globals style; the unused `name` field looks like a half-wired name-based lookup. | Recommend a named-field struct (`cst,bjt,sya,sc *corpus`) or `map[string]*corpus` in a follow-up; not blocking this thread. |
| 4 | nit | `kamma/threads/20260707_frequency_go_study/plan.md` task 11 | Plan text says "5 `ReadJson*` helpers"; the actual diff touches 6 (`ReadJsonSliceString`, `ReadJsonMapStringString`, `ReadJsonMapStringInt`, `ReadJsonMapStringMapStringInt`, `ReadJsonBjt`, `ReadJsonSliceMapStringSliceString`). Code is correct and complete — just a wording slip. | Doc accuracy only. | Corrected below in this review; not worth re-editing plan.md. |
| 5 | nit | `go_modules/tools/json.go` behavior | Old code called `json.Valid` (syntax-only check) then `Unmarshal` *without checking its error* — so a syntactically-valid-but-type-mismatched JSON file previously failed silently (partial/zero-value population). New code panics in that case via `Unmarshal`'s own error. This is a behavior *tightening* (arguably a latent-bug fix), not a strict no-op. | Worth knowing before merge in case any known frequency-map JSON has a type mismatch that was silently tolerated before — none found in this repo's actual data. | No action needed; called out for visibility. |
| — | housekeeping | repo root | `go build ./go_modules/frequency/` and `.../setup/` (run without `-o` during ad hoc verification) left two stray untracked binaries (`./frequency` 11MB, `./setup` 3.2MB) at repo root; `gofmt -l` also flagged a stray trailing blank line in `2SC.go` after the `writeFileList` deletion. | A careless `git add -A` would have committed multi-MB binaries. | **Fixed during review**: both binaries deleted, `gofmt -w` applied to `2SC.go` — confirmed clean (`gofmt -l` empty, `git status` clean of stray files). |
| 6 | rejected | `go_modules/frequency/main.go:260` (`tx.Prepare` in `updateDb`) | CodeRabbit CLI flagged the `*sql.Stmt` from `tx.Prepare` as never explicitly closed, calling it a potential resource leak. | **Rejected after verification**: statements prepared on a `*sql.Tx` are tracked internally and auto-closed by `Tx.Commit()`/`Tx.Rollback()` (confirmed against Go 1.22's `database/sql` source, `closePrepared()` called from both paths). The existing `defer tx.Rollback()` + explicit `tx.Commit()` already guarantees this; no leak exists. | No fix applied — false positive. |

No blocking or major findings from any of the three independent passes: a general-purpose model review, a dedicated Fable-model review, and a CodeRabbit CLI review (`coderabbit review --agent`, both default and `--base main --type uncommitted` runs — 1 combined finding, verified and rejected above).

## Fixes Applied
- Deleted stray root-level binaries `frequency` and `setup` (build artifacts from ad hoc `go build` verification, not gitignored, not meant to be committed).
- Ran `gofmt -w` on `go_modules/frequency/setup/2SC.go` to remove a stray blank line left by the `writeFingList` deletion.
- No blocking/major code fixes were needed — both independent reviews returned PASSED with only minor/nit findings, none of which required a code change to unblock finalize.

## Test Evidence
- `go build ./go_modules/...` → clean (verified independently by both reviewers and by me).
- `go vet ./go_modules/...` → clean (same).
- `gofmt -l` on all 5 changed files → clean after the `2SC.go` fix.
- Brute-force equivalence check of `gradient.go`'s new `bucket()` vs the old `stepsStruct` branching over 1,548,946 (min,max,value) combinations + large-magnitude spot checks → zero mismatches (run during implementation, artifact deleted after passing per spec).
- End-to-end acceptance run: rewritten `main.go` against a fresh throwaway copy of the live `dpd.db` in a sandbox — **15.9s wall / 2.73GB peak RSS** vs baseline **3m49s / 6.65GB**; md5 of `(id, freq_html, freq_data)` across all 89,144 rows **identical** to the live db.
- SYA data bug fix verified: `go run ./go_modules/frequency/setup sya` (and the other 3 corpora) regenerated; file-map ∩ freq-map intersection went from 0/115 to 115/115 for SYA.
- CodeRabbit CLI review (`coderabbit review --agent`, both default and `--base main --type uncommitted`): completed, 1 combined finding across both runs, verified against Go's `database/sql` semantics and rejected as a false positive (see Findings #6).

## Verdict
PASSED
- Review date: 2026-07-07
- Reviewer: three independent passes — a general-purpose model review, a dedicated Fable-model review (run explicitly per user request), and a CodeRabbit CLI review — plus inline verification of every finding raised by any of them.
