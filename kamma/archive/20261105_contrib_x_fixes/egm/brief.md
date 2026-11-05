# EGM brief: contrib_x_fixes

Thread: 20261105_contrib_x_fixes. Source: triage of `kamma/threads/20261030_contrib_x_problem_children` (spec.md items 1 to 30; plan.md holds the owner's decisions of 2026-11-05).

## Anchored hypothesis

The triage left twelve small, owner-approved fixes in gui2 (the dictionary editing app), the contributor-server scripts and the tests. They need no new design. One thread does them in order, one task each, with a test where the fix has behaviour. Two larger items (audio in the preview on desktop, and a contributor changing their own password) need a design of their own and move to separate threads.

## The twelve fixes (the owner decided each one)

1. Pass2 Add: wrap both `ft.Clipboard().set(...)` calls (`gui2/pass2_add_view.py`) so a refused copy never stops the rest of a save.
2. `gui2/main.py`: make the preview folder `gui2/assets/preview` before `ft.run`.
3. `gui2/database_manager.py`: skip `save_decon_no_headwords_cache` quietly when the db is read-only.
4. Remove the helper web server start (`start_dpd_server`) from gui2, with its dead code and tests.
5. `rename_pattern_in_headwords` (`gui2/database_manager.py`): call `mark_corpus_stale()`.
6. `gui2/pass1_add_controller.py`: remove the unused `additions_manager`.
7. `scripts/server_contrib/contrib_pull.py`: send the desktop notice on every "editor open" skip.
8. Server nightly window: delete `dpd.db.prev` and `_contrib_worktree/` after a good run only.
9. `gui2/user.py` and `gui2/toolkit.py`: `is_not_primary()` and `resolve_username() or "1"` must use one value.
10. Read-only tabs (DB, Roots, Infl): grey out the Save Changes button instead of showing a message.
11. DB tab: contributor starter preset is one filter, `lemma_1`; columns shown are id, pos, grammar, meaning_1, meaning_2, meaning_lit.
12. Alt shortcuts: turn them off in the web version only. The desktop keeps them.
Plus: investigate one flaky test (`tests/scripts/server_contrib/test_maintenance_window.py`, `test_status_file_reports_a_failure_and_its_reason`).

## Facts verified in the code on 2026-11-05 (claims to re-check, not facts)

- `start_dpd_server` is called only at `gui2/main.py:746`. `request_dpd_server` is called only from `archive/`. `exporter/wxt_extension/wxt.config.ts` lists `127.1.1.1:8080`; the owner says the extension is not used against a gui2-started server.
- The two clipboard calls are at `gui2/pass2_add_view.py` ~1066 and ~1344, not in a try block. Pass1 Add copies with `pyperclip`, inside a try for `PyperclipException`.
- `write_preview()` in `gui2/preview.py` makes the folder; `gui2/main.py` does not.
- `rename_pattern_in_headwords` (`gui2/database_manager.py` ~795) commits and never calls `mark_corpus_stale()`; other write methods in that file do.
- The decon cache save is already in a try/except that prints `decon cache refresh failed`.
- `gui2/contributor_tabs.py` shows contributors only Pass1 Add plus the extra tabs named in `DPD_GUI2_TABS` (safe or read-only).
- Alt keys live in `GlobalView.on_keyboard` and `_TAB_JUMP_KEYS` in `gui2/main.py`: G T P E D S B R C I, X (clear), ? and /, Arrow Left and Right.
- The pull writes no status and sends no notice on a skip (`contrib_pull.py` ~476 and ~526 set the outcome "skipped: editor open").
- `dpd.db.prev` and `_contrib_worktree/` stay on the server after a good run (owner's note; not read in code this session).
- One run of the full suite failed `test_status_file_reports_a_failure_and_its_reason` once (`problems: 0`, expected 1) and passed 5 later runs. Cause not found.

## Assumptions not verified

- The web version can be told apart from the desktop by `page.web` (used in `gui2/preview.py`).
- "Read-only tab" is the set `READ_TABS` in `gui2/contributor_tabs.py`, and a Save button can be found on each.
- Where the DB tab keeps its preset list and who writes the starter preset.
- Where in the nightly window script the old database copy and the worktree are made.
