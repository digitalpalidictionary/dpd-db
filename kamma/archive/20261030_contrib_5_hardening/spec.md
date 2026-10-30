# Spec: contributor hardening — login, per-user tabs, safe sync

**Thread:** 20261030_contrib_5_hardening
**Date:** 2026-10-30
**GitHub issue:** [#215 — Contributor Onboarding](https://github.com/digitalpalidictionary/dpd-db/issues/215) (commits reference `#215`)
**Builds on:** `20261023_contrib_1_web_server` (read its spec first) and
`20261023_contrib_2_edits_json` (contributor saves go to JSON only).
**Order:** contrib_2 → **this thread** → contrib_3 (preview; it edits the same
Pass2Add save code) → contrib_4 live checks → contrib_1 Phases 3–4.
**Supersedes:** contrib_1 spec points 7, 8 and 10 (absorption invariant,
snapshot reconcile, rebuild gate), and contrib_1 plan task 3.5's script, which
is written here.

## Overview

No real contributor uses the server until this thread is done and tested
locally and on the server. A review on 2026-10-29 found these flaws:

1. Every contributor sees all 17 tabs. Seven of them write `dpd.db` directly
   (DB, ', Sp, √, CT, Infl, Global "Update Inflections"). Global's Ctrl+S runs
   Backup & Quit (a git commit on the server), and its Anki button runs
   `pkill -9 -f anki`.
2. There is no login. The plan named nginx basic auth, but nothing exists.
3. A second browser tab builds a second app copy (~2.5 GB). Both copies hold the
   contributor JSON in memory and rewrite the whole file on save, so one tab
   wipes the other's saves.
4. The nightly sync is broken:
   - `contrib_push` switches the server's only clone to the `contributions`
     branch. Every later `git merge --ff-only <main>` fails once main moves.
   - `absorption_check` treats "file absent on main" as "absorbed". Before the
     PR is merged, the rebuild is allowed and `contrib_reconcile` drops the
     unmerged entries. The next push then deletes them from the PR.
   - The PR branch is never reset to main, so the second PR conflicts with your
     processing commits on the same file.
   - Once main tracks `gui2/data/additions_alice.json`, the server's live copy
     at the same path blocks every pull.
5. Five per-user flag files (user dictionary, sandhi checked, sandhi
   corrections, variant readings, spelling mistakes) are gitignored and never
   pushed. Nothing on the desktop merges them in.
6. Pass1Add's test popup "Add exception" writes the shared, git-tracked
   `db_tests/db_tests_columns.tsv`. On the server this is never pushed, and
   the change blocks the nightly pull.
7. Your review side: there is no way to reject a contribution, so the
   contributor file never empties. A correction stores every field of the
   word, so stale fields show as red proposals that can undo your newer edits.
   The Add button copies the contributor's id into the id proposal field.
8. A contributor's new word takes `db max id + 1`, which a real word on main
   can later take.
9. Desktop first run: `ToolKit` routes paths with `resolve_username() or "1"`,
   but `UsernameManager.is_not_primary()` is True for `None`. A save in that
   state goes to `additions.json`, which nothing reads.

## Decisions (user, 2026-10-29/30 — do not relitigate)

- **Login lives in the web server, not the app.** nginx basic auth over HTTPS.
  Each contributor has their own path (`/alice/`), which goes only to their own
  gui2 instance and accepts only their own password. The app never sees a
  password. The desktop has no nginx, so the maintainer never sees a login.
- **Passwords live only in the server's nginx password files** (hashed), never
  in the repo.
- **Contributor tabs come in four kinds. The tab decides, not the user:**

  | Kind | Tabs | Contributor gets |
  |---|---|---|
  | Base | Pass1Auto, Pass1Add | always, full access |
  | Safe (no writes) | Transl, Bold Search | if listed for the user |
  | Read | DB, √, Infl | if listed; looking only, every save refused |
  | Hidden | Global, Pass2Pre, Pass2x, Pass2Auto, Pass2Add, ', Sp, Sandhi, Tests, CT | never, for now |

  A hidden tab is opened up later, in its own thread, when a contributor needs
  it. When Pass2Add is opened, contributors need only its P2A and New buttons.
- **A second browser tab is refused.**
- Pass1Auto keeps one shared queue file per book (20260719 decision C): two
  contributors must not work on the same book.
- **Each user's settings live in one server-only env file** (decided during
  planning, 2026-10-30): username, role, data folder, port and extra tabs. A
  tracked users file was dropped, because the add-contributor script would
  modify a tracked file on the server and block the nightly pull.

## What it should do

### A. Per-user tabs
1. `DPD_GUI2_TABS` (comma-separated tab labels, e.g. `Bold Search,DB`) lists a
   server user's extra tabs. The add-contributor script writes it into the
   user's env file.
2. It applies only when the role is `contributor-server`
   (`tools/server_mode.is_headless_server()`). The desktop is unchanged for
   everyone, including legacy desktop contributors.
3. A server user gets the base tabs plus their listed safe and read tabs. A
   listed hidden or unknown label is ignored with a warning in the server log.
4. Only given tabs appear in the tab bar, get built, or get warmed up. The app
   opens on Pass1Auto. Alt+letter jumps, Alt+arrow moves, Alt+X and Ctrl+S reach
   only given tabs. `_get_current_lemma` and every other index-based lookup in
   `gui2/main.py` keep working.

### B. Read tabs and the read-only db
5. In a read tab, these actions refuse with "Read only: you can look but not
   save here." and change nothing:
   - DB: Save Changes (`filter_tab_view._save_changes_clicked`) and the
     on-screen Save Changes button, which lives in `FilterComponent` and calls
     `FilterComponent._save_changes` directly (found in 1.3; `FilterComponent`
     also gets `read_only`, and the DB and Infl views pass it on).
   - √: Save (`roots_tab_view._save_root`) and Delete (`_delete_root`).
   - Infl: Save (`inflection_templates_tab_view._save_template`), Rename
     (`_rename_template`) and Delete (`_delete_template`).
   - Ctrl+S in any of the three (it calls the same handlers).

   Searching, filtering, loading and the user's own filter presets (a
   per-user file) keep working.
6. **Safety net:** a `contributor-server` process opens `dpd.db` with
   `PRAGMA query_only = ON`, so any db write it reaches fails. Contributors never
   need a db write: their saves go to JSON (contrib_2). The startup decon-cache
   save (`gui2/database_manager.py` ~line 329) already catches its failure; it
   also gets a `db_session.rollback()` so the session stays usable. Only gui2
   instance env files set the role, so the nightly rebuild still writes.

### C. One browser tab per user
7. A process allows one live session. A second session shows "This app is
   already open in another tab or window." and builds nothing. When the live
   session disconnects or closes, the next session is allowed. A page reload of
   the live tab must still work.

   **Amended 2026-10-30 (live run 7.1, user decision): newest tab wins.** F5 left
   the old session holding the lock: Flet's send loop raises when the socket
   closes mid-update, and it then skips its disconnect step, so `on_disconnect`
   never fires. A new session now always takes over. The old page, if it is
   still open, is replaced by "This app is already open in another tab or
   window." A second live tab is therefore no longer refused; it takes over from
   the first. Both copies of the app stay in memory until Flet drops the old
   session (up to an hour).

### D. Server files live outside the code
8. `DPD_GUI2_DATA_DIR` moves every per-user file in `Gui2Paths.for_user` to
   that folder. Unset → `gui2/data/` as today.
9. The nightly window refuses to pull when the server clone has any modified
   tracked file, and logs the file names as an error.

### E. Contributor-side data
10. Contributor additions take ids from a reserved range:
    `max(10_000_000, own additions max) + 1`. User 1 is unchanged.
11. A contributor correction also stores `_changed`: the column names whose
    value differs from the db row (read without the overlay) at save time.
12. A contributor's Add exception (Pass1Add test popup) goes to a per-user
    file `db_test_exceptions_{u}.tsv` (`test_name<TAB>id`). Their own test runs
    treat those as exceptions too. User 1 is unchanged.
13. `is_not_primary()` uses the same username the toolkit routed paths with at
    start-up. A name typed into the first-run dialog takes effect on the next
    start, and the dialog says so.

### F. Your review side (user 1)
14. `tools/contrib_entry.py::entry_hash(entry)` = sha1 of
    `json.dumps(entry, sort_keys=True, ensure_ascii=False)`.
15. Saving a processed addition or correction also logs `_source_key` and
    `_source_hash` (the hash of the contributor's original entry) in
    `additions_added.json` / `corrections_added.json`.
16. A **Reject** button next to "Add to DB" in Pass2Add, shown only while a
    contributor addition or correction is loaded. It removes the entry from the
    contributor file, logs `_source_key`, `_source_hash`, `_contributor`,
    `lemma_1` and `"_rejected": true` in the same log, and clears the form.
17. The Add button never fills the id proposal field. The word gets the next
    real id on save.
18. The Cor button fills only the proposal fields named in `_changed`. Old
    entries without `_changed` behave as today.
19. `scripts/server_contrib/merge_contrib_files.py` (run by the maintainer
    after merging a PR) folds each contributor's flag files and test exceptions
    into the shared files, in each file's existing format and sort order, and
    reports what it added.

### G. Nightly sync, redesigned
20. The server clone stays on `main`. The window runs:
    stop instances → dirty-tree check → `git pull --ff-only` → reconcile →
    push → rebuild the db only if main moved since the last good build (with
    the existing rollback) → start instances.
21. Reconcile, for JSON entries: drop a local entry when its
    `(key, entry_hash)` is in main's `additions_added.json` or
    `corrections_added.json` (accepted or rejected). For flag lines and test
    exceptions: drop a local line once main's shared file holds it. No
    `last_pushed` snapshots.
22. Push from a separate git worktree: reset `contributions` to `origin/main`,
    copy in every contributor file from `DPD_GUI2_DATA_DIR` (force-add the
    gitignored kinds), commit if anything differs, and
    `git push --force-with-lease`. The PR then always shows only pending work
    and cannot conflict.
23. `absorption_check.py`, its tests and the snapshot code are deleted.
    Contributors never write the db, so a rebuild can never lose their work.

**Amendment 2026-10-30 (Phase 4 check, case table in plan 4.1; user
decisions A–C).** Where these points differ from 19–22 above, these win.

- G.a **Merged-lines log** (decision A). The merge script keeps a tracked log
  `gui2/data/contrib_lines_merged.json` = `{contributor_file_name: [line, …]}`.
  It skips every line already logged, and logs every line it handles (added,
  already present, or skipped as an unknown test). Only the maintainer writes
  it. Reconcile drops a local flag line or test-exception line when it is
  logged for that file; this replaces "once main's shared file holds it" in
  21. The header line of an own variant/spelling file is never dropped (it
  equals the shared header, and `read_tsv_2col_to_dict` reads line 1 as the
  header). Why: a line the maintainer deletes or changes in a shared file must
  not come back, and the main copies of contributor files lag one cycle.
- G.b **Reserved-id test exceptions.** The merge script skips and reports
  exception ids ≥ `CONTRIB_ID_BASE` and does not log them. Reconcile drops a
  reserved-id exception line once the contributor's additions no longer hold
  that id (`get_next_id` reuses the id after processing).
- G.c **Logs travel with the words** (decision B). The maintainer's local
  Backup & Quit (`db/backup_tsv/backup_dpd_headwords_and_roots.py::git_commit`)
  adds `gui2/data/additions_added.json`, `corrections_added.json` and
  `contrib_lines_merged.json` to its path-limited commit. The server never runs
  it.
- G.d **Window order and rollback.** Capture the rollback before the pull: db,
  `HEAD`, and every delivered contributor file in `DPD_GUI2_DATA_DIR`. A failed
  dirty-tree check or pull skips reconcile, push and rebuild. A failed rebuild
  restores all three, so the overlay matches the old db. After a good rebuild,
  restore the tracked files the build rewrote (`db/sanskrit/root_families_sanskrit.tsv`
  every run, `CITATION.cff` on uposatha days) and log their names; the tree
  was clean before the pull, so only the build changed them. Otherwise the
  next night's dirty-tree check refuses.
- G.e **Push.** Base `contributions` on the server clone's `HEAD` after the
  pull (the commit reconcile read), not a fresh `origin/main`. Run
  `git fetch --prune <remote>` before `--force-with-lease`, so a branch GitHub
  deleted after a merge does not fail the lease. Copy only the delivered kinds
  (additions, corrections, user dictionary, checked, manual corrections,
  variants, spelling, test exceptions; never history, daily log, presets or
  stash), from one list shared by push, reconcile and the merge script. Push
  even when nothing is staged, so a discarded entry leaves the branch.
  Reconcile writes an emptied file, never deletes it.
- G.f **No pull requests** (decision C). The maintainer merges
  `contributions` straight into local `main` with one `just` recipe: fetch,
  merge `origin/contributions`, run the merge script, show its report. "The PR
  cannot conflict" in 22 is wrong: the branch can conflict when main's copy of
  a contributor file changed after the branch was built (processing). Skip
  that merge; the next night's branch is built on current main and is clean.
  Merge before processing to avoid it.
- G.g **Removing a contributor** (README procedure): run a window first,
  process or reject their entries, archive (not delete) their files (`*_<user>.*`),
  then remove their env, htpasswd and nginx files.

### H. Login
24. `scripts/server_contrib/nginx_contrib.conf.template`: HTTPS server, one
    `location /<user>/` per contributor with its own `auth_basic_user_file`,
    websocket headers, proxying to that user's local port.
25. `scripts/server_contrib/add_contributor.sh <user> <port> [extra tabs]`:
    writes the user's htpasswd file (asks for the password), their env file
    (`DPD_GUI2_USERNAME`, `DPD_GUI2_ROLE=contributor-server`,
    `DPD_GUI2_DATA_DIR`, `DPD_GUI2_TABS`, port) and their nginx location. It
    prints the URL to hand over. Removal is a documented procedure in
    `scripts/server_contrib/README.md`.

## Facts verified by reading the code (2026-10-29/30)
- Tabs: `gui2/main.py` builds 17 views keyed by index (`_view_builders`),
  labels in `tab_labels`, `_TAB_JUMP_KEYS` by index, Ctrl+S dispatch on
  `self.tabs.selected_index`, `_get_current_lemma` hard-codes indices 3 and 7,
  and Pass1Add's builder calls `self._view(2)`. No role check gates any tab.
- Transl (`translations_view.py`) and Bold Search (`bold_search_view.py`,
  `bold_search_controller.py`) contain no file or db writes.
- DB, √ and Infl write only through the six handlers in B.5. Their other
  buttons change the screen or the per-user presets file.
- `gui2/main.py::main(page)` builds a new `App`/`ToolKit` per page (per tab).
- `AdditionsManager` / `CorrectionsManager` hold the dict in memory and
  rewrite the whole file (`_save_dict`).
- `contrib_push.py`, `contrib_reconcile.py`, `absorption_check.py` and
  `maintenance_window.py` behave as described in Overview point 4.
- `.gitignore` lines 106-110 ignore the five per-user flag files.
  `contributor_files()` pushes only `additions_*` / `corrections_*` JSON.
- main tracks `gui2/data/additions_deva.json` and `corrections_deva.json`;
  both are `{}`.
- Pass2Add's addition flow: `clear_fields`, then every entry key including
  `id` goes to its `_add` field. `get_current_values` uses `get_next_id()`
  when `id` is empty.
- Pass1Add runs the same `GuiTestManager` popup, whose Add exception calls
  `DbTestManager.add_exception` (`db_tests/db_tests_manager.py:363`), which
  appends to `test.exceptions` and rewrites the TSV. Exceptions are checked at
  `db_tests_manager.py:240` (`headword.id in test.exceptions`).
- `db/db_helpers.py::_get_cached_engine` makes one engine per db per process,
  which gives one place to set `query_only`.
- htpasswd and openssl exist locally. nginx does not.

## Assumptions & uncertainties
- **Flet behind a path prefix** (`/alice/`) is untested. Flet may need a
  base-path setting. Probe on the server in contrib_4 Phase 4. Fallback: one
  subdomain per user (`alice.<ip-dashes>.sslip.io`), same nginx config shape.
- **Flet session events** (`on_disconnect`, `on_close`, reconnect on reload)
  are taken from `resources/flet-docs`, which may predate 1.0.1. Verify live.
  Risk: a closed tab may hold its session for up to 60 minutes and lock the
  user out that long. The user accepted this.
- **`query_only` with WAL**: assumed to allow reads with no write beyond what a
  reader needs. Tested on a small temp db, then live.
- **Merge formats** of the five flag files and the tests TSV are read from
  their writers during the work, not assumed here.
- **The `entry_hash` round trip**: the entry loaded on the desktop must hash the
  same as the server's copy. A test covers it.
- **Rebuild time** on the real VPS is still unknown (contrib_1 3.3).

## Constraints
- User 1 on desktop: unchanged, except the Reject button, the Add button
  leaving id empty, and the Cor button filling only changed fields.
- No secrets in the repo. htpasswd and env files exist only on the server.
- Project rules: ruff check --fix, ruff format,
  `uv run pyright --project /dev/null` for gui2/ and tests/ files, related
  pytest on every touched file, `just typecheck` at the end. Modern type hints,
  pathlib, no `__init__.py` re-exports.
- No git commands on the local repo. Sync tests use throwaway repos with
  `file://` remotes in a temp dir.

## How we'll know it's done
1. Unit tests: tab sets (base only, extras, hidden label ignored, desktop
   ignores it); tab-to-index mapping; each read-tab action refuses; the
   `query_only` net blocks a db write and allows reads; second session refused;
   per-user paths under `DPD_GUI2_DATA_DIR`; reserved ids; `_changed`; per-user
   test exceptions; `entry_hash` round trip; Reject; Cor fills only changed
   fields; the merge script; reconcile; push from a worktree; dirty-tree
   refusal.
2. A scripted local round trip with throwaway repos: contributor saves →
   window pushes → "maintainer" merges, processes one, rejects one, leaves one
   → window reconciles → only the pending one remains on the server and in the
   next PR. The PR merges with no conflict on the second and third cycles.
3. A live local web run as "alice" with extra tabs Bold Search + DB: exactly
   Pass1Auto, Pass1Add, Bold Search and DB show; shortcuts to other tabs do
   nothing; DB Save Changes refuses; a second tab is refused; saves land in
   `DPD_GUI2_DATA_DIR`.
4. A live desktop run as user 1: all 17 tabs, Reject works, Cor shows only
   changed fields, Add leaves id empty.
5. Full pytest suite and `just typecheck` pass.

## What's not included
- Opening any hidden tab to contributors, and the per-user P2A/New queues
  Pass2Add would need.
- Running nginx, certbot or systemd (contrib_4 and contrib_1 Phase 3).
- An in-app login screen.

**Amendment 2026-10-30 (review round, two independent reviewers).**
- All users share ONE flat data folder, `/var/lib/dpd/contrib_data`. The sync
  scripts glob one folder and the file names carry the user, so a per-user folder
  (`/var/lib/dpd/<user>`) made the nightly window find no files. Spec D.8 and
  G.g read "per-user folder" as "one folder, user in the file name".
- A failed `systemctl stop` refuses the window (an instance could still write
  the files it reads). After a rollback the db's `-wal`/`-shm` are removed.
  `last_built_commit` is written last.
- `_changed` lists only columns the form supplied (the form never sets dates,
  inflection tables, frequency data).
- A retired tab (C.7) also loses its keyboard handler.
