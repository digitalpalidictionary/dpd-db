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
