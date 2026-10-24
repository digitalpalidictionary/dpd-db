# Plan: inflection templates as TSV files, with a gui2 editor tab

**Thread:** 20261024_inflection_templates_tsv · **Spec:** `spec.md` (read first)
**GitHub issue:** none

## Architecture Decisions

- **Format A (user's choice):** one index TSV (`pattern`, `like`)
  plus one grid TSV per template, shaped like the spreadsheet block. Multi
  forms joined with `", "`. Grammar labels stay stored (only 63% derivable).
- **One file module, shared by build and gui2:**
  `db/inflections/inflection_template_files.py` owns all TSV reading and
  writing and the loader checks. Nothing else touches the TSV files.
- **One sync function, shared by build and gui2:** the add / update / delete
  logic in `create_inflection_templates.py` becomes
  `sync_templates(db_session, templates) -> list[str]`. gui2 calls it on its
  own session, so a Save and a build can never disagree.
- **Changed-template lists become pending lists** (sync adds, reader clears).
  Without this a gui2 Save followed by a build loses the regeneration
  silently (see spec §2).
- **gui2 follows the Roots tab pattern:** the view in its own module, db
  writes as `DatabaseManager` methods, pure helpers testable without Flet.
- **The word list reuses `FilterComponent`** (DB tab / Tests tab results
  table): paging, in-place editing and saving already exist there. Only the
  filter is new, anchored `^…$` because the filter is a regex match.
- **Not abstracted:** no generic "TSV table" class, no new dependency (stdlib
  `csv` only), no change to `InflectionTemplates` or its readers.
- **Migration is a one-off script** in this thread's `artifacts/`. It uses the
  current spreadsheet code, so it must run before Phase 2 rewrites that code.

## Phase 1 — New files, loader, migration

- [x] 1.1 Paths and file module.
      Add to `tools/paths.py` next to `inflection_templates_path` (keep that
      one): `inflection_templates_index_path = base_dir /
      "db/inflections/templates_index.tsv"` and `inflection_templates_dir =
      base_dir / "db/inflections/templates"`.
      Create `db/inflections/inflection_template_files.py` with:
      `@dataclass TemplateFile(pattern: str, like: str,
      data: list[list[list[str]]])`;
      `load_templates(index_path: Path, templates_dir: Path) -> list[TemplateFile]`;
      `write_template(t, index_path, templates_dir) -> None` (writes the grid
      file, inserts or replaces the index row, rewrites the index sorted by
      `pali_sort_key(pattern)`);
      `remove_template(pattern, index_path, templates_dir) -> None`;
      `rename_template(old, new, index_path, templates_dir) -> None`.
      Grid format and loader checks exactly as spec §1: top-left cell = pattern
      name on disk, `[""]` in `data`; forms `", "`-joined and
      `pali_list_sorter`-sorted; full-width rows; `newline=""`, `\n` line
      terminator, `csv.QUOTE_NONE`, UTF-8. A failed check raises `ValueError`
      naming the file.
      → verify: `uv run pytest tests/db/inflections/test_inflection_template_files.py`
      (new) passes: a round trip of a 3-row template with a multi-form cell
      and an empty cell gives the same `TemplateFile`; each loader check
      (missing file, file without index row, wrong top-left, ragged row,
      empty like) raises `ValueError`; rename and remove update both files.
- [x] 1.2 Migration script
      `kamma/threads/20261024_inflection_templates_tsv/artifacts/xlsx_to_tsv.py`.
      It reads the spreadsheet with the CURRENT functions of
      `create_inflection_templates.py` (build `GlobalVars` with `__new__` as
      `tests/db/inflections/test_create_inflection_templates.py` does, so no db
      session opens). (The group computed by this script was dropped later:
      templates have no group, spec §1.)
      It splits the `ant adj` / `loc` / `fem sg` form `antiyaṃ antiyā` into
      two forms and re-sorts that cell with `pali_list_sorter`. It writes all
      templates with `write_template`. Then it re-loads with `load_templates`
      and compares with the live `dpd.db` (read-only sqlite URI): it prints
      every pattern whose `like` or `data` differs.
      → verify: run `uv run kamma/threads/20261024_inflection_templates_tsv/artifacts/xlsx_to_tsv.py`.
      Expect 154 files in `db/inflections/templates/`, 154 data rows in the
      index, and the only difference
      reported = `ant adj`. Paste the output here. If any other pattern
      differs, STOP and report it to the user.
- [x] 1.3 Real-data test: in the new test file, load the committed files with
      `ProjectPaths()` paths and assert 154 templates, unique names, and
      `"ant adj"` loc / fem sg = the four split forms.
      → verify: `uv run pytest tests/db/inflections/test_inflection_template_files.py`
      passes. Open `db/inflections/templates/natthi pr.tsv` and confirm it
      matches the example in the spec.
- [x] 1.4 Phase gate: `uv run ruff check --fix`, `uv run ruff format`,
      `uv run pyright` on `tools/paths.py` and the new module;
      `uv run pyright --project /dev/null` on the test file. Report only.
      → verify: all clean; paste the counts here.

## Phase 2 — The build reads the files; pending lists

- [x] 2.1 Rewrite `db/inflections/create_inflection_templates.py`.
      Remove pandas, the column-letter list and the xlsx functions. Keep:
      `sync_templates(db_session: Session, templates: list[TemplateFile]) -> list[str]`
      (same add / update / delete comparison as today, returns changed
      patterns, does not commit); pending-list helpers
      `add_pending_templates(db_session, pth, changed)` (union into `DbInfo
      changed_templates_list` and the pickle at `pth.template_changed_path`,
      missing = empty, result sorted with `pali_list_sorter`);
      `main()` = load files → sync → add pending → commit → print what
      changed. Use plain functions, no `GlobalVars` class.
      Replace `tests/db/inflections/test_create_inflection_templates.py`:
      keep `test_import_has_no_db_side_effects`; add tests on a temp sqlite db
      (`create_tables`) for add, update, delete and "no change", and for two
      `add_pending_templates` calls adding up.
      → verify: `uv run pytest tests/db/inflections/` passes. Then on a copy
      (`cp dpd.db <scratchpad>/dpd_copy.db`, never the real db) call
      `sync_templates` with the loaded files and print the result: expect
      `["ant adj"]` only. Paste it here.
- [x] 2.2 Readers clear their pending list.
      `db/inflections/generate_inflection_tables.py::InflectionsManager.run`:
      before the commit, set `DbInfo changed_templates_list` to `[]` (create
      the row if missing), so it clears in the same commit as the regenerated
      words; a rollback keeps it.
      `db/inflections/transliterate_inflections.py::main`: after
      `_write_translit_to_db` returns, write `[]` to the pickle.
      Add a clear helper next to `add_pending_templates` if both need the
      same code; otherwise inline.
      → verify: `uv run pytest tests/db/inflections/` passes, with a test that
      the DbInfo clear happens through the helper on a temp db. Read both
      edited functions again and confirm the clear sits after the success
      path only.
- [x] 2.3 Phase gate: ruff check, ruff format, pyright on the three edited
      scripts and the test files (`--project /dev/null` for tests);
      `uv run pytest tests/db/inflections/`.
      → verify: all clean, all pass; paste the counts here. Note any test that
      was already failing before this thread.

## Phase 3 — gui2 "Infl" tab

- [x] 3.1 `gui2/database_manager.py` (other threads have uncommitted edits in
      this file: add methods only, touch nothing else). Add, near the root
      methods: `get_pattern_headword_count(pattern) -> int`;
      `rename_pattern_in_headwords(old, new) -> int` (updates
      `DpdHeadword.pattern`, commits, returns the count);
      `sync_inflection_templates() -> list[str]` (loads files, calls
      `sync_templates` and `add_pending_templates` on `self.db_session`,
      commits, refreshes `self.all_patterns` via `get_all_patterns()`).
      → verify: new `tests/gui2/test_inflection_templates_db.py` on a temp db
      (copy the setup of `tests/gui2/test_roots_db.py`, do not edit that
      file): count, rename count and new value, sync adds a template and
      lists it as pending. `uv run pytest tests/gui2/test_inflection_templates_db.py`.
- [x] 3.2 View `gui2/inflection_templates_tab_view.py` — load, show, edit.
      Read `gui2/roots_tab_view.py` and `gui2/tests_tab_view.py` first; the
      layout rules are in spec §3 ("Layout"). Class
      `InflectionTemplatesTabView(ft.Column)` with sections:
      top bar (Roots style: `HIGHLIGHT_COLOUR` borders; searchable pattern
      dropdown with `editable`, `enable_filter`, `enable_search`, options from
      `load_templates` sorted with `pali_list_sorter`; Copy, Rename, Clear
      buttons of one `BUTTON_WIDTH`; read-only message field) → fields row
      (pattern read-only, like text box) → grid →
      shape buttons → bottom bar (Save, Delete).
      Grid: module constants `LABEL_WIDTH = 140`, `FORMS_MIN_WIDTH = 150`,
      `GRAMMAR_MIN_WIDTH = 170` (widths per column and heights per row come from
      `grid_dimensions`, spec §3); no `expand` on any grid control; row 0 = empty
      label-width cell, then per column a heading box and an empty grammar-width spacer; rows 1+ = row-label box, then per column a
      forms box (multi-line, `min_lines = max_lines =` the template's largest
      form count in its row, minimum 2) and a grammar box (smaller grey text). Wrap the
      grid in a `ft.Row(scroll=ft.ScrollMode.AUTO)` so a wide grid scrolls
      sideways instead of shrinking. Keep the grid container at one place in
      the tree; on a shape change rebuild only its `controls` list (repo rule
      on TextFields). Shape buttons keep the grid rectangular.
      Module-level pure helpers, no Flet:
      `grid_values_to_data(headings, rows) -> list[list[list[str]]]` (cleans
      forms per spec §3, empty cell → `[""]`),
      `max_form_count(data) -> int`,
      `validate_new_name(name, existing_patterns) -> str | None` (empty,
      duplicate, `/` or tab), and
      `validate_template(t) -> str | None` (Save's checks in spec §3).
      → verify: `tests/gui2/test_inflection_templates_tab_view.py` (new) tests
      the helpers: forms trimmed, blank lines dropped, sorted, empty cell →
      `[""]`; `max_form_count` of `ant adj` data = its real maximum; each
      refusal returns a message; a valid input returns `None`; a name that
      differs from an existing one only by surrounding spaces is refused.
- [x] 3.3 Copy, Rename, Save, Delete.
      Copy (needs a loaded pattern): dialog with a name box, OK, Cancel. OK
      runs `validate_new_name`; on a refusal show the message inside the
      dialog and keep it open. On success: the form keeps the grid and like,
      the pattern field shows the new name, a flag records "unsaved
      copy of <old>", and the message says "copy of <old> — edit, then Save".
      Nothing is written.
      Save: `validate_template` → for an unsaved copy also
      `validate_new_name` again → `write_template` →
      `db_manager.sync_inflection_templates()` → refresh dropdown and select
      the saved pattern → message "saved, N words use it, press Update
      Inflections on the Global tab".
      Rename: the same name dialog and checks as Copy →
      `rename_template` → `rename_pattern_in_headwords` → sync → message with
      the word count. Rename is refused for an unsaved copy (save it first).
      Delete (confirm dialog with Cancel): if
      `get_pattern_headword_count > 0`, show the count and stop; else
      `remove_template` → sync. Guard dialog reopen ("Dialog is already
      opened", see AGENTS.md Flet notes).
      → verify: on a temp copy of the files and a temp db, a test drives the
      handlers' non-Flet core (factor it into helpers if the handlers are
      hard to call): copy to an existing name is refused and writes nothing;
      copy + save creates one file and one index row; save edits one line of
      one file; rename moves words; delete of a used pattern changes nothing. `uv run pytest tests/gui2/test_inflection_templates_tab_view.py`.
- [x] 3.4 Words using the pattern (spec §3, "Words using this pattern").
      Reuse `FilterComponent` (`gui2/filter_component.py`) exactly as the
      Tests tab does: a `ft.Container(expand=True)` placeholder under the
      bottom bar, and a `set_word_list(pattern | None)` method that sets its
      `content` to a new `FilterComponent(page, toolkit,
      data_filters=[("pattern", f"^{re.escape(pattern)}$")],
      display_filters=["id", "lemma_1", "pos", "stem", "pattern", "meaning_1"])`
      or to `None` (see `gui2/tests_tab_view.py::set_filter_component` and
      `gui2/tests_tab_controller.py:250`). Call it on pattern load, after
      Save / Rename / Delete, with `None` on Clear and for an unsaved copy.
      Put the filter in a pure helper `pattern_word_filter(pattern) ->
      list[tuple[str, str]]`. Do not change `FilterComponent`.
      → verify: test in `tests/gui2/test_inflection_templates_tab_view.py`:
      run `build_filter_conditions(pattern_word_filter("a nt"))` against a
      temp db holding words with patterns `a nt`, `ā nt` and `a nt irreg`
      (or any name containing `a nt`) → only the `a nt` word matches. Then
      on the real db (read-only), for `natthi pr` the filtered count equals
      `select count(*) from dpd_headwords where pattern = 'natthi pr'`.
- [x] 3.5 Register the tab in `gui2/main.py`: append `"Infl"` to `tab_labels`,
      `16: lambda: InflectionTemplatesTabView(self.page, self.toolkit)` to
      `_view_builders`, `"I": 16` to `_TAB_JUMP_KEYS` (confirm `I` is not
      bound elsewhere in `on_keyboard`). Check `tests/gui2/test_main.py` and
      `gui2/shortcuts_dialog.py` for tab-count or key lists that need the new
      entry.
      → verify: `uv run pytest tests/gui2/test_main.py tests/gui2/test_shortcuts_dialog.py`
      passes.
- [x] 3.6 Phase gate: ruff check, ruff format on every touched gui2 file;
      `uv run pyright --project /dev/null` on them (report only errors on
      lines this thread wrote; gui2 has known Flet-typing noise — see
      `gui2/README.md`); `uv run pytest tests/gui2/`.
      → verify: clean on this thread's lines; paste counts; list any
      pre-existing failures.

## Phase 4 — Docs and final checks

- [x] 4.1 Docs: `db/inflections/README.md` (new source files, loader checks,
      pending lists, the Infl tab; the `.xlsx` is unused and kept for now);
      `docs/technical/style_guide_for_dpd_entries.md:222` link →
      `https://github.com/digitalpalidictionary/dpd-db/tree/main/db/inflections/templates`;
      `docs/technical/project_folder_structure.md` (new index file and folder).
      → verify: `rg -n --hidden "inflection_templates\.xlsx" --glob '!kamma/archive/**' --glob '!archive/**' --glob '!graphify-out/**'`
      shows only `tools/paths.py`, the migration script and the README's
      "unused" note.
- [x] 4.2 Final checks: `just typecheck`; `uv run pytest tests/db/inflections/ tests/gui2/`;
      `graphify update .`.
      → verify: typecheck clean (or only narrowly suppressed pyrefly-only
      limitations with a reason); tests pass; paste counts here.
      **Done 2026-10-24:** typecheck 0 errors (119 suppressed, 89 warnings —
      normal); 514 tests pass. `graphify update .` DEFERRED by user until
      after the thread is proven, signed off and committed — run it then.
- [x] 4.3 Live check by the user (the only part that needs the screen). Hand
      the user `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && just gui`, with
      these steps: open Infl, pick `ati pr` (widest kind of grid) and confirm
      it lines up as a spreadsheet with no sideways scroll at the default
      window size; press Copy and try the name `ati pr` (refused), then
      `ati pr test` (accepted), Save, then Delete it (unused, so allowed). Then
      pick `natthi pr`, press Show words and confirm the list shows `natthi 1`,
      `natthi 2` and `natthī` (it is hidden until you press the button) (plus any others that use it), change one form, Save, then
      press Update Inflections on the Global tab and open the word
      `natthi 1` (id 35540).
      → verify: the user confirms the table shows the change. Read
      `db/inflections/templates/natthi pr.tsv` and confirm only that one line
      changed (no git commands — the user runs git). Then the user reverts the
      form in the tab and saves again.
