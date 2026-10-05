# Spec: server update script cleans up after itself, and the server folder is split

## Overview
`scripts/server/update-dpd.sh` deploys the dpdict.net webapp. Each run leaves large
files behind and replaces live databases without testing them. After months of runs
this grows to gigabytes on the server. This thread makes each step download into a
temporary folder, test the result, swap it in, and delete the temporary files.

Keep it simple. This is a small update script.

It also splits `scripts/server/` in two, because it holds two unrelated systems:
- `scripts/server_dpdict/` — the dpdict.net webapp deploy (`update-dpd.sh` only).
- `scripts/server_contrib/` — the gui2 contributor web server (everything else).

Underscores, not dashes: the contributor scripts import each other as
`scripts.server.<module>`, and a dash makes a folder name unimportable.

## Current behaviour (verified by reading the code, 2026-10-05)
1. Audio — `audio/db_release_download.py`:
   - Downloads `dpd_audio_<version>.tar.gz` (~963 MB) into `audio/db/` and never
     deletes it. The name changes each release, so one new archive piles up per run.
   - Unpacks straight over the live `audio/db/dpd_audio.db` (~1.2 GB, the only file in
     the archive). No test of the result.
   - On failure `main()` returns False, but `__main__` ignores the return value, so the
     process exits 0 and `set -e` in the bash script does not stop the run.
2. Main db — step 6 of `update-dpd.sh`:
   - `wget -qO- URL | tar -xJ` unpacks straight over the live `dpd.db`.
   - There is no `pipefail`, so a failed `wget` does not stop the run.
   - The `[ ! -f dpd.db ]` check after it always passes, because the old db is still there.
   - No test of the new db. No archive is left on disk (it is streamed).
3. `uv sync` — the uv download cache grows on each dependency change, never pruned.
4. Overwritten in place, nothing builds up: `exporter/webapp/static/search_index.json`,
   `audio/db/dpd_audio_index.tsv`.

## What it should do
1. Audio download (`audio/db_release_download.py`), used on the server AND locally:
   - Download the archive into a `tempfile.TemporaryDirectory` inside `audio/db/`
     (same filesystem, so the final move is atomic; deleted automatically, also on error).
   - Unpack it there.
   - Test the unpacked db: table `dpd_audio` has more than 0 rows.
   - Only if the test passes, move it over `audio/db/dpd_audio.db` with `Path.replace`.
   - Exit non-zero on any failure, so the bash script stops.
   - Never delete or overwrite any other file in `audio/db/`.
2. Main db (`update-dpd.sh`):
   - Download `dpd.db.tar.xz` into a temporary folder `update_tmp/` inside `dpd-db/`.
   - Unpack it there.
   - Test the db: `dpd_headwords` has more than 0 rows.
   - Only then `mv` it over `dpd.db`.
3. The bash script as a whole:
   - `set -euo pipefail`.
   - Clear `update_tmp/` at the start (in case a past run was killed) and remove it on
     exit with a `trap`.
   - Run `uv cache prune` after `uv sync`.
   - A db that fails its test never goes live, and a failed step stops the script
     before the webapp restart, so the old webapp keeps running. The steps are not one
     unit: if the main db step fails after the audio swap, the new audio db stays.
     That is accepted (review 2026-10-05), not worth more machinery.
4. Folder split:
   - Move `update-dpd.sh` → `scripts/server_dpdict/`.
   - Move the rest → `scripts/server_contrib/`; `tests/scripts/server/` →
     `tests/scripts/server_contrib/`.
   - Use plain `mv`. The user runs all git commands.
   - Update every reference (sweep below).

## One-off cleanup of existing waste (user runs by hand on the server, once)
```bash
rm ~/dpd-db/audio/db/dpd_audio_v*.tar.gz
```
After this thread, no new archive reaches that folder, so the script does not need
to do this on every run.

## Reference sweep (rg --hidden, excluding graphify-out, .git, kamma/archive)
- `justfile:329` — `dpdict-push` scp path.
- `scripts/server/README.md` — becomes the contrib README; drop the dpdict note,
  fix paths. No new README for `server_dpdict/` (the script's header comment is enough).
- `scripts/server/config_server.md:5,103` — paths.
- `scripts/server/contrib_push.py:16`, `maintenance_window.py:34-36,103,106` — imports/paths.
- `tests/scripts/server/*.py` — 5 files, imports.
- `docs/technical/project_folder_structure.md:58` — folder tree.
- `kamma/threads/20260719_contributor_web_server/{spec,plan}.md` — 25 path
  references. That thread is still open (Phase 3 not done), so update its paths.
- `kamma/threads/20260713_scripts_triage/` — historical notes, leave as is.
- The contributor server is not deployed yet (cron task 3.6 open), so no server
  cron or unit points at the old path.

## Assumptions & uncertainties
- `dpd.db.tar.xz` holds `dpd.db` at its root. Inferred from CI (`tar -xJf` then use
  `dpd.db`), not checked by opening the archive. The script fails cleanly if not.
- A damaged download makes the unpack fail, because gzip and xz both carry checksums.
  So a row count is enough as the db test.
- The server has room for old db + archive + new db at once (~3.4 GB peak for audio).
- The server has `wget` and `tar` (already used). The db test uses
  `uv run python -c` with stdlib `sqlite3`, so no `sqlite3` CLI is needed.
- The running webapp keeps the old db file open until restart. `mv` replaces the
  name atomically, so it is safe while the webapp runs.
- No `shellcheck` installed locally; the bash script is checked with `bash -n`.

## Constraints
- Keep it simple: no new modules, no config keys, no flags, no shared helpers.
- Do not touch logs or any other user data.
- The local audio build (`audio/db_create.py` → `audio/db_release_upload.py`) writes
  `audio/db/dpd_audio_<version>.tar.gz` and reads it back. The audio download must
  not delete these.

## How we'll know it's done
- After an update run on the server, `audio/db/` holds no `.tar.gz` and `update_tmp/`
  does not exist.
- A failed download or failed db test stops the script with an error, and the live
  dbs are unchanged.
- `uv run pytest tests/scripts/server_contrib tests/audio` passes; ruff and pyright
  are clean on touched Python files; `just typecheck` passes.
- `rg --hidden "scripts/server/|scripts\.server\."` finds only archived/historical notes.

## What's not included
- Logs — left alone.
- The three old local audio archives on the user's machine — made by the local build,
  not by the download. The user deletes them by hand if wanted.
- The versioned `dpd_audio_index_v*.tsv` files locally — not made by these scripts.
- The commented-out tipitaka translation step.
