# Spec: Replace 1 GB audio db download with small audio index TSV

**GitHub issue:** none filed; tracked here.

## Overview
The dpd-db release workflow currently downloads a 1 GB `dpd_audio.db` SQLite
file at build time, just to read four boolean fields per headword
(`needs_audio_button`, `audio_male1`, `audio_male2`, `audio_female1`). When the
download silently fails — as it did on 2026-05-01 due to a race between the
dpd-audio release creation and its asset upload — every GoldenDict worker
crashes on `OperationalError: no such table: dpd_audio`, producing a corrupt
19 MB `dpd-goldendict.zip`.

This thread adds a tiny TSV asset to each `dpd-audio` release and switches the
build to consume the TSV instead of the SQLite file. The 1 GB tarball remains
on the release page for users who want the full audio database.

## What it should do
1. `audio/db_create.py` produces `audio/db/dpd_audio_index_<version>.tsv`
   alongside the existing tarball. Columns: `lemma_clean`, `has_male1`,
   `has_male2`, `has_female1`. Header row included.
2. `audio/db_release_upload.py` uploads the **index TSV first**, then the
   tarball. The index asset is therefore present milliseconds after the
   release exists, regardless of how long the tarball upload takes.
3. `audio/db_release_download.py` is unchanged in spirit — it still fetches
   the tarball — but additionally fetches the index TSV alongside it. Both
   files end up on disk.
4. New `audio/index_release_download.py` — minimal CI-only script that
   fetches *only* the index TSV. Used by the release workflow. `sys.exit(1)`
   on any failure.
5. `tools/cache_load.py:load_audio_set()` and `load_audio_dict()` read the
   TSV instead of opening the SQLite db. The audio sqlalchemy session/model
   imports are no longer touched at build time.
6. `.github/workflows/draft_release.yml` calls
   `audio/index_release_download.py` and drops the "Delete Audio Database to
   free space" step (no big db is downloaded any more).

## Assumptions & uncertainties
- **Audio db build runs locally on Bodhirasa's machine**, not in CI. The
  index TSV is generated there alongside the tarball, then uploaded as a
  release asset. Confirmed by reading `audio/db_create.py:main()` which
  expects audio mp3 dirs to exist.
- **Asset name pattern** `dpd_audio_index_*.tsv` does not collide with any
  existing asset.
- **`make_version()`** (in `audio/db/db_helpers.py`) returns a stable version
  string used by both tarball and index TSV.
- **No external consumer of the audio db** depends on the index being inside
  the SQLite file — the dpd-db build is the only known consumer at build time.
- **Only one other contributor builds locally** and they always download the
  audio db via `audio/db_release_download.py`, which after this change also
  fetches the index TSV. So they always have the TSV.

## Constraints
- TSV format (matches `db/backup_tsv/` convention).
- Versioned asset filename (matches existing `dpd_audio_<version>.tar.gz`).
- The 1 GB tarball must remain available on each release.
- Existing `load_audio_set` / `load_audio_dict` API signatures must not change
  — only their internals.
- `audio/db_release_download.py` must continue to fetch the tarball; this
  thread only *adds* TSV fetch behaviour to it.

## How we'll know it's done
- Local: run `python audio/db_create.py` (when audio mp3s present), confirm
  both `dpd_audio_<v>.tar.gz` and `dpd_audio_index_<v>.tsv` are produced.
- Local: run `python audio/index_release_download.py` against a real release,
  confirm `audio/db/dpd_audio_index.tsv` appears.
- Local: run `python exporter/goldendict/main.py` with the TSV in place,
  confirm GoldenDict export completes and `needs_audio_button` is True for
  known-with-audio lemmas.
- CI: next Draft Release run completes without "no such table: dpd_audio"
  errors, and `dpd-goldendict.zip` is full size (~270 MB).

## What's not included
- Race-condition guard via GitHub API `asset.state == "uploaded"` polling —
  uploading the TSV first makes this unnecessary.
- Refactor of audio playback wiring on the consumer side (GoldenDict JS).
- Any change to `dpd-audio` repo itself (only release assets are affected).
- Graceful fallback when TSV is missing locally — out of scope; loud failure
  is acceptable.
