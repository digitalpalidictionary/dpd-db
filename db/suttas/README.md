# db/suttas/

## Purpose & Rationale
`db/suttas/` is the project's gateway to textual metadata. Its rationale is to provide a reliable, up-to-date link between dictionary headwords and the primary Pāḷi sutta literature. By synchronizing metadata from authoritative external sources (like websites and Dhamma Vinaya tools on GitHub), it ensures that the DPD project has accurate titles, summaries, and IDs for all suttas referenced in the database.

## Architectural Logic
This subsystem follows a "Metadata Synchronization" pattern:
1.  **Ingestion:** `suttas_update.py` downloads the latest curated metadata from collaborative Google Sheets and stores it as local TSVs.
2.  **Reconstruction:** It handles the dropping and recreation of the `SuttaInfo` table to ensure the database schema remains clean and synchronized with the latest curated columns.
3.  **Refinement:** `dv_catalogue_suttas.py` performs specialized updates for Dhamma Vinaya Tools sutta catalogue fields, providing deep scholarly context.
4.  **Lookup Integration:** `suttas_to_lookup.py` ensures that sutta names and IDs are searchable within the main project index.

## Relationships & Data Flow
- **Source:** Pulls from live collaborative spreadsheets and local metadata files in **resources/**.
- **Output:** Populates the `SuttaInfo` model in **db/models.py**.
- **Display:** This data is essential for the "Sutta Information" popups and search results in the **WebApp** and **Exporters**.

## Interface
- **Full Update:** `uv run python db/suttas/suttas_update.py` (Downloads, drops, recreates, and populates the table).
- **Lookup Sync:** `uv run python db/suttas/suttas_to_lookup.py`
