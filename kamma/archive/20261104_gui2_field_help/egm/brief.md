# Brief — 20261104_gui2_field_help

## Request
gui2: add help to every field in the form. Todoist 6hvxgxqPJHrhFG4g (2026-11-04): "Help pop-ups on every single field in GUI 2". A contributor on any field can learn what it wants without leaving the form or reading docs.

## Facts verified by reading the source (claims to re-check, not facts)
- Flet 1.0.1 installed (pyproject pins `flet[all]==1.0.1`).
- `DpdFields.__init__` (gui2/dpd_fields.py:92-306) declares 50 `FieldConfig` entries. Pass 1 filters them with PASS1_FIELDS; Pass 2 shows all.
- `_create_field_row` (gui2/dpd_fields.py:458) builds every row: a `ft.Text` label (width 150, selectable=True) + the field control + optional edit button + optional transfer button + `_add` field. It is called only from `add_to_ui`, used by pass1_add_view.py:337 and pass2_add_view.py:788. The label sits outside composite controls.
- In Flet 1.0.1 `tooltip` is a kw field on Text, TextField and Dropdown, typed `str | Tooltip`. `ft.Tooltip` has message, wait_duration, trigger_mode (default LONG_PRESS on touch; hover on desktop), text_style, text_align. It has no max-width field.
- TextField has `helper` (and `helper_text` is already written by code at dpd_fields.py:614, 1125, 1425; DpdMeaningField forwards helper_text).
- Existing tooltips: only on buttons (dpd_fields.py:476, 489, 504, main.py:631).
- Existing help surface: Alt+? opens a shortcuts dialog (gui2/shortcuts_dialog.py, main.py:359).
- `DpdTextField`/`DpdDropdown` record focus through `track_focus` and all composite fields are built on them.
- docs/technical/style_guide_for_dpd_entries.md has `###` sections for 41 of the 50 field names (missing: id, family_idioms, translation_1, example_2, translation_2, var_phonetic, var_text, link, origin).
- docs/technical/dpd_headwords_table.md lists columns with one-line descriptions.

## Anchored hypothesis
Problem: the 50 editor rows show only a bare column name. A contributor cannot learn what a field wants without leaving the form.
Approach: keep one help text per field in a single data file the maintainer edits. Show it from the one place every row is built (the label in `_create_field_row`), as a hover tooltip.
Scope: all 50 fields, Pass 1 and Pass 2. Dropdown option lists and the `_add` column are in question, not decided.
