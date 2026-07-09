# Plan: Deconstructor CI Memory Fit

## RESUME HERE (handoff 2026-07-09)
- **Branch:** `deconstructor-ci-memory`.
- **DONE + committed** (`18a3b3de`): determinism fix — split-text final tiebreak
  in `data/matchdata.go` `Summary()` comparator. Output now deterministic.
- **GOLDEN GATE:** 20k-sample `deconstructor_output.json` MD5 = `82a9e465aa18b5c94fa74e01957a2ea3`.
  Regenerate baseline by building the bench harness (below) and running
  `-words 20000`; the committed code reproduces this MD5. All Phase 2 work must
  keep this MD5 identical.
- **Bench harness** (untracked, on disk, throwaway — remove before finalize):
  `go_modules/deconstructor/cmd/bench/main.go`. Runs import + deconstruct on a
  deterministic sorted N-word sample + `SaveTopEntriesJson`. Build to scratchpad
  with `-o`, run `-words 20000` for the gate, `-words 0` for full corpus.
- **Baseline peak RSS ≈ 23 GB** (before); target: comfortably under 16 GB.
- **MANUAL CORRECTIONS (confirmed semantics):** `importer.makeMatchItems()` loads
  `manual_corrections.tsv` (~4,064 hand-verified splits) as `MatchItemList`,
  seeded into `M.MatchedItems` before compute. They have `ProcessCount = 0` so
  they sort FIRST and are **always first in the top-5 for their words** (they
  override deconstructor guesses). These words are excluded from the input
  (`MapDifference(allWords, manualCorrections)` in `MakeUnmatched`), so workers
  never process them. In the streaming refactor they must be **overlaid into
  `TopFive` at the merge/finalize step**, always leading each word's list.
- **NEXT — Phase 2 (streaming refactor):** rewrite accumulation core so RAM stays
  low. Key moves: (a) reset per-word state each `deconstruct(w)` — especially
  `TriedMap` (a top memory hog, holds ~10M tried strings across a worker's words);
  (b) stream all candidate rows to a per-worker file (keeps full `matches.tsv`
  for quality work; disk is not a constraint — 2.4 GB on a 14 GB runner);
  (c) inline per-word top-5 into a per-worker `topDict` (drops 14.5M items to
  ~851k); (d) merge worker topDicts + overlay manual corrections → `TopFive`;
  (e) `matches.tsv` = concat of per-worker files. Because the sort is now a total
  order, inline per-word top-5 == the old global selection — verify against
  `82a9e465`. Files: `data/matchdata.go`, `data/stats.go`, `main.go`, harness.
- **Then Phases 3–5** as written below (full-run RSS, test CI workflow, real
  integration). Phases 4–5 delegated to Sonnet subagents per user.


Read `spec.md` first. Binding gates: after Phase 1, `deconstructor_output.json`
MD5 must stay identical to the **deterministic** baseline established in Phase 1
(NOT the old non-deterministic main — see below); full-run peak RSS must be
comfortably under 16 GB; output deterministic; race-clean. Every measurement =
fresh process, peak RSS via `/usr/bin/time -v`. Work on branch
`deconstructor-ci-memory` (already created).

## Critical finding (Phase 0, verified)
The current `deconstructor_output.json` is **non-deterministic**: two runs of
identical current code differ on ~21.5% of words' top-5 (~4.5% keep genuinely
different splits). Root cause: `Summary()` sorts MatchItems by
(Word, ProcessCount, Weight, SplitRatio) with a non-total comparator, so
candidates tied on all four are left in non-stable-sort order, which varies
run-to-run with worker-completion order. The full match SET is deterministic;
only the top-5 *selection among ties* is not. Fix (Phase 1): add the split text
as a final tiebreak → total order → deterministic (verified 3× identical,
MD5 82a9e465 on the 20k sample). This changes the output vs the old premade
artifact ONLY in the previously-arbitrary tie positions, and becomes the stable
baseline the memory work is gated against.

## Architecture Decisions
- **Stream to disk, select on read-back** (not trim-in-RAM): keeps all
  candidates for quality work; RAM near-zero for match storage. Chosen by user.
- **Per-worker output files**, not one shared file: avoids write contention and
  guarantees each word's rows are contiguous (a word is processed by exactly one
  worker in one `deconstruct` call), which is what makes one-word-at-a-time
  read-back selection correct.
- **Single code path** — replaces accumulate-then-trim entirely; no CI flag.
  (Prior thread rejected two-path CI gating as unmaintainable.)
- **Reuse the existing top-5 rule** (`SaveTopEntriesJson` logic) verbatim in the
  read-back pass; do not redesign selection — only change *where* candidates live
  between production and selection (disk, not one big slice).
- **Correctness target is `deconstructor_output.json`**, not `matches.tsv`.
- **Test workflow downloads a prebuilt `dpd.db`** to isolate the generation
  stage rather than rebuilding the whole db.

## Phase 0 — baseline + harness  [DONE]
- [x] 0.1 Bench harness recreated (`go_modules/deconstructor/cmd/bench/`,
      scratchpad-only, removed before finalize).
- [x] 0.2 Discovered current output is non-deterministic (see Critical finding).
- [ ] 0.3 Record baseline full-run peak RSS with `/usr/bin/time -v` (expect
      ~23 GB) as the before-number.
      → verify: Max RSS captured to `baseline_rss.txt`.

## Phase 1 — make top-5 selection deterministic (IMMEDIATE)  [DONE]
- [x] 1.1 Add split-text final tiebreak to the `Summary()` `SortFunc`
      comparator in `data/matchdata.go` so the ranking is a total order.
      → verify: run the 20k sample 3×; `deconstructor_output.json` MD5 identical
      all three (was ~21.5% of words differing before). ✓ MD5 82a9e465.
- [ ] 1.2 Confirm the fix only reorders/re-selects among tied candidates, not
      the matched-word set: the set of words with output is unchanged vs a
      baseline run, and per-word splits are drawn from the same candidate pool.
      → verify: same word count in output; spot-check tie positions.
- [ ] 1.3 Capture the deterministic golden as the gate for all later phases:
      full-run `deconstructor_output.json` MD5 (and 20k sample MD5 82a9e465).
      → verify: two full runs identical.

## Phase 2 — streaming refactor (inline per-word top-5)  [DONE]
NOTE (drift): implemented the RESUME-HERE **inline per-word selection** (Variant
A), NOT the separate read-back pass the older sub-tasks described. Selection runs
on in-memory float64 candidates per word (never round-tripping sort keys through
the lossy tsv), so it is simpler and float-precision-safe. Decisive pre-work:
a throwaway full-corpus probe found **0 words produced by >1 worker** (847,307
distinct), confirming per-worker contiguity, so per-word flush == old global
selection. `FinishWordDupes` counter guards the assumption at runtime (stayed 0).
- [x] 2.1 Per-worker file writer via `NewWorkerFactory(dir)` (csv/tab), opened in
      `RunCollect`'s newState; temp dir `output/worker_tmp_*`.
      → verify: builds; run produces N worker files, cleaned up after. ✓
- [x] 2.2 `MakeMatch` streams each candidate row to the worker file AND buffers
      it in `wordBuf`; per-word maps (`MatchedMap`/`TriedMap`/`ProcessCount`)
      cleared each word via `ResetWord`; global `MatchedItems` slice dropped.
      → verify: 20k golden MD5 == `82a9e465` (all rows accounted). ✓
- [x] 2.3 `FinishWord` sorts `wordBuf`, groups by word, runs the verbatim top-5
      selection → per-worker `topDict`. `Merge` unions worker topDicts + overlays
      manual corrections → `TopFive`; Summary from running counters.
      → verify: 20k golden MD5 identical 2× (deterministic); dupes=0. ✓
- [x] 2.4 `matches.tsv` = header + concat of worker files; temp files removed;
      `SaveToDb`/`SaveTopEntriesJson` read `TopFive` (unchanged interface).
      → verify: `go vet ./go_modules/...` clean; no leftover temp dirs. ✓

## Phase 3 — full-run memory + determinism
- [x] 3.1 Full-corpus run under `/usr/bin/time -v`. **Peak RSS = 3.41 GB**
      (3,579,268 KB), down from **18.7 GB** baseline probe (~5.5×); compute
      4m52s; 14,494,453 match items; finish-word dupes = 0.
      → verify: Max RSS 3.41 GB, comfortably under 16 GB (single-digit target
      met). ✓
- [x] 3.2 Full-run golden: new full MD5 = `77f9b2ae01c16d6b7be2cd19ea76b631` ==
      old-code (18a3b3de) full MD5 `77f9b2ae01c16d6b7be2cd19ea76b631` — BYTE
      IDENTICAL. Old baseline peak RSS = **23.9 GB** (25,061,560 KB) vs new
      **3.41 GB** (~7×). Both 14,494,453 match items.
      → verify: MD5s match. ✓
- [x] 3.3 (Conditional) N/A — 3.1 RSS (3.41 GB) far under the ~12 GB threshold,
      no inflection-map compaction needed.
- [x] 3.4 `go test -race ./go_modules/deconstructor/...` and `go vet
      ./go_modules/...` clean; added `data/matchdata_test.go` (selectTopEntries
      min-PC/limit/dedup, compareMatchItems total order, FinishWord grouping).
      → verify: all tests pass under `-race`. ✓

## Phase 4 — test CI workflow (PROVE IT)
KEY FINDING: the deconstructor's input word lists (`shared_data/frequency/
*_wordlist.json`) are generated (gitignored), made by `initial_setup_run_once.py`
→ `go run go_modules/frequency/setup/*.go`, which runs early in the release
build. So a downloaded `dpd.db` alone is NOT enough — the workflow mirrors
draft_release's build prefix (per user: "just get the steps from draft release")
through inflections so all inputs exist, then runs the Go deconstructor.
- [x] 4.1 New workflow `.github/workflows/deconstructor_ci_test.yml`
      (`workflow_dispatch`): draft_release setup+build prefix (checkout submodules,
      python+uv+deps, Go, config, build db, initial setup [word lists], version,
      inflection templates+tables), then `go build -o` + `/usr/bin/time -v` the
      deconstructor, print Max RSS + wall time, stop. No export/upload.
      → verify: YAML valid ✓. Live dispatch pending (user runs it).
- [ ] 4.2 Confirm the run's reported peak RSS and wall time against local
      numbers (local full run: 3.41 GB, ~5 min compute).
      → verify: CI Max RSS < 16 GB with headroom. (awaiting live run)

## Phase 5 — integrate into real release
Config enabler: added `generate: {deconstructor: "yes"}` to the `github_release`
profile in `tools/configger.py` (the profile had no `generate` section, so the Go
binary's one gate `[generate] deconstructor` was never set on the runner).
- [x] 5.1 `draft_release.yml` + `mobile_release.yml`: removed "Unzip
      deconstructor_output" step; replaced `deconstructor_output_add_to_db.py`
      with `go run go_modules/deconstructor/main.go` at the same build position
      (inflections + word lists already present there). `deconstructor_exporter.py`
      unchanged. mobile's `use_last_release_db` variant untouched (skips decon).
      → verify: all 3 workflow YAMLs valid ✓; ruff/pyright clean on configger.py ✓.
- [~] 5.2 Premade path removed from the two named release workflows. NOT touched
      (out of scope, per user): `pdf_test.yml` (no Go setup; its unzip is
      vestigial — never runs add_to_db) and `submodules_update.yml`. The
      `resources/deconstructor_output` submodule + `deconstructor_output_add_to_db.py`
      script are left in place (retiring them is a separate call).
      → verify: no premade ref in draft_release/mobile_release ✓.
- [ ] 5.3 End-to-end: a release-workflow run regenerates the deconstructor in CI
      and downstream export proceeds; deconstructor column matches a baseline.
      → verify: workflow green through export. (awaiting live run — user tests)
      NOTE: Go `SaveToDb` does `DELETE FROM lookup` + full rewrite (vs the Python
      `sync_lookup_column`); it is the canonical original writer, but this is the
      main thing to watch in the live e2e.

## Phase 6 — finalize
- [ ] 6.1 Remove the scratchpad bench harness; `git status` shows only intended
      files.
- [ ] 6.2 Write results (before/after peak RSS, CI run link, golden-equivalence
      statement) into this thread; update `spec.md`/`plan.md` if reality drifted.

## Notes
- No task changes the real dictionary output; the golden gate is the proof.
- Phases 4 and 5 require actually dispatching GitHub workflows — expect to
  iterate on runner-specific setup (deps, db download) there.
