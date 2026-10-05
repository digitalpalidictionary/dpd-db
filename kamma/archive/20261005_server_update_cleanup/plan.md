# Plan: server update script cleans up after itself, and the server folder is split

Spec: `kamma/threads/20261005_server_update_cleanup/spec.md`

## Architecture Decisions
- Move files with plain `mv`, not `git mv`. The user runs all git commands.
- Split the folders first, so later edits land at the final paths.
- Fix the audio download in the Python script, not the bash script. It is the file
  that makes the archive, and the local machine uses it too.
- The db test is a row count only. Unpacking already fails on a damaged archive
  (gzip and xz both carry checksums).
- One temp folder per tool: `tempfile.TemporaryDirectory` in Python, `update_tmp/`
  plus `trap` in bash. No shared helper.

## Phase 1 — Split the server folder
- [x] 1.1 Move `scripts/server/update-dpd.sh` → `scripts/server_dpdict/update-dpd.sh`.
  Move the rest of `scripts/server/` → `scripts/server_contrib/`.
  Move `tests/scripts/server/` → `tests/scripts/server_contrib/`.
  Delete the empty old folders and their `__pycache__`.
  → verify: `ls scripts/server_dpdict scripts/server_contrib tests/scripts/server_contrib`
    shows the expected files; `scripts/server/` no longer exists.
- [x] 1.2 Update every reference listed in the spec's sweep: `justfile:329`, the contrib
  README (drop the dpdict note, fix paths), `config_server.md`, imports in
  `contrib_push.py` and `maintenance_window.py` (plus the path at line 106),
  the 5 test files, `docs/technical/project_folder_structure.md`, and the paths in
  `kamma/threads/20260719_contributor_web_server/{spec,plan}.md`.
  → verify: `rg --hidden -n "scripts/server/|scripts\.server\." --glob '!graphify-out/**' --glob '!kamma/archive/**' --glob '!.git/**'`
    returns only `kamma/threads/20260713_scripts_triage/` and this thread's own lines.
- [x] 1.3 Phase check.
  → verify: `uv run pytest tests/scripts/server_contrib` all pass; ruff check, ruff format
    and pyright clean on the two edited scripts and the 5 test files; `just typecheck` passes.

## Phase 2 — Audio download tests and swaps
- [x] 2.1 In `audio/db_release_download.py`: download and unpack into a
  `tempfile.TemporaryDirectory(dir=pth.dpd_audio_db_path.parent)`; count rows in
  `dpd_audio`; if > 0, `Path.replace` it over `pth.dpd_audio_db_path`; else fail.
  Change `__main__` to `sys.exit(0 if main() else 1)`.
  → verify: ruff check, ruff format, pyright clean on the file.
- [x] 2.2 Add `tests/audio/test_db_release_download.py` with two tests, faking
  `requests.get` to serve a small `.tar.gz` holding a sqlite db, and pointing the
  paths at `tmp_path`:
  (a) a db with rows replaces the live db, and the audio db folder holds no `.tar.gz`
      and no temp dir afterwards;
  (b) a db with 0 rows leaves the live db unchanged and `main()` returns False.
  → verify: `uv run pytest tests/audio` all pass. Then revert the swap logic in 2.1,
    re-run, and record here how many tests fail. Restore at once.
  Result (2026-10-05): with the old flow restored (unpack over the live db, no test),
  2 of 2 fail — (a) `['dpd_audio.db', 'dpd_audio_v0.0.1.tar.gz'] == ['dpd_audio.db']`
  (archive left behind), (b) `assert True is False` (empty db accepted). Restored;
  6 passed in `tests/audio`.
- [x] 2.3 Phase check.
  → verify: `uv run pytest tests/audio` all pass; `just typecheck` passes.

## Phase 3 — Update script
- [x] 3.1 Edit `scripts/server_dpdict/update-dpd.sh`:
  `set -euo pipefail`; after `cd dpd-db`, `rm -rf update_tmp && mkdir update_tmp` and
  `trap 'rm -rf update_tmp' EXIT`; `uv cache prune` after `uv sync`;
  step 6 becomes: `wget` into `update_tmp/`, `tar -xJf ... -C update_tmp`, count rows in
  `dpd_headwords` with `uv run python -c` and stdlib `sqlite3` (non-zero exit if 0),
  then `mv update_tmp/dpd.db dpd.db`. Remove the useless `[ ! -f dpd.db ]` check.
  → verify: `bash -n scripts/server_dpdict/update-dpd.sh` prints nothing.
- [ ] 3.2 Phase check (user, on the server). DEFERRED by the user to the next server update (2026-10-05), not blocking finalize.
  → verify: the user runs `just dpdict-push`, then the one-off `rm` from the spec, then
    the update. Afterwards `ls ~/dpd-db/audio/db/*.tar.gz` finds nothing,
    `~/dpd-db/update_tmp` does not exist, and dpdict.net serves words and audio.

## Smoke gate (2026-10-05)
`uv run pytest tests/` — 1972 passed, 12 deselected (slow). No failures. Task 3.2 is the user's server run.

## Review (2026-10-05) — parallel: CodeRabbit + Sonnet from-scratch audit
- CodeRabbit (`--agent --uncommitted --include-untracked`, 36 files): 0 findings.
- Sonnet audit: no real defects. MINOR, accepted: (1) the steps are not one unit,
  so a main-db failure after the audio swap keeps the new audio db (spec wording fixed);
  (2) a stale `dpd.db-wal` could in theory apply to the swapped file, same exposure as
  before; (3) SIGKILL leaves one `audio/db/tmpXXXX` dir, rare one-off. Not acted on.
