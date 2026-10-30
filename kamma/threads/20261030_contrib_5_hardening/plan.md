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
- [ ] 1.1 `gui2/contributor_tabs.py`: `BASE_TABS = ("Pass1Auto", "Pass1Add")`,
      `SAFE_TABS = ("Transl", "Bold Search")`, `READ_TABS = ("DB", "√", "Infl")`.
      `resolve_extra_tabs() -> list[str]` parses `DPD_GUI2_TABS`.
      `allowed_tabs(all_labels, extras) -> tuple[list[int], set[int]]` returns the
      visible original indices (in tab order) and the read-only indices; it
      logs and drops hidden or unknown labels.
      → verify: `uv run pytest tests/gui2/test_contributor_tabs.py`: base only;
      base + safe + read; a hidden label (`Pass2Add`) and a typo dropped with a
      warning; empty env var.
- [ ] 1.2 `gui2/main.py`: when `is_headless_server()`, build the tab bar and
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
- [ ] 1.3 Read tabs: add `read_only: bool = False` to `FilterTabView`,
      `RootsTabView` and `InflectionTemplatesTabView`. Check it at the top of
      `_save_changes_clicked`, `_save_root`, `_delete_root`, `_save_template`,
      `_rename_template`, `_delete_template`: show "Read only: you can look but
      not save here." and return.
      → verify: one test per handler with `read_only=True`: no db call
      (mocked `db_manager` / session), the message is shown. With `False`, the
      existing tests still pass.
- [ ] 1.4 Read-only db: in `db/db_helpers.py::_get_cached_engine`, when
      `tools.server_mode.is_headless_server()`, attach a `connect` event that
      runs `PRAGMA query_only = ON`. In `gui2/database_manager.py` (the decon
      cache save, ~line 329), add `self.db_session.rollback()` in the `except`.
      → verify: `tests/db/test_db_helpers_query_only.py` on a small temp WAL db
      (not `dpd.db`): with `DPD_GUI2_ROLE=contributor-server`, an insert raises
      and a select works; without it, the insert works. Clear the engine cache
      between cases. A test that the decon cache failure leaves the session
      usable (a query after it works).
- [ ] 1.5 One session per process: a module-level guard in `gui2/main.py`.
      `main(page)` claims it, or shows "This app is already open in another tab
      or window." and returns without building `App`. `page.on_disconnect` and
      `page.on_close` release it when the page is the holder. Applies to every
      role (desktop has one window anyway).
      → verify: unit test of the guard (claim, refuse, release, claim again).
      The live reload and second-tab check is 7.1.
- [ ] 1.6 Phase gate: `uv run ruff check --fix`, `uv run ruff format`,
      `uv run pyright --project /dev/null` (gui2/, tests/) or `uv run pyright`
      (db/, tools/) on every touched file, then `uv run pytest tests/gui2 tests/db`.
      Report only, no commit.
      → verify: all clean. Paste the counts here.

## Phase 2 — Contributor-side data — *Sonnet*
- [ ] 2.1 `Gui2Paths.for_user`: when `DPD_GUI2_DATA_DIR` is set, every per-user
      path it routes (and the new one in 2.4) goes into that folder. Unset →
      `gui2/data/` as today. User 1 unaffected.
      → verify: `tests/gui2/test_paths.py`: with and without the env var, for
      "alice" and "1".
- [ ] 2.2 Reserved ids: `DatabaseManager.get_next_id` with an overlay set
      returns `max(10_000_000, own additions max) + 1`. Name the constant
      `CONTRIB_ID_BASE`. No overlay → unchanged.
      → verify: `tests/gui2/test_database_manager_overlay.py`: first contributor
      id is 10_000_001, next follows own max; user 1 unchanged.
- [ ] 2.3 `_changed`: in `gui2/save_router.py`, the contributor correction
      branch reads the db row without the overlay
      (`db_session.get(DpdHeadword, word.id)`) and lists the columns whose
      values differ. `CorrectionsManager.update_corrections` takes it and stores
      `_changed` in the entry.
      → verify: `tests/gui2/test_save_router.py`: a changed `meaning_1` gives
      `_changed == ["meaning_1"]`; a re-edit of an own correction compares with
      the db row, not the earlier correction.
- [ ] 2.4 Per-user test exceptions: `Gui2Paths.db_test_exceptions_path`
      (contributor only: `db_test_exceptions_{u}.tsv`). `DbTestManager` takes an
      optional own-exceptions path. With it, `load_tests` adds the file's ids to
      each test's `exceptions`, and `add_exception` appends `test_name<TAB>id`
      to that file instead of calling `save_tests`. The toolkit passes the path
      for contributors only.
      → verify: test that a contributor `add_exception` leaves
      `db_tests/db_tests_columns.tsv` byte-identical (checksum), writes the
      per-user line, and the next `load_tests` treats the id as an exception.
      User 1 path unchanged.
- [ ] 2.5 Username: `UsernameManager` keeps the username the toolkit routed
      paths with (`resolve_username() or "1"` at start-up). `is_not_primary()`
      compares that. The first-run dialog text adds "This takes effect the next
      time you start the app."
      → verify: `tests/gui2/test_user.py`: no username → `is_not_primary()` is
      False and saves go to the db path; env "alice" → True.
- [ ] 2.6 Phase gate as 1.6, then `uv run pytest tests/gui2 tests/db_tests`.
      → verify: all clean. Paste the counts here.

## Phase 3 — Maintainer review side — *Sonnet*
- [ ] 3.1 `tools/contrib_entry.py::entry_hash(entry: dict) -> str`.
      → verify: a test writes an entry with `AdditionsManager.add_additions`,
      reloads the file the way the primary loader does, and gets the same hash.
- [ ] 3.2 `save_processed_addition` / `save_processed_correction` take the
      original entry and log `_source_key` and `_source_hash`. `pass2_add_view`
      passes `self.current_addition` / `self.current_correction`.
      → verify: manager tests: the log entry has both fields and the hash
      matches the original entry, not the edited word.
- [ ] 3.3 Reject: `reject(origin_path, source_key, original_entry)` on both
      managers: log `_source_key`, `_source_hash`, `_contributor`, `lemma_1`,
      `"_rejected": true`, then remove the key from the origin file. A "Reject"
      button next to "Add to DB" in `pass2_add_view`, visible only while
      `flags.addition` or `flags.correction` is set with a contributor origin;
      it calls `reject`, clears the flags and the form.
      → verify: manager tests (log + removal, other keys kept). Live in 7.2.
- [ ] 3.4 Proposal fields: a small pure helper `proposal_fields(entry, kind)`
      in `gui2/pass2_add_view.py` (or a sibling module): additions drop `id`;
      corrections with `_changed` keep only those fields (plus nothing else);
      corrections without `_changed` keep all. `_click_additions_button` and
      `_click_corrections_button` use it.
      → verify: tests for the three cases.
- [ ] 3.5 `scripts/server_contrib/merge_contrib_files.py`: for the user
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
- [ ] 3.6 Phase gate as 1.6, then `uv run pytest tests/gui2 tests/scripts tests/tools`.
      → verify: all clean. Paste the counts here.

## Phase 4 — Sync design check — *Opus*
⚠️ MODEL SWITCH REQUIRED (Opus): analysis only, before any sync code.
- [ ] 4.1 Walk spec section G, plus the merge script from 3.5, through each
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

## Phase 5 — Sync implementation — *Sonnet*
⚠️ MODEL SWITCH REQUIRED (Sonnet): mechanical execution resumes.
- [ ] 5.1 Rewrite `scripts/server_contrib/contrib_reconcile.py`:
      `reconcile_entries(local, processed: set[tuple[str, str]])` and
      `reconcile_lines(local_lines, shared_lines)`; `reconcile_all(project_root,
      data_dir)` reads main's logs and shared files from the working tree (the
      server is on main after the pull) and rewrites the contributor files
      atomically (keep `write_json_dict`). Remove snapshot code.
      → verify: rewritten `tests/scripts/server_contrib/test_contrib_reconcile.py`
      covers every Phase 4 row that touches reconcile.
- [ ] 5.2 Rewrite `scripts/server_contrib/contrib_push.py`:
      `push_contributions(project_root, data_dir, worktree, remote)`: create the
      worktree once (`git worktree add`), then `fetch`, `checkout -B
      contributions <remote>/main`, copy every contributor file kind from
      `data_dir` into `worktree/gui2/data/`, `git add -f` those paths only,
      commit if anything is staged, `git push --force-with-lease <remote>
      contributions`.
      → verify: test with a bare `file://` origin: first push creates the
      branch; a second push after main moved is a fast, conflict-free reset;
      nothing changed → no commit; gitignored kinds arrive on the branch.
- [ ] 5.3 Rewrite `scripts/server_contrib/maintenance_window.py` to spec G.20:
      dirty-tree check (`git status --porcelain --untracked-files=no`, refuse
      and log names), `git pull --ff-only`, reconcile, push, rebuild only if
      `HEAD` differs from `logs/last_built_commit` (write it after a good
      build), the existing rollback (db + HEAD), start instances in `finally`.
      Add `--data-dir` and `--worktree` options.
      → verify: rewritten `tests/scripts/server_contrib/test_maintenance_window.py`
      with stub steps: dirty tree → no pull, FAILED, instances restarted; main
      unchanged → no rebuild; rebuild failure → rollback; push failure → logged,
      rebuild still runs.
- [ ] 5.4 Delete `scripts/server_contrib/absorption_check.py` and its test.
      Update `scripts/server_contrib/README.md` and `config_server.md`.
      `rg --hidden "absorption|last_pushed|snapshot_dir"` over the repo.
      → verify: the sweep shows no live references (archive and kamma notes
      excepted).
- [ ] 5.5 Round trip: `tests/scripts/server_contrib/test_round_trip.py` with a
      bare origin, a "server" clone + worktree, and a "maintainer" clone. Three
      cycles: contributor files written → window → maintainer merges the
      branch into main, processes one (`save_processed_*`), rejects one, leaves
      one, runs the merge script, pushes main → window. Mark `slow` if needed.
      → verify: after each cycle only the pending entry remains on the server
      and on the contributions branch; each merge into main has no conflict;
      merged flag lines leave the server's files.
- [ ] 5.6 Phase gate as 1.6, then `uv run pytest tests/scripts/server_contrib -m "slow or not slow"`.
      → verify: all clean. Paste the counts here.

## Phase 6 — Login files — *Sonnet*
- [ ] 6.1 `scripts/server_contrib/nginx_contrib.conf.template`: one HTTPS
      `server` block with a `include /etc/nginx/dpd/*.conf;` line, and a
      per-user `location` snippet template: `auth_basic`,
      `auth_basic_user_file /etc/nginx/dpd/<user>.htpasswd`,
      `proxy_pass http://127.0.0.1:<port>/`, `proxy_http_version 1.1`,
      Upgrade/Connection headers, long read timeout.
      → verify: on the server later, `nginx -t` (contrib_4 Phase 4). Here: the
      template renders with `sed` for a test user, by eye.
- [ ] 6.2 `scripts/server_contrib/add_contributor.sh <user> <port> [tabs]`
      with `--root <dir>` (default `/`) for test runs: `htpasswd -B -c` (prompts
      for the password), the env file (`/etc/dpd/<user>.env`), the nginx
      location (`/etc/nginx/dpd/<user>.conf`), `mkdir` the data folder; prints
      the URL and the commands to enable the unit and reload nginx. Refuses an
      existing user or a port in use by another env file. Removal steps go in
      `scripts/server_contrib/README.md`.
      → verify: `bash -n`; a run with `--root <tmp>` and the password piped via
      `htpasswd -i` mode creates the three files with the right contents; a
      second run for the same user refuses.
- [ ] 6.3 Phase gate: `bash -n` on the script, ruff/pyright on any Python.
      → verify: clean.

## Phase 7 — Live checks and finish — *Sonnet*
- [ ] 7.1 Live local web run WITH the user, in their terminal:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && DPD_GUI2_USERNAME=alice DPD_GUI2_ROLE=contributor-server DPD_GUI2_TABS="Bold Search,DB" DPD_GUI2_DATA_DIR=<scratchpad>/alice uv run flet run --web -p 8551 gui2/main.py`.
      Check: exactly Pass1Auto, Pass1Add, Bold Search, DB; Alt shortcuts to
      other tabs do nothing; DB Save Changes refuses; a Pass1Add save lands in
      the data folder; the db row count is unchanged
      (`sqlite3 dpd.db "select count(*) from dpd_headwords"` before/after); a
      reload keeps working; a second tab is refused; after closing the tab, how
      long until a new tab is allowed.
      → verify: every item logged here with the observed result.
- [ ] 7.2 Live desktop run as user 1 WITH the user, after backing up `dpd.db` to
      the scratchpad: all 17 tabs; load a hand-made contributor addition and
      correction (with `_changed`) from a test `additions_test.json` /
      `corrections_test.json`; Add leaves id empty; Cor fills only changed
      fields; Reject logs and removes; a processed save logs `_source_hash`.
      Remove the test files and log entries after.
      → verify: every item logged here.
- [ ] 7.3 Finish (contrib_1's spec and plan already carry the "superseded by
      contrib_5" notes, added 2026-10-30). Update `gui2/README.md` (contributor tabs, read tabs),
      `scripts/server_contrib/README.md` (new window, push, merge script, add
      and remove a contributor), `kamma/tech.md` (env vars). Run `just
      typecheck`, `uv run pytest tests/` and `graphify update .`.
      → verify: all pass. Paste the counts here.
