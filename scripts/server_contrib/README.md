# Contributor web server tooling

Server-side scripts for the hosted gui2 **contributor web server** (issue #215,
round 2 — the zero-install web version of gui2 for non-technical contributors).
Each contributor gets one gui2 web instance. Their work goes to per-user files
in `DPD_GUI2_DATA_DIR` (outside the repo). A nightly window pulls `main`,
drops what the maintainer has handled, pushes the rest to the `contributions`
branch, and rebuilds the scratch db when `main` has moved.

See also: `config_server.md` (the lean rebuild — kept/dropped step rationale),
`spec.md`/`plan.md` in `kamma/threads/20261030_contrib_5_hardening/`.

## The nightly maintenance window

`maintenance_window.py` is the orchestrator:

```
stop instances
  → capture rollback     (db copy, HEAD, every delivered contributor file)
  → dirty-tree check     (tracked files only; a dirty tree refuses the window)
  → git pull --ff-only + submodule update
  → contrib_reconcile    (drop what main has processed or merged)
  → contrib_push         (contributions branch; a failure is logged, not fatal)
  → rebuild only if HEAD differs from logs/last_built_commit
       db_rebuild_from_tsv.py → generate_components_server.py → health check
       → re-apply WAL → restore the tracked files the build rewrote
  on ANY failure after the pull: restore db, HEAD and contributor files
start instances (always)
```

A failed instance stop, a failed dirty-tree check or a failed pull skips
reconcile, push and rebuild. Every run logs to `logs/maintenance_YYYYMMDD.log`.

- Every user shares one data folder, `/var/lib/dpd/contrib_data`
  (`add_contributor.sh` sets it; file names carry the user). Pass the same folder
  to the window with `--data-dir`, or set `DPD_GUI2_DATA_DIR` for it.
- A corrupt contributor JSON stops the window (it rolls back) every night until
  someone fixes the file. This is deliberate: it never guesses.
- The push overwrites whatever is on the remote `contributions` branch. Do not
  commit to it by hand.
- `htpasswd` files are written mode 640. The nginx worker must be able to read
  them: give the file to nginx's group on the server (not checked locally).

### Run it

Production (cron on the server):

```bash
cd <server clone> && uv run scripts/server_contrib/maintenance_window.py \
    --data-dir /var/lib/dpd/contrib_data \
    --instance dpd-gui@alice --instance dpd-gui@bob
```

Local dry-run (no systemd, no push — safe against a scratch copy):

```bash
cd <scratch repo> && uv run scripts/server_contrib/maintenance_window.py --no-systemd --no-push
```

Flags: `--no-systemd`, `--no-push`, `--instance <unit>` (repeatable),
`--db-path`, `--data-dir` (default: `DPD_GUI2_DATA_DIR`, else `gui2/data`),
`--worktree` (default: `<project-root>_contrib_worktree`), `--log-dir`,
`--remote`, `--branch`.

## The pieces

| Script | Does |
|---|---|
| `contrib_reconcile.py` | Drops a JSON entry when main's `additions_added.json` / `corrections_added.json` holds its `(key, hash)`. Drops a flag line when `contrib_lines_merged.json` holds it for that file. Never drops the header of a variant or spelling file. Writes an emptied file, never deletes it. |
| `contrib_push.py` | Resets `contributions` to the clone's `HEAD` in a separate worktree, copies in the delivered files, commits if anything differs, and always `git push --force-with-lease` after `git fetch --prune`. |
| `merge_contrib_files.py` | Maintainer side. Folds each contributor's flag files into the shared files and logs every handled line in `gui2/data/contrib_lines_merged.json`. |
| `maintenance_window.py` | The orchestrator above. |
| `generate_components_server.py` | LEAN rebuild — only the steps gui2 reads. No pytest. See `config_server.md`. |
| `config_server.template` | Server `config.ini` template. Copy to `config.ini`; NEVER commit the result. |

The delivered file kinds (additions, corrections, user dictionary, checked,
manual corrections, variants, spelling, test exceptions) come from one list in
`tools/contrib_entry.py`. History, daily log, presets and stash files are
never delivered.

## Maintainer: taking in contributions

There are no pull requests. From the repo root:

```bash
cd ~/MyFiles/3_Active/dpd-db && just contrib-merge
```

This fetches `origin/contributions`, merges it into local `main`, and runs
`merge_contrib_files.py`.

- **Merge before you process.** Processing removes entries from main's copy of
  a contributor file. A branch built before that can conflict.
- **A conflicted merge:** abort it (`git merge --abort`). The next night's
  branch is built on current main and is clean.
- **Backup & Quit** commits `additions_added.json`, `corrections_added.json`
  and `contrib_lines_merged.json` with the TSV backup, so the logs reach main
  together with the words they describe. The server never runs it.

## Removing a contributor

1. Run a maintenance window.
2. Process or reject all their entries.
3. Archive their files in `/var/lib/dpd/contrib_data` (`*_<user>.*`; do not
   delete them).
4. Remove their env file, htpasswd entry and nginx files.

Deleting their files first loses any work not yet pushed.
