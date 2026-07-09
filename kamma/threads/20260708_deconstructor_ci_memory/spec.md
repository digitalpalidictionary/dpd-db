# Spec: Deconstructor CI Memory Fit — Stream to Disk + Test Workflow + Integration

## Overview

The Go deconstructor (`go_modules/deconstructor/`) peaks at **23.3 GB RSS** on a
full-corpus run (934k words → 14.5M match items held in RAM before writing).
GitHub's free `ubuntu-latest` runner for public repos (dpd-db is public) has
**16 GB**, and it OOMs *hard* — the prior thread `20260707_deconstructor_ci_serial_revert`
shows a 16 GB runner being killed VM-and-all by a memory spike. So the
deconstructor cannot regenerate in CI today; instead every release **unzips a
premade `deconstructor_output.json.tar.gz`** that a maintainer must regenerate
locally and upload by hand.

Goal: cut peak RSS to single-digit GB (comfortable headroom under 16 GB) so the
deconstructor can regenerate *in* CI, then prove it with a test workflow, then —
if the proof passes — wire regeneration into the real release and delete the
manual-upload step. Wall time (~8 min local; est. 20–30 min on a 4-core runner)
is acceptable.

## Related prior work
- `20260707_deconstructor_ci_serial_revert`: a 16 GB CI OOM, but in the *Python
  exporter* (`deconstructor_exporter.py`) parallel path, since reverted to
  serial. That export stage already fits CI. This thread targets the upstream
  *Go generation* stage, which currently never runs in CI. That thread also
  **rejected keeping two code paths behind a CI gate** ("two code paths to
  maintain") — reinforcing the single-path decision below.

## What it should do (approach: stream to disk, select top-5 on read-back)

The root cause is holding all 14.5M candidates in RAM to sort-and-trim at the
end. Chosen fix (user's call): **stream every candidate to disk as produced,
keep them all, and select the top-5 per word in a read-back pass.** This keeps
the full candidate set (valuable for ongoing quality work) while dropping RAM
to near-zero for match storage.

Why it is correct and low-RAM: every candidate for a word is produced within a
single worker's `deconstruct(w)` call, so a worker's output file has each word's
rows **contiguous**, and each word appears in exactly one worker's file.
Therefore the read-back selection groups a word's rows by simple contiguity and
holds only **one word's candidates** in RAM at a time.

1. **Stream match rows to per-worker files during compute.** `MakeMatch` writes
   a tab-separated row to the worker's buffered file instead of appending to an
   in-RAM slice. Per-worker files (not one shared file) avoid write contention
   and preserve per-word contiguity.
2. **Per-word dedup only.** `MakeMatch` currently dedups a (word, split) against
   `MatchedMap[word]`. Keep a small per-word dedup set that resets when the
   worker moves to the next word (a word's matches all occur in one
   `deconstruct` call), so no large map accumulates.
3. **Read-back selection pass builds the real output.** After compute, stream
   each worker file, group contiguous rows by word, sort each word's block by
   the existing keys (processCount, weight, splitRatio), apply the existing
   top-5 selection rule, and build `TopFive`/`deconstructor_output.json`, then
   `SaveToDb`. Compute Summary stats incrementally in the same pass.
4. **`matches.tsv` = concatenation of the streamed worker files** (all
   candidates preserved; row order is production order, not globally sorted —
   acceptable for a debug artifact). `stats.tsv` streamed per-word similarly.
5. **Single code path.** This *replaces* the current accumulate-then-trim flow —
   no CI-only mode, no flag. What runs locally is what runs in CI.
6. **Test CI workflow** that downloads a recent `dpd.db` release asset, runs the
   Go deconstructor against it, and stops — reporting wall time and peak RSS
   (`/usr/bin/time -v`). No release steps, no upload. Purpose: prove it fits.
7. **Final integration (gated on the proof passing).** Replace the release
   workflows' "unzip premade + `deconstructor_output_add_to_db.py`" steps with a
   direct `go run go_modules/deconstructor/main.go` (which writes to the db
   itself), leaving the existing `deconstructor_exporter.py` step unchanged.
   Retire the manual premade-artifact upload.

## Assumptions & uncertainties
- **Top-5 determinism (highest risk).** Current selection sorts all items by
  (word, processCount, weight, splitRatio) with non-stable `slices.SortFunc`,
  then applies a processCount-allowance rule (`SaveTopEntriesJson`). Per-word
  read-back selection must reproduce this exactly. Since the rule is per-word
  state and within-word ordering uses the same keys, per-word sort+select should
  equal the global sort+select — *unless* exact ties order differently. If the
  golden differs, switch that per-word sort to stable and preserve MakeMatch
  write order. The golden gate catches any discrepancy before it ships.
- **Peak RSS after streaming.** Match storage drops to near-zero; the remaining
  floor is the three inflection maps (~1–4 GB, fixed) plus per-worker buffers.
  Expected well under 16 GB. If a full run still exceeds ~12 GB, a conditional
  follow-up compacts the inflection maps (`map[string]string` →
  `map[string]struct{}`). Gated on measurement.
- The correctness target is `deconstructor_output.json` (→ `lookup.deconstructor`
  column), **not** `matches.tsv` (debug). Confirmed from `SaveToDb`.
- The test workflow assumes a downloadable `dpd.db` release asset exists (used by
  `mobile_release.yml` via `gh release download`). If not, it builds the db far
  enough to populate inflections first.
- Runner is 4 vCPU / 16 GB / 14 GB SSD for public repos — confirm in the run.
- Disk is not a constraint: `matches.tsv` (2.4 GB) + `dpd.db` (2.2 GB) + rest ≈
  7–8 GB < 14 GB.

## Constraints
- `deconstructor_output.json` MUST be byte-identical (MD5) to current output —
  20k sample and full run.
- Single code path (no CI-only branch).
- Output deterministic across repeated runs (same MD5).
- Race-clean (`go test -race`), and follow project Go rules (never `go build` a
  single main package; use `go vet ./...` / `-o` to scratchpad).
- No `.ini` edits by the agent.
- Temp/worker files cleaned up; nothing stray committed.

## How we'll know it's done
- `deconstructor_output.json` MD5 identical (baseline current-main == new) on a
  20k sample and a full run; identical across two repeated runs.
- Full-corpus peak RSS (`/usr/bin/time -v` Max RSS) comfortably under 16 GB.
- `go vet ./go_modules/...` clean; `go test -race ./go_modules/deconstructor/...`
  passes.
- Test workflow runs the deconstructor to completion on a GitHub runner and
  reports wall time + peak RSS under 16 GB.
- (Final phase) A release workflow regenerates the deconstructor in CI and the
  downstream export proceeds; the manual premade-artifact path is removed.

## What's not included
- Deconstructor *quality* work (false positives, unmatched mining) — separate.
- Compacting inflection maps unless the RSS measurement requires it (conditional).
- Changing the Python exporter (already serial-fitted for CI).
