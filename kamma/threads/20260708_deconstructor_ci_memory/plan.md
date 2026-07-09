# Plan: Deconstructor CI Memory Fit

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

## Phase 2 — stream match rows to per-worker files
- [ ] 1.1 Give each worker a buffered writer to its own file (in output/temp
      dir). Thread it through the per-worker accumulator (`MatchData` gets a
      writer; `RunCollect`'s `newState` opens the file).
      → verify: builds; a 5k-word run produces N worker files.
- [ ] 1.2 `MakeMatch` writes a tab-separated row (same columns as `matches.tsv`)
      to the worker's writer instead of appending to `MatchedItems`. Keep a
      small per-word dedup set that resets on new word; drop the global
      `MatchedItems`/`MatchedMap` accumulation.
      → verify: total streamed rows across worker files == baseline match-item
      count for the same sample (no rows lost or duplicated).
- [ ] 1.3 Remove the now-dead `Merge` concatenation of `MatchedItems` (the
      merge-doubling source). Workers own their files; nothing to concat in RAM.
      → verify: `go vet` clean; no references to removed fields; `-race` on a
      small run is clean.

## Phase 2 — read-back top-5 selection + outputs (GOLDEN GATE)
- [ ] 2.1 Read-back pass: for each worker file, stream rows, group contiguous by
      word, sort each word's block by (processCount, weight, splitRatio), apply
      the existing top-5 selection rule → build `TopFive`. Hold only one word's
      rows at a time. Compute Summary stats incrementally here.
      → verify: `TopFive` for the 20k sample yields `deconstructor_output.json`
      MD5 == `golden_output_20k`. STOP and diagnose if it differs (check tie
      ordering; use stable per-word sort if needed).
- [ ] 2.2 `matches.tsv` = header + concatenation of worker files (all
      candidates). `stats.tsv` from streamed per-word stats. Wire `SaveToDb`
      to read the `TopFive` built in 2.1 (unchanged interface).
      → verify: `matches.tsv` row count == baseline; `SaveToDb` path unchanged
      (dry check, no live-db write in sample mode).
- [ ] 2.3 Clean up worker temp files after the read-back pass.
      → verify: after a run, only the intended outputs remain in output/.

## Phase 3 — full-run memory + determinism
- [ ] 3.1 Full-corpus run (against a scratchpad copy of `dpd.db`) under
      `/usr/bin/time -v`. Record peak RSS.
      → verify: Max RSS comfortably under 16 GB (target single-digit GB); if
      over ~12 GB, do the conditional inflection-map compaction sub-task below.
- [ ] 3.2 Full-run golden: `deconstructor_output.json` MD5 identical to a
      baseline full run; identical across two repeated full runs.
      → verify: MD5s match.
- [ ] 3.3 (Conditional) If 3.1 over ~12 GB: switch inflection maps to
      `map[string]struct{}`; re-measure.
      → verify: RSS drops; golden still identical.
- [ ] 3.4 `go test -race ./go_modules/deconstructor/...` and `go vet
      ./go_modules/...` clean; add/adjust unit tests for the read-back selection
      (per-word top-5 on a synthetic block) and the streaming writer.
      → verify: tests pass under `-race`.

## Phase 4 — test CI workflow (PROVE IT)
- [ ] 4.1 New workflow `.github/workflows/deconstructor_ci_test.yml`
      (`workflow_dispatch`): checkout, setup Go + uv + deps, `gh release
      download` a recent `dpd.db`, set config to regenerate, run
      `/usr/bin/time -v go run go_modules/deconstructor/main.go`, print wall time
      + Max RSS, then stop. No export, no upload.
      → verify: workflow runs on the runner, deconstructor completes, logged Max
      RSS is under 16 GB. (Run via `gh workflow run` / `workflow_dispatch`.)
- [ ] 4.2 Confirm the run's reported peak RSS and wall time against local
      numbers; note any runner-vs-local gap.
      → verify: CI Max RSS < 16 GB with headroom; wall time within estimate.

## Phase 5 — integrate into real release (GATED on Phase 4 passing)
- [ ] 5.1 In `draft_release.yml` (and `mobile_release.yml`): replace the "Unzip
      deconstructor_output" + `deconstructor_output_add_to_db.py` steps with a
      `go run go_modules/deconstructor/main.go` step at the same point in the
      build order (after inflections exist in the db). Keep the existing
      `deconstructor_exporter.py` step.
      → verify: workflow YAML valid; step ordering preserves db-state
      prerequisites (inflections populated before the run).
- [ ] 5.2 Retire the manual premade-artifact path (the tarball unzip and its
      generation/upload docs/scripts) once regeneration is in place.
      → verify: no remaining reference to `deconstructor_output.json.tar.gz` in
      the active release path.
- [ ] 5.3 End-to-end: a release-workflow run regenerates the deconstructor in CI
      and the downstream export proceeds; output matches the premade baseline.
      → verify: workflow green through the export stage; deconstructor column in
      the produced db matches a baseline build.

## Phase 6 — finalize
- [ ] 6.1 Remove the scratchpad bench harness; `git status` shows only intended
      files.
- [ ] 6.2 Write results (before/after peak RSS, CI run link, golden-equivalence
      statement) into this thread; update `spec.md`/`plan.md` if reality drifted.

## Notes
- No task changes the real dictionary output; the golden gate is the proof.
- Phases 4 and 5 require actually dispatching GitHub workflows — expect to
  iterate on runner-specific setup (deps, db download) there.
