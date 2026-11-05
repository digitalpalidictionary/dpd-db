PASSED — 4 nits, 0 blocking, 0 major, 0 minor. Ready for `/kamma:4-finalize`.

## Thread
- **ID:** 20261105_contrib_x_fixes
- **Objective:** 13 small contributor-server and gui2 fixes for issue #215 (11 triage fixes, Transl tab for every contributor, translation db always on the server), plus the two fixes from the first review (`review_fixes.md`).

## Files Changed
Read against plan task 15.4 and `review_fixes.md`; every listed file exists, both deleted files are gone, no git was used.
- `gui2/pass2_add_view.py` — `_copy_lemma` helper; a refused clipboard copy no longer cuts off a save; message set after `clear_all_fields()`.
- `gui2/main.py` — `run_app()` makes the preview folder; helper-server start removed; `_make_filter_tab` (contributor starter preset); Alt keys guarded by one `alt` variable (the only `e.alt` left); `save_button` disabled for read-only tabs.
- `gui2/database_manager.py` — silent only for "readonly database" (rollback and print kept for other errors); `mark_corpus_stale()` after a pattern rename.
- `gui2/filter_component.py`, `roots_tab_view.py`, `inflection_templates_tab_view.py` — `save_button` attribute, disabled when read-only.
- `gui2/filter_tab_view.py` — starter constants; Reset gives the constructor defaults.
- `gui2/contributor_tabs.py`, `gui2/README.md` — `Transl` is a base tab.
- `gui2/pass1_add_controller.py` — unused additions manager removed.
- `scripts/server_contrib/contrib_pull.py` — notice on every "skipped: editor open".
- `scripts/server_contrib/maintenance_window.py` — deletes `dpd.db.prev` when the run did not fail; `translation_db` step; log formatter set after `addHandler` (review fix 1).
- `scripts/server_contrib/ensure_translation_db.py` (new) — exit 0/1; deletes a broken zip and retries once (review fix 2).
- `scripts/server_contrib/server_setup.sh`, `README.md`, `NEW_SERVER_RUNBOOK.md`, `config_server.md`, `config_server.template`, `.gitignore` — fourth submodule, docs, ignore lines.
- Deleted: `tools/fast_api_utils.py`, `tests/tools/test_fast_api_utils.py`. Tests: 5 new files and 8 edited, as listed in 15.4.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `archive/gui/functions_db.py:17`, `archive/gui/gui_main.py:100` | Still import the deleted `tools.fast_api_utils`. | Dead archive code now fails on import. `archive/` is excluded from lint and the plan's sweep. | Leave, or delete the two imports with the archive next time it is touched. |
| 2 | nit | `justfile:163` | `flet run gui2/main.py -d` never reaches `run_app()`, so that dev path does not make the preview folder. | Desktop dev reload only; the server unit and `just gui` use `python gui2/main.py`. | Leave (known, owner aware). |
| 3 | nit | server rollout | On the server that already runs, the window logs `translation db missing` every night (status page `problems: 1`) until the owner loads the submodule by hand; the first download happens while instances are stopped. | Expected and documented (plan 15.5, `README.md`). | Owner runs the one-off in 15.5. |
| 4 | nit | `plan.md` 15.1 | Old sentence "owner to decide the fix" remains next to the new 0-failed line. | Cosmetic, can mislead a reader. | Delete the stale clause. |

Checks on the review fixes: `_make_logger` now sets the formatter after `addHandler` with a WHY comment, and `TestLogFormat` restores the logger class in a `finally`. The ensure script deletes the zip only when the db is still missing after the first try, and retries once. `plan.md` 4.1, 14.2, 14.3, 15.1, 15.4 and Phase 7, and `spec.md` item 12, match `review_fixes.md` Fix 3. Axes: security, architecture, performance and docs reviewed, nothing found.

## Fixes Applied
- None by this review. The two review fixes were applied by another agent before this review and were checked here.

## Test Evidence
- `uv run pytest tests -q -p no:cacheprovider` (scope: whole project, 12 slow tests deselected by default) → 2970 passed, 0 failed, 85.5 s
- `uv run pytest tests -k "<the two logging tests>" -q` (scope: collects the whole suite, `pyglossary` included, runs 2 tests; the real proof for fix 1) → 2 passed, 21 s
- `uv run pytest tests/gui2 tests/scripts/server_contrib -q` (scope: both folders) → 933 passed
- `ruff check` and `ruff format --check` on the 23 changed Python files → clean
- `pyright` on the 3 changed scripts and 5 new or changed test files → 0 errors

## Not Verified
- Live behaviour: Alt keys in Chrome, greyed Save button, starter preset on screen, a refused clipboard copy, the Transl tab on the server.
- A real download of the translation database from GitHub, and the nightly window on the real server.
- Load of regex searches on the 2 CPU server.
- The downloader (separate submodule) does no checksum check on the zip; not changed by this thread.
- CodeRabbit not run (it needs git; the owner ruled git out for this review). `just typecheck` not rerun here (0 errors recorded in plan 16.4). Plan statuses were read, not re-executed.

## Verdict
PASSED
- Review date: 2026-11-05
- Reviewer: Claude (Sonnet 5.5), review session; did not implement this thread, but made the earlier read-only review of it
