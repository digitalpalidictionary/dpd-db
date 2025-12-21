# scripts/export/

## Purpose & Rationale
While the `exporter/` directory handles the generation of final dictionary products, the `scripts/export/` folder exists to provide flexible, ad-hoc export capabilities for data analysis, external collaboration, and targeted reporting. Its rationale is to allow developers and lexicographers to quickly extract specific subsets of the database into common formats like Excel or TSV.

## Architectural Logic
Scripts in this folder follow a "Filter and Flatten" pattern:
1.  **Querying:** They typically utilize `pandas` or direct SQL queries to pull data from the SQLite database.
2.  **Filtering:** Targeted logic allows for selecting rows based on specific criteria (e.g., only words with Sanskrit cognates, or only words from a certain part of speech).
3.  **Normalization:** Complex relational data is flattened into a tabular format suitable for spreadsheets.
4.  **Serialization:** The data is then written to `.xlsx` or `.tsv` files for external use.

## Relationships & Data Flow
- **Source:** Reads from the live `dpd.db` using **db/** models.
- **Output:** Generates temporary or project-specific data files (often stored in the project root or `temp/`).
- **Inward Bound:** These exports are sometimes used by translators or specialists who return the edited files for re-ingestion.

## Interface
- **Targeted Export:** `uv run python scripts/export/db_filter_export.py` (Edit the `main()` function to adjust filtering criteria).
