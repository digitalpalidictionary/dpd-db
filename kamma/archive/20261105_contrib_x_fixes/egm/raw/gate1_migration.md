I have enough. `dpd.db.prev` does not appear in `maintenance_window.py` at all, and the worktree path is configurable via `--worktree`.

## Findings

**Blocker — Task 8 (nightly window cleanup) deletes a configurable path and has no rollback.**
Evidence: `scripts/server_contrib/maintenance_window.py:456-478` — the worktree is `args.worktree or project_root.parent / f"{project_root.name}_contrib_worktree"`, i.e. caller-supplied via `--worktree`.
Failure: the plan says "delete `_contrib_worktree/` after a good run". A script that hardcodes `_contrib_worktree/` and `rmtree`s it will delete whatever the operator passed to `--worktree` (a real clone on another mount, or `/root/mem`-style path). If the run is judged "good" by a wrong condition, a live worktree holding uncommitted contributions vanishes; `git worktree prune` metadata is also left behind, and the next run then fails on "already registered". There is no rollback: deleted worktrees are not in `.git`, and the brief admits `dpd.db.prev` "was captured mid-rebuild once" (`plan.md` task 9) — so it is not a usable backup either.
Fix: delete only the path the script itself created (compare against the resolved default and record it in the status file), never a user-supplied `--worktree`; refuse when the path is outside `project_root.parent`; use `git worktree remove --force` rather than `rmtree`; keep a `--keep` flag. Also confirm what `dpd.db.prev` is: it does not appear anywhere in `maintenance_window.py`, so "delete it" is an unverified target — re-check before wiring an `unlink`.

**Major — Task 3 (skip decon cache save when read-only) risks the wrong predicate mutating the contributor server's session.**
Evidence: `gui2/database_manager.py:390-399`. The current block already swallows the error *and* rolls back the session, with a comment (`:397-399`) saying the failed write leaves a "rolled-back-pending" state. A "skip when read-only" predicate will be consulted on every start, and any false negative leaves today's behaviour (harmless), but a false positive on a *writable* db silently stops refreshing the cache — the set stays in memory only, and every server start pays the live scan, which is the exact cost item 16 wanted removed. Worse, if the guard is implemented as "skip if `db_path` not writable by `os.access`", the build pipeline's lock-held case (`:393-395`) is no longer caught and no rollback runs.
Fix: keep the try/except and its `rollback()` exactly as-is; add the read-only check as an additional early return, not a replacement. Test both a read-only file and a lock-held-session case.

**Major — Task 11/12 (DB tab starter preset) has no migration, and stored presets are per-user files.**
Evidence: `gui2/filter_presets_manager.py:16-23` writes a whole dict with `open(..., "w")`; `gui2/paths.py:90` puts contributor presets at `filter_presets_{username}.json`. Nothing validates preset contents on load (`:14-19` returns raw JSON).
Failure: changing the columns shown to `id, pos, grammar, meaning_1, meaning_2, meaning_lit` breaks any *existing* saved contributor preset that names a column no longer offered. `save_preset` writes `display_filters` verbatim, so an old preset will still load, and the DB tab will try to render a field the new column list does not build — a crash or an empty grid, not a graceful fallback. Presets live in a per-user dir (`DPD_GUI2_DATA_DIR`) so there is no git rollback for them.
Fix: version the preset dict (`{"version": 2, "presets": {...}}`) and on load drop unknown `display_filters` entries with a warning; keep the old starter under a renamed key rather than overwriting. Rollback = restore the JSON file, which the plan does not mention recording.

**Major — Task 4 (remove `start_dpd_server`) can break a running desktop app with no rollback path in code.**
Evidence: `gui2/main.py:22,746`. `start_dpd_server()` fires *after* the UI paints (`:743-747`), and per the spec (`spec.md` item 28) the spawned uvicorn survives Ctrl+C on `127.1.1.1:8080`. The `wxt` extension lists that address (`plan.md` task 4).
Failure: contributors/owner whose extension or a second gui2 instance still expects the helper will lose it silently after the change — nothing warns. Rollback requires reverting code and reinstalling the desktop app; there is no feature flag.
Fix: keep `start_dpd_server` behind a config key (default off) for one release, or print an explicit "helper web server no longer started" line on first run. Update `exporter/wxt_extension/wxt.config.ts` in the same task, or state in the thread why not.

**Nit — Task 9 is already done; the plan's task 10 is stale.**
Evidence: `gui2/user.py:29,78` — `routed_username` already backs `is_not_primary()`, and `gui2/toolkit.py:52,64` uses the same `resolve_username() or "1"`. Building task 10 as written will duplicate or regress it.
Fix: mark task 10 as verified-done with these line refs, and drop it from the twelve.

**Nit — the thread has no plan.md/spec.md of its own.**
`kamma/threads/20261105_contrib_x_fixes/` contains only `egm/`. Task order, tests, and rollback steps exist only in the brief, so nothing is auditable after review.
Fix: write `plan.md` into the thread and list a rollback line per task.
