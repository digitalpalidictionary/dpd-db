# db/bold_definitions/

## Purpose & Rationale
This directory contains the logic for harvesting and managing "Bold Definitions" from the Chaṭṭha Saṅgāyana Tipitaka (CST) corpus. In Pāḷi commentaries, the word being defined is traditionally formatted in bold. By extracting these instances, the project creates a high-quality bridge between dictionary headwords and their authoritative traditional explanations.

## Architectural Logic
The subsystem follows an "Extract, Transform, Search" pattern:
1.  **Extraction:** `extract_bold_definitions.py` parses XML files from the CST corpus, identifying bolded text and their surrounding context (the commentary).
2.  **Transformation:** The extracted data is cleaned and structured into JSON and TSV formats for easy integration.
3.  **Database Integration:** `update_bold_definitions_db.py` syncs this data into the `bold_definitions` table in the main database.
4.  **Application:** `search_bold_definitions.py` provides the logic for querying this corpus, enabling the GUI and other tools to display relevant commentary snippets for any given word.

## Relationships & Data Flow
- **Input:** Reads raw Pāḷi text artifacts from the `resources/` directory (specifically the CST submodules).
- **Output:** Populates the `BoldDefinition` model in `db/models.py`.
- **Display:** The results are rendered in the **GUI** and exported to various formats to provide users with traditional context.

## Interface
- **Update:** `uv run python db/bold_definitions/extract_bold_definitions.py`
- **Sync:** `uv run python db/bold_definitions/update_bold_definitions_db.py`
