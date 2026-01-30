# exporter/grammar_dict/

## Purpose & Rationale
While the main dictionary provides definitions, the `grammar_dict/` exporter exists to provide a standalone, highly specialized reference focused purely on Pāḷi morphology. Its rationale is to help students and scholars quickly identify the grammatical role of any inflected word-form (e.g., "this word is an aorist 3rd person plural") without the clutter of full dictionary definitions.

## Architectural Logic
This subsystem follows a "Specialized Index Export" pattern:
1.  **Data Extraction:** It pulls "packed" grammatical data from the `Lookup` table, which already contains the pre-calculated results from the `db/grammar/` subsystem.
2.  **HTML Templating:** It uses Jinja2 templates (`templates_jinja2/`) to transform these grammatical possibilities into clean, consistent HTML tables.
3.  **Cross-Format Export:** It utilizes the project's standard export tools (`tools/goldendict_exporter.py` and `tools/mdict_exporter.py`) to generate the final binaries for GoldenDict and MDict.
4.  **Minification:** Like other exporters, it applies CSS and HTML minification to ensure the resulting dictionary files are as efficient as possible.

## Relationships & Data Flow
- **Source:** Pulls from the `Lookup` table in the database, relying on the `grammar` column.
- **Consumption:** Provides a standalone dictionary product that users can install alongside the main DPD.
- **Identity:** Uses project-standard CSS to ensure the tables look consistent with the main dictionary entries.

## Interface
- **Export:** `uv run python exporter/grammar_dict/grammar_dict.py`
