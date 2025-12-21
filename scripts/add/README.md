# scripts/add/

## Purpose & Rationale
The `add/` directory provides the project's ingestion pipeline. Its rationale is to streamline the process of adding new data to the Digital Pāḷi Dictionary from diverse sources, ranging from curated TSV files to words extracted from new commentaries or specific text corpora (EBTs). It existence prevents the manual entry bottleneck.

## Architectural Logic
Scripts in this folder follow a "Staging and Ingestion" pattern:
1.  **Extraction:** Identifying new words or data points from external resources (e.g., `add_words_commentaries.py`).
2.  **Mapping:** Linking new entries to existing database structures (lemmas, POS, roots).
3.  **Deduplication:** Ensuring that additions do not create redundant entries in the main database.
4.  **Transaction:** Writing the new records into the SQLite database in a safe, atomic operation.

## Relationships & Data Flow
- **Source:** Pulls from **shared_data/additions.tsv** and external Pāḷi text resources in **resources/**.
- **Destination:** Populates the `DpdHeadword` table in **db/**.
- **Validation:** Newly added words are immediately subject to the integrity checks in **db_tests/**.

## Interface
- **Process Additions:** `uv run python scripts/add/add_additions_to_db.py`
- **Targeted Additions:** Use scripts like `add_words_ebts.py` when focusing on specific literary layers.
