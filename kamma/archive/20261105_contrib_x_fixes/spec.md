# Spec: contributor problem children, the small fixes

**Thread:** 20261105_contrib_x_fixes
**GitHub issue:** [#215](https://github.com/digitalpalidictionary/dpd-db/issues/215)
**Source:** triage of `kamma/threads/20261030_contrib_x_problem_children` (`spec.md` items 1 to 30, owner decisions in its `plan.md`, 2026-11-05).

## TL;DR

The triage left 11 small fixes. The owner added two more: the Translations tab for every contributor, and the translation database always on the server. One thread does all 13 tasks, plus a time-boxed look at the flaky test.

**What the thread changes**
- The Pass2 clipboard copy no longer cuts off a save. A failed copy shows a message.
- The preview folder is made before the app starts.
- The read-only database warning is silent. Other errors still print.
- The helper web server start is removed from gui2, with its dead code and tests.
- Renaming an inflection pattern marks the word cache stale.
- The unused additions manager is removed from the Pass1 controller.
- The daily pull sends a desktop notice every time it skips because the editor is open.
- The nightly window deletes the 883 MB database copy after a good run. The git checkout stays, and both are added to `.gitignore`.
- Save is greyed out on the DB, √ and Infl tabs for contributors. Ctrl+S still shows the old message.
- A contributor with no saved preset sees the DB tab filtered on `lemma_1`, showing id, pos, grammar, meaning_1, meaning_2 and meaning_lit.
- The Alt shortcuts are off in the web version only. The desktop keeps them.
- Every contributor sees the Translations tab.
- The server loads a fourth submodule. A nightly step downloads the translation database when it is missing. A failure goes to the log and the status page, and the window carries on.

**Decisions already made**
- Audio in the preview, and a contributor changing their own password, get their own threads.
- The username fix is dropped because the code already does it.

**Open risks**
- The regex search over the 807 MB database may be heavy for several contributors on the 2 CPU server. The tab's limits were not read.
- The server must be able to reach GitHub to download the database.
- Chrome's Alt+D, Alt+E and Alt+F clashes are from memory. Only Alt+Left and Alt+Right are confirmed.

**Review:** three rounds with DeepSeek flash through pi, 104 findings. 61 were accepted, 42 rejected after the code was checked, and 1 went to the owner.

## Overview

The triage left eleven small fixes and one investigation. The owner decided each one. The owner then added two more (items 13 and 14): the Translations tab for every contributor, and the translation database always present on the server. They touch gui2 (the dictionary editing app), the contributor-server scripts in `scripts/server_contrib/`, and their tests. None needs a new design. Do them one task each, with a test where the fix has behaviour.

Two larger wishes from the same triage are NOT in this thread and get their own threads later: audio in the preview on the desktop, and a contributor changing their own password.

## What it should do

Each fix is stated with the current behaviour (read from the code on 2026-11-05).

### 1. Clipboard copy in Pass2 Add
`gui2/pass2_add_view.py` awaits `ft.Clipboard().set(...)` at two places (~1066 after a save, ~1344 after the X-word button). Neither is in a try block. A browser that refuses the copy raises `PlatformException` and cuts off the rest of the save.
Wanted: one small async helper on `Pass2AddView`, `_copy_lemma(self, lemma_1: str) -> bool`, that does `await ft.Clipboard().set(lemma_1)` inside `try/except Exception` (not `CancelledError`) and returns `True` on success and `False` on failure. Both sites call it. The rest of the save continues. The message goes through the view's `update_message`, as a plain string without the exception text:
- At ~1066 (inside `_save_previewed_word`, success branch): `clear_all_fields()` ends with `self.update_message("")`, which erases any message set before it. So the failure message goes AFTER `self.clear_all_fields()` and before `self._show_missing_words_dialog(word_to_save)`: `self.update_message("Saved, but lemma_1 was not copied (clipboard blocked)")`. On success nothing changes.
- At ~1344 (X-word button): the existing two messages stay word for word when the copy worked. On failure the same two messages end with `(lemma_1 NOT copied: clipboard blocked)` in place of `(lemma_1 copied)`.

### 2. Preview folder before the app starts
Flet checks once, at `ft.run`, that the assets folder exists. A fresh clone has none; `write_preview()` in `gui2/preview.py` makes `PREVIEW_DIR` (`gui2/assets/preview`) only after start.
Wanted: `gui2/main.py` makes `PREVIEW_DIR` (imported from `gui2.preview`) with `mkdir(parents=True, exist_ok=True)` immediately before `ft.run(main)` (now at ~755, inside `if __name__ == "__main__":`). That line cannot be tested where it stands, so move the two lines into a small function `run_app() -> None` and let the `__main__` block call `run_app()`. The test replaces `gui2.main.ft.run` with a recorder and `gui2.main.PREVIEW_DIR` with a path under `tmp_path`, calls `run_app()`, and checks that the folder existed when `ft.run` was called. The path is relative to the working folder, as in `preview.py`.

### 3. Decon cache save on a read-only database
`gui2/database_manager.py` (~388-399) wraps `save_decon_no_headwords_cache` in `try/except Exception`, prints `decon cache refresh failed: <exc>`, and rolls back the session. On the read-only server database this prints on every start.
Wanted: keep the try, the `self.db_session.rollback()` and the print for every other error. Skip only the print when `"readonly database" in str(exc).lower()`. SQLite fixes that text ("attempt to write a readonly database"), and SQLAlchemy keeps it inside `str(exc)`. No new probe, no new query. The test makes the error with a real read-only SQLite file (a temp db opened read-only, then a write), not with a typed-in string.

### 4. Remove the helper web server
`gui2/main.py` imports and calls `start_dpd_server()` (~746) and prints `FastAPI server started in ...`. `tools/fast_api_utils.py` starts uvicorn on `127.1.1.1:8080`. Nothing in gui2 calls the helper any more: `request_dpd_server` is called only from `archive/`. The owner says the browser extension (`exporter/wxt_extension/wxt.config.ts` lists that address) is not used against a gui2-started server.
Wanted: delete the call, its import and its print from `gui2/main.py`. Delete `tools/fast_api_utils.py` and `tests/tools/test_fast_api_utils.py`. Remove the two lines `monkeypatch.setattr("gui2.main.start_dpd_server", MagicMock())` in `tests/gui2/test_main.py` (~627 and ~652; they would raise `AttributeError` once the name is gone). The comment above the call ("Start the FastAPI server after the UI has painted ...") goes too. Sweep with `rg --hidden` for `start_dpd_server`, `fast_api_utils`, `DPD_API_PORT`, `127.1.1.1:8080` and `FastAPI server`. Rule for each hit outside `archive/`, `exporter/wxt_extension/` and the `justfile` `webapp` recipe: if it names the gui2-started helper or its port variable (`DPD_API_PORT`), remove that mention. Known hit: the comment at `scripts/server_contrib/config_server.template:16` lists `DPD_API_PORT` among the per-instance environment variables; take it out of that list. Anything that describes the webapp itself (its own port, the extension) stays. List every edited and every kept hit in `plan.md`.

### 5. Pattern rename marks the corpus stale
`rename_pattern_in_headwords` (`gui2/database_manager.py` ~795) commits and never calls `mark_corpus_stale()`, unlike the other write methods. `mark_corpus_stale()` only sets a flag; the corpus reloads on its next use.
Wanted: call `self.mark_corpus_stale()` after the commit. Add a test that the flag is set.

### 6. Unused additions manager
`gui2/pass1_add_controller.py` imports `AdditionsManager` (line 8) and stores `self.additions_manager` (line 48). Nothing reads it.
Wanted: delete both lines, after an `rg` sweep (including `tests/`) that proves nothing reads `Pass1AddController.additions_manager`.

### 7. Notice when the pull skips because the editor is open
`scripts/server_contrib/contrib_pull.py` sets `status.outcome = "skipped: editor open"` at two places: in `run` (~526, before the pull) and in `_pull` (~476, the editor opened during the pull). `main` (~596) sends no notice for any outcome that starts with `skipped`. The status file is not written for a skip.
Wanted: a module constant `EDITOR_OPEN = "skipped: editor open"` used at both sites (and in `main`), a new function `notify_editor_open(status: Status) -> None` that calls `notify(status.outcome)` and swallows `OSError` and `subprocess.SubprocessError`, and in `main` the single `if not args.dry_run and not status.outcome.startswith("skipped"):` block becomes:
```
if not args.dry_run:
    if status.outcome == EDITOR_OPEN:
        notify_editor_open(status)
    elif not status.outcome.startswith("skipped"):
        (the existing maybe_notify and notice_error lines, unchanged)
```
The skip notice writes no status file and never sets `notice_error` (a skip writes no status). The text is the outcome string, the same for both sites. The "already done today" and "another run" skips stay silent. The owner decided "every time"; no once-a-day limit. Tests: `run` returns that outcome when `editor_running` is true, and `main` calls `notify` once for it, not for the two other skips, not on a dry run, and survives a failing `notify`.

### 8. Server cleanup after a good run
`run_maintenance` (`scripts/server_contrib/maintenance_window.py` ~373-442) copies the database to `dpd.db.prev` through `_capture_rollback` on every run that passes the dirty check, and `_restore_rollback` reads it back after a failure. The copy is 883 MB and is never removed.
Wanted: in the `finally` block of `run_maintenance`, after `_systemctl("start", ...)` and before `_write_status`, when `outcome is not Outcome.FAILED`, delete `config.db_path.with_name(config.db_path.name + ".prev")` with `unlink(missing_ok=True)`. Build the path from `config`; do not use the `rollback` variable, which is not set when the run returns early (instances would not stop, or the working tree was dirty). Both early returns set `FAILED`, so they delete nothing. Log the file name and size with `log.info` before the delete. An `OSError` on the delete is logged with `log.warning` and never raised (it is in a `finally`). A failed run keeps the file. A `SKIPPED` run (rebuild skipped, main unchanged) deletes it too: nothing in the window writes `dpd.db` except the rebuild steps, and `reconcile_all` only edits contributor files. If `_systemctl("start")` fails the copy is still deleted; the copy is only for rolling back a failed rebuild.
The temporary git checkout (`<project-root>_contrib_worktree`, made by `contrib_push._ensure_worktree`) is NOT deleted: the push script reuses it every night, and a deleted one costs a full checkout while the instances are stopped. Owner decision 2026-11-05. Add `dpd.db.prev` and `*_contrib_worktree/` to `.gitignore`, so a checkout placed inside the clone never shows as untracked. The default path is beside the clone, outside the repo.
The old safety copies in the server's `/root/mem` are a one-off command for the owner, not part of this fix.

### 9. Save Changes button on read-only tabs
`GlobalView._view` (`gui2/main.py` ~486-487) sets `read_only = True` on a view right after building it, for tabs in `_read_only` (DB, √, Infl for a contributor). Their save handlers then show `READ_ONLY_MESSAGE`. The save buttons, by tab:
- DB tab: `FilterComponent` (`gui2/filter_component.py` ~174) builds `ft.Button("Save Changes", on_click=self._save_changes)`. `FilterComponent` is built later by `FilterTabView` (`filter_tab_view.py` ~497-504) with `read_only=self.read_only`. Handler `_save_changes` (~426-431).
- √ tab: `roots_tab_view.py` ~177 `ft.Button("Save to DB", on_click=self._save_root)`, built in the constructor, so before `read_only` is set. Handlers `_save_root` (~293) and one more guard at ~343.
- Infl tab: `inflection_templates_tab_view.py` ~426 `ft.Button("Save", on_click=self._save_template)`, built in the constructor. Handler guards at ~789, ~844, ~881.
Wanted: on a read-only tab the Save button is disabled (greyed out). All three keep the button in an attribute named `save_button`. DB tab: `FilterComponent._build_ui` builds it with `disabled=self.read_only` (the component receives `read_only` in its constructor). √ and Infl: build it in `_build_bottom_section` as `self.save_button = ft.Button(...)` and use that attribute in the row; in `GlobalView._view` after `setattr(view, "read_only", True)` add `save_button = getattr(view, "save_button", None)` and, when it is not None, `save_button.disabled = True`. The Delete, Rename, Copy and other write buttons are not changed (the owner asked for Save only); their handlers still refuse. Keep the refusal in the handlers: the Ctrl+S key reaches them without the button, and the message is kept for that path only. Tests: the button is disabled for a read-only DB tab and a read-only √ and Infl view, and enabled otherwise.

### 10. Starter preset for contributors on the DB tab
`GlobalView` builds the DB tab with `FilterTabView(self.page, self.toolkit)` (`gui2/main.py:188`). `FilterTabView.__init__` (`gui2/filter_tab_view.py` ~20-87) has the parameters `data_filters` (default `[("root_key", ""), ("family_root", "")]`, a list of `(column, regex)` pairs) and `display_filters` (default `["id", "lemma_1", "meaning_1", "meaning_lit", "root_key", "family_root"]`). It loads the first saved preset from `filter_presets_<username>.json`; when none exists it uses those parameters. `_reset_to_default_clicked` (~771-830) does the same, but with the same values typed in again in its `else` branch.
Wanted: for a non-primary user (`self.toolkit.username_manager.is_not_primary()`, the instance method) with no saved preset, the defaults are `data_filters=[("lemma_1", "")]` and `display_filters=["id", "pos", "grammar", "meaning_1", "meaning_2", "meaning_lit"]` (all six are `DpdHeadword` columns; the task checks with the model). Do it by passing these two arguments at `main.py:188` when the user is non-primary. In `_reset_to_default_clicked`, make the `else` branch use the values the constructor received (stored as attributes) instead of its typed-in copy, so Reset gives the same starter. The default values of the parameters stay as they are, so the primary user and `gui2/test_app.py` see no change. A saved preset always wins. No migration of stored presets: the set of columns offered does not change. Tests: a non-primary user with no preset file gets the starter; with a preset file gets the preset; a primary user gets the old defaults; Reset gives the starter.

### 11. Alt shortcuts off in the web version
`GlobalView.on_keyboard` (`gui2/main.py`, from ~299) handles Alt+G T P E D S B R C I (tab jump, `_TAB_JUMP_KEYS`), Alt+X (clear), Alt+? and Alt+/ (the shortcuts popup), and Alt+Arrow Left and Right (tab left and right). Some clash with Chrome. Chrome's own list ([Chrome keyboard shortcuts](https://support.google.com/chrome/answer/157179)) confirms only Alt+Left and Alt+Right (back and forward); the owner says those are fine in Chrome. Alt+D, Alt+E and Alt+F as Chrome keys are from memory and unverified.
Wanted: at the top of `on_keyboard` define `alt = e.alt and not self.page.web` and use `alt` in place of `e.alt` in all five branches that test it (Arrow Left, Arrow Right, X, the popup, the tab jump). The desktop keeps all of them. Do not work from a key list; guard by the `e.alt` test. The popup (`build_shortcuts_dialog`) is opened only from the Alt+? branch (checked: no other caller), so in the web it cannot open and lists no dead keys. Ctrl keys and the page-scroll keys are untouched. Add a test: Alt+G changes the tab when `page.web` is false and does nothing when it is true.
Effect on the existing tests in `tests/gui2/test_main.py` (read 2026-11-05): `_app_on_tab` builds the page as a `SimpleNamespace` with no `web` attribute, so `self.page.web` would raise `AttributeError`; add `web=False` to it. `_server_app` builds the page as a `MagicMock`, whose `.web` is a truthy `MagicMock`, which would turn Alt off in every server test; set `app.page.web = False` there, with a comment that these tests cover tab visibility and that web behaviour has its own test. Tests that use Alt keys on a `_server_app`: `test_server_alt_jump_selects_a_listed_tab`, `test_server_marks_read_tabs_read_only_and_ctrl_s_reaches_the_handler`, `test_server_alt_arrows_stay_inside_the_visible_tabs` (all keep passing with `web = False`).
Later, maybe: a settings section to customise shortcuts. Not now.

### 12. The flaky maintenance test
`tests/scripts/server_contrib/test_maintenance_window.py::TestHappyPath::test_status_file_reports_a_failure_and_its_reason` failed once in a full run (`problems: 0`, expected `problems: 1`) and passed 5 later runs. The cause is unknown. `_write_status` (`maintenance_window.py` ~180-215) reads that day's log from the last `INFO maintenance window start` line and counts ERROR and WARNING lines. The test runs one window in a fresh `tmp_path`, so a "two runs in one log" theory does not fit it.
Wanted: a time-boxed look. Run the test alone 30 times and the whole file 10 times, and record the exact commands in `plan.md`. If it fails, keep the status file and the log file (name and text) from that run and find the cause. If it never fails, record "not reproduced" in `plan.md` and stop. Change no code without a proven cause.

Cause found 2026-11-05: importing pyglossary changes the logger class for the whole process and its addHandler replaces the handler's formatter; _make_logger now sets the formatter after addHandler. See plan task 16.1.

### 13. The Translations tab for every contributor (added by the owner 2026-11-05)
`gui2/contributor_tabs.py` has `BASE_TABS = ("Pass1Add",)` and `SAFE_TABS = ("Transl", "Bold Search")`. A contributor sees `Transl` only when the maintainer lists it in `DPD_GUI2_TABS`.
Wanted: every contributor on the web server sees the Transl tab, whatever `DPD_GUI2_TABS` says. Make `BASE_TABS = ("Pass1Add", "Transl")` and `SAFE_TABS = ("Bold Search",)`. The tab is search-only (`gui2/translations_view.py` writes nothing). Tab order does not change (Transl is index 1, so it is shown before Pass1Add, which stays the start tab). Update the tests that name the visible tabs (`tests/gui2/test_contributor_tabs.py`, the server tests in `tests/gui2/test_main.py`) and the table in `gui2/README.md`.

### 14. The translation database is always on the server (added by the owner 2026-11-05)
The tab reads `resources/tipitaka_translation_db/tipitaka-translation-data.db` (807 MB on the laptop; the download zip is 183 MB). It is gitignored. `tools/tipitaka_db.ensure_db_exists()` downloads it from the GitHub releases of `digitalpalidictionary/tipitaka-translation-db` when it is missing, through `resources/tipitaka_translation_db/download_and_unzip_db.py`, and is called on every search (`get_db_engine`). It prints an error and returns when the download fails, so a search then fails.
Read 2026-11-05: the server loads only three submodules (`scripts/server_contrib/server_setup.sh` line 17: `sc-data`, `dpd_submodules`, `tipitaka.rte`). The download script lives inside the fourth one, `resources/tipitaka_translation_db`, so on the server `ensure_db_exists()` cannot import it and the database never arrives. The nightly window runs `git submodule update --recursive` without `--init`, so it never loads a new submodule either.
Wanted:
- `server_setup.sh` loads `resources/tipitaka_translation_db` as a fourth submodule (a new server gets it).
- A new script `scripts/server_contrib/ensure_translation_db.py` calls `ensure_db_exists()` and exits 0 when the database file exists afterwards and 1 when it does not (the function only prints on failure).
- The nightly window gets one more injectable step, `translation_db`, run after the push step and before the rebuild decision, every night (also when the rebuild is skipped). The default step is `uv run scripts/server_contrib/ensure_translation_db.py` from the project root. A failure is logged with `log.error("translation db missing (window goes on): ...")` and never stops the window, like the push step. The log's ERROR line also lands in the status file the maintainer reads. Success logs `translation db present`.
- The docs that count submodules or list the server's network needs are updated (`scripts/server_contrib/README.md`, `NEW_SERVER_RUNBOOK.md`, `config_server.md`).
- For the server that already runs, the owner does a one-off (not part of the code): load the submodule once by hand, then let the next window download the database or run the new script detached. The plan's last task lists the commands.
Not done here: a message in the tab when the database is missing; limits on how many regex searches run at once on the server.

## Assumptions & uncertainties

Verified in the code on 2026-11-05 (re-read before editing, other threads share the tree):
- Everything quoted above with a file and a line.
- The username item from the triage is already done: `UsernameManager.routed_username = self.username or "1"` is set at start-up and `is_not_primary()` reads it; `gui2/toolkit.py` uses the same expression. It is dropped.
- `dpd.db.prev` is created at `maintenance_window.py:288` and read back by `_restore_rollback`.

Not verified:
- The server can reach `api.github.com` and the release download over HTTPS (it already pulls from GitHub; the first download is the proof).
- The regex search over an 807 MB database is cheap enough for several contributors on the 2 vCPU server. The webapp limits concurrent searches (`tools/search_deadline.py`); whether gui2's Transl tab does is not read. Risk, owner to watch.
- `self.page.web` is true for the Flet web server that contributors use. `gui2/preview.py:170` already relies on it. Task 11 proves it with a test that sets the value; a live check is the owner's.
- Where the DB tab's defaults are passed to `FilterTabView` (probably in `gui2/main.py`), and where each read-only tab keeps its Save controls. Tasks 9 and 10 find them.
- Whether the server passes `--worktree` a path inside the clone. The default is outside it.
- A contributor on the web server that has a saved preset file keeps that preset.

Goldfish findings accepted at Gate 1 (details in `egm/gate1.md`):
- Delete the database copy only when the run did not fail, and log what is deleted (Major, from four reviewers).
- Keep the checkout (the owner answered the escalation).
- Hide the cache print only for the read-only error; keep it for others (Blocker, from two reviewers).
- Show a message when a copy fails; do not swallow it silently (Major).
- Keep the Ctrl+S refusal when the Save button is disabled (Major).
- A saved preset wins over the new starter (Major).

## Constraints

- Follow `CLAUDE.md`: type hints, `Path`, `ic` not `print` in new code, `ruff check --fix`, `ruff format`, `pyright` (for `gui2/` and `tests/` use `uv run pyright --project /dev/null <file>`), related tests, then `just typecheck`.
- Never `git stash`, `checkout --`, `restore` or `reset --hard`. Stage by explicit file list. The owner commits; no commit and no GitHub write by this thread.
- No change to `.env` or `.ini` files.
- Keep each fix to the smallest change that does what it says. No flags, no helpers beyond what a fix needs.

## How we'll know it's done

- Each fix has a test that fails without the fix (revert the change, run, count the failures) or, for a deletion, an `rg --hidden` sweep that shows no leftover mention.
- `uv run pytest tests/` passes, apart from failures that were already there and are logged in `plan.md`.
- `just typecheck` passes. `ruff` and `pyright` pass on every touched file.
- The owner confirms in a live run, which no test can show: Alt keys act on the desktop and not in Chrome; Save is greyed on a read-only tab; the starter preset appears for a contributor with no saved preset; a contributor session shows the Transl tab and a search returns text; the next nightly window logs `translation db present`.

## What's not included

- Audio in the preview on the desktop (own thread).
- A contributor changing their own password (own thread).
- Deleting the nightly checkout; the owner chose to keep it.
- The username value fix (already in place).
- Items the triage dropped or parked (see `20261030_contrib_x_problem_children/plan.md`).
- Removing `/root/mem` safety copies on the server (a one-off command for the owner).
- A message in the Transl tab when the database is missing, and a limit on concurrent regex searches on the server.
- Updating the translation database to a newer release (the window only makes sure a copy exists).

## Review record

Backend: pi with `deepseek-flash` (thinking off, read-only tools), one Goldfish at a time. The first probe on `azure` / `deepseek-v4.1-flash` hung and was replaced by the direct `deepseek` provider.
- Gate 1, the idea: `egm/gate1.md`. Six Goldfish, 40 findings: 22 accepted, 17 rejected, 1 escalated (the nightly checkout; the owner chose to keep it).
- Gate 2, this spec: `egm/gate2.md`. Two Goldfish, 17 findings: 12 accepted, 5 rejected, 0 escalated.
- Gate 3, the plan: `egm/gate3.md`. Five Goldfish (one per part of the plan), 47 findings: 27 accepted, 20 rejected, 0 escalated.
- Total: 104 findings, 61 accepted, 42 rejected, 1 escalated. Raw reports are in `egm/raw/`.
- Not reviewed by a Goldfish: the two items the owner added after Gate 2 (spec items 13 and 14) were reviewed at Gate 3 only, as plan tasks 12 and 13.
