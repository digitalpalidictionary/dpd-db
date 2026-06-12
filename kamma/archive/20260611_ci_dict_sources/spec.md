# Spec: External dictionaries missing from CI-built mobile DB releases

## Overview

Users of the DPD Flutter app (v0.1.10, DB v0.4.20260531) report that Monier-Williams
shows no results. Diagnosis: **no CI-built mobile database has ever contained MW, CPD,
or BHS.** The release workflow checks out the `other-dictionaries` submodule but never
materializes the dictionary *source files* (which are gitignored), and
`mobile_exporter.py` silently skips missing sources, so three broken releases shipped
without any failure signal.

Evidence (CI log, run 26704672647 → release v0.4.20260531):

```
exporting CPD                      CPD source not found, skipping
exporting Monier Williams          MW source not found, skipping
exporting BHS                      BHS source not found, skipping
```

A same-day local build contains all three (mw: 194,083 / cpd: 29,734 / bhs: 17,836
entries; 207 MB zip vs the released 141 MB).

## Root cause chain

1. `exporter/mobile/mobile_exporter.py` reads sources from
   `resources/other-dictionaries/dictionaries/*/source/` (paths in `tools/paths.py`:
   `cpd_source_path`, `mw_source_json_path`, `bhs_source_path`).
2. The `other-dictionaries` repo gitignores all of `/dictionaries/*/source/`; only
   `*.tar.zst` archives are tracked (cpd, bhs, cone, etc. — **not mw**).
3. `.github/workflows/draft_release.yml` never runs
   `scripts/decompress_sources.py`, so even the tracked archives are never extracted.
4. MW has no tracked archive at all — `mw.json` is a *generated* artifact, built by
   `dictionaries/mw/mw_from_cologne.py`, which downloads `mwweb1.zip` (46 MB) from the
   Cologne server and writes `source/mw.json`.
5. The exporter treats every missing source as non-fatal (`pr.red(...not found,
   skipping)`) and exits 0, so the release succeeds.

## Validated facts (clean-clone dry run, 2026-06-11)

A `git clone` of other-dictionaries into /tmp (= exactly what CI sees) confirmed:

- `decompress_sources.py` works as-is: restores `cpd_clean.db` (29 MB), `bhs.xml`
  (8.5 MB), `cone_dict.json` (294 MB) from tracked archives.
- The full MW chain works end-to-end in a clean clone: Cologne download → unpack →
  `load_mw_data()` → `build_mw_entries()` → **194,084 entries**, `mw.json` 200 MB.
- **Bug 1:** Cologne's server blocks python-requests' default User-Agent (HEAD → 500
  via Varnish, GET → 403). A descriptive custom UA
  (`dpd-other-dictionaries-build/1.0`) gets 200. `download_fresh_source()` is
  therefore currently broken everywhere, including local machines — it just hasn't
  re-run since Cologne added the block.
- **Bug 2:** `download_fresh_source()` checks no status and validates no content — it
  wrote the empty error response straight over `mwweb1.zip`. With a tracked fallback
  zip this would *destroy the fallback with garbage*.
- **BHS fresh-fetch is NOT viable in this thread:** Cologne's current BHS XML editions
  (2013 `bhsxml.zip` and the actively-maintained 2020 edition, last-modified
  2026-06-05) both use different markup than the tracked `bhs.xml`. `bhs.py` parses
  `<div n="lb">` and `¦`, which exist only in the tracked edition. The 2020 edition
  uses `<lang>`, `<ls>`, `<span class=...>` — adopting it is a renderer-upgrade
  project, out of scope here.

## What it should do

**A. One prepare-sources entry point** — new `scripts/prepare_sources.py` in
`other-dictionaries`, usable locally and in CI:

1. Run `decompress_sources()` — restores CPD, BHS, Cone, etc. from tracked
   `.tar.zst` archives. BHS comes from here, period (no fresh download).
2. MW: fresh-fetch via hardened `download_fresh_source()` (see B), then build and
   write `source/mw.json` via a new `build_mw_json()` function refactored out of
   `mw_from_cologne.main()` (no GoldenDict/MDict export — not needed for mobile DB).

**B. Harden `download_fresh_source()`** in `dictionaries/mw/mw_helpers.py`:

- Send a descriptive custom User-Agent (Cologne blocks the python-requests default).
- `raise_for_status()` on both HEAD and GET.
- Download to a temp file, validate with `zipfile.is_zipfile()`, only then replace
  `mwweb1.zip`. Never overwrite a valid zip with a failed response.
- If Cologne is unreachable or returns invalid data **and** a valid local
  `mwweb1.zip` exists: warn loudly and fall back to it.
- Unpack the zip when `source/web/sqlite/` is missing, even if the zip is
  "up to date" (currently it only unpacks after a download).

**C. MW fallback = track the raw upstream zip** — commit `mwweb1.zip` (46 MB, under
GitHub's 100 MB limit) with a gitignore negation
(`!/dictionaries/mw/source/mwweb1.zip`). It then serves as both download cache (HEAD
size match → no download) and offline fallback. NOTE: pushing this is a one-time
~46 MB upload — coordinate with the user's data availability.

**D. Hard-fail in the mobile exporter** — in `mobile_exporter.py`, a missing CPD, MW,
or BHS source raises an error (message pointing to `prepare_sources.py`) instead of
skipping. Cone stays optional behind its existing `--cone` flag. Update
`tests/exporter/mobile/test_mobile_exporter.py`, which currently codifies the
silent-skip behavior (`test_skips_missing_cpd_source_...`).

**E. Workflow changes in dpd-db:**

1. In `draft_release.yml`, before "Export Mobile DB":

   ```yaml
   - name: Prepare dictionary sources
     working-directory: resources/other-dictionaries
     run: uv run python scripts/prepare_sources.py
   ```

   (`other-dictionaries` is its own uv project, `requires-python >=3.12`; first
   `uv run` resolves its lockfile — verified working in the clean-clone test.)

2. **New `mobile_release.yml` workflow** (workflow_dispatch): builds *only* the
   mobile DB and creates a draft release, so a fixed DB can ship without the full
   1.5 h all-formats pipeline. Mirrors `draft_release.yml`'s Setup and Build Database
   sections (checkout through "Test Dealbreakers"), then: Prepare dictionary sources
   → Export Mobile DB → set release date/tag (same `version_print.py` scheme) →
   draft release containing only `dpd-mobile-db.zip`. Skips: audio index, grammar
   dict export, GoldenDict/MDict/Kindle/Kobo/TPR/TXT/Anki/Apple exports, the macOS
   job, uposatha commit. Single job, direct `softprops/action-gh-release@v2` with
   `draft: true`. The app only sees *published* releases via the GitHub API, so the
   draft stays invisible until manually published.

## Assumptions & uncertainties

- A descriptive custom UA passes Cologne's filter today (verified
  `dpd-other-dictionaries-build/1.0` → 200); they appear to blocklist
  `python-requests` specifically. If they tighten later, the tracked-zip fallback
  covers it.
- MW upstream (`mwweb1.zip`) is actively updated (last-modified 2026-06-05) and its
  sqlite schema has been stable; a schema change would hard-fail the release loudly —
  intended behavior.
- The mobile-only workflow needs all DB build steps up through "Test Dealbreakers"
  because the mobile DB copies lookup, suttas, frequency, EBT counts, and family
  tables. Steps after that point in `draft_release.yml` are export-only and safe to
  skip. Verify table completeness on first dispatch run.
- `zstd` is preinstalled on `ubuntu-latest` runners.
- Disk: MW sources add ~500 MB; the runner had ~75 GB free at that workflow stage.
- `vendor/dpd_tools/` in other-dictionaries is synced from dpd-db (`scripts/sync.py`)
  — no new code goes there; MW changes live in `dictionaries/mw/`.
- Changes span two repos: the `other-dictionaries` submodule first (commit + push),
  then `dpd-db` (workflows, mobile_exporter, tests, submodule pointer bump). The user
  authorizes all commits explicitly.

## Constraints

- CI must never push refreshed source data back to the repo; refreshing tracked
  archives/zips stays a manual local task.
- Cologne fully down + no valid tracked fallback → release fails loudly. Intended.
- Preserve existing exporter output for all other tables — this thread touches only
  external-dictionary source preparation, failure behavior, and the new workflow.
- Follow other-dictionaries conventions: modern type hints, `pathlib.Path`, printer
  (`pr`) for output.
- No heavy downloads during local development/verification while the user's internet
  data is constrained — reuse the already-validated /tmp/od-citest clone artifacts.

## How we'll know it's done

1. other-dictionaries: `uv run pytest` passes, including new tests for the hardened
   `download_fresh_source()` (mocked requests; no live downloads).
2. dpd-db: `uv run pytest tests/exporter/mobile/` passes, including new hard-fail
   tests.
3. Clean-clone check: `prepare_sources.py` in /tmp/od-citest completes using the
   already-present mwweb1.zip (HEAD check only, no download) and yields
   `cpd_clean.db`, `bhs.xml`, `mw.json` (≥194k entries).
4. With sources missing and prepare step skipped, `mobile_exporter.py` exits non-zero
   with a clear message.
5. First `mobile_release.yml` dispatch run logs real entry counts (mw ≈194,084,
   cpd 29,734, bhs 17,836) and produces a draft release whose `dpd-mobile-db.zip`
   (~200 MB) has `entry_count > 0` for cpd/mw/bhs in `dict_meta`.
6. After the user publishes the draft, app users get MW results via the in-app
   database update — **no app-side change needed**.

## What's not included

- BHS upgrade to Cologne's 2020 edition (different markup; needs `bhs.py` renderer
  work) — future thread.
- Apte (also lacks a tracked archive, but is not in the mobile exporter).
- Including Cone in the mobile DB (stays behind `--cone`, off by default).
- App-side (Flutter) changes of any kind.
- Webapp / GoldenDict / MDict export pipelines (beyond the `build_mw_json()` refactor
  leaving `mw_from_cologne.py`'s full export intact).
- CI committing refreshed sources back to the repo.
