# Plan: External dictionaries missing from CI-built mobile DB releases

Spec: `kamma/threads/20260611_ci_dict_sources/spec.md` — read it first; it contains
the validated facts (Cologne UA block, BHS edition mismatch, clean-clone test
results) this plan depends on.

## Architecture Decisions

- **Preparation is a separate explicit step, not exporter self-healing.**
  `mobile_exporter.py` stays a pure reader and hard-fails on missing sources;
  `scripts/prepare_sources.py` (other-dictionaries) is the single entry point that
  materializes them. One place to debug, identical behavior locally and in CI.
- **MW fallback = the raw upstream `mwweb1.zip` tracked in git** (46 MB), not a
  generated artifact. It doubles as download cache (HEAD size match → skip download)
  and offline fallback. Generated `mw.json` stays untracked.
- **BHS comes only from the tracked `bhs.tar.zst`.** Fresh-fetch was tested and
  rejected: Cologne's current XML editions use markup `bhs.py` cannot parse
  (spec, "Validated facts"). Upgrade is a future thread.
- **New code goes in `dictionaries/mw/` and `scripts/`**, never `vendor/dpd_tools/`
  (synced from dpd-db by `scripts/sync.py`, would be overwritten).
- **`mobile_release.yml` is a copy-and-trim of `draft_release.yml`**, not a reusable
  composite action — two workflows, plain steps, easy to diff. Build steps kept:
  checkout through "Test Dealbreakers" (the mobile DB copies lookup/suttas/
  frequency/EBT/family tables, all populated in that range). Everything after is
  export-only and dropped, except the new prepare step + mobile export.
- **Commit discipline:** other-dictionaries (submodule) commits/pushes first, then
  dpd-db (including submodule pointer bump). Nothing is committed without the user's
  explicit go-ahead. The mwweb1.zip push is a one-time ~46 MB upload — coordinate
  with the user's internet data availability (currently constrained; no heavy
  downloads/uploads without asking).

## Phase 1 — other-dictionaries submodule

Repo: `resources/other-dictionaries/` (own git repo, own uv project).

- [x] Task 1.1: Harden `download_fresh_source()` in `dictionaries/mw/mw_helpers.py`
  - Custom User-Agent constant (e.g. `dpd-other-dictionaries-build/1.0`) on HEAD and
    GET — Cologne 403/500-blocks the python-requests default
  - `raise_for_status()` after both requests
  - Download to a temp path; accept only if `zipfile.is_zipfile()` passes; then
    atomically replace `mwweb1.zip`. Never clobber a valid existing zip
  - On any download failure with a valid local `mwweb1.zip` present: `pr.red(...)`
    warning, use the local zip (fallback path)
  - Unpack when `source/web/sqlite/` is missing even if the zip is up to date
  - Add unit tests with mocked `requests` (success, 403, empty body, server down +
    fallback, up-to-date-but-not-unpacked). No live network in tests
  - → verify: `cd resources/other-dictionaries && uv run pytest` — all pass, new
    cases covered

- [x] Task 1.2: Extract `build_mw_json()` in `dictionaries/mw/mw_from_cologne.py`
  - Move the download → `load_mw_data()` → `build_mw_entries()` → write
    `source/mw.json` sequence into `build_mw_json(pth) -> list[DictEntry]`;
    `main()` calls it then continues with GoldenDict/MDict export unchanged
  - → verify: `uv run pytest` still passes; `python -c "from dictionaries.mw.
    mw_from_cologne import build_mw_json"` imports cleanly

- [x] Task 1.3: Create `scripts/prepare_sources.py`
  - Calls `decompress_sources()` then `build_mw_json()`; prints a final summary of
    the three mobile-critical files (cpd_clean.db, bhs.xml, mw.json) with sizes;
    exits non-zero if any is missing
  - → verify: run it in the existing clean clone `/tmp/od-citest` (mwweb1.zip and
    sources already present from the 2026-06-11 dry run — HEAD check only, **no
    download**); expect success summary. Then `rm` one source file, rerun, expect
    non-zero exit

- [x] Task 1.4: Track `mwweb1.zip`
  - `.gitignore`: add `!/dictionaries/mw/source/mwweb1.zip` after the source-dir
    ignore rule
  - Copy the validated zip from `/tmp/od-citest/dictionaries/mw/source/mwweb1.zip`
    (fresh from Cologne 2026-06-11, 46,120,709 bytes) into the real repo's
    `dictionaries/mw/source/` — do NOT download again
  - `git add` it (local commit only; the ~46 MB push happens when the user's data
    allows)
  - → verify: `git check-ignore dictionaries/mw/source/mwweb1.zip` exits 1
    (not ignored); `git status` shows it staged; no other source files become
    trackable

- [x] Task 1.5: Phase checkpoint — per user instruction (2026-06-11): no
  mid-thread commits; the user commits everything in one go at the end.
  Implementation verified (full test suite + clean-clone runs).

## Phase 2 — dpd-db main repo

- [x] Task 2.1: Hard-fail in `exporter/mobile/mobile_exporter.py`
  - Replace the three `pr.red("... not found, skipping")` branches (CPD, MW, BHS)
    with a raised `FileNotFoundError` naming the missing path and pointing to
    `resources/other-dictionaries: uv run python scripts/prepare_sources.py`
  - Cone keeps its `--cone` opt-in behavior untouched
  - Rewrite `test_skips_missing_cpd_source_and_keeps_existing_dictionary_exports`
    (tests/exporter/mobile/test_mobile_exporter.py) to expect the raise; add
    equivalent MW and BHS cases
  - → verify: `uv run pytest tests/exporter/mobile/` — all pass

- [x] Task 2.2: Add prepare step to `.github/workflows/draft_release.yml`
  - Insert before "Export Mobile DB":
    `working-directory: resources/other-dictionaries`,
    `run: uv run python scripts/prepare_sources.py`
  - → verify: `uv run python -c "import yaml; yaml.safe_load(open('.github/
    workflows/draft_release.yml'))"` parses; diff shows only the new step

- [x] Task 2.3: New `.github/workflows/mobile_release.yml`
  - workflow_dispatch only; single ubuntu-latest job, `contents: write`
  - Steps copied verbatim from draft_release.yml: Setup section (checkout w/
    submodules + GH_PAT, remove large dirs, unzip deconstructor_output, Python 3.12,
    uv, `uv sync --all-groups`, Go) and Build Database section (config, db_rebuild,
    initial setup, version, inflections, roots/families, sets/idioms, families JSON,
    variants, deconstructor add, api_ca_eva_iti, transliterate, inflections-to-
    headwords, suttas, suttas-to-lookup, grammar-to-lookup, spelling, lookup
    transliterate, help/abbrev, frequency (Go), EBT counter, bold definitions,
    EPD-to-lookup, dealbreakers)
  - Then: Prepare dictionary sources → Export Mobile DB → Set Release Date + Tag
    (same `scripts/build/version_print.py`) → `softprops/action-gh-release@v2`,
    `draft: true`, files: `exporter/share/dpd-mobile-db.zip` only, body: short
    fixed text ("Mobile database update"), `GITHUB_TOKEN: secrets.GH_PAT`
  - Omit: dictzip/ICU installs are kept only if `uv sync --all-groups` needs PyICU
    (it does — keep the ICU apt line); omit audio index, grammar dict export, all
    other exporters, artifact upload/download, macOS job, uposatha commit, release
    notes generator
  - → verify: YAML parses; `actionlint` if available (else careful review); step
    list diffed side-by-side against draft_release.yml to confirm nothing
    DB-populating was dropped

- [x] Task 2.4: Phase checkpoint — per user instruction (2026-06-11): no
  mid-thread commits; the user commits both repos in one go at the end
  (other-dictionaries first, then dpd-db incl. submodule pointer bump).
  All Phase 2 verifications passed (98 mobile exporter tests, both YAML
  files parse, build step lists diffed identical).

## Phase 3 — release verification (needs internet; user-driven, after the
## user commits and pushes both repos)

- [x] Task 3.1: Push both repos (other-dictionaries first: ~46 MB), then dispatch
  `mobile_release.yml` from the Actions tab
  - → verified 2026-06-12, run 27391990372 (use_last_release_db mode): log shows
    `exporting CPD 29,734`, `exporting Monier Williams 194,084`, `exporting BHS
    17,836` — no "not found, skipping"; draft v0.4.20260612 created with
    `dpd-mobile-db.zip` 175.1 MB

- [ ] Task 3.2: Spot-check the draft asset, then user publishes
  - Download the draft `dpd-mobile-db.zip` (or inspect via `gh`), open with sqlite:
    `SELECT dict_id, entry_count FROM dict_meta` → cpd/mw/bhs all > 0
  - User publishes the release; app picks it up via in-app DB update
  - → verify: user confirms MW results appear in the app after DB update
