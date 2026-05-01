# Plan: Audio index TSV

**GitHub issue:** none.

## Architecture Decisions
- **TSV at `audio/db/dpd_audio_index.tsv`** (un-versioned local path) so cache
  loaders have a stable path. The release asset is versioned
  (`dpd_audio_index_<version>.tsv`) but the download scripts always save to
  the static path.
- **Upload TSV before tarball** in `db_release_upload.py`. Sidesteps the race
  observed on 2026-05-01 without adding API polling.
- **`load_audio_set` / `load_audio_dict` parse TSV directly with `csv`** — no
  sqlalchemy. Keeps the build pipeline free of audio db dependencies.
- **`sys.exit(1)` in `index_release_download.py`** (and on TSV-fetch failure
  within `db_release_download.py`) so CI fails fast at the audio step.
- **Two download scripts**: `db_release_download.py` keeps fetching the
  tarball plus now also the TSV (for local users). New
  `index_release_download.py` fetches only the TSV (for CI).
- **No path constant changes for tarball** — only add
  `dpd_audio_index_tsv_path` to `tools/paths.py`.

## Phase 1: Generate index TSV during audio db creation
- [x] Add `dpd_audio_index_tsv_path` to `tools/paths.py`, alongside
      `dpd_audio_db_path`. Points at `audio/db/dpd_audio_index.tsv`.
      → verify: `python -c "from tools.paths import ProjectPaths; p=ProjectPaths(); print(p.dpd_audio_index_tsv_path)"`
      prints the expected absolute path.
- [x] Add `create_index_tsv(version: str) -> Path` in `audio/db_create.py`.
      Reads the audio db, writes versioned TSV
      (`dpd_audio_index_<version>.tsv`) to the same dir as the tarball, with
      header `lemma_clean\thas_male1\thas_male2\thas_female1`. Returns the
      versioned path.
      → verify: read function; confirm header + booleans formatted as
      `"True"`/`"False"` strings or `"1"`/`"0"`. Pick `"1"`/`"0"` for
      compactness.
- [x] Wire `create_index_tsv(make_version())` into `db_create.main()`
      between `create_archive()` and `cleanup_old_tarballs()`.
      → verify: re-read main(); flow is create_audio_db → populate → archive
      → index_tsv → cleanup.
- [x] Update `cleanup_old_tarballs()` to also prune
      `dpd_audio_index_*.tsv` files — keep latest 3 by mtime.
      → verify: function loops over both globs.

## Phase 2: Upload index TSV first, tarball second
- [x] In `audio/db_release_upload.py`, add `get_index_path(version)` mirroring
      `get_archive_path`. Returns versioned TSV path or logs red and returns
      `None`.
      → verify: function returns expected path; missing case handled.
- [x] Update `main()` to fetch both `archive_path` and `index_path` up-front
      and bail out (return) if either is missing.
      → verify: re-read main(); both paths checked before any GitHub call.
- [x] In `create_github_release()`, accept both paths. Upload the index TSV
      asset immediately after `repo.create_git_release(...)`, before the
      tarball upload.
      → verify: re-read function; index upload occurs before tarball upload.

## Phase 3: Add TSV fetch to existing download script + new index-only script
- [x] In `audio/db_release_download.py`, add `find_index_asset(release_info)`
      and `download_index(asset)` helpers (mirror existing archive helpers).
      → verify: read; matcher uses `startswith("dpd_audio_index_") and
      endswith(".tsv")`.
- [x] Update `main()` to fetch the index asset after the tarball is
      successfully extracted. Save to `pth.dpd_audio_index_tsv_path`.
      → verify: read main(); both downloads happen, both end up in
      `audio/db/`.
- [x] Create new file `audio/index_release_download.py`. Minimal: fetch
      latest release, find `dpd_audio_index_*.tsv` asset, stream to
      `pth.dpd_audio_index_tsv_path`. Use `sys.exit(1)` on every failure
      branch (no release info, no asset, download error, empty/tiny file).
      Successful run prints a clear "ok" line.
      → verify: read file; every error path calls `sys.exit(1)`. Run with no
      network (or temporarily renamed asset matcher) to confirm exit code.

## Phase 4: Read TSV in cache_load
- [x] Rewrite `load_audio_set()` in `tools/cache_load.py` to parse
      `pth.dpd_audio_index_tsv_path` with `csv.reader`. Returns frozenset of
      `lemma_clean` where any of `has_male1/has_male2/has_female1` is `"1"`.
      Drop the sqlalchemy/audio-db imports.
      → verify: place a small fake TSV at the path, call function, assert
      returned frozenset matches expected lemmas.
- [x] Rewrite `load_audio_dict()` similarly to return
      `dict[str, tuple[bool, bool, bool]]`. Same TSV.
      → verify: with the same fake TSV, call function, assert mapping is
      correct (e.g. `{"abhi": (True, False, True)}`).
- [x] Remove now-unused `from audio.db.db_helpers import get_audio_session`
      and `from audio.db.models import DpdAudio` if they were the only audio
      imports in the file.
      → verify: `grep -n "audio\.db" tools/cache_load.py` returns nothing.

## Phase 5: Workflow cleanup
- [x] In `.github/workflows/draft_release.yml`, change the "Download Audio
      Database" step to run `audio/index_release_download.py`. Rename step to
      "Download Audio Index".
      → verify: yaml shows new path and name.
- [x] Remove the "Delete Audio Database to free space" step entirely.
      → verify: step no longer present; surrounding indentation correct.
- [x] Run `python -c "import yaml; yaml.safe_load(open('.github/workflows/draft_release.yml'))"`.
      → verify: no parse error.

## Phase 6: End-to-end verification
- [x] Generate the TSV locally from the existing audio db (one-shot: run
      `python audio/db_create.py` if mp3s are present, OR temporarily call
      `create_index_tsv` directly via a small repl). Confirm
      `audio/db/dpd_audio_index.tsv` exists and is non-empty.
      → verify: `wc -l audio/db/dpd_audio_index.tsv` shows >1k lines.
- [x] Run `python exporter/goldendict/main.py` to completion (locally) — only
      if user asks. Otherwise, settle for a smaller smoke test: import
      `tools.cache_load` and call both functions, assert they return non-empty.
      → verify: no "no such table" errors; both loaders populated.
- [x] Spot-check a known audio-bearing lemma in the loaded set.
      → verify: `"abhi" in load_audio_set()` (or another known lemma) → True.
