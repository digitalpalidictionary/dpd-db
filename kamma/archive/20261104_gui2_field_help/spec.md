# Spec — help on every field in gui2

Thread: `20261104_gui2_field_help`
Source: Todoist task 6hvxgxqPJHrhFG4g, "Help pop-ups on every single field in GUI 2" (added 2026-11-04). No GitHub issue.
An older Todoist task (6hp2vvwQHhCgqgmg, "help is identical to keyboard shortcuts") is unverified background. It is labelled for ePitaka. gui2 already has a shortcuts popup (`gui2/shortcuts_dialog.py`, opened in `gui2/main.py` by Alt plus `?` or `/`, see `_SHORTCUTS_KEYS`). This thread does not touch it.

## Overview

The editor form (Pass 1 and Pass 2) shows each field as a row with a bare column name such as `root_sign` or `family_compound`. A contributor who does not know a column cannot learn what it wants without leaving the form. Today there is no per-field help. The only tooltips are on buttons (`gui2/dpd_fields.py:476, 489, 504`; `gui2/main.py:631`).

This thread adds one help text per field and shows it as a hover tooltip on the field name.

## What it should do

1. **Data file.** `gui2/field_help.json` maps each field name to its help text.
   - Flat object: `{"lemma_1": "text", ...}`. By convention the keys follow the order of the `FieldConfig` list. The order is not tested.
   - Keys are the 50 base field names from `FieldConfig`. There are no keys for the `_add` fields.
   - Each text is plain text, 1 to 300 characters. Line breaks are allowed (changed after review, 2026-11-04). Long lines still wrap by width in the tooltip (item 3). A line that shows a key press, a button or a special symbol goes on its own line, and key words are written in CAPITALS (no bold or quote marks, a tooltip takes plain text only).
   - The wording is for Pāḷi scholars, not for database people. It is similar to, but not copied from, `docs/technical/style_guide_for_dpd_entries.md` and `docs/technical/dpd_headwords_table.md`.
   - Sources for drafting: 40 of the 50 names have a style-guide heading. Of the other 10, seven (`id`, `family_idioms`, `example_2`, `var_phonetic`, `var_text`, `link`, `origin`) have a line in `dpd_headwords_table.md`. `example_2` is also covered by the mistyped heading `example_1 and example_1`. Three (`translation_1`, `translation_2`, `comment`) have no doc source. The agent drafts those from how the field is used in the code and lists them in the final report so the maintainer checks them first.
2. **Loader.** New module `gui2/field_help.py`.
   - `get_field_help(name: str) -> str | None` returns the text, or `None` if there is none.
   - The file is read once per process and cached at module level, because `clear_all_fields` rebuilds the whole `DpdFields` object (and so the whole form) on every clear.
   - The path is `Path("gui2/field_help.json")`, relative to the project root, and the file is opened with `encoding="utf-8"`. The project rule is to assume the app runs from the project root.
   - Any load failure (file missing, malformed JSON, top level not an object, a value that is not a string) gives an empty dict. It is logged once per process with `ic`. The form still opens. A missing key returns `None` with no log, because the test is the guard against drift.
   - `validate_field_help(help_texts: dict[str, object], names: list[str]) -> list[str]` returns a list of problems: keys missing, keys not in `names`, a non-string or empty value, a value over 300 characters. (A newline was a problem at first; allowed after review.) The test calls it on the real data and on deliberately broken copies.
3. **Wiring.** In `DpdFields._create_field_row` (`gui2/dpd_fields.py:458`), after the label is built, set `label.tooltip` from `get_field_help(field_name)` when it is not `None`.
   - The tooltip is `ft.Tooltip(message=text, wait_duration=500, size_constraints=ft.BoxConstraints(max_width=360))`. `wait_duration` is `Duration | int` and the Flet docstring says milliseconds. `size_constraints` is how a Flet tooltip gets a maximum width.
   - 360 and 500 are starting values. The spike (assumption A) may change them.
4. **Where it shows.** Every row in Pass 1 and Pass 2. The tooltip is attached when the row is built, so it needs no logic for rows that Pass 1 hides or shows.
5. **Test.** `tests/gui2/test_field_help.py` (path mirrors `gui2/field_help.py`) checks:
   - The real JSON passes `validate_field_help` against the 50 names. The names come from the `FieldConfig("...")` calls inside `DpdFields.__init__`, read with `ast`, and the test asserts that exactly 50 were found. (No existing test builds a real `DpdFields`, and its constructor needs a database, a toolkit and a spell checker.)
   - Each of these broken copies fails `validate_field_help`, each in its own test: one key removed, one key renamed, one text empty, one text of 301 characters, one `_add` key added. A text with a newline must pass.
   - The loader returns `{}` and does not raise for a missing file, malformed JSON, a list at the top, and a non-string value. These use a temporary file path passed to an inner function, so the test does not touch the real file.
   - A label built by `DpdFields._create_field_row`, called with a stand-in `self` that holds one real `DpdTextField`, has a non-empty tooltip when the help data has a text for that name.

## Decisions made by the owner (this session)

- **Mechanism:** hover tooltip on the field name. The options offered were this, a help line that follows the focused field, and both.
  - Accepted limit: a keyboard-only contributor never sees the tooltip, because the field name cannot take focus. Nothing on screen tells a contributor that tooltips exist. A help line or a "?" cue can be a later thread.
- **Storage:** a JSON file, with its own wording for Pāḷi readers rather than text taken from the docs. The planner chose the location, `gui2/` beside the code. `gui2/data/` holds per-user state files, and `field_help.json` is shared reference data.

## Verified facts (read from the source on 2026-11-04)

- Flet installed: 1.0.1 (`pyproject.toml:65`).
- `DpdFields.field_configs` has 50 entries (`gui2/dpd_fields.py:92-306`). It is assigned inside `__init__`, not at class level.
- `_create_field_row` is called only from `add_to_ui` (`dpd_fields.py:447`). `add_to_ui` is called from `pass1_add_view.py:337` and `pass2_add_view.py:788`. `clear_all_fields` in both views calls `_build_middle_section`, which builds a new `DpdFields` and calls `add_to_ui` again.
- The label is `ft.Text(field_name, color=GREY_500, size=12, width=150, selectable=True)` (`dpd_fields.py:461-467`). The row uses `vertical_alignment=CENTER` (`dpd_fields.py:517`).
- Composite fields (meaning, example, commentary, notes, compound construction, family set) sit in a row with the same label, so the label tooltip covers them.
- In Flet 1.0.1, `Text`, `TextField` and `Dropdown` take `tooltip: str | ft.Tooltip`. `ft.Tooltip` has `message`, `wait_duration: Duration | int`, `text_align`, `text_style`, `trigger_mode`, `size_constraints` (`flet/controls/material/tooltip.py:157, 199`).
- `helper_text` is cleared at `dpd_fields.py:614` and written at `:1125` and `:1425`. It must not carry static help.
- Style guide: 39 `###` headings. 40 of the 50 names appear in a heading. Not covered: `id`, `family_idioms`, `translation_1`, `example_2`, `translation_2`, `var_phonetic`, `var_text`, `link`, `origin`, `comment`.
- No existing test calls `_create_field_row` or `add_to_ui`. No code in `gui2/` indexes a field row's `controls[0]` for these rows (the `controls[...]` hits in `sandhi_find_replace_view.py` and `bold_search_view.py` are other views' own rows).

## Assumptions & uncertainties

Not verified. The plan tests A first. Its result is written into `plan.md`.

- **A. Tooltip on a selectable label (Goldfish G2-3, G3-4, Major).** A tooltip on a `selectable=True` `ft.Text` shows on hover in the web client, wraps at the `size_constraints` width, and does not stop text selection of the name.
  - Pass: in the web gui2, resting the pointer on `lemma_1` for under one second shows the tooltip, the text wraps, and a drag over the name still selects it.
  - Fail: wrap the label in `ft.Container(width=150, tooltip=...)`, keep `selectable=True` on the inner `Text`, and drop `width` from the inner `Text`. Repeat the check. If this also fails, stop and ask the owner. Never drop `selectable`.
- **B.** Whether Flutter's tooltip also shows on keyboard focus. Not needed (the owner accepted the keyboard limit). Record the answer.
- **E (Goldfish G1-7, Nit).** A plain grey name gives no sign that help exists. Accepted by the owner's choice. Open risk.
- **F (Goldfish G1-2, Major).** For tall multiline rows the label sits at the vertical middle of the row, far from where the contributor types. Accepted by the owner's choice. Open risk.

Goldfish findings accepted into this spec (full list in `egm/gate1.md` and `egm/gate2.md`): drift test, load once and cache, 300-character cap, selectable-label spike, no `helper_text`, no `gui2/data/`, 500 ms wait, one rule for load failures, the loader's name and signature, `size_constraints` instead of manual wrapping.

## Constraints

- No dropdown option lists get their own help. Any explanation of the options goes in the field's text.
- Do not change any field's behaviour, size or layout. The label keeps `width=150`.
- Do not touch the shortcuts popup.
- Python rules from `CLAUDE.md`: type hints, `Path`, `icecream` not `print`, no `sys.path` tricks. Files under `gui2/` and `tests/` need `uv run pyright --project /dev/null <file>`. For each touched Python file run `ruff check --fix`, `ruff format`, pyright, then the related tests. Never run `ruff format` on the JSON file.
- The working tree holds other threads' uncommitted files. Leave them alone. No commit, branch or PR.

## How we'll know it's done

1. `gui2/field_help.json` has exactly the 50 `FieldConfig` names as keys, each with 1 to 300 characters.
2. `uv run pytest tests/gui2/test_field_help.py` passes, and each broken copy in item 5 makes `validate_field_help` return a problem.
3. Live check in the web gui2, in Pass 1 and in Pass 2, after the pointer rests on the field name for one second: the tooltip shows for `lemma_1` (text), `pos` (dropdown), `meaning_1` (multiline composite), `example_1` (composite), `commentary`, `family_set`, `compound_construction`, `notes`, `comment`. Hover on the name, not on the input. The run is driven with `playwright-cli` after the owner agrees to start the server.
4. `uv run pytest tests/gui2` passes (any failure that existed before is named, not ignored).
5. `ruff check`, `ruff format --check`, and pyright are clean on each touched Python file (for `gui2/dpd_fields.py`, plain `uv run pyright` is clean; `--project /dev/null` shows 90 pre-existing errors, none on this thread's lines), and `just typecheck` is clean for the whole repo.
6. The final report lists the three texts with no doc source and tells the maintainer to skim all 50 texts.

A contributor with a mouse can learn what any field wants without leaving the form. A keyboard-only contributor cannot. That limit is the owner's choice and not a failure of this thread.

## What's not included

- A help line or panel that follows keyboard focus.
- A "?" icon or any other cue that help exists.
- Help for dropdown option values, or for the `_add` column.
- Help in other tabs (roots, sandhi, tests, and so on).
- Any change to files under `docs/`.
- Translating the help.

The one line in `gui2/README.md` that names `field_help.json` is part of the work.

## Review record

- Gate 1 (idea): 3 Goldfish, 13 findings after merging, 10 accepted, 1 rejected, 2 escalated and answered. See `egm/gate1.md`.
- Gate 2 (spec): see `egm/gate2.md`.
- Gate 3 (plan readiness): see `egm/gate3.md`.
