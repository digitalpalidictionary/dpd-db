# db/lookup/

## Purpose & Rationale
The `lookup/` directory is responsible for building and managing the project's high-speed search index. Its rationale is to consolidate diverse data types (headwords, abbreviations, help content, spelling corrections) into a single, optimized table that can be queried instantly by the WebApp or other frontends without complex relational joins.

## Architectural Logic
This subsystem follows a "Consolidated Search Index" pattern:
1.  **Integration:** It aggregates data from multiple sources: the core `DpdHeadword` data, the `InflectionTemplates`, spelling mistake logs, and abbreviation TSVs.
2.  **Packing:** Complex data (like lists of grammatical possibilities or multiple meanings) are "packed" (serialized into strings/JSON) into the `Lookup` table's specialized columns.
3.  **Correction Logic:** `spelling_mistakes.py` adds common Pāḷi spelling errors to the index, allowing the dictionary to gracefully redirect users to the correct entry.
4.  **Transliteration:** It also handles the conversion of the index into multiple scripts (Sinhala, Thai, Devanagari) to ensure that users can search in their native script.

## Relationships & Data Flow
- **Sources:** Pulls from **db/models.py** (`Lookup`, `DpdHeadword`), **shared_data/** (abbreviations, help), and the **inflections/** generated outputs.
- **Output:** Updates the `Lookup` table in the SQLite database.
- **Application:** This table is the "Hot Data" that powers the search bar in the **WebApp**, **GoldenDict**, and **GUIs**.

## Interface
- **Update Help/Abbrev:** `uv run python db/lookup/help_abbrev_add_to_lookup.py`
- **Spelling Corrections:** `uv run python db/lookup/spelling_mistakes.py`
- **Transliterate Index:** `uv run python db/lookup/transliterate_lookup_table.py`
