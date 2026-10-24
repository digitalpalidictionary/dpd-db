# Review: inflection templates as TSV files, with a gui2 editor tab

**Thread:** 20261024_inflection_templates_tsv · **GitHub issue:** #273
**Verdict: PASSED**

The review was done outside the thread, by a separate pi agent ("inflectione
system 2", herdr pane wB:p59) in three rounds on the uncommitted tree. This
file records those reports. It was written at finalize.

## Files Changed

Source: `db/inflections/inflection_template_files.py` (new),
`db/inflections/create_inflection_templates.py`,
`db/inflections/generate_inflection_tables.py`,
`db/inflections/transliterate_inflections.py`, `gui2/inflection_templates_tab_view.py`
(new), `gui2/database_manager.py`, `gui2/main.py`, `tools/paths.py`.

Data: `db/inflections/templates_index.tsv` and 154 files in
`db/inflections/templates/` (new). The old spreadsheet moved to
`misc/inflection_templates_legacy.xlsx`.

Tests: `tests/db/inflections/test_inflection_template_files.py` (new),
`tests/db/inflections/test_create_inflection_templates.py`,
`tests/gui2/test_inflection_templates_db.py` (new),
`tests/gui2/test_inflection_templates_tab_view.py` (new),
`tests/gui2/test_main.py`.

Docs: `db/inflections/README.md`, `docs/technical/project_folder_structure.md`,
`docs/technical/style_guide_for_dpd_entries.md`.

## Findings

Round 1:
- Delete removed the files before the confirm dialog, so Cancel did nothing.
- A template file that failed to load made Copy, Rename and Save treat the list as empty, so a save could overwrite a template.
- Rename kept spaces around the new name in the file name and the db.
- Forms boxes became single-line when every cell held one form, so a second form could not be typed.
- The loader did not trim or sort forms, unlike the old spreadsheet builder.
- The two pending lists were merged into each other, and the tables step cleared its whole list.
- Rename does not update pattern names written in other files (traditional-lemma table, gui2 pattern guess, db_tests, additions and corrections). **User decision: renames are very rare, no warning wanted.**
- Minor: Clear did not reset the pattern dropdown, rename could overwrite an existing file, no error handling around the db step of Rename.

Round 2:
- `_clear_all` still wrote to the removed `_group_dropdown`, so Clear and every successful Delete would raise AttributeError. The tests drive the cores, not the view, and missed it. My own pyright run missed it too: plain `pyright` skips `gui2/`.

Round 3 (from scratch, no blockers):
- `_pattern_dropdown` was built before `_message_field`, so a template load error during construction raised AttributeError.
- Nit: `dialog_ref` in the name dialog was never read.

## Fixes Applied

All findings above were fixed, except the three not fixed below.
- Delete now removes files in the confirm handler, with the count re-read.
- Copy, Rename and Save stop with a message when the files do not load.
- Rename trims, refuses an existing target file, and rolls back files and words if the db step fails.
- Forms, grammar and row-label boxes are always multi-line; the grid grows on blur.
- The loader splits on a bare comma, trims, drops empties and sorts multi-form cells.
- Each pending list merges only with itself; each reader removes only the names it used.
- The stale group line was deleted, then the group column was removed everywhere (user decision).
- The message box is built first, and the dead variable was removed.
- A test now builds the tab with no index file.

Not fixed:
- Rename does not update other files (user decision above).
- The header row of each grid file ends with a tab (the loader copes).
- A word-list page change swaps the db session during a Save (never seen to fail).

## Changes after the last external review (not reviewed by the agent)

Covered by tests and by the user's live use of the tab: blue headings and row
titles, Alt+X clear, Ctrl+S save, focus on the pattern box when the tab opens,
reload of the grid after Save, content-based column widths, "neut" headings
changed to "nt" in 39 files, the spreadsheet move. An automatic inflections
update after Save was built and then removed at the user's request.

## Test Evidence

- `uv run pytest tests/db/inflections tests/gui2`: 531 passed.
- `just typecheck` (pyrefly): 0 errors.
- `uv run ruff check` on the touched source files: all checks passed.
- `uv run pyright --project /dev/null gui2/inflection_templates_tab_view.py`: 24 errors, all Flet typing noise (ControlEventHandler, list[Control], `_BaseControlType`); the untouched Roots tab gives 14 the same way. The reviewer confirmed none is a real error.
- The 154 files loaded from disk equal the live db rows, except `ant adj` (split bad form).
- Live check by the user in gui2: done, "finally happy" (2026-10-24).

## Verdict

PASSED. No blocking finding is open.
