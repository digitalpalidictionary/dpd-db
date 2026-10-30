# Plan: contributor hardening — login, per-user tabs, safe sync

**Thread:** 20261030_contrib_5_hardening · **Spec:** `spec.md` (read first)
**GitHub issue:** [#215](https://github.com/digitalpalidictionary/dpd-db/issues/215) — commits reference `#215`
**Start only after** `20261023_contrib_2_edits_json` is finished. Finish this
thread before `20261023_contrib_3_preview_before_save` starts (both edit
`gui2/pass2_add_view.py`).

## Architecture Decisions
- **The tab decides what a contributor may do** (base / safe / read / hidden,
  spec table). The only per-user setting is the list of extra tabs, in the
  user's server env file (`DPD_GUI2_TABS`). No users file in the repo.
- **Tab gating keeps the original 17 indices internally.** The tab bar shows a
  subset; one position→index list maps between them. Every existing
  index-based lookup keeps its meaning, and the desktop gets the identity map.
- **Read tabs: a `read_only` flag on the three views**, checked at the top of
  their six write handlers. Ctrl+S calls the same handlers, so it needs no
  extra code.
- **`PRAGMA query_only` as the net** for any db write a contributor process
  reaches. Set once, in `db/db_helpers.py::_get_cached_engine`.
- **Server per-user files outside the repo** (`DPD_GUI2_DATA_DIR`), so pulls
  never meet a local copy of a file main tracks.
- **Positive "processed" signal for reconcile**: `(key, entry_hash)` in main's
  `*_added.json` logs, and line presence in main's shared files. No snapshots.
- **Push from a worktree, branch reset to main each night, force-with-lease.**
  The PR can never conflict.
- New shared helper `tools/contrib_entry.py` (used by gui2 and
  `scripts/server_contrib/`). Not abstracted: no generic "role/permission"
  layer.
- Tests mirror source paths. Sync tests build throwaway git repos with
  `file://` remotes under `tmp_path`.

## Model Strategy

| Phase | Model | Why |
|---|---|---|
| 1 Tabs, read tabs, read-only db, one session | Sonnet | Edits that follow existing patterns, with tests |
| 2 Contributor-side data | Sonnet | Small, local changes with tests |
| 3 Maintainer review side | Sonnet | Small, local changes with tests |
| 4 Sync design check | **Opus** | Analysis only: walk the redesign through every failure case before code |
| 5 Sync implementation | Sonnet | Writes the design that Phase 4 checked |
| 6 Login files | Sonnet | Template and shell script, tested in a temp dir |
| 7 Live checks and finish | Sonnet | Runs checks with the user, docs |

Run `/kamma:3-review` for this thread on **Opus** (security and sync).

## Phase 1 — Tabs, read tabs, read-only db, one session — *Sonnet*
- [x] 1.1 `gui2/contributor_tabs.py`: `BASE_TABS = ("Pass1Auto", "Pass1Add")`,
      `SAFE_TABS = ("Transl", "Bold Search")`, `READ_TABS = ("DB", "√", "Infl")`.
      `resolve_extra_tabs() -> list[str]` parses `DPD_GUI2_TABS`.
      `allowed_tabs(all_labels, extras) -> tuple[list[int], set[int]]` returns the
      visible original indices (in tab order) and the read-only indices; it
      logs and drops hidden or unknown labels.
      → verify: `uv run pytest tests/gui2/test_contributor_tabs.py`: base only;
      base + safe + read; a hidden label (`Pass2Add`) and a typo dropped with a
      warning; empty env var.
- [x] 1.2 `gui2/main.py`: when `is_headless_server()`, build the tab bar and
      bodies from the visible indices only, and keep a position→index list.
      Map through it everywhere `self.tabs.selected_index` or `_views`/
      `_mounted_tabs` is used: `_on_tab_activated`, `_ensure_tab_built`,
      Ctrl+S, Alt+X, Alt+letter (ignore keys whose tab is not visible),
      Alt+arrow, `_get_current_lemma`, the warm-up order (visible only), and
      the shortcuts dialog. Pass1Add's builder still calls `self._view(2)`. The
      desktop uses the identity list, so nothing changes there. Set
      `view.read_only = True` on read-tab views when they are built.
      → verify: extend `tests/gui2/test_main.py`: with role contributor-server
      and `DPD_GUI2_TABS="Bold Search,DB"`, exactly 4 tab labels in order; Alt+P
      (Pass2Pre) does nothing; Alt+D selects DB; Ctrl+S on DB calls the guarded
      handler. Existing `test_main.py` tests still pass (desktop path).
- [x] 1.3 Read tabs: add `read_only: bool = False` to `FilterTabView`,
      `RootsTabView` and `InflectionTemplatesTabView`. Check it at the top of
      `_save_changes_clicked`, `_save_root`, `_delete_root`, `_save_template`,
      `_rename_template`, `_delete_template`: show "Read only: you can look but
      not save here." and return.
      → verify: one test per handler with `read_only=True`: no db call
      (mocked `db_manager` / session), the message is shown. With `False`, the
      existing tests still pass.
      DRIFT (found while doing 1.3): the DB tab's on-screen Save Changes
      button is inside `FilterComponent` and bypasses `_save_changes_clicked`.
      `FilterComponent` got a `read_only` param, checked at the top of
      `_save_changes`; `FilterTabView` and `InflectionTemplatesTabView` pass it
      when they create a component. Tests: `tests/gui2/test_read_only_views.py`
      (14 pass; with the guards reverted, 7 fail).
- [x] 1.4 Read-only db: in `db/db_helpers.py::_get_cached_engine`, when
      `tools.server_mode.is_headless_server()`, attach a `connect` event that
      runs `PRAGMA query_only = ON`. In `gui2/database_manager.py` (the decon
      cache save, ~line 329), add `self.db_session.rollback()` in the `except`.
      → verify: `tests/db/test_db_helpers_query_only.py` on a small temp WAL db
      (not `dpd.db`): with `DPD_GUI2_ROLE=contributor-server`, an insert raises
      and a select works; without it, the insert works. Clear the engine cache
      between cases. A test that the decon cache failure leaves the session
      usable (a query after it works).
- [x] 1.5 One session per process: a module-level guard in `gui2/main.py`.
      `main(page)` claims it, or shows "This app is already open in another tab
      or window." and returns without building `App`. `page.on_disconnect` and
      `page.on_close` release it when the page is the holder. Applies to every
      role (desktop has one window anyway).
      → verify: unit test of the guard (claim, refuse, release, claim again).
      The live reload and second-tab check is 7.1.
- [x] 1.6 Phase gate: `uv run ruff check --fix`, `uv run ruff format`,
      `uv run pyright --project /dev/null` (gui2/, tests/) or `uv run pyright`
      (db/, tools/) on every touched file, then `uv run pytest tests/gui2 tests/db`.
      Report only, no commit.
      → verify: all clean. Paste the counts here.
      RESULT (2026-10-30): ruff check + format clean, pyright 0 errors (scripts,
      tools, db; tests via `--project /dev/null`), `just typecheck` 0 errors
      (fixed one pyrefly error in Phase 1's `tests/gui2/test_read_only_views.py`).
      `uv run pytest tests/scripts/server_contrib tests/gui2 tests/tools tests/db
      tests/db_tests -m "slow or not slow"` = 1803 passed (absorption tests deleted).
      Drift recorded: `WindowSteps` now has `pull(config)` and `push(config) -> str`
      steps; `WindowConfig` has `worktree`, no `snapshot_dir`; `--data-dir`
      defaults to `DPD_GUI2_DATA_DIR`; rollback keeps all delivered kinds.
      RESULT: ruff check + format clean on all 11 files; pyright clean on db/ and
      tools/ files, tests and new gui2 module; `uv run pytest tests/gui2 tests/db`
      = 806 passed. PRE-EXISTING — NOT CAUSED BY THIS THREAD: pyright
      `--project /dev/null` Flet typing errors in gui2/main.py (24),
      filter_component (9), filter_tab_view (22), roots_tab_view (14),
      inflection_templates_tab_view (24); same counts at HEAD (gui2 is excluded
      from the real gate).

## Phase 2 — Contributor-side data — *Sonnet*
- [x] 2.1 `Gui2Paths.for_user`: when `DPD_GUI2_DATA_DIR` is set, every per-user
      path it routes (and the new one in 2.4) goes into that folder. Unset →
      `gui2/data/` as today. User 1 unaffected.
      → verify: `tests/gui2/test_paths.py`: with and without the env var, for
      "alice" and "1".
- [x] 2.2 Reserved ids: `DatabaseManager.get_next_id` with an overlay set
      returns `max(10_000_000, own additions max) + 1`. Name the constant
      `CONTRIB_ID_BASE`. No overlay → unchanged.
      → verify: `tests/gui2/test_database_manager_overlay.py`: first contributor
      id is 10_000_001, next follows own max; user 1 unchanged.
- [x] 2.3 `_changed`: in `gui2/save_router.py`, the contributor correction
      branch reads the db row without the overlay
      (`db_session.get(DpdHeadword, word.id)`) and lists the columns whose
      values differ. `CorrectionsManager.update_corrections` takes it and stores
      `_changed` in the entry.
      → verify: `tests/gui2/test_save_router.py`: a changed `meaning_1` gives
      `_changed == ["meaning_1"]`; a re-edit of an own correction compares with
      the db row, not the earlier correction.
- [x] 2.4 Per-user test exceptions: `Gui2Paths.db_test_exceptions_path`
      (contributor only: `db_test_exceptions_{u}.tsv`). `DbTestManager` takes an
      optional own-exceptions path. With it, `load_tests` adds the file's ids to
      each test's `exceptions`, and `add_exception` appends `test_name<TAB>id`
      to that file instead of calling `save_tests`. The toolkit passes the path
      for contributors only.
      → verify: test that a contributor `add_exception` leaves
      `db_tests/db_tests_columns.tsv` byte-identical (checksum), writes the
      per-user line, and the next `load_tests` treats the id as an exception.
      User 1 path unchanged.
- [x] 2.5 Username: `UsernameManager` keeps the username the toolkit routed
      paths with (`resolve_username() or "1"` at start-up). `is_not_primary()`
      compares that. The first-run dialog text adds "This takes effect the next
      time you start the app."
      → verify: `tests/gui2/test_user.py`: no username → `is_not_primary()` is
      False and saves go to the db path; env "alice" → True.
- [x] 2.6 Phase gate as 1.6, then `uv run pytest tests/gui2 tests/db_tests`.
      → verify: all clean. Paste the counts here.
      RESULT: ruff check + format clean on 13 files; pyright clean except 3
      PRE-EXISTING Flet typing errors in gui2/user.py (same 3 at HEAD);
      `uv run pytest tests/gui2 tests/db_tests tests/db` = 905 passed.

## Phase 3 — Maintainer review side — *Sonnet*
- [x] 3.1 `tools/contrib_entry.py::entry_hash(entry: dict) -> str`.
      → verify: a test writes an entry with `AdditionsManager.add_additions`,
      reloads the file the way the primary loader does, and gets the same hash.
- [x] 3.2 `save_processed_addition` / `save_processed_correction` take the
      original entry and log `_source_key` and `_source_hash`. `pass2_add_view`
      passes `self.current_addition` / `self.current_correction`.
      → verify: manager tests: the log entry has both fields and the hash
      matches the original entry, not the edited word.
- [x] 3.3 Reject: `reject(origin_path, source_key, original_entry)` on both
      managers: log `_source_key`, `_source_hash`, `_contributor`, `lemma_1`,
      `"_rejected": true`, then remove the key from the origin file. A "Reject"
      button next to "Add to DB" in `pass2_add_view`, visible only while
      `flags.addition` or `flags.correction` is set with a contributor origin;
      it calls `reject`, clears the flags and the form.
      → verify: manager tests (log + removal, other keys kept). Live in 7.2.
- [x] 3.4 Proposal fields: a small pure helper `proposal_fields(entry, kind)`
      in `gui2/pass2_add_view.py` (or a sibling module): additions drop `id`;
      corrections with `_changed` keep only those fields (plus nothing else);
      corrections without `_changed` keep all. `_click_additions_button` and
      `_click_corrections_button` use it.
      → verify: tests for the three cases.
- [x] 3.5 `scripts/server_contrib/merge_contrib_files.py`: for the user
      dictionary, sandhi checked, sandhi corrections, variant readings,
      spelling mistakes and test exceptions, read each writer first (paths in
      `gui2/paths.py`, writers in `tools/spelling.py`, `gui2/mixins.py`,
      `gui2/sandhi_files_manager.py`, `gui2/variants.py`, `gui2/spelling.py`,
      `db_tests/db_tests_manager.py`) and record each format and sort rule in
      the module docstring. Merge every contributor file's new lines into the
      shared file in that format and order, and print what was added per file.
      Contributor files are left as they are (the server drops merged lines).
      → verify: tests with fixtures copied from real lines of each shared file:
      lines added once, order kept, a second run adds nothing, the tests TSV
      gains the id in the right test's exceptions.
- [x] 3.6 Phase gate as 1.6, then `uv run pytest tests/gui2 tests/scripts tests/tools`.
      → verify: all clean. Paste the counts here.
      RESULT: ruff check + format clean on 12 files; pyright clean on all
      except gui2/pass2_add_view.py, 50 PRE-EXISTING Flet typing errors (same
      50 at HEAD). `uv run pytest tests/gui2 tests/scripts tests/tools tests/db
      tests/db_tests` = 1927 passed, 7 deselected (slow).
      DECISION TO CONFIRM (3.4): a correction with `_changed` shows only the
      changed fields as proposals, per spec. That drops the contributor's
      `comment` from the proposal side. Additions keep it.

## Phase 4 — Sync design check — *Opus*
⚠️ MODEL SWITCH REQUIRED (Opus): analysis only, before any sync code.
- [x] 4.1 Walk spec section G, plus the merge script from 3.5, through each
      case below, and write a table here (case → what the window does → where
      each entry ends up → safe?):
      PR not merged yet; merged, not processed; processed; rejected; re-edit
      after push; re-edit after processing (same stable key); two contributors
      editing the same word; a flag line merged; a flag line you later delete
      from the shared file; pull fails (dirty tree, network); push fails;
      rebuild fails (rollback); main unchanged (no rebuild); the server down
      for a week; a contributor deleted (`remove` procedure); an entry whose
      word you deleted on main.
      → verify: every row is "safe", or the spec and the Phase 5 tasks are
      amended (with a dated note) before Phase 5 starts.

      RESULT (2026-10-30, Opus). Read from the code: `gui2/additions_manager.py`,
      `gui2/corrections_manager.py` (processing and Reject remove the key from
      main's contributor file), `merge_contrib_files.py`, the flag-file readers
      (`tools/spelling.py`, `gui2/variants.py`, `gui2/spelling.py`,
      `gui2/database_manager.py` read shared + own; `SandhiFileManager` reads
      own only, for its duplicate check), `tools/tsv_read_write.py`,
      `maintenance_window.py`, `generate_components_server.py`,
      `db/backup_tsv/backup_dpd_headwords_and_roots.py::git_commit`,
      `gui2/dpd_fields.py` (lemma check). F-numbers refer to the list below.

      | # | Case | What the window does | Where the entry ends up | Safe? |
      |---|---|---|---|---|
      | 1 | PR not merged yet | pull; `(key, hash)` not in logs → kept; branch = main + server files | server + open PR | yes |
      | 2 | Merged, not processed | kept (not in logs); main already holds the same bytes → no diff for it | server + main's contributor file | yes |
      | 3 | Processed | desktop logs `(key, hash)`, removes key from main's copy; window drops it; PR has no diff for it | log + db (after rebuild) | yes, if the log and the TSV backup reach main together (F2) |
      | 4 | Rejected | as 3, with `_rejected` | log only | yes |
      | 5 | Re-edit after push | server holds v2; PR carries v2. If v1 was processed first, v2's hash is not in the log → kept, re-reviewed. A PR built before that processing edits X while main deleted X → that PR conflicts | server, re-reviewed | yes, but "the PR cannot conflict" is wrong (F3) |
      | 6 | Re-edit after processing, same key | correction: v2 re-reviewed, fields v1 already set show no change. Addition: arrives again; Pass2Add refuses "lemma already in db" → Reject | server until rejected | yes |
      | 7 | Two contributors, same word | keys differ (`alice_N`, `bob_N`); Cor fills each one's `_changed` only; a second addition hits the lemma check. Flag files: bob's variant value overwrites alice's, reported "(was …)"; two sandhi splits are both appended | both reviewed separately | yes |
      | 8 | Flag line merged | merge script adds it; spec rule G.21 drops each local line the shared file holds — **including the header line** of the own variant/spelling file (same header as the shared one). `read_tsv_2col_to_dict` then reads the first pair as the header: that pair is lost on the server and never merged | — | **no** (F1) |
      | 9 | Flag line you later delete from the shared file | if deleted before the server's next reconcile, the server keeps it and the next PR sends it again. Even after, `merge_all` re-reads every contributor file still on main (they lag one cycle) and re-adds it. Same for a variant value you change | comes back | **no** (F1) |
      | 10 | Pull fails (dirty tree, network) | must skip reconcile, push and rebuild; FAILED; instances start | server only, retried next night | yes, if push is skipped too (F4) |
      | 11 | Push fails | logged; rebuild still runs; next night retries | server | yes, except the lease: once GitHub deletes the branch after a merge, the stale tracking ref makes every later `--force-with-lease` fail (F5) |
      | 12 | Rebuild fails (rollback) | plan 5.3 restores db + HEAD only, but reconcile already dropped accepted entries → the contributor's accepted word is in neither the overlay nor the old db for a night; they may add it again | — | **no** (F4) |
      | 13 | Main unchanged | no rebuild; reconcile drops nothing new; push sends new work | server + PR | yes |
      | 14 | Night after a good rebuild | the lean rebuild rewrites tracked `db/sanskrit/root_families_sanskrit.tsv` (every run) and `CITATION.cff` (uposatha days). The dirty-tree check then refuses every later pull | — | **no** (F6) |
      | 15 | Server down a week | no windows; on return one normal window with a bigger pull | server | yes |
      | 16 | Contributor deleted | push copies only existing users' files; their files stay on main and processing empties them. Unpushed work is lost if the data folder is deleted first | main | yes, with the README procedure in F7 |
      | 17 | Entry whose word you deleted on main | correction: Cor finds no db word, the form shows only the changed fields → Reject; the server overlay shows it until then. Accepted addition later deleted: logged → dropped | log | yes |
      | 18 | Contributor test exceptions (extra) | G.21's "shared file holds the line" cannot match `test<TAB>id` against the tests TSV. Pass1Add tests a new word under its reserved id; that id means nothing on main, and once the addition is processed `get_next_id` hands the same id (10_000_001…) to the next new word, so the old exception hides a real failure | — | **no** (F8) |
      | 19 | Main moves during the window (extra) | 5.2 fetches `origin/main` again in the worktree. A main push between the server's pull and that fetch gives a PR based on newer main than reconcile saw → it re-adds entries processed in that gap | main | **no** (F9) |

      Findings and proposed amendments (not yet applied; decisions A–D with
      the user):
      - F1 (rows 8, 9, 18) → decision A. Proposed: the merge script keeps a
        tracked log `gui2/data/contrib_lines_merged.json` =
        `{contributor_file_name: [line, …]}`. It skips any line already logged
        and logs every line it handles (added, already present, or skipped as
        unknown test). Reconcile drops a local line when it is logged for that
        file. The header line of an own variant/spelling file is never dropped.
        Only the maintainer writes the log, so it never conflicts.
      - F2 (row 3) → decision B. `git_commit` in Backup & Quit commits only the
        TSV parts. Proposed: add `additions_added.json`,
        `corrections_added.json` (and the F1 log) to its path-limited commit.
      - F3 (row 5): amend spec G.22. A PR can conflict when main's copy of a
        contributor file changed after the PR was built (processing). Skip a
        conflicted PR; the next night's PR is built on current main and is
        clean. README: merge the open PR before processing.
      - F4 (rows 10, 12): 5.3 captures the rollback before the pull: db, HEAD
        and every delivered contributor file in `DPD_GUI2_DATA_DIR` (all kinds,
        not only JSON). A failed pull skips reconcile, push and rebuild. A
        failed rebuild restores the pre-reconcile files.
      - F5 (row 11): 5.2 runs `git fetch --prune <remote>` before the push.
      - F6 (row 14): 5.3, after a good rebuild, lists tracked files the build
        changed (`git status --porcelain --untracked-files=no`), logs them and
        restores them (`git checkout -- <names>`; the tree was clean before
        the pull, so only the build changed them).
      - F7 (row 16) → decision C (PR lifecycle). After a PR is merged GitHub
        does not reopen it on the next push; contrib_1's "opened once and stays
        open" no longer holds. README: either open a new PR each time, or merge
        the branch locally (`git fetch && git merge origin/contributions`).
        Remove procedure: run a window first, process or reject their entries,
        archive (not delete) their data folder, then remove env, htpasswd and
        nginx files.
      - F8 (row 18): the merge script skips and reports exception ids ≥
        `CONTRIB_ID_BASE` (not logged). Reconcile drops a reserved-id
        exception line when the contributor's additions no longer hold that id.
      - F9 (row 19): 5.2 bases `contributions` on the server clone's `HEAD`
        after the pull (the commit reconcile read), not a fresh `origin/main`.
      - F10 (5.2 wording): copy only the delivered kinds (additions,
        corrections, user dictionary, checked, manual corrections, variants,
        spelling, test exceptions), never history, daily log, presets or
        stash files; one shared list for push, reconcile and the merge script.
        Push even when nothing is staged, so a discarded entry leaves an open
        PR. Reconcile writes an emptied file, never deletes it.
      - D (carried from 3.4): no change needed. Both save paths pass the
        word's own `comment` field, so a changed comment is already in
        `_changed` and shows; an unchanged one is the existing text.

      DECISIONS (user, 2026-10-30): A = merged-lines log; B = Backup & Quit
      commits the logs (local only, the server never runs it); C = no pull
      requests, merge `contributions` straight into local main with one `just`
      recipe. All findings applied to spec (amendment block after G.23) and to
      Phase 5 below.

## Phase 5 — Sync implementation — *Sonnet*
⚠️ MODEL SWITCH REQUIRED (Sonnet): mechanical execution resumes.
Amended 2026-10-30 after the Phase 4 check (spec G.a–G.g win over G.19–22).
- [x] 5.0 Shared list + merge script + backup + recipe (spec G.a, G.b, G.c, G.f):
      one module-level list of delivered kinds (glob pattern, kind) used by
      push, reconcile and the merge script. Merge script: read/write
      `gui2/data/contrib_lines_merged.json`, skip logged lines, log every
      handled line, skip and report exception ids ≥ `CONTRIB_ID_BASE`
      (not logged). `git_commit` in
      `db/backup_tsv/backup_dpd_headwords_and_roots.py` adds the two
      `*_added.json` logs and `contrib_lines_merged.json` to `files_to_add`
      (only those that exist). A `just` recipe (check `just --list` for the
      naming style): `git fetch <remote>`, `git merge origin/contributions`,
      then the merge script.
      DONE 2026-10-30: list + `delivered_files` in `tools/contrib_entry.py`;
      `Gui2Paths.contrib_lines_merged_path`; recipe `just contrib-merge`; the
      merge script's `merge_all` takes `log_path` (None = no memory). The merge
      functions now take the unlogged lines, not a path. The header line of a
      variant/spelling file is skipped and not logged.
      → verify: extend `tests/scripts/server_contrib/test_merge_contrib_files.py`:
      a line deleted from the shared file after a merge is not re-added on a
      second run; a changed variant value is not changed back; a reserved id
      is reported and not merged or logged. A test that `git_commit` passes
      the log paths (mocked `subprocess.run`).
- [x] 5.1 Rewrite `scripts/server_contrib/contrib_reconcile.py`:
      `reconcile_entries(local, processed: set[tuple[str, str]])` and
      `reconcile_lines(local_lines, merged_lines, keep_header: bool)`;
      reserved-id exception lines are dropped when the contributor's additions
      no longer hold that id. `reconcile_all(project_root, data_dir)` reads
      main's `*_added.json` logs and `contrib_lines_merged.json` from the
      working tree (the server is on main after the pull) and rewrites the
      contributor files atomically (keep `write_json_dict`; an emptied file is
      written, never deleted). Remove snapshot code.
      → verify: rewritten `tests/scripts/server_contrib/test_contrib_reconcile.py`
      covers Phase 4 rows 1–9, 17, 18: including an own variant file whose
      header survives and whose first pair is kept.
- [x] 5.2 Rewrite `scripts/server_contrib/contrib_push.py`:
      `push_contributions(project_root, data_dir, worktree, remote)`: create the
      worktree once (`git worktree add`), then `git fetch --prune <remote>`,
      `checkout -B contributions <server clone HEAD sha>` (the commit reconcile
      read, not a fresh `origin/main`), copy the delivered kinds only from
      `data_dir` into `worktree/gui2/data/`, `git add -f` those paths only,
      commit if anything is staged, and always `git push --force-with-lease
      <remote> contributions`.
      → verify: test with a bare `file://` origin: first push creates the
      branch; a second push after main moved is a fast, conflict-free reset;
      nothing changed → no commit, branch equals the base; gitignored kinds
      arrive; history/daily-log/stash files do not; the branch deleted on the
      remote → the next push still succeeds; origin/main moved after the pull →
      the branch is based on the pulled commit.
- [x] 5.3 Rewrite `scripts/server_contrib/maintenance_window.py` to spec G.20
      and G.d: capture the rollback first (db, `HEAD`, delivered contributor
      files of every kind in the data dir), dirty-tree check
      (`git status --porcelain --untracked-files=no`, refuse and log names),
      `git pull --ff-only` + submodule update; a failed check or pull skips
      reconcile, push and rebuild. Then reconcile, push, rebuild only if `HEAD`
      differs from `logs/last_built_commit` (write it after a good build). A
      failed rebuild restores db, `HEAD` and the contributor files. After a
      good rebuild, log and restore the tracked files the build changed
      (`git checkout -- <names>` on the server clone). Start instances in
      `finally`. Add `--data-dir` and `--worktree` options.
      → verify: rewritten `tests/scripts/server_contrib/test_maintenance_window.py`
      with stub steps: dirty tree → no pull, no push, FAILED, instances
      restarted; pull failure → no reconcile, no push; main unchanged → no
      rebuild; rebuild failure → db, HEAD and pre-reconcile contributor files
      restored; push failure → logged, rebuild still runs; a stub rebuild that
      modifies a tracked file → the file is restored and the next window's
      dirty-tree check passes.
- [x] 5.4 Delete `scripts/server_contrib/absorption_check.py` and its test.
      Update `scripts/server_contrib/README.md` (no pull requests: the `just`
      recipe; merge before processing; a conflicted merge is skipped, the next
      night's branch is clean; the remove procedure of spec G.g) and
      `config_server.md`. `rg --hidden "absorption|last_pushed|snapshot_dir"`
      over the repo.
      → verify: the sweep shows no live references (archive and kamma notes
      excepted).
- [x] 5.5 Round trip: `tests/scripts/server_contrib/test_round_trip.py` with a
      bare origin, a "server" clone + worktree, and a "maintainer" clone. Three
      cycles: contributor files written → window → maintainer merges the
      branch into main, processes one (`save_processed_*`), rejects one, leaves
      one, runs the merge script, deletes one merged flag line from the shared
      file, pushes main → window. Mark `slow` if needed.
      → verify: after each cycle only the pending entry remains on the server
      and on the contributions branch; each merge into main has no conflict;
      merged flag lines leave the server's files; the deleted flag line does
      not come back.
- [x] 5.6 Phase gate as 1.6, then `uv run pytest tests/scripts/server_contrib -m "slow or not slow"`.
      → verify: all clean. Paste the counts here.

## Phase 6 — Login files — *Sonnet*
- [x] 6.1 `scripts/server_contrib/nginx_contrib.conf.template`: one HTTPS
      `server` block with a `include /etc/nginx/dpd/*.conf;` line, and a
      per-user `location` snippet template: `auth_basic`,
      `auth_basic_user_file /etc/nginx/dpd/<user>.htpasswd`,
      `proxy_pass http://127.0.0.1:<port>/`, `proxy_http_version 1.1`,
      Upgrade/Connection headers, long read timeout.
      → verify: on the server later, `nginx -t` (contrib_4 Phase 4). Here: the
      template renders with `sed` for a test user, by eye.
      DONE 2026-10-30. Drift: two files. `nginx_contrib.conf.template` holds the
      server block (`@SERVER_NAME@`); the per-user location is its own
      `nginx_contrib_user.conf.template` (`@USER@`, `@PORT@`), which
      `add_contributor.sh` renders with `sed`. Rendered by eye for alice: OK.
      OPEN RISK (not verified): the location is `/<user>/` with a trailing-slash
      `proxy_pass`. Whether a Flet web app works under a path prefix (static
      base href, asset URLs, websocket path) is untested and cannot be proven
      without nginx; `FLET_WEB_APP_PATH` exists in Flet but sets the page name.
      Prove it in contrib_4 Phase 4. Fallback if it fails: one sub-domain per
      user (`<user>.<host>`, `location /`), same script, one template change.
- [x] 6.2 `scripts/server_contrib/add_contributor.sh <user> <port> [tabs]`
      with `--root <dir>` (default `/`) for test runs: `htpasswd -B -c` (prompts
      for the password), the env file (`/etc/dpd/<user>.env`), the nginx
      location (`/etc/nginx/dpd/<user>.conf`), `mkdir` the data folder; prints
      the URL and the commands to enable the unit and reload nginx. Refuses an
      existing user or a port in use by another env file. Removal steps go in
      `scripts/server_contrib/README.md`.
      → verify: `bash -n`; a run with `--root <tmp>` and the password piped via
      `htpasswd -i` mode creates the three files with the right contents; a
      second run for the same user refuses.
      DONE 2026-10-30, run by hand in the scratchpad with `--root`, password
      piped: creates `etc/dpd/alice.env`, `etc/nginx/dpd/alice.htpasswd`
      (bcrypt `$2y$`), `etc/nginx/dpd/alice.conf`, `var/lib/dpd/alice`; env holds
      USERNAME, ROLE, DATA_DIR, TABS (quoted), `FLET_FORCE_WEB_SERVER=true`,
      `FLET_SERVER_PORT`. Refused: same user again, same port for another user,
      username `1` (the maintainer). A refused run creates nothing. Run
      the gui2 web server as `uv run python gui2/main.py` with that env file.
      No automated test: the script is root-path shell glue, checked by hand.
- [x] 6.3 Phase gate: `bash -n` on the script, ruff/pyright on any Python.
      → verify: clean. `bash -n` OK; no Python added in this phase.

## Phase 7 — Live checks and finish — *Sonnet*
- [x] 7.1 Live local web run WITH the user, in their terminal:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && DPD_GUI2_USERNAME=alice DPD_GUI2_ROLE=contributor-server DPD_GUI2_TABS="Bold Search,DB" DPD_GUI2_DATA_DIR=<scratchpad>/alice FLET_FORCE_WEB_SERVER=true FLET_SERVER_PORT=8551 uv run python gui2/main.py`
      (not `flet run`: it starts in `gui2/.flet/storage/data` and breaks every
      relative path; corrected 2026-10-30).
      Check: exactly Pass1Auto, Pass1Add, Bold Search, DB; Alt shortcuts to
      other tabs do nothing; DB Save Changes refuses; a Pass1Add save lands in
      the data folder; the db row count is unchanged
      (`sqlite3 dpd.db "select count(*) from dpd_headwords"` before/after); a
      reload keeps working; a second tab is refused; after closing the tab, how
      long until a new tab is allowed.
      → verify: every item logged here with the observed result.
- [x] 7.1a Reload fix (found in 7.1, 2026-10-30): `claim_session` in `gui2/main.py`
      always takes over; the old page is retired with the "already open"
      message. Spec C.7 amended. Tests in `tests/gui2/test_main.py` rewritten.
      → verify: pytest on `tests/gui2/test_main.py`; then F5 live, twice.
      LIVE 7.1 results so far (user, 2026-10-30): tabs = exactly Pass1Auto,
      Pass1Add, Bold Search, DB OK. Alt+number opens no hidden tab (Chrome
      reacts instead; logged in problem_children). DB Save Changes refuses OK
      (user wants it greyed out; logged in problem_children). Pass1Add save wrote
      `additions_alice.json` (id 10000001), headword count stayed 89765 OK.
      F5 first FAILED (old session never released), fixed by 7.1a, then F5 OK twice.
      Own word after reload: loads from Pass1Add history (overlay works); not in
      the DB tab search. By design; user decided 2026-10-30: drop, the DB tab
      shows only the real db.
      Second tab: with 7.1a the newest tab takes over; the old tab loses its tabs
      and shows "already open" (blue top bar and bottom message stay; checked
      headless on the real app, port 8602, 2026-10-30). User decision: keep ONE
      tab, newest wins; the leftover bar is fine. "How long until a new tab is
      allowed" is moot: a new tab is always allowed.
      7.1 DONE.
- [x] 7.2 Live desktop run as user 1 WITH the user, after backing up `dpd.db` to
      the scratchpad: all 17 tabs; load a hand-made contributor addition and
      correction (with `_changed`) from a test `additions_test.json` /
      `corrections_test.json`; Add leaves id empty; Cor fills only changed
      fields; Reject logs and removes; a processed save logs `_source_hash`.
      Remove the test files and log entries after.
      → verify: every item logged here.
      LIVE 7.2 results (user, 2026-10-30; `dpd.db` backed up with `sqlite3 .backup`
      to the scratchpad, restored afterwards, integrity ok, 89765 headwords):
      all 17 tabs OK. Add: id field empty, no id proposal, other fields as red
      proposals OK. Cor: only `meaning_1` proposed (`_changed`) OK. Reject on a
      correction: "Rejected dhamma 1.01", row logged with `_rejected: true`,
      entry removed from the file, db row unchanged OK. Real save of an addition:
      worked, new word got the next real id (90369), log row carries
      `_source_key` and `_source_hash` OK. NOT TESTED LIVE: Reject on an addition
      (the app had already taken it from its in-memory queue; the unit test
      `tests/gui2/test_pass2_add_reject.py` covers it). Cleanup done: test files,
      the two test log rows and the test history entry removed.
- [x] 7.3 Finish (contrib_1's spec and plan already carry the "superseded by
      contrib_5" notes, added 2026-10-30). Update `gui2/README.md` (contributor tabs, read tabs),
      `scripts/server_contrib/README.md` (new window, push, merge script, add
      and remove a contributor), `kamma/tech.md` (env vars). Run `just
      typecheck`, `uv run pytest tests/` and `graphify update .`.
      → verify: all pass. Paste the counts here.

      RESULT (2026-10-30): docs done: `gui2/README.md` (contributor server tabs
      section), `scripts/server_contrib/README.md` (rewritten in Phase 5),
      `kamma/tech.md` (env vars). `just typecheck` 0 errors. `uv run pytest tests/`
      = 2636 passed, 12 deselected (slow). Ruff + format clean on all 43 touched
      .py files (the repo has 169 other ruff errors in untouched files; not this
      thread). `graphify update .` done: 27777 nodes, 47715 edges; old snapshots pruned.
