# db/sinhala/

## Purpose & Rationale
Sri Lanka has a long and venerable tradition of Pāḷi scholarship. The `sinhala/` directory exists to integrate Sinhala translations and context into the Digital Pāḷi Dictionary. It solves the problem of cross-linguistic accessibility by providing high-quality Sinhala meanings for Pāḷi headwords, specifically targeting the Sinhala-speaking Buddhist community.

## Architectural Logic
This subsystem follows an "External Curation & Ingestion" pattern:
1.  **Curation:** Translations are often managed in specialized spreadsheets (e.g., `dpd sinhala 1.1.xlsx`) to allow translators to work in a familiar environment.
2.  **Ingestion:** `sinhala_xlxs_importer.py` maps these spreadsheet rows back to the primary `DpdHeadword` IDs and populates the `Sinhala` table in the database.
3.  **Synchronization:** `sinhala_xlxs_exporter.py` allows for the export of current database state back to Excel, enabling an iterative translation and review workflow.

## Relationships & Data Flow
- **Input:** Excel spreadsheets provided by the translation team.
- **Output:** Populates the `Sinhala` model in `db/models.py`.
- **Application:** Power the "Sinhala" button and definitions in the **WebApp** and specialized **Sinhala GoldenDict** exports.

## Interface
- **Import:** `uv run python db/sinhala/sinhala_xlxs_importer.py`
- **Export:** `uv run python db/sinhala/sinhala_xlxs_exporter.py`
