# Spec: Pass2Add "X" filter-queue button

## GitHub issue
None.

## Overview
Add a new generic "X" button to the Pass2Add screen toolbar in `gui2/pass2_add_view.py`. The button runs a database filter (defined in a separate, easily-editable file), builds a queue of matching headwords, and on each click loads the next headword into the edit fields — same UX pattern as the existing `PRead` button.

## What it should do
- Show a button labelled "X" between the "Add" button and the "PRead" button in the top toolbar row.
- On first click: run the configured DB filter, store the resulting headword IDs in an in-memory queue, then load the first one into the editing fields and report `Loaded {lemma}. {N} X remaining.`
- On every subsequent click: pop the next ID, load that headword into the edit fields, report remaining.
- When queue is empty: rebuild it (re-run the filter) so newly-non-matching rows fall out automatically; if still empty, show "No more X words".
- The current filter is: `meaning_1 != ""` AND `commentary == ""` AND `source_1 == "-"`.
- The filter function lives in its own file so it can be swapped/edited without touching view logic.

## Repo context
- Toolbar buttons live in `gui2/pass2_add_view.py` lines ~92–110, added to the row at lines ~177–188.
- The closest existing pattern is `_click_pread_button` (line 953): get next item from a manager, load via `self._db.get_headword_by_id`, then `clear_all_fields()`, set `headword`, `headword_original`, populate `_enter_id_or_lemma_field`, call `dpd_fields.update_db_fields(headword)` and `add_headword_to_examples_and_commentary()`.
- The view holds `self._db: DatabaseManager` with `get_headword_by_id`.
- `DpdHeadword` model: `db/models.py` — columns `meaning_1`, `commentary`, `source_1` are all string columns.

## Assumptions
- "list of words" means: load them one at a time into the existing edit fields, like PRead/Cor/Add.
- "query DB then iterate" — a snapshot at queue-build time is acceptable; we refresh by re-running the filter when the queue empties.
- Order: by `id` ascending.
- The filter `source_1 == "-"` means the literal single-hyphen string, not empty.

## Constraints
- Filter function must be at the top of its own file, easy to edit.
- View code (button wiring, queue handling, message updates) must be stable — only the filter function changes.
- No new dependencies. Modern type hints. No unnecessary comments.

## How we'll know it's done
- Button "X" appears between "Add" and "PRead" with tooltip.
- Clicking it runs the filter and loads a matching headword.
- Message shows lemma + remaining count.
- Empty result shows "No more X words".
- `uv run ruff check` passes on changed files.

## What's not included
- No persistence of the queue across app restarts.
- No filter selection dropdown — switching filters means editing the file.
