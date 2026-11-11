# Plan: contributor server fixes, server memory, laptop gui2 speed

**GitHub issue:** #215. Never comment on, edit or close the issue.
**Spec:** `kamma/threads/20261111_contrib_fixes_gui2_speed/spec.md` — read it fully
first. Section letters (A to F) below refer to it.

## Executor rules

Read these before every phase. They are not optional.

- **The laptop rule.** The owner's desktop gui2 must not get slower, lose a
  feature or behave differently. If a task cannot be done without changing what
  the desktop does, STOP, write what you found under the task, and go on to the
  next task. Do not invent a workaround.
- **No git.** Never run a git command that changes anything (`add`, `commit`,
  `stash`, `checkout`, `restore`, `reset`, `init`). The owner commits at the end.
  Read-only `git log`, `git show`, `git diff`, `git status` are allowed.
- **Never write to GitHub.**
- **Shared working tree.** Other sessions may edit this repo at the same time.
  Touch only the files named in the tasks. If a file you edited shows your
  pre-edit text again, stop and report it.
- **Phases 1 to 7 run on the laptop.** Phase 8 changes the live server. It is run
  by the owner or by the server agent (`/herdr-remote` skill), never by the
  laptop agent over ssh, and only after the owner has committed and pushed.
- **Test first.** For every fix: write the test, run it, see it fail for the
  reason the task names, paste the failing lines (the `FAILED`/`assert` lines,
  not the whole log) into this file under the task, then write the fix.
- **After editing any Python file**, run in this order and fix everything,
  including errors that were there before you:
  1. `uv run ruff check --fix <file>`
  2. `uv run ruff format <file>`
  3. pyright — for a file under `gui2/` or `tests/`:
     `uv run pyright --project /dev/null <file>`; for a file under `scripts/` or
     `tools/` or `db/`: `uv run pyright <file>`
  4. the test files named in the task.
  For `gui2/main.py` pyright reports about 24 Flet typing errors that were there
  before (`kamma/archive/20261102_contrib_mem_wordfinder_lazy/artifacts/results.md`,
  done check 3). Count them before your first edit and do not add to the count.
- **Never use `# noqa` or a bare `# type: ignore`.** A `# pyright: ignore[rule]`
  with the rule name is allowed in tests only, as `tests/gui2/test_main.py` does.
- **Scratch files** (probes, timing scripts) go in the session scratchpad, never
  in the repo root or the home folder. A probe worth keeping is copied to
  `kamma/threads/20261111_contrib_fixes_gui2_speed/artifacts/` at the end of its
  task.
- **No home path and no server address** in any file in the repo. Write
  `<repo root>` and `<server-ip>`. Check `artifacts/` for `/home/` before Phase 7
  ends.
- **Do not start gui2**, a db rebuild, `makedict` or the deconstructor.
- **A command that may run over 60 s** runs in the background with a bounded
  wait: `timeout 600 bash -c 'until <check>; do sleep 5; done'`.
- **Record as you go.** Tick `[x]` and add one or two lines under each task:
  what was done, the test counts, and any number measured.

## Architecture Decisions

- **The preview latch is keyed by page, held in `gui2/preview.py`.** One
  module-level `_owner: ft.Page | None` replaces the `_in_progress` bool. This
  keeps "one preview at a time per page", lets a new page work at once, and lets
  the retired page's Save do nothing. No registry, no per-page dict: the process
  has one live page.
- **`claim_session` stays the one place that retires a page.** It gains three
  small steps: tell the preview module, close the old page's dialogs, and (server
  only) release the old app's data. Each step has its own `try`, so a dead old
  connection cannot stop the takeover (the existing test
  `test_a_dead_old_page_does_not_break_the_takeover` must stay green).
- **Memory release is a method on the object that owns the data.**
  `DatabaseManager.release_memory()` resets its own fields to their `__init__`
  values; `App.release_memory()` clears its views and the toolkit's lazy cache
  and calls it. Nothing outside those classes reaches into their fields.
- **Server gates use what already exists.** `is_headless_server()` for the db
  manager; `2 in self._visible` (the Pass1Auto tab) for the AI manager, the same
  shape as the existing word-finder gate `7 in self._visible` in
  `gui2/main.py`. No new role flag, no new env variable.
- **`ai_manager` on `Pass1AutoController` becomes a `functools.cached_property`.**
  It is still assignable, so `tests/gui2/test_pass1_auto_controller.py:69`
  (`ctrl.ai_manager = SimpleNamespace(...)`) keeps working. On the desktop the AI
  manager is built a few lines later than today (by the view's model dropdown),
  inside the same view build.
- **Safe writes copy the existing three-line pattern** of
  `AdditionsManager._save_dict` (`gui2/additions_manager.py:66-70`). No new shared
  helper: two callers do not justify one.
- **The rollback keeps its signature and its success log lines.** Only the order
  and the guards change.
- **Laptop speed changes are gated on numbers measured in this thread.** A gate
  that is not met means "do not build, record the numbers". This is a normal,
  successful outcome.
- **Not built:** a shared corpus load for the detector worker (unsafe across
  threads), a skip notice for the pull, any change to which user the server runs
  as. See the spec, "What's not included".

## Model Strategy

| Phase | Tier | Suggested model | Reason |
|---|---|---|---|
| 1 — Preview latch and takeover | Pro | Opus | Session and dialog logic across two pages; a wrong read loses a contributor's word |
| 2 — Daily log and presets files | Fast | Sonnet | Two small file managers, fixed pattern |
| 3 — Nightly window and pull check | Fast | Sonnet | Reorder, guards and one regex against a fixed spec |
| 4 — Server memory: decon set, AI manager | Fast | Sonnet | Two gated changes with exact snippets |
| 5 — Server memory: release on takeover, unit limits | Pro | Opus | Object lifetimes and threads; judgement on what is safe to reset |
| 6 — Laptop speed, measured | Fast | Sonnet | Run timing scripts, apply a numeric gate, mechanical edits |
| 7 — Detector measurement, docs, final checks | Fast | Sonnet | Run probes, write results, run the suites |
| 8 — Server rollout | Fast | Sonnet | Ordered runbook steps through the server agent |

---

## Phase 1 — Preview latch and takeover — *Pro*

Spec section A. Files: `gui2/preview.py`, `gui2/main.py`,
`tests/gui2/test_preview.py`, `tests/gui2/test_main.py`.

Read first: `gui2/preview.py` lines 176-259, `gui2/main.py` lines 777-812 and
814-843, `tests/gui2/test_preview.py` lines 103-180,
`tests/gui2/test_main.py` lines 622-683.

- [x] 1.1 Write three failing tests in `tests/gui2/test_preview.py`, after
  `test_second_preview_while_one_is_open_is_ignored`. They use the existing
  `flow` fixture, `FakePage` and `button` helper. A second page is another
  `FakePage()`; start a preview on it with
  `asyncio.run(preview_module.preview_and_confirm(other, None, None, "alice", on_save))`
  (copy the `# pyright: ignore[reportArgumentType]` comment from the fixture).
  The fixture's `on_save` is not reachable from the test, so give the fixture's
  returned `SimpleNamespace` one more field, `on_save=on_save`.
  - `test_a_new_page_can_preview_while_an_old_page_left_its_dialog_open`:
    `flow.start()`, then start on a second page; assert the second page got one
    dialog.
  - `test_save_on_a_retired_page_saves_nothing`: `flow.start()`, call
    `preview_module.retire_page(flow.page)`, press Save on the first dialog;
    assert `flow.saves == []`.
  - `test_save_on_the_old_page_saves_nothing_after_a_new_page_took_the_preview`:
    `flow.start()`, start on a second page, press Save on the FIRST page's
    dialog; assert `flow.saves == []`. Then press Save on the second page's
    dialog; assert `flow.saves == [1]`.
  → verify: `uv run pytest tests/gui2/test_preview.py -q`. The three new tests
  fail (the first with `assert 0 == 1` or similar, the second with
  `AttributeError: ... has no attribute 'retire_page'`). Paste the failing lines
  here. The other tests in the file still pass.

  Done. Failing lines:

  ```
  test_a_new_page_can_preview...: E assert 0 == 1  (where 0 = len([]) = other.dialogs)
  test_save_on_a_retired_page_saves_nothing:
      E AttributeError: module 'gui2.preview' has no attribute 'retire_page'
  test_save_on_the_old_page_saves_nothing_after...: E assert [1] == []
  ```
  3 failed, 18 passed.

- [x] 1.2 Change `gui2/preview.py`. Replace the block from `_in_progress = False`
  to the end of `preview_and_confirm` so that it reads:

  ```python
  # The page whose preview dialog is open. Held per page, not per process: a
  # reload or a second tab makes a new page, and a process-wide flag left set
  # by the old page's dialog would block every later save.
  _owner: ft.Page | None = None


  def retire_page(page: ft.Page) -> None:
      """Forget a page that a newer page replaced. Its dialog can no longer save."""
      global _owner
      if _owner is page:
          _owner = None


  async def preview_and_confirm(
      page: ft.Page,
      db_session: Session,
      word: DpdHeadword,
      username: str,
      on_save: Callable[[], Awaitable[None]],
  ) -> None:
      """Open the preview in the browser, then ask: Save or Cancel. A second call
      from the same page while its preview is open or saving does nothing."""
      global _owner
      if _owner is page:
          return
      _owner = page

      def release() -> None:
          global _owner
          if _owner is page:
              _owner = None

      async def save() -> None:
          # A retired page holds a stale copy of the contributor's file; a save
          # from it would be overwritten by the live page's next save.
          if _owner is not page:
              return
          try:
              await on_save()
          finally:
              release()
  ```

  The `try: ... show_preview_dialog ... except Exception: release(); raise` tail
  stays exactly as it is. In `tests/gui2/test_preview.py` change the fixture line
  `monkeypatch.setattr(preview_module, "_in_progress", False)` to
  `monkeypatch.setattr(preview_module, "_owner", None)`.
  Then run `rg -n --hidden "_in_progress" gui2/preview.py tests/gui2/test_preview.py`:
  it must print nothing. (`_run_in_progress` in other files is a different thing;
  leave it.)
  → verify: `uv run pytest tests/gui2/test_preview.py -q` — all pass, including
  the three new tests and the four older dialog tests. Record the count.

  Done. `rg "_in_progress"` on both files prints nothing. **21 passed**
  (18 old + 3 new).

- [x] 1.3 Write two failing tests in `tests/gui2/test_main.py`, after
  `test_a_dead_old_page_does_not_break_the_takeover`. Use the `free_session`
  fixture.
  - `test_a_takeover_retires_the_old_pages_preview`: `monkeypatch.setattr("gui2.preview._owner", first)`
    where `first = MagicMock()`; `claim_session(first)`; `claim_session(MagicMock())`;
    assert `gui2.preview._owner is None` (import the module as
    `import gui2.preview as preview_module`).
  - `test_a_takeover_closes_the_old_pages_dialogs`: `first = MagicMock()`;
    `dialog = ft.AlertDialog(modal=True)`; `dialog.open = True`;
    `first._dialogs = SimpleNamespace(controls=[dialog])`; `claim_session(first)`;
    `claim_session(MagicMock())`; assert `dialog.open is False`.
  → verify: `uv run pytest tests/gui2/test_main.py -q -k takeover`. Both new tests
  fail. Paste the failing lines here.

  Done. Failing lines:

  ```
  test_a_takeover_retires_the_old_pages_preview:
      E AssertionError: assert <MagicMock id=...> is None  (+ preview_module._owner)
  test_a_takeover_closes_the_old_pages_dialogs:
      E AssertionError: assert True is False  (+ dialog.open)
  ```
  2 failed, 1 passed (the dead-old-page test), 83 deselected.

- [x] 1.4 Change `claim_session` in `gui2/main.py`. Keep the existing `try` block
  as it is. After it, still inside `if previous is not None and previous is not page:`,
  add two more guarded steps:

  ```python
          try:
              from gui2.preview import retire_page

              retire_page(previous)
              # A modal left open on the old page still has working buttons.
              for dialog in list(previous._dialogs.controls):
                  dialog.open = False
              previous.update()
          except Exception as e:
              pr.red(f"could not close the old page's dialogs: {e}")
  ```

  `retire_page` must run before the loop, so a failure in the loop cannot skip
  it. The import is local on purpose: `gui2.preview` pulls in the webapp
  templates, and `gui2/main.py` does not import it at module top today.
  → verify: `uv run pytest tests/gui2/test_main.py tests/gui2/test_preview.py -q`
  — all pass. `test_the_newest_page_takes_over_and_the_old_one_is_retired` and
  `test_a_dead_old_page_does_not_break_the_takeover` pass unchanged.

  Done. **107 passed** (both files), takeover tests unchanged.

- [x] 1.5 Revert check. Comment out the `retire_page(previous)` line, run
  `uv run pytest tests/gui2/test_main.py -q -k takeover`, confirm
  `test_a_takeover_retires_the_old_pages_preview` fails, and restore the line in
  the same step. Then in `gui2/preview.py` change `if _owner is not page:` to
  `if False:`, run `uv run pytest tests/gui2/test_preview.py -q`, confirm exactly
  two tests fail (`..._retired_page_saves_nothing` and
  `..._after_a_new_page_took_the_preview`), and restore it.
  → verify: after restoring, `uv run pytest tests/gui2/test_main.py tests/gui2/test_preview.py -q`
  is all green. Record the two failure counts here.

  Done. Without `retire_page(previous)`: **1 failed**
  (`test_a_takeover_retires_the_old_pages_preview`). With the save guard as
  `if False:` in preview.py: **2 failed** (`..._retired_page_saves_nothing`,
  `..._after_a_new_page_took_the_preview`). Restored: **107 passed**.

- [x] 1.6 Phase check: lint steps 1 to 3 of the executor rules on
  `gui2/preview.py`, `gui2/main.py`, `tests/gui2/test_preview.py`,
  `tests/gui2/test_main.py`.
  → verify: ruff clean; pyright count on `gui2/main.py` not higher than before
  the phase; `uv run pytest tests/gui2 -q` passes (record the count).

  Done. ruff clean on all four (ruff format reformatted test_preview.py once,
  harmless); pyright: preview.py 0, test files 0, **main.py 24** = the
  documented pre-existing baseline, none added. `uv run pytest tests/gui2 -q`:
  **796 passed**.

---

## Phase 2 — Daily log and presets files — *Fast*

Spec section B. Files: `gui2/daily_log.py`, `gui2/filter_presets_manager.py`,
`tests/gui2/test_daily_log.py`, `tests/gui2/test_filter_presets_manager.py`.

Read first: both source files whole, `gui2/additions_manager.py` lines 44-70 (the
pattern to copy), and the helper at the top of each test file.

- [x] 2.1 Write failing tests.
  In `tests/gui2/test_daily_log.py`, class `TestInitialState`, add:
  - `test_an_empty_file_starts_at_zero_and_is_kept_aside`: make the data folder
    as `_log` does, write an empty string to `Gui2Paths(base_dir=tmp_path).daily_log_path`,
    then build the log with `_log(tmp_path)`. Assert `log.get_history() == {}`,
    and that a file named `<daily log name>.corrupt` exists beside it.
  - `test_a_save_leaves_no_temp_file`: `log.increment("pass1")`; assert no file
    ending `.tmp` is in the data folder, and that the saved text equals
    `json.dumps(log.data, indent=4, sort_keys=True)`.
  In `tests/gui2/test_filter_presets_manager.py` add the same two tests for
  `FilterPresetsManager` (damaged file → `presets == {}` and a `.corrupt` file;
  after `save_preset(...)` no `.tmp` file, and the text equals
  `json.dumps(manager.presets, ensure_ascii=False, indent=4)`). Build the manager
  the way the existing tests in that file do.
  → verify: `uv run pytest tests/gui2/test_daily_log.py tests/gui2/test_filter_presets_manager.py -q`.
  The two "damaged file" tests fail with `json.decoder.JSONDecodeError`. Paste
  the failing lines here. (The two "no temp file" tests may already pass; they
  guard the byte-for-byte rule in step 2.2.)

  Done. Both damaged-file tests:

  ```
  E json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
  ```
  2 failed, 20 passed (both no-temp-file guards already pass).

- [x] 2.2 Fix `gui2/daily_log.py`. Add `from tools.printer import printer as pr`.
  `_load` becomes:

  ```python
      def _load(self) -> dict[str, dict[str, int]]:
          try:
              with open(self.file_path, "r", encoding="utf-8") as f:
                  return json.load(f)
          except FileNotFoundError:
              return {}
          except json.JSONDecodeError:
              # A write cut off mid-way leaves an empty file. Without this the
              # editor could not start at all until someone repaired it by hand.
              corrupt = self.file_path.with_name(self.file_path.name + ".corrupt")
              self.file_path.replace(corrupt)
              pr.red(f"{self.file_path.name} is damaged, kept as {corrupt.name}")
              return {}
  ```

  `_save` becomes (same JSON arguments as today, so the file content does not
  change):

  ```python
      def _save(self) -> None:
          # Write then swap, so a kill mid-write cannot leave a half-written file.
          tmp = self.file_path.with_name(self.file_path.name + ".tmp")
          tmp.write_text(
              json.dumps(self.data, indent=4, sort_keys=True), encoding="utf-8"
          )
          tmp.replace(self.file_path)
  ```

  Leave the two existing docstrings' wording alone except where the code under
  them changed.
  → verify: `uv run pytest tests/gui2/test_daily_log.py -q` — all pass.

  Done. **10 passed**.

- [x] 2.3 Fix `gui2/filter_presets_manager.py` the same way: `load_presets`
  catches `json.JSONDecodeError`, moves the file to `<name>.corrupt`, prints with
  `pr.red`, returns `{}`; `save_presets` writes `<name>.tmp` with
  `json.dumps(self.presets, ensure_ascii=False, indent=4)` and replaces.
  `self.presets_path` must be a `Path` for `.with_name`; check how
  `Gui2Paths.filter_presets_path` is defined in `gui2/paths.py` and wrap it in
  `Path(...)` only if it is a string.
  → verify: `uv run pytest tests/gui2/test_filter_presets_manager.py tests/gui2/test_filter_tab_starter.py -q`
  — all pass.

  Done. **17 passed**. Both `daily_log_path` and `filter_presets_path` are
  already `Path` in `gui2/paths.py`, no wrap needed.

- [x] 2.4 Phase check: lint steps on the four files.
  → verify: ruff and pyright clean on all four; `uv run pytest tests/gui2 -q`
  passes (record the count).

  Done. ruff clean (it removed one unused `import json` from the presets test);
  pyright 0 on all four. `uv run pytest tests/gui2 -q`: **800 passed**.

---

## Phase 3 — Nightly window and pull check — *Fast*

Spec sections C and D. Files: `scripts/server_contrib/maintenance_window.py`,
`scripts/server_contrib/contrib_pull.py`,
`tests/scripts/server_contrib/test_maintenance_window.py`,
`tests/scripts/server_contrib/test_contrib_pull.py`.

Read first: `maintenance_window.py` lines 244-262, 299-367 and 414-509; the test
file's helpers `_setup`, `_steps`, `Calls`, `Setup` (lines 55-152), class
`TestRollback` (308-338) and class `TestStopFailure` (380-402).

- [x] 3.1 C1, failing test. In class `TestRollback` add
  `test_a_failed_db_restore_still_restores_the_contributor_files`. Copy the body
  of `test_failed_rebuild_restores_db_head_and_contributor_files`. Make the db
  restore fail by patching `shutil.copy2` in the module so that it raises
  `OSError("disk full")` only when the SOURCE path's name ends with `.prev`, and
  calls the real `shutil.copy2` otherwise:

  ```python
  real_copy2 = shutil.copy2

  def failing_copy2(src, dst, *args, **kwargs):
      if str(src).endswith(".prev"):
          raise OSError("disk full")
      return real_copy2(src, dst, *args, **kwargs)

  monkeypatch.setattr(
      "scripts.server_contrib.maintenance_window.shutil.copy2", failing_copy2
  )
  ```

  Apply the patch inside `corrupting_rebuild` (just before `raise`), so the
  capture step earlier in the run still makes its `.prev` copy. Assert: outcome
  is `Outcome.FAILED`; `load_json_dict(path) == {"alice_1": done}`;
  `checked_alice.csv` text is `"word\n"`; `setup.head() == before`; the log holds
  `"rollback of the database FAILED"` and does NOT hold
  `"maintenance aborted before the pull"`.
  → verify: `uv run pytest tests/scripts/server_contrib/test_maintenance_window.py -q -k failed_db_restore`
  fails (the contributor file assertion or the log assertion). Paste the failing
  lines here.

  Done. Failing lines:

  ```
  >       assert load_json_dict(path) == {"alice_1": done}
  E       AssertionError: assert {} == {'alice_1': {...}}
  ```
  1 failed, 36 deselected.

- [x] 3.2 C1, fix `_restore_rollback`. New order and guards; the three success
  log lines keep their exact text:

  ```python
  def _restore_rollback(
      config: WindowConfig, rollback: Rollback, log: logging.Logger
  ) -> None:
      # Each step is guarded so one failure cannot skip the others. Contributor
      # files go first: they are the only copy of a contributor's work, and the
      # db and the working tree can be rebuilt.
      try:
          # Iterate the backup (ground truth), not the current dir: a contributor
          # file deleted by the failed window must still be restored.
          for backup_file in rollback.data_backup.iterdir():
              shutil.copy2(backup_file, config.data_dir / backup_file.name)
          log.info("restored contributor files")
      except Exception as exc:
          log.error(f"rollback of the contributor files FAILED: {exc}")
      try:
          if rollback.db_backup is not None and rollback.db_backup.exists():
              # Copy beside the db, then swap: a copy that fails half-way must
              # not leave a truncated dpd.db for the instances to start on.
              staged = config.db_path.with_name(config.db_path.name + ".restoring")
              shutil.copy2(rollback.db_backup, staged)
              os.replace(staged, config.db_path)
              # A -wal left by the failed rebuild would be replayed over the old db.
              for suffix in ("-wal", "-shm"):
                  config.db_path.with_name(config.db_path.name + suffix).unlink(
                      missing_ok=True
                  )
              log.info(f"restored db from {rollback.db_backup.name}")
      except Exception as exc:
          log.error(f"rollback of the database FAILED: {exc}")
      try:
          if rollback.pre_commit is not None:
              ...  # the existing git reset + submodule block, unchanged
      except Exception as exc:
          log.error(f"rollback git restore FAILED: {exc}")
  ```

  Move the existing git block (the two `subprocess.run` calls and the
  `if reset.returncode != 0 ...` / `else` log lines) into the third `try`
  without changing a line of it. Move the two existing comments with their code.
  Check that `import os` is already at the top of the file (it is used by
  `_config_from_args`); add it if not.
  → verify: `uv run pytest tests/scripts/server_contrib/test_maintenance_window.py -q`
  — all pass, including `TestRollback`, `TestRollbackWal` and
  `TestDatabaseCopyCleanup`. Record the count.

  Done. **37 passed** (includes the new failing-db-restore test, TestRollbackWal
  and TestDatabaseCopyCleanup unchanged). `import os` was already at the top.

- [x] 3.3 C2, failing test. In class `TestStopFailure` add
  `test_a_failed_start_fails_the_run`. Copy
  `test_a_failed_stop_refuses_the_window_and_still_restarts`, but make `fake_run`
  return exit code 1 when `cmd[1] == "start"` and 0 otherwise. `fake_run` replaces
  `subprocess.run` for the whole module, so the git calls inside the run are
  faked too: use `_steps(calls)` as that test does, and if the run needs real git
  (it calls `_tracked_changes` and `_git_head`), call the real function for any
  command whose first word is not `systemctl`:

  ```python
  real_run = subprocess.run

  def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
      if cmd[0] != "systemctl":
          return real_run(cmd, **kwargs)  # pyright: ignore[reportCallIssue, reportArgumentType]
      seen.append(" ".join(cmd))
      return subprocess.CompletedProcess(cmd, 1 if cmd[1] == "start" else 0)
  ```

  Assert `outcome is Outcome.FAILED` and that the status text
  (`setup.config.status_file` if the setup sets one, else read
  `setup.config.log_dir / "status.txt"`) starts with a failed outcome — look at
  `test_status_file_reports_a_failure_and_its_reason` for the exact line it
  checks and use the same check.
  Add a second test, `test_a_start_that_times_out_fails_the_run_and_writes_the_status`:
  `fake_run` raises `subprocess.TimeoutExpired(cmd, 300)` for `start`. Assert
  `outcome is Outcome.FAILED` and that the status file exists.
  → verify: `uv run pytest tests/scripts/server_contrib/test_maintenance_window.py -q -k "failed_start or times_out"`
  — both fail (the first on the outcome, the second with an uncaught
  `TimeoutExpired`). Paste the failing lines here.

  Done. Failing lines:

  ```
  test_a_failed_start_fails_the_run:
  >       assert outcome is Outcome.FAILED
  E       AssertionError: assert <Outcome.REBUILT: 'rebuilt'> is <Outcome.FAILED: 'failed'>
  test_a_start_that_times_out_fails_the_run_and_writes_the_status:
  E       subprocess.TimeoutExpired: Command '['systemctl', 'start', 'dpd-gui@alice']' timed out after 300 seconds
  ```
  2 failed, 37 deselected.

- [x] 3.4 C2, fix. In `run_maintenance`, the first line of the `finally` block is
  `_systemctl("start", config.instances, config, log)`. Replace it with:

  ```python
          try:
              start_failed = _systemctl("start", config.instances, config, log)
          except (subprocess.TimeoutExpired, OSError) as exc:
              log.error(f"could not start the instances: {exc}")
              start_failed = list(config.instances)
          if start_failed:
              # An editor that stayed down is a failed night, whatever the
              # rebuild did: the owner must see it in the status and exit code.
              outcome = Outcome.FAILED
  ```

  Nothing else in the `finally` block changes. Note for the reader: the two early
  `return outcome` statements inside the `try` (stop failed, dirty tree) already
  return `FAILED`, so the value they captured is right; the normal path ends at
  the last `return outcome` of the function, after the `finally`, and so returns
  the updated value.
  → verify: `uv run pytest tests/scripts/server_contrib/test_maintenance_window.py -q`
  — all pass. `test_main_exits_1_only_when_the_window_failed` passes unchanged.

  Done. **39 passed**, including `test_main_exits_1_only_when_the_window_failed`.

- [x] 3.5 D, failing test. In `tests/scripts/server_contrib/test_contrib_pull.py`,
  next to `test_a_flag_file_with_no_final_newline_is_refused` (line ~145), add
  two tests written the same way as that one (read it and reuse its helper):
  - `test_a_carriage_return_inside_a_line_is_refused`: content
    `b"a\tb\rjunk\n"` for kind `manual_corrections`; expect the reason
    `"carriage return inside a line"`.
  - `test_windows_line_endings_still_pass`: content `b"a\tb\r\nc\td\r\n"` for the
    same kind; expect no reason (`None`).
  → verify: `uv run pytest tests/scripts/server_contrib/test_contrib_pull.py -q -k "carriage or windows"`
  — the first fails (the check returns `None`), the second passes. Paste the
  failing line here.

  Done. Failing line:

  ```
  E AssertionError: assert None == 'carriage return inside a line'
  ```
  1 failed, 1 passed, 130 deselected.

- [x] 3.6 D, fix `scripts/server_contrib/contrib_pull.py`. Under the
  `CONTROL_CHARACTERS` line add:

  ```python
  # A bare carriage return is a line break to some readers, so one line here
  # could reach a shared file as two, the second with the wrong column count.
  LONE_CARRIAGE_RETURN = re.compile(r"\r(?!\n)")
  ```

  In `_check_lines`, directly after the `CONTROL_CHARACTERS` check, add:

  ```python
      if LONE_CARRIAGE_RETURN.search(text):
          return "carriage return inside a line"
  ```

  → verify: `uv run pytest tests/scripts/server_contrib/test_contrib_pull.py -q`
  — all pass. Record the count.

  Done. **132 passed**.

- [x] 3.7 Phase check: lint steps on the two scripts (`uv run pyright <file>`)
  and the two test files (`uv run pyright --project /dev/null <file>`).
  → verify: all clean; `uv run pytest tests/scripts -q` passes (record the
  count). If
  `TestHappyPath::test_status_file_reports_a_failure_and_its_reason` fails, run
  it alone three times: it failed once before this thread for an unknown reason
  (problem item 27 in
  `kamma/archive/20261030_contrib_x_problem_children/spec.md`). Record what you
  saw; do not change it.

  Done. ruff and pyright clean on all four (ruff reformatted the pull test
  once). `uv run pytest tests/scripts -q`: **428 passed**
  — `test_status_file_reports_a_failure_and_its_reason` passed in the run, no
  flake seen.

---

## Phase 4 — Server memory: decon set, AI manager — *Fast*

Spec sections E1 and E2. Files: `gui2/database_manager.py`,
`gui2/pass1_auto_controller.py`, `gui2/main.py`,
`tests/gui2/test_database_manager_decon_cache.py`,
`tests/gui2/test_pass1_auto_controller.py`, `tests/gui2/test_main.py`.

Tests switch a process to server mode with
`monkeypatch.setenv("DPD_GUI2_ROLE", "contributor-server")`, as `_server_app` in
`tests/gui2/test_main.py` (line 313) does. Read `tools/server_mode.py` to confirm
before using it.

- [x] 4.1 E1, failing tests. In `tests/gui2/test_database_manager_decon_cache.py`
  (read the whole file first and build the manager the way it does) add:
  - `test_a_contributor_server_never_loads_the_decon_set`: server mode on; patch
    `DatabaseManager.get_all_decon_no_headwords` with a function that appends to
    a list; call `manager.initialize_db()` (if the file's fixture cannot run
    `initialize_db`, patch every other `get_all_*` method it calls with a no-op,
    listed in `gui2/database_manager.py` lines 184-192); assert the list is empty
    and `manager.all_decon_no_headwords == set()`.
  - `test_the_desktop_still_loads_the_decon_set`: the same with server mode off
    (`monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)`); assert the list has
    one entry.
  → verify: `uv run pytest tests/gui2/test_database_manager_decon_cache.py -q` —
  the server test fails, the desktop test passes. Paste the failing line here.

  Done. Failing line:

  ```
  E assert ['decon'] == []
  ```
  1 failed, 3 passed.

- [x] 4.2 E1, fix. In `initialize_db` (`gui2/database_manager.py`) replace the
  line `self.get_all_decon_no_headwords()` with:

  ```python
          # Only the Pass2Pre tab reads this set, and a contributor never has
          # that tab. The server's db is read-only, so the cache can never be
          # saved there and every start would pay the live scan.
          if not is_headless_server():
              self.get_all_decon_no_headwords()
  ```

  `is_headless_server` is already imported in this file (it is used in
  `load_corpus`); check with `rg -n "is_headless_server" gui2/database_manager.py`.
  → verify: `uv run pytest tests/gui2/test_database_manager_decon_cache.py tests/gui2/test_database_manager_corpus.py -q`
  — all pass.

  Done. **33 passed**.

- [x] 4.3 E2, make the controller's AI manager lazy. In
  `gui2/pass1_auto_controller.py`:
  - add `from functools import cached_property` to the imports;
  - in `__init__`, replace `self.ai_manager = toolkit.ai_manager` with
    `self._toolkit: ToolKit = toolkit`;
  - add this method to the class, after `__init__`:

    ```python
        @cached_property
        def ai_manager(self) -> AIManager:
            # Built on first use: a contributor's Pass1Add reuses this controller
            # for its word lists and never sends an AI request.
            return self._toolkit.ai_manager
    ```

  - `AIManager` is needed only for the type. Add it under the file's existing
    `if TYPE_CHECKING:` block (`from tools.ai_manager import AIManager`); if the
    file has no such block, add one, and add `from __future__ import annotations`
    only if the file already uses it — otherwise quote the type:
    `-> "AIManager"`.
  Run `rg -n "_toolkit\b" gui2/pass1_auto_controller.py` first: if the name is
  already used for something else, stop and report.
  → verify: `uv run pytest tests/gui2/test_pass1_auto_controller.py -q` — all
  pass, with no edit to that test file
  (`ctrl.ai_manager = SimpleNamespace(...)` at line 69 still works on a
  `cached_property`).

- [x] 4.4 E2, failing tests in `tests/gui2/test_main.py`, next to
  `test_server_warmup_skips_the_word_finder_without_pass2add` (line ~489). Read
  that test and `_WordFinderAccessToolkit` and follow the same shape.
  - `test_server_warmup_skips_the_ai_manager_without_an_ai_tab`: a server app
    (`_server_app(monkeypatch, "DB")`) whose toolkit records every access of
    `ai_manager`; run `app._warmup_in_background()`; assert no access.
  - `test_desktop_warmup_still_builds_the_ai_manager`: build the app the way the
    file's existing desktop warm-up test does (search the file for a test that
    calls `_warmup_in_background` without `_server_app`; if there is none, build
    with `_server_app` and then set `app._visible = list(range(len(TAB_LABELS)))`
    and rebuild the tab bar as `_give_server_app_pass2add` does); assert one
    access.
  - `test_server_pass1add_does_not_build_the_pass1auto_view`: on a server app,
    replace `app._view_builders[2]` with a function that appends to a list, and
    restore the real builder for index 3 by calling the new method from 4.5
    (`app._make_pass1_add()`) with `gui2.pass1_add_view.Pass1AddView` and
    `gui2.pass1_auto_controller.Pass1AutoController` patched to `MagicMock()`;
    assert the list is empty and that `Pass1AutoController` was called once with
    `None` as its first argument.
  - `test_desktop_pass1add_shares_the_pass1auto_views_controller`: with
    `app._visible` holding 2, `app._make_pass1_add()` passes
    `app._view(2).controller` to `Pass1AddView` (the same object), and
    `Pass1AutoController` is not called.
  → verify: `uv run pytest tests/gui2/test_main.py -q -k "ai_manager or pass1add or pass1auto"`
  — the two server tests fail; the `_make_pass1_add` tests fail with
  `AttributeError`. Paste the failing lines here.

  Done. Failing lines:

  ```
  test_server_warmup_skips_the_ai_manager_without_an_ai_tab: FAILED
  test_server_pass1add_does_not_build_the_pass1auto_view:
      E AttributeError: 'App' object has no attribute '_make_pass1_add'
  test_desktop_pass1add_shares_the_pass1auto_views_controller:
      E AttributeError: 'App' object has no attribute '_make_pass1_add'
  ```
  3 failed, 5 passed (the desktop warm-up test passed before the fix, since the
  old code always built the AI manager).

- [x] 4.5 E2, fix `gui2/main.py`.
  - Add a method to `App`, next to `_make_filter_tab`:

    ```python
        def _make_pass1_add(self) -> ft.Control:
            from gui2.pass1_add_view import Pass1AddView

            if 2 in self._visible:
                controller = self._view(2).controller  # the Pass1Auto view's own
            else:
                # Pass1Add reads only this controller's word lists. Building the
                # hidden Pass1Auto view for it would build every AI client, which
                # nothing on a contributor's page can use.
                from gui2.pass1_auto_controller import Pass1AutoController

                controller = Pass1AutoController(None, self.toolkit)
            return Pass1AddView(self.page, self.toolkit, controller)
    ```

    Keep whatever attribute access form the present line 225 uses for
    `.controller` (if pyright needed a cast or ignore there, keep it).
    `Pass1AutoController.__init__` takes `ui` untyped, so `None` needs no cast.
  - In `_view_builders`, change entry 3 to `3: self._make_pass1_add,`.
  - Update the comment above `self._views` (lines 207-213): its last clause says
    Pass1Add builds Pass1Auto "even where its tab is hidden". Rewrite that clause
    to say: where the Pass1Auto tab is hidden, Pass1Add gets a controller with no
    view (see `_make_pass1_add`).
  - In `_warmup_in_background`, replace the line `self.toolkit.ai_manager` with:

    ```python
              # Only the two Auto tabs send AI requests.
              if 2 in self._visible or 6 in self._visible:
                  self.toolkit.ai_manager
    ```

  - Before finishing, run `rg -n "_view\(2\)|_views\.get\(2\)|_views\[2\]" gui2/`
    and confirm no other code needs the Pass1Auto view to exist on the server.
    Then read `Pass1AutoController.get_auto_processed_dict` and `remove_word`
    once more and confirm neither reads `self.ui`. Write both results here.
  → verify: `uv run pytest tests/gui2/test_main.py tests/gui2/test_pass1_add_view.py tests/gui2/test_pass1_add_controller.py tests/gui2/test_pass1_auto_controller.py -q`
  — all pass. Record the count.

  Done. **111 passed**. The `rg` check: `_view(2)` appears only in
  `_make_pass1_add` and a comment — no other code needs the Pass1Auto view on
  the server. `get_auto_processed_dict` and `remove_word` read no `self.ui`
  (only view-driven methods like `load_auto_processed` do, and those never run
  without a view).

- [x] 4.6 Revert check for 4.2 and 4.5: turn each gate off in turn (make the
  `if` always true), run the two test files of 4.1 and 4.4, record how many
  tests fail (expect 1 for the decon gate, at least 2 for the AI gates), and
  restore in the same step.
  → verify: after restoring, both files are green. Failure counts recorded here.

  Done. Decon gate always-true: **1 failed** (the server decon test). AI gates
  always-true: **2 failed** (server AI-manager warm-up, server pass1add view).
  After restoring: both green (8 passed on the -k selection).

- [x] 4.7 Phase check: lint steps on the three source files and three test
  files.
  → verify: clean (pyright count on `gui2/main.py` not higher than before);
  `uv run pytest tests/gui2 tests/tools -q` passes (record the count).

  Done. ruff clean (it removed the now-unused `Pass1AddView` import from
  `App.__init__` — it lives in `_make_pass1_add` now); pyright 0 on all but
  `gui2/main.py` at **24** = baseline. `uv run pytest tests/gui2 tests/tools -q`:
  **1645 passed, 7 deselected**.

---

## Phase 5 — Server memory: release on takeover, unit limits — *Pro*

Spec sections E3 and E4. Files: `gui2/database_manager.py`, `gui2/main.py`,
`scripts/server_contrib/dpd-gui@.service`, `scripts/server_contrib/README.md`,
`tests/gui2/test_database_manager_corpus.py`, `tests/gui2/test_main.py`.

Read first: `DatabaseManager.__init__` (lines 76-164), `load_corpus` and
`mark_corpus_stale` (210-266), `gui2/toolkit.py` lines 42-48 and 100-110,
`gui2/main.py` `claim_session`, `release_session` and `main` (789-843).

- [x] 5.1 Failing test for the db manager, in
  `tests/gui2/test_database_manager_corpus.py` (use the file's `db_manager`
  fixture): `test_release_memory_empties_the_big_data_and_a_reload_still_works`.
  Call `load_corpus()` and `initialize_db()` (or set the fields by hand if the
  fixture cannot run `initialize_db`: `all_lemma_1 = {"a"}`,
  `all_inflections = {"a"}`, `_relationship_detector = object()`). Call
  `db_manager.release_memory()`. Assert: `db_manager.db == []`;
  `_relationship_detector is None`; `all_lemma_1 is None`;
  `all_inflections == set()`; `is_db_loaded()` is false. Then call
  `load_corpus()` again and assert it returns every row (same count as the
  file's `test_load_corpus_loads_all_rows`).
  → verify: `uv run pytest tests/gui2/test_database_manager_corpus.py -q -k release_memory`
  fails with `AttributeError: ... 'release_memory'`. Paste it here.

  Done.

  ```
  E AttributeError: 'DatabaseManager' object has no attribute 'release_memory'
  ```

- [x] 5.2 Add `release_memory` to `DatabaseManager`, in the "CORPUS CACHE"
  section after `mark_corpus_stale`:

  ```python
      def release_memory(self) -> None:
          """Drop every large structure. For a page that a newer page replaced:
          its app can do no more work, and the new app needs the room."""
          with self._corpus_lock:
              self.db = []
              self._corpus_stale = True
          self._relationship_detector = None
          self.db_loaded = False
          self._inflections_ready = False
          self._inflections_gen = -1
          self._pass2_gen = -1
          self._components_gen = -1
          self.all_inflections = set()
          self.all_inflections_missing_meaning = set()
          self.all_inflections_missing_example = set()
          self.all_inflections_missing_any_example = set()
          self.all_suffixes = set()
          self.compound_components_map = {}
          self.all_decon_no_headwords = set()
          self.all_lemma_1 = None
          self.all_lemma_clean = None
          self.all_pos = None
          self.all_roots = None
          self.all_compound_families = None
          self.all_root_families = None
          self.all_word_families = None
          self.all_patterns = None
  ```

  Compare this list with `__init__` line by line. Every field there that holds a
  set, list or dict built from the db must be in the method with the same
  initial value as in `__init__`. Leave alone: `sandhi_ok_list`, the four
  `all_plus_cases` / `all_compound_types` / `all_family_sets` / `all_verbs`
  lists (small, read at view build), the root and family index fields, the
  locks, `_own_edits`, `db_session`. If `__init__` has a large field that is not
  in the snippet, add it and note it here.
  → verify: `uv run pytest tests/gui2/test_database_manager_corpus.py -q` — all
  pass.

  Done. **30 passed**. Compared with `__init__` line by line: every db-built
  set/list/dict is in the method; no additional large field found (the snippet
  already covers all of `db`, the lookup sets, the missing-infl./suffix/
  component sets, `all_decon_no_headwords`, the lemma/pos/root/family sets and
  the detector). `all_plus_cases`, `all_compound_types`, `all_family_sets`,
  `all_verbs`, `sandhi_ok_list`, root/family index fields, locks, `_own_edits`,
  `db_session` left alone per plan.

- [x] 5.3 Failing tests in `tests/gui2/test_main.py`, with the `free_session`
  fixture; also patch `gui2.main._session_app` to `None` in each
  (`monkeypatch.setattr("gui2.main._session_app", None, raising=False)` — after
  5.4 exists, drop `raising=False`).
  - `test_a_server_takeover_releases_the_old_app`: server mode on;
    `monkeypatch.setattr("gui2.main.App", built)` where `built = MagicMock()`
    returns a new `MagicMock()` per call (`side_effect=[first_app, second_app]`);
    pages `first, second = MagicMock(), MagicMock()` with `first.web = True`
    etc.; patch `gui2.main.server_lifecycle.attach` to a no-op; `main(first)`,
    `main(second)`; assert `first_app.release_memory.assert_called_once()` and
    `second_app.release_memory.assert_not_called()`.
  - `test_a_desktop_takeover_releases_nothing`: the same with server mode off;
    assert `first_app.release_memory.assert_not_called()`.
  - `test_a_failing_release_does_not_break_the_takeover`: server mode on;
    `first_app.release_memory.side_effect = RuntimeError("boom")`;
    `main(second)` must not raise, and `built.call_count == 2`.
  → verify: `uv run pytest tests/gui2/test_main.py -q -k "release"` — the first
  fails (`release_memory` never called). Paste the failing lines here.

  Done. Failing lines:

  ```
  >       first_app.release_memory.assert_called_once()
  E           AssertionError: Expected 'release_memory' to have been called once. Called 0 times.
  ```
  1 failed, 3 passed (the desktop and failing-release tests pass trivially
  before the fix).

- [x] 5.4 Fix `gui2/main.py`.
  - Next to `_session_page` add:

    ```python
    # The app built for the live page, so a takeover can empty it (server only).
    _session_app: "App | None" = None
    ```

  - In `claim_session`, take the old app under the same lock and release it
    after the page steps:

    ```python
        global _session_page, _session_app
        with _session_lock:
            previous = _session_page
            _session_page = page
            previous_app = _session_app
            _session_app = None
        ...  # the existing page steps and the Phase 1 dialog step, unchanged
        if previous_app is not None and is_headless_server():
            try:
                # Each open copy holds its own corpus and lookup sets; emptying
                # the old one first lets the new app reuse that memory.
                previous_app.release_memory()
            except Exception as e:
                pr.red(f"could not release the old app: {e}")
    ```

    The release sits outside the `if previous is not None and previous is not page:`
    block: after a disconnect `_session_page` is `None` but the old app is still
    held, and it must be released too.
  - In `main`, change `App(page)` to keep the result and register it, only if
    this page still holds the session (a third page may have taken over while
    the app was being built):

    ```python
        app = App(page)
        global _session_app
        with _session_lock:
            if _session_page is page:
                _session_app = app
    ```

    Put the `global` statement at the top of `main` with any existing ones.
  - Add to `App`, after `_make_pass1_add`:

    ```python
        def release_memory(self) -> None:
            """Empty this app's data once a newer page has replaced its page."""
            with self._build_lock:
                self._views.clear()
                self._view_builders = {}
            with self.toolkit._lazy_lock:
                self.toolkit._lazy_cache.clear()
            self.toolkit.db_manager.release_memory()
    ```

  - Fix the stale figure in the comment above `_session_lock`: it says a second
    copy costs "~2.5 GB". Change the words in the brackets to
    "(about 560 MB measured, 2026-11-02)" — the difference between 2,059.4 MB
    for three pages and 943.3 MB for one, halved
    (`kamma/archive/20261102_contrib_mem_savings/artifacts/results.md`, caveats).
    This is the one existing comment this thread edits, because the measure
    thread listed it as wrong.
  → verify: `uv run pytest tests/gui2/test_main.py -q` — all pass, including the
  five older session tests (lines 628-683). Record the count.

  Done. **93 passed**.

  REVIEW FIX (2026-11-12): review found the release sat inside the
  `if previous is not None and previous is not page:` guard, so after a real
  disconnect (`_session_page = None`) the held old app was never released —
  the exact case the plan's snippet places the release outside the guard for.
  Moved out of the guard, comment added, and a new regression test
  `test_a_server_release_happens_even_after_a_disconnect` added
  (94 passed after the fix).

- [x] 5.5 Revert check: in `claim_session` change
  `if previous_app is not None and is_headless_server():` to `if False:`, run
  `uv run pytest tests/gui2/test_main.py -q -k release`, record the failure
  count (expect 1), restore.
  → verify: green after restoring.

  Done. Gate off: **1 failed** (`test_a_server_takeover_releases_the_old_app`).
  Restored: 4 passed.

- [x] 5.6 E4, the unit file. In `scripts/server_contrib/dpd-gui@.service`, in the
  `[Service]` section after `TimeoutStopSec=30`, add:

  ```ini
  # One runaway instance must not starve the others. Above MemoryHigh the
  # kernel slows it and reclaims; at MemoryMax it is killed, and Restart=always
  # brings back an empty process. A warm instance holds about 775 MB.
  MemoryHigh=1500M
  MemoryMax=2G
  ```

  Then run `rg -n --hidden "dpd-gui@.service" tests scripts/server_contrib` and
  read every test that reads the unit file; make sure none asserts the exact
  line list. In `scripts/server_contrib/README.md`, section "New server", add
  one bullet after the bullet that begins "The systemd unit `dpd-gui@.service`
  is installed":

  ```markdown
  - Each instance has a memory limit in the unit: `MemoryHigh=1500M` (slowed
    above it) and `MemoryMax=2G` (killed, then restarted empty). A warm instance
    holds about 775 MB. Check with
    `systemctl show dpd-gui@<user> -p MemoryHigh -p MemoryMax`.
  ```

  → verify: `uv run pytest tests/scripts/server_contrib -q` passes;
  `rg -n "MemoryHigh|MemoryMax" scripts/server_contrib` shows the unit, the
  README and the password unit's own `MemoryMax=128M`, nothing else.

  Done. **280 passed**; rg shows exactly the three places.

- [x] 5.7 Phase check: lint steps on `gui2/database_manager.py`, `gui2/main.py`
  and the two test files.
  → verify: clean; `uv run pytest tests/gui2 tests/tools tests/scripts -q`
  passes (record the count).

  Done. ruff clean; pyright 0 except `gui2/main.py` at **24** = baseline.
  `uv run pytest tests/gui2 tests/tools tests/scripts -q`: **2077 passed,
  7 deselected**.

---

## Phase 6 — Laptop speed, measured — *Fast*

Spec sections F1 and F2. Results go to
`kamma/threads/20261111_contrib_fixes_gui2_speed/artifacts/laptop_speed.md`.
Every timing: one warm-up run thrown away, then 5 runs, report the median and
the min to max. Each run is a fresh process. Run `uptime` first and write the
load average in the results; if the 1-minute load is above 2, say so beside the
numbers.

- [x] 6.1 F1, measure. In the scratchpad write `time_imports.py`. It takes a
  variant name (`all` or `start`), imports `flet` and `gui2.toolkit` first
  (not timed), then times with `time.perf_counter()` the import of:
  - `start`: `gui2.global_tab_view` only (the desktop's first tab);
  - `all`: the 16 view modules that `gui2/main.py` imports before first paint —
    the five at lines 13-20 (`gui2.compound_type_tab_view`,
    `gui2.roots_tab_view`, `gui2.sandhi_find_replace_view`, `gui2.sandhi_view`,
    `gui2.spelling_find_replace_view`) and the eleven at lines 115-125. Copy the
    module names from the file, do not type them from memory.
  It prints one line: `<variant> <seconds>`. Write `run_imports.sh` beside it
  that runs each variant 6 times as
  `PYTHONPATH=. uv run python <scratchpad>/time_imports.py <variant>` from the
  repo root, and prints all 12 lines.
  → verify: `artifacts/laptop_speed.md` has a table: variant, median, min, max;
  and the line `saving bound = median(all) − median(start) = <x> s`. Copy the two
  scripts into `artifacts/`.

  Done. saving bound = 0.452 − 0.266 = **0.186 s** (load 1.89 — under 2). Note:
  the measured "all" set is 15 modules, not the plan's 16 — Phase 4 moved
  `Pass1AddView` into `_make_pass1_add`, so 5 + 10 is what `gui2/main.py`
  imports before first paint today. Scripts copied to `artifacts/`.

- [x] 6.2 F1, gate and build.
  **If the saving bound is under 0.15 s:** write "F1 not built: saving bound
  <x> s is under the 0.15 s gate" in `laptop_speed.md`, tick this task, go to
  6.3.
  **Otherwise:** in `gui2/main.py`
  - delete the five view imports at module top (lines 13, 15-17, 20) and the
    eleven in `App.__init__` (lines 115-125);
  - replace the `_view_builders` lambdas with small methods on `App`, one per
    tab, each doing its own import, in the shape of the existing
    `_make_filter_tab`. Example:

    ```python
        def _make_global(self) -> ft.Control:
            from gui2.global_tab_view import GlobalTabView

            return GlobalTabView(self.page, self.toolkit)
    ```

    and `_view_builders = {0: self._make_global, 1: self._make_translations, ...}`.
    Entry 3 stays `self._make_pass1_add` from Phase 4, entry 11 stays
    `self._make_filter_tab`;
  - run `rg -n "GlobalTabView|TranslationsView|Pass1AutoView|Pass2PreProcessView|Pass2xInCommentaryView|Pass2AutoView|Pass2AddView|SandhiFindReplaceView|SpellingFindReplaceView|SandhiView|TestsTabView|BoldSearchView|RootsTabView|CompoundTypeTabView|InflectionTemplatesTabView" gui2/main.py`
    and confirm each name appears only inside its own builder method. If a name
    is used elsewhere (an `isinstance`, a type hint), put that import under
    `if TYPE_CHECKING:` for a hint, or stop and report for anything else;
  - run `rg -n "gui2\.main\.[A-Z]\w*(View)" tests` — any test that patches a
    view class on `gui2.main` must now patch it on its own module.
  **Before the first edit of this task**, take the "before" figure: run
  `PYTHONPATH=. uv run python -X importtime -c "import gui2.main" 2>&1 | tail -1`
  three times and write the last column (cumulative microseconds of `gui2.main`)
  of each run in `laptop_speed.md`. This covers only the five module-top
  imports; the eleven in `App.__init__` are covered by the 6.1 figure.
  → verify: `uv run pytest tests/gui2 -q` passes. Run the same `importtime`
  command three times after the edit and write the three "after" figures beside
  the "before" ones. The "after" median must be lower. If it is not, undo this
  task's edits by hand (restore the imports and the lambdas exactly), run the
  tests again, and write "F1 reverted: no gain" with the figures.

  Done. Gate met (0.186 s ≥ 0.15 s) → built. `uv run pytest tests/gui2 -q`:
  **810 passed**. rg gate: every view name appears only inside its own builder
  method; no test patches a view class on `gui2.main`. importtime median
  337,815 → 106,326 µs (lower — kept).

- [x] 6.3 F2, measure. In the scratchpad write `time_lemmas.py`: build
  `DatabaseManager()` from `gui2.database_manager` (it only opens a session),
  then time `get_all_lemma_1_and_lemma_clean()` six times in the same process
  (this one is a warm in-process cost, as it is after a save), print the six
  values. Run it from the repo root with
  `PYTHONPATH=. uv run python <scratchpad>/time_lemmas.py`. It only reads
  `dpd.db`. Make sure `DPD_GUI2_ROLE` is not set in the shell
  (`env | cut -d= -f1 | grep -c DPD_GUI2` must print 0).
  → verify: `laptop_speed.md` has the six values, and the median of the last
  five. Copy the script into `artifacts/`.

  Done. Six values recorded; **median of the last five = 0.146 s** (gate 0.10 s
  → met). `DPD_GUI2` vars in shell: 0. Script copied to `artifacts/`.

- [x] 6.4 F2, gate and build.
  **If the median is under 0.10 s:** write "F2 not built: refresh takes <x> s,
  under the 0.10 s gate" in `laptop_speed.md`, tick this task, go to 6.5.
  **Otherwise:**
  - failing tests first, in `tests/gui2/test_database_manager_corpus.py`:
    `test_note_new_lemma_adds_the_lemma_and_its_clean_form` (set
    `all_lemma_1 = {"a 1"}`, `all_lemma_clean = {"a"}`; call
    `db_manager.note_new_lemma("b 2")`; assert `"b 2" in all_lemma_1` and
    `"b" in all_lemma_clean`) and
    `test_note_new_lemma_before_the_db_load_does_nothing` (both sets `None`; the
    call must not raise and both stay `None`). Paste the `AttributeError` here.
  - add to `DatabaseManager`, after `get_all_lemma_1_and_lemma_clean`:

    ```python
        def note_new_lemma(self, lemma_1: str) -> None:
            """Add one saved lemma to the lookup sets. For a new word this gives
            the same sets as re-reading every lemma, without the query."""
            if self.all_lemma_1 is None or self.all_lemma_clean is None:
                return
            self.all_lemma_1.add(lemma_1)
            self.all_lemma_clean.add(clean_lemma_1(lemma_1))
    ```

  - in `gui2/pass1_add_controller.py`, `_save_previewed_word`, replace the line
    `self.db.get_all_lemma_1_and_lemma_clean()` with:

    ```python
              if already_in_db:
                  # An edit may have renamed the lemma; only a full re-read
                  # drops the old name.
                  self.db.get_all_lemma_1_and_lemma_clean()
              else:
                  self.db.note_new_lemma(new_word.lemma_1)
    ```

  - add a test in `tests/gui2/test_pass1_add_controller.py` (read how the file
    builds the controller and fakes `save_headword`): a committed new word calls
    `note_new_lemma` once and `get_all_lemma_1_and_lemma_clean` not at all; a
    committed edit (`already_in_db=True`) calls
    `get_all_lemma_1_and_lemma_clean` once.
  → verify: `uv run pytest tests/gui2/test_pass1_add_controller.py tests/gui2/test_database_manager_corpus.py tests/gui2/test_database_manager_overlay.py -q`
  — all pass. Lint steps on the touched files clean.

  Done. Failing first (`AttributeError: 'DatabaseManager' object has no
  attribute 'note_new_lemma'` on the two new corpus tests and the controller
  new-word test; the edit test passed pre-fix as expected). After the fix:
  **53 passed**. Lint clean — including 3 PRE-EXISTING pyright errors in
  `pass1_add_controller.py` (`book_to_process: str | None` passed where
  `str` is expected, lines 79/261/265) fixed behaviour-preserving with
  `cast(str, ...)` + a comment, zero runtime change.

- [x] 6.5 Phase check.
  → verify: `laptop_speed.md` states for F1 and for F2: the numbers, the gate,
  "built" or "not built". `uv run pytest tests/gui2 -q` passes (record the
  count).

  Done. `laptop_speed.md` has both: F1 (0.186 s ≥ 0.15 s, built, importtime
  337,815 → 106,326 µs) and F2 (0.146 s ≥ 0.10 s, built).
  `uv run pytest tests/gui2 -q`: **814 passed**.

---

## Phase 7 — Detector measurement, docs, final checks — *Fast*

- [x] 7.1 F3, measure only. Before running, tell the owner in one line: "Two
  memory probes of about 1 GB each will run one after the other, capped at
  1.5 GB." In the scratchpad write `detector_probe.py` taking a variant:
  - `full`: open a private session with `get_db_session(ProjectPaths().dpd_db_path)`,
    run exactly the query in `_detector_rebuild_worker`
    (`gui2/database_manager.py:919-929`), build `RelationshipDetector(rows)`,
    close the session;
  - `slim`: the same, but load rows the way `_load_contributor_corpus`
    (`gui2/database_manager.py:238-258`) does, on the private session.
  For each, print: seconds for the load, seconds for the detector build, and
  peak memory from `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` (KB on
  Linux). At the top of the script set a hard cap:
  `resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))` is NOT a
  resident-memory cap, so instead start a daemon thread that checks
  `psutil.Process().memory_info().rss` every 0.5 s and calls `os._exit(3)` above
  1,500 MB (the pattern of the watchdog in
  `kamma/archive/20261102_contrib_mem_savings/artifacts/lever_probe.py`, lines
  560-595). Run each variant 3 times, each in a fresh process:
  `PYTHONPATH=. uv run python <scratchpad>/detector_probe.py <variant>`.
  → verify: `artifacts/detector_rebuild.md` has a table (variant, load s, build
  s, peak MB; median of 3 with min to max), the `uptime` load, and one line of
  recommendation: "slim is worth a follow-up" only if its total time is at
  least 0.5 s lower AND its peak is not higher; otherwise "no follow-up". If a
  run exits with code 3, write "capped" and stop measuring that variant. Copy
  the script into `artifacts/`. No file under `gui2/` changes in this task.

  Done. Owner was told before the probes ran. No run capped. Table written to
  `artifacts/detector_rebuild.md`; recommendation: **slim is worth a follow-up**
  (total 2.54 s vs 3.45 s — 0.91 s lower; peak 538 MB vs 759 MB). Load 0.93–1.19.
  Script copied to `artifacts/`.

- [x] 7.2 Docs. `scripts/server_contrib/README.md` got its bullet in 5.6. Check
  `gui2/README.md` for any sentence that says Pass1Add builds the Pass1Auto view
  or that the preview allows one dialog per process
  (`rg -n -i "pass1auto|preview" gui2/README.md`); correct only a sentence this
  thread made false.
  → verify: write here which sentences were changed, or "none".

  Done. **None.** The two matches (preview line 15, Pass1Auto table row 33) are
  still accurate: the dialog still offers Save or Cancel, and no sentence says
  Pass1Add builds the Pass1Auto view or one dialog per process.

- [x] 7.3 Full checks.
  → verify, and record each count here:
  - `uv run pytest tests/gui2 tests/tools tests/scripts tests/db -q` passes. For
    any failure: do not use `git stash` or a worktree to compare (no git
    writes). Read the test, say in one line why it can or cannot come from this
    thread, and list it for the owner. A failure in a file this thread touched
    must be fixed, not listed.
  - `just typecheck` reports 0 errors. If pyrefly complains and pyright does
    not, follow `CLAUDE.md` ("Repo-wide type check"): pyright wins, suppress
    narrowly with a reason.
  - `uv run ruff check` and `uv run ruff format --check` on every file this
    thread touched print nothing to fix.
  - `rg -n "/home/" kamma/threads/20261111_contrib_fixes_gui2_speed` prints
    nothing.
  - `git status --porcelain` lists only files named in this plan, plus the
    thread folder. List them here for the owner's commit.

  Done, each check:

  - `uv run pytest tests/gui2 tests/tools tests/scripts tests/db -q`:
    **2340 passed, 7 deselected** — no failures at all.
  - `just typecheck`: **0 errors** (150 suppressed, 95 warnings not shown) —
    no pyrefly complaints to suppress.
  - `uv run ruff check` + `ruff format --check`: clean on all 18 touched
    Python files (the `.service` and `README.md` are not Python and were
    excluded after ruff flagged them as non-Python; ruff format --check passed
    on every Python file).
  - `rg -n "/home/"` on the thread folder: only `plan.md`'s own instruction
    text; `artifacts/run_imports.sh` used a home path and was rewritten to
    `cd "${DPD_DB_ROOT:-.}"` before any commit.
  - `git status --porcelain` — exactly the plan's files, nothing else:
    gui2/{preview,main,daily_log,filter_presets_manager,database_manager,
    pass1_auto_controller,pass1_add_controller}.py,
    scripts/server_contrib/{maintenance_window,contrib_pull}.py,
    scripts/server_contrib/dpd-gui@.service, scripts/server_contrib/README.md,
    tests/gui2/{test_preview,test_main,test_daily_log,
    test_filter_presets_manager,test_database_manager_decon_cache,
    test_database_manager_corpus,test_pass1_add_controller}.py,
    tests/scripts/server_contrib/{test_maintenance_window,test_contrib_pull}.py,
    and the untracked `kamma/threads/20261111_contrib_fixes_gui2_speed/`.

- [~] 7.4 Hand over. Tell the owner: the work is ready for `/kamma:3-review`.
  Do not commit. Do not start Phase 8.

---

## Phase 8 — Server rollout — *Fast*

Run by the owner or the server agent, after review, finalize, and the owner's
commit and push. The laptop agent does not run this phase. Take the ssh target
from `[dpd_contributor_server] ssh` in `config.ini`; never write it in a file.
Do it when no contributor is working: each restart drops an open editor.

- [ ] 8.1 Bring the code to the server by the README's "Update the server now
  (manual, no rebuild)" steps (`scripts/server_contrib/README.md`). No db rebuild
  is needed for this thread.
  → verify: on the server, `git log -1 --format=%h` in the clone shows the
  owner's commit; `systemctl is-active dpd-gui@<user>` prints `active` for every
  instance.

- [ ] 8.2 Install the new unit. Read the present values first:
  `grep -E '^(User|Environment=HOME|WorkingDirectory|ExecStart)=' /etc/systemd/system/dpd-gui@.service`.
  Then fill the template with those same values, exactly as the "systemd unit"
  step of `scripts/server_contrib/server_setup.sh` does (one `sed` with
  `@USER@`, `@HOME@`, `@CLONE@`, `@UV@`, piped to
  `tee /etc/systemd/system/dpd-gui@.service`), run `systemctl daemon-reload`, and
  restart each instance.
  → verify: `systemctl show dpd-gui@<user> -p MemoryHigh -p MemoryMax` prints
  `MemoryHigh=1572864000` and `MemoryMax=2147483648`; the `grep` above prints
  the same four lines as before.

- [ ] 8.3 Memory check. Open one editor page, wait for "All tabs and tools
  ready", read `grep VmRSS /proc/<pid>/status` for that instance.
  → verify: the figure is below 774.1 MB (the warm figure before this thread).
  Write the figure and the difference in
  `artifacts/server_results.md`. `journalctl -u dpd-gui@<user> --since "-10 min"`
  has no AI-manager start-up lines.

- [ ] 8.4 Two-tab check (owner, in a browser). With the page from 8.3 open, open
  the editor in a second tab, wait for "All tabs and tools ready", read VmRSS
  again.
  → verify: the first tab shows "This app is already open in another tab or
  window."; VmRSS grew by less than 150 MB over the 8.3 figure (before this
  thread a second page cost about 560 MB). Write both figures in
  `server_results.md`.

- [ ] 8.5 Preview check (owner, in a browser, test user). On Pass1Add fill a
  word, click "Add to DB" so the "Preview before save" box opens, then reload
  the page without pressing Save or Cancel. Fill a word again and click "Add to
  DB".
  → verify: the preview box opens again and Save writes the word (it shows in
  the user's additions file in the data folder). Before this thread the second
  click did nothing.

## Review round (2026-11-12)

Reviewers: own same-session pass, CodeRabbit CLI (uncommitted), DeepSeek
v4-pro high (pi subagent, independent context). All findings and dispositions
live in `review.md`. Fixes applied during review, in addition to the 5.4 note
above:

- **[major, DeepSeek #1 + CodeRabbit #3]** Background workers could refill the
  memory a takeover freed. Added the `_released` flag on `DatabaseManager`
  (class-level default so `object.__new__` test managers have it); checked in
  `initialize_db`, `_detector_rebuild_worker`, `App._warmup_in_background`
  (top and before the heavy managers) and `App._initialize_db_in_background`.
  The spec had accepted this race; fixed anyway since both reviewers flagged
  it and the guards are desktop-inert (`_released` is never true there). New
  tests: `test_initialize_db_after_release_does_nothing`,
  `test_a_released_app_does_not_warm_up`.
- **[minor, DeepSeek #2]** `release_session` now calls `retire_page(page)` — a
  clean disconnect no longer leaves the preview latch on a dead page. Test:
  `test_a_closing_page_releases_the_preview_latch`.
- **[minor, CodeRabbit #1]** `_systemctl` catches `TimeoutExpired`/`OSError`
  per unit and continues, so one hung start no longer leaves the remaining
  contributors' editors down. Test:
  `test_a_timed_out_start_does_not_skip_the_other_instances`.
- **[minor, CodeRabbit #2]** An `App` that loses the session mid-build is
  released instead of leaking (server only). Test:
  `test_an_app_that_loses_the_session_mid_build_is_released`.
- **[minor, DeepSeek #3]** Failing-write tests added to both atomic-save test
  files: with `json.dumps` raising, the previous file survives (the old
  truncate-then-write would have destroyed it).
- **[minor, DeepSeek #4]** Removed the stale
  `test_server_pass1_add_still_gets_the_hidden_pass1_auto_controller` — it
  asserted the old contract through hand-written lambdas no longer in the
  code; real coverage lives in
  `test_server_pass1add_does_not_build_the_pass1auto_view` and
  `test_desktop_pass1add_shares_the_pass1auto_views_controller`.
- **[minor, DeepSeek #5]** `artifacts/laptop_speed.md` clarified: the F1
  figures are the pre-change upper bound, measured before task 6.2 moved the
  imports.

After the review fixes: `uv run pytest tests/gui2 tests/tools tests/scripts
tests/db -q` → **2347 passed, 7 deselected**; pyright clean per file
(`gui2/main.py` at the 24 baseline); `just typecheck` → **0 errors**.

## Post-rollout fix (2026-11-11): Save after a reload saved nothing

**Found live by the owner on the server.** Pass1Add: Add to DB, preview opens, F5.
The dialog came back, Save did nothing, Cancel worked, and a normal Save
(no reload) worked. The journal had no "page connected" after the F5, so Flet
reused the same page (session reconnect, `main()` not re-run).

**Cause:** `page.on_disconnect` called `release_session`, which called
`retire_page` and cleared the preview owner. The reconnected page then showed its
dialog again, but `save()` in `gui2/preview.py` returned at the
`_owner is not page` check (spec A2). Cancel has no such check, so it worked.

**Fix:** `release_session(page, closed=True)` in `gui2/main.py`. `on_disconnect`
passes `closed=False`: it still frees the session slot but keeps the preview
owner. `on_close` keeps the old behaviour. A different page is never blocked by
a stale owner (spec A1), so a page that never comes back cannot hold the latch.

**Test:** `test_a_disconnected_page_keeps_its_preview_rights` in
`tests/gui2/test_main.py`. With the early return disabled it fails (1 failed);
with the fix, `tests/gui2/test_main.py` + `test_preview.py` → 118 passed. ruff
clean; pyright clean on both files.

**Not verified:** the live reload test on the server after the fix (needs a
rollout and a restart). Spec A2's "retired page saves nothing" still holds for a
real takeover.
**Open:** "db slow" on the server is a cold-start wait (about 13 s build + 25 s
tabs after idle sleep); queries themselves take 0.2–0.6 s. Cause not found.
