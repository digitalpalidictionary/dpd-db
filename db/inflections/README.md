# db/inflections/

## Purpose & Rationale
Pāḷi is a highly inflected language where a single lemma can take dozens of different forms depending on case, number, gender, and person. The `inflections/` directory exists to solve the problem of systematically generating and displaying these millions of potential forms. It ensures that the dictionary is useful not just for base words, but for every variant form encountered in actual texts.

## Architectural Logic
This subsystem follows a "Template-Driven Generation" pattern:
1.  **Templates:** Defines `InflectionTemplates` (declensions for nouns, conjugations for verbs) that act as blueprints for how different word patterns evolve.
2.  **Generation:** `generate_inflection_tables.py` applies these templates to every headword in the database, calculating all valid inflected forms.
3.  **Visualization:** It renders these forms into optimized HTML tables for immediate display in the dictionary.
4.  **Transliteration:** `transliterate_inflections.py` handles the conversion of these tables into different scripts (Sinhala, Devanagari, Thai) to serve diverse linguistic communities.

## Relationships & Data Flow
- **Source:** Consumes the `pattern` and `stem` data from the `DpdHeadword` table.
- **Output:** Updates the `inflections` and `inflections_html` columns in the main database.
- **Inward Bound:** Also populates the `InflectionTemplates` table in the database.
- **Consumption:** The **Exporters** and **GUIs** use the generated tables and form lists for lookup and display.

## Interface

- **Sync Templates:** `uv run python db/inflections/create_inflection_templates.py`
- **Regenerate Tables:** `uv run python db/inflections/generate_inflection_tables.py`
- **Transliterate:** `uv run python db/inflections/transliterate_inflections.py`

## Template source files

The inflection templates live in plain TSV files, one index plus one grid
per template:

- `templates_index.tsv` — columns `pattern`, `like`; one row per
  template, sorted by pattern (Pāḷi order).
- `templates/<pattern>.tsv` — the stem/ending grid, shaped like the old
  spreadsheet block: row 0 holds the pattern name and the column headings;
  rows 1+ hold row label, forms, grammar label triples. Multiple forms in
  one cell are joined with `", "` in Pāḷi alphabetical order; an empty cell
  is an empty string; LF line endings, UTF-8, no quoting.

All reading and writing of these files belongs to
`inflection_template_files.py`, which also checks on load: every index row
has a table file and vice versa, pattern names are unique, the top-left
cell equals the file name, every row is full width, and `like`
is not empty. A broken file raises `ValueError` naming it.

Edit the files in the gui2 **Infl** tab (Alt+I), or by hand and run the
sync. Saving or renaming in the tab does not regenerate the words: press
**Update Inflections** on the Global tab afterwards. Either way `create_inflection_templates.py` adds, updates or deletes
`inflection_templates` rows to match the files, and **adds** the changed
pattern names to two pending lists instead of overwriting them:
`DbInfo.changed_templates_list` (cleared by `generate_inflection_tables.py`
in the same commit as the regenerated words) and the gitignored pickle
`shared_data/changed_templates` (cleared by `transliterate_inflections.py`
after it writes). A gui2 Save followed by a build therefore never loses a
regeneration.

`inflection_templates.xlsx` is the old source of these files. It is unused
and kept for now; its `abbreviations` and `scripts` sheets are not carried
into the TSV files.
