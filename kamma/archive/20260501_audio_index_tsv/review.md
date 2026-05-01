## Thread
- **ID:** 20260501_audio_index_tsv
- **Objective:** Replace 1 GB audio db download in CI with a small index TSV containing per-lemma audio presence flags.

## Files Changed
- `tools/paths.py` — added `dpd_audio_index_tsv_path`
- `audio/db_create.py` — added `create_index_tsv()`, wired into `main()`, extended `cleanup_old_tarballs()` to also prune old index TSVs
- `audio/db_release_upload.py` — added `get_index_path()`, upload TSV before tarball in `create_github_release()`
- `audio/db_release_download.py` — added `find_index_asset()` / `download_index()`, fetched after tarball in `main()`
- `audio/index_release_download.py` — new CI-only script; `sys.exit(1)` on every failure branch
- `tools/cache_load.py` — `load_audio_set()` / `load_audio_dict()` now parse TSV via `_read_audio_index()`; all audio.db sqlalchemy imports removed
- `.github/workflows/draft_release.yml` — "Download Audio Index" step calls new script; "Delete Audio Database to free space" step removed

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `db_release_download.py:find_archive_asset` | `not name.startswith("dpd_audio_index_")` guard is redundant since `.tar.gz` can't match `.tsv` | Belt-and-braces; harmless and makes intent explicit. No fix needed. | — |

## Fixes Applied
None — only nit found, deliberately left as-is.

## Test Evidence
- `python -c "from tools.paths import ProjectPaths; p=ProjectPaths(); print(p.dpd_audio_index_tsv_path)"` → correct absolute path
- `python -c "from audio.db_create import create_index_tsv; from audio.db.db_helpers import make_version; create_index_tsv(make_version())"` → wrote 75,366 rows, 1.6 MB
- `python audio/index_release_download.py` (asset missing) → exit 1
- `just audio-upload` → index TSV uploaded first, tarball upload started
- `rm audio/db/dpd_audio_index.tsv && python audio/index_release_download.py` → fetched in 9s, 1,578,908 bytes
- `grep -n "audio\.db" tools/cache_load.py` → no matches
- Cache loaders: set size 75,366, dict size 75,366, known lemmas (`a`, `abhi`, `buddha`, `dhamma`) all `(True, True, True)` ✓

## Verdict
PASSED
- Review date: 2026-05-01
- Reviewer: kamma (inline)
