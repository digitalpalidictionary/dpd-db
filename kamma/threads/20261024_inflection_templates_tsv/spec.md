# Spec: inflection templates as TSV files, with a gui2 editor tab

**Thread:** 20261024_inflection_templates_tsv · **GitHub issue:** none

## Overview

Inflection templates are the stem/ending grids that turn `stem + pattern` into
inflection tables. Today their only source is a spreadsheet,
`db/inflections/inflection_templates.xlsx`. A binary `.xlsx` file gives no
readable git diff, and code must find each table by its cell range.

This thread moves the templates into plain TSV files that people and code can
both read and that diff line by line. It adds a gui2 tab to edit, copy,
rename and delete templates.

The database table `inflection_templates` (`db/models.py::InflectionTemplates`:
`pattern`, `like`, `data` = JSON nested list) does NOT change. Every consumer
downstream of it stays as it is.

## Current behaviour (verified 2026-10-24)

- `db/inflections/create_inflection_templates.py` is the only code that reads
  the spreadsheet (`ProjectPaths.inflection_templates_path`). It runs from
  `justfile` (`inflections` recipe), `scripts/bash/generate_components.py`,
  `scripts/server_contrib/generate_components_server.py`,
  `.github/workflows/draft_release.yml:131` and `mobile_release.yml:116`.
- It reads sheet `index` (columns: `inflection name`, `cell range`, `like`;
  154 rows) and sheet `declensions` (154 tables side by side, columns A–DK).
  It cuts each range into a nested list `table[row][cell] = list[str]`, splits
  multi-form cells on `\n`, sorts them with `pali_list_sorter`, and blanks the
  top-left cell (which holds the pattern name in the sheet).
- It adds, updates or deletes rows in `inflection_templates`, and records the
  changed pattern names in two places, both overwritten each run:
  `DbInfo` key `changed_templates_list` (read by
  `db/inflections/generate_inflection_tables.py` to decide which words to
  regenerate) and the pickle `shared_data/changed_templates`
  (`ProjectPaths.template_changed_path`, gitignored; read by
  `db/inflections/transliterate_inflections.py`).
- Readers of `inflection_templates` rows (unchanged by this thread):
  `generate_inflection_tables.py`, `db/grammar/grammar_to_lookup.py`,
  `db/inflections/inflections_raw.py`, `scripts/find/missing_pr_verbs.py`,
  `gui2/database_manager.py::get_all_patterns`.
- The spreadsheet also has sheets `abbreviations` (65 rows) and `scripts`
  (17 rows). No code reads them (`rg` over the repo, 2026-10-24).

### Shape of the data (measured on the live `dpd.db`, 2026-10-24)

- 154 templates; the spreadsheet index and the db hold the same 154 names.
  153 patterns are used by headwords. 67 have `like = irreg`.
- Row 0 is the header: cell 0 empty, odd cells = column headings
  (`masc sg`, `pl`, `reflexive sg` …), even cells empty.
- Rows 1+: cell 0 = row label (`nom`, `pr 3rd`, `in comps` …); odd cells =
  forms (a list); the even cell after each = grammar label (`masc nom sg`).
- Every row has the same width as the header. Row labels, column headings and
  grammar labels are always exactly one string. No multi-form cell mixes an
  empty form with real ones. Empty cells are stored as `[""]` (289 cells).
- 1,597 of 3,741 form cells hold more than one form. No form contains a tab
  or a comma.
- Grammar labels can NOT be derived from headings: only 2,374 of 3,741 match
  `heading + row label`. Others use `nt` for `neut`, `reflx …`, or are empty
  in the `in comps` row. So grammar labels stay stored.
- Pattern names use only letters and spaces; none is unsafe as a file name.
- The sheet's row-1 headings name 9 families (adjectives, pronouns, regular
  verbs …). They exist only as layout and nothing reads them. The first draft
  of this spec kept them as a `group` column; the user dropped it on
  2026-10-24 ("i dont see the point"), so templates have no group.
- One data error: `ant adj`, row `loc`, column `fem sg` holds the form
  `antiyaṃ antiyā` (two forms in one). The user chose to split it.

## What it should do

### 1. New source files

- **Index:** `db/inflections/templates_index.tsv`, columns
  `pattern`, `like`. One row per template. Sorted by `pattern` with
  `pali_sort_key` (repo rule for code-written data files).
  This replaces the spreadsheet's `index` sheet. The cell range is gone; the
  file name takes its place.
- **One table per template:** `db/inflections/templates/<pattern>.tsv`, file
  name = the exact pattern name (e.g. `ati pr.tsv`). Content = the same block
  as in the spreadsheet:
  - row 0: top-left cell = pattern name, then the column headings with empty
    grammar cells between, exactly as the db's row 0 (apart from the name);
  - rows 1+: row label, then `forms`, `grammar label` pairs;
  - multiple forms in one cell are joined with `", "` and kept in
    `pali_list_sorter` order; an empty cell is an empty string; the loader
    also normalizes a hand-edited cell: it splits on a bare comma, trims,
    drops empty forms and re-sorts multi-form cells;
  - every row is written at full width (no trimmed trailing cells), LF line
    endings, UTF-8, no quoting.

  Example (`natthi pr.tsv`, tabs shown as spaces):
  ```
  natthi pr  sg            pl
  pr 3rd     natthi  pr 3rd sg  natthi  pr 3rd pl
  pr 2nd     nasi    pr 2nd sg  nattha  pr 2nd pl
  pr 1st     namhi   pr 1st sg  namha   pr 1st pl
  ```
- **Loader checks** (fail with a clear message naming the file): every index
  row has a table file, every table file has an index row, pattern names are
  unique, the top-left cell equals the file name, all rows have the header's
  width, `like` is not empty.
- A load of the new files must give exactly the nested list the db holds
  today, for all 154 templates, except the one `ant adj` cell, which becomes
  four sorted forms (`atiyaṃ`, `atiyā`, `antiyaṃ`, `antiyā` in
  `pali_list_sorter` order).

### 2. The build reads the new files

- `create_inflection_templates.py` keeps its name and command line (CI and
  the justfile call it), but loads the TSV files instead of the spreadsheet.
  `pandas` is no longer needed in it.
- The sync logic (add / update / delete rows, record changed names) becomes a
  function that takes a db session, so the gui2 tab can call the same code.
- **Changed-template lists become pending lists.** Today each sync overwrites
  them. After this thread, a sync ADDS its changed names to what is already
  there, and each reader removes only the names it actually used:
  - `add_pending_templates` unions the changed names into EACH list with
    itself only (never across the two — the readers empty at different
    times, so mixing would bring back names one reader had already used).
  - `generate_inflection_tables.py` removes from `DbInfo
    changed_templates_list` exactly the names it regenerated, in the same
    commit as the words; a rollback keeps them pending. Names synced while
    it was running stay pending.
  - `transliterate_inflections.py` removes the names it used from the
    `shared_data/changed_templates` pickle, after the db write succeeds.
  - A missing `DbInfo` row or missing pickle counts as an empty list.

  **Why:** a gui2 Save syncs the db at once. Without this, a later build's
  sync sees "no change", overwrites the lists with `[]`, and the words using
  that template keep their old tables and transliterations. Nothing would
  report it.

### 3. gui2 tab "Infl"

New tab, last in the tab bar (index 16), jump key Alt+I.

**Layout (user, 2026-10-24): symmetrical and rigid, like a spreadsheet.**
It reuses the two existing tabs' conventions:

- From the Roots tab (`gui2/roots_tab_view.py`): a top bar framed by
  `HIGHLIGHT_COLOUR` (`ft.Colors.BLUE_200`) top/bottom borders holding the
  dropdown, buttons of one fixed width, and a read-only message field; a
  scrollable middle section; a bottom bar with Save and Delete;
  `field_border()` on every box; grey (`ft.Colors.GREY_500`) labels.
- From the Tests tab (`gui2/tests_tab_view.py`): fixed pixel widths from
  module constants, never `expand`, so every box lines up; row labels as
  right-aligned grey text of one fixed width (`LABEL_WIDTH`).

Sections, top to bottom:

- **Top bar:** one searchable dropdown of all patterns (`editable=True`,
  `enable_filter=True`, `enable_search=True`, as in the Roots and Tests tabs),
  then the buttons Copy, Rename, Clear, then the message field.
- **Fields row:** pattern name (read-only: names change only through Copy or
  Rename, so a typed name can never clash), like (text box).
- **Grid (user, 2026-10-24, after the first live look):** a rigid grid with
  room to breathe, whatever the content.
  - Every box is as wide as the widest box in its column and as tall as the
    tallest box in its row. Widths come from the longest text in the column
    (`CHAR_WIDTH` 11 px per character plus `BOX_PADDING` 36 px), never below
    `FORMS_MIN_WIDTH = 150` and `GRAMMAR_MIN_WIDTH = 170`; the row-label
    column is `LABEL_WIDTH = 140`. Row height is the largest form count in
    the row, at least 2 lines. No control in the grid uses `expand`.
    The first version used fixed 90/120 px widths and wrapped forms such as
    `amhākaṃ` (screenshot, `aham pron`).
  - The grid grows, never shrinks, while editing: when a box is left holding
    more forms or longer text than its row or column has room for, the grid
    is rebuilt (on blur, not per key, because a rebuild drops the focus).
  - Column 0 is the row-label column (`LABEL_WIDTH`). Then each table column
    is a pair of cells: forms, then grammar label.
  - Row 0 holds the column headings, each above its forms cell, with an
    empty cell of the same size above each grammar cell. The top-left cell is
    empty.
  - Forms, grammar and row-label boxes are multi-line, so a second form can
    always be typed. Newlines in a grammar or row-label box become spaces on
    save.
  - Grammar cells use a smaller grey text, so the eye separates them from
    forms.
  - The grid sits in a row that scrolls sideways if it is wider than the
    window, so cells never shrink or wrap.
- **Shape buttons** under the grid: add row, remove last row, add column,
  remove last column. They keep the grid rectangular.
- **Bottom bar:** Save, Delete, Show words / Hide words.
- **Words using this pattern (user, 2026-10-24; only when asked, never
  automatic):** the "Show words" button opens, and "Hide words" closes, under
  the bottom bar, the
  existing editable results table `gui2/filter_component.py::FilterComponent`
  (the same one the DB tab and the Tests tab use), filtered to the chosen
  pattern. It already pages 100 words at a time (`PAGE_SIZE`) with Previous
  / Next, lets you tap a cell to edit it, and has its own "Save Changes"
  button (with the spelling gate). No new list widget is built.
  - Filter: `data_filters=[("pattern", f"^{re.escape(pattern)}$")]`.
    `build_filter_conditions` (`gui2/filter_logic.py`) uses `regexp_match`,
    so without the `^…$` anchors `a nt` would also match other patterns
    that contain it.
  - Columns: `id`, `lemma_1`, `pos`, `stem`, `pattern`, `meaning_1`;
    sorted by `lemma_1` (its default).
  - The list is hidden when the tab opens, when a pattern loads, after Copy
    and after Clear, and it takes no screen space while hidden. While open it
    is rebuilt after Save and Rename. An unsaved copy has no list (no words
    can use it yet; the button says so).
  - Measured 2026-10-24: 82 patterns have 20 words or fewer; the biggest
    are `a nt` 16,714, `a adj` 15,882, `a masc` 14,143.

**Making a new pattern (user, 2026-10-24):** pick an existing pattern in
the dropdown, press Copy, type a new name in a dialog, then edit and Save.

- The Copy dialog has a name box, OK and Cancel. OK refuses (message in the
  dialog, dialog stays open) an empty name, a name that already exists, or a
  name with `/` or a tab. Identical names are impossible.
- After OK the form shows the copied grid and like under the new
  name. Nothing is written yet; the message says "copy of <old> — edit, then
  Save". Save creates the new file and index row.
- There is no "New empty template" button: every new pattern starts as a copy.

Behaviour of the other buttons:

- **Save** writes the index row and the table file, then runs the shared sync
  on gui2's db session. The db row is then current and the pattern is in the
  pending list, so the Global tab's "Update Inflections" button regenerates
  the words that use it; the message line says so. (User, 2026-10-24: an
  automatic update after every Save was tried and removed, because many edits
  in a row made it too slow. Rename is the same: it moves the words and tells
  you to press Update Inflections.) The pattern dropdown and
  `db_manager.all_patterns` refresh.
- **Rename** (name dialog with the same checks as Copy; the input is
  trimmed): renames the file and index row (refused if the target file
  exists), sets `DpdHeadword.pattern` from old to new for every word that
  uses it, syncs, and reports how many words changed. If the db step fails,
  the words and the files are rolled back, so files, index and words never
  disagree.
- **Delete** (confirm dialog): blocked with a message while any word uses
  the pattern (shows the count, checked before the dialog opens and again
  inside it, in case a word took the pattern meanwhile). The files are
  removed only after the confirm, then the sync deletes the db row.
- Forms are cleaned on save: trimmed, empty lines dropped, sorted with
  `pali_list_sorter`; a cell with no forms is saved empty.
- Save refuses: no pattern loaded, an empty `like`, an empty
  column heading or row label, a form containing a comma or a tab. (Name
  checks happen in the Copy and Rename dialogs; Save checks the name again
  for a copy, in case a file appeared in the meantime.)
- **Clear** empties the form, the grid and the pattern dropdown, like the
  Roots tab's Clear.
- Dialogs follow the repo's Flet 1.0 rules: a "Cancel" button; reopen paths
  guarded against "Dialog is already opened".

### 4. Docs

- `db/inflections/README.md`: the new source files and the gui2 tab.
- `docs/technical/style_guide_for_dpd_entries.md:222`: the link to the
  `.xlsx` now points to the `db/inflections/templates/` folder on GitHub.
- `docs/technical/project_folder_structure.md`: the new index file and folder.

## Assumptions & uncertainties

- **Verified:** everything under "Current behaviour" and "Shape of the data"
  (read from code, `rg` sweeps, and queries on the live `dpd.db` and the
  `.xlsx` via `openpyxl`).
- **Assumed:** the spreadsheet and the db are in step. Set-wise they match;
  the migration's equality check will show any cell-level difference before
  anything else changes.
- **Assumed:** no code depends on the row order of `inflection_templates`
  (all readers use dicts, sets or per-word relationships; checked by reading
  them). The new index order is therefore free to be the canonical sort.
- **Assumed:** gating the tab for contributors is not needed. No gui2 tab is
  gated today; the Roots tab also writes the db for every user.
- **Uncertain:** whether the pending-list change alters any build run in a
  way not covered here. The only readers are the two named scripts (`rg`
  2026-10-24). On a fresh CI db both lists start empty and `db_rebuild`
  regenerates everything, so CI output should not change.
- **Uncertain:** whether Flet 1.0's editable dropdown with `enable_filter`
  copes with 154 options. The Roots tab uses the same control with more
  options, so it is expected to work.
- `InflectionsManager.run` (behind "Update Inflections") can ask for terminal
  `input()` in its checks. That is existing behaviour and out of scope.

## Constraints

- Do not change `InflectionTemplates`, its JSON shape, or any reader of it.
- `create_inflection_templates.py` keeps its path and command line.
- Leave `inflection_templates.xlsx` in place, unused. Do not delete it. Do not
  carry its `abbreviations` and `scripts` sheets into the new files.
- Code-written data files: canonical `pali_sort_key` order, LF endings.
- Concurrent threads share this tree: `gui2/database_manager.py`,
  `tests/gui2/test_roots_db.py` and others already have uncommitted edits from
  other work. Edit with targeted additions only; never use whole-tree git
  commands.
- Repo gates: `ruff check --fix`, `ruff format`, `pyright` on every touched
  file; `just typecheck` (pyrefly) before finishing.

## How we'll know it's done

- A test loads every TSV file and compares it with the db's current `data`
  and `like` for all 154 patterns: all equal except the one `ant adj` cell.
- The rewritten `create_inflection_templates.py` run on a copy of `dpd.db`
  reports zero added, updated or deleted templates except `ant adj` (updated).
- A unit test shows the pending lists add up across two syncs and are cleared
  by their readers.
- In gui2: open a template, change a form, Save → one-line `git diff` in that
  template's file; the db row changes; "Update Inflections" regenerates the
  words using it.
- Copy refuses an existing name. Copy + edit + Save creates a new file and
  index row. Rename moves the words to the new name. Delete is blocked for a
  used pattern and works for an unused one.
- Picking a pattern lists exactly the words that use it (count matches
  `select count(*) from dpd_headwords where pattern = ?`), and a cell edited
  there saves through the table's own "Save Changes".
- The grid lines up as a spreadsheet: same-width columns, same-height rows,
  headings exactly above their forms cells, at the window size gui2 opens at.
- ruff, pyright and `just typecheck` are clean; existing inflection tests pass.

## What's not included

- The `abbreviations` and `scripts` sheets.
- Deleting the spreadsheet (later, by hand).
- Any change to how tables, grammar or transliterations are generated.
- Running "Update Inflections" automatically on Save (tried, removed: too slow
  with many edits in a row).
- A "New empty template" button (every new pattern starts as a copy).
- A new word-list widget, a "show more" button, or a page size other than the
  results table's existing 100.
- Editing the grid in a spreadsheet-like widget with keyboard cell navigation.
