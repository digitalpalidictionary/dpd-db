# db/epd/

## Purpose & Rationale
`db/epd/` (English-to-Pāḷi Dictionary) is responsible for the inverse mapping of the DPD database. While the core database is Pāḷi-centric, this subsystem extracts English meanings from the headword data to enable fast English-to-Pāḷi lookup functionality.

## Architectural Logic
This subsystem follows an "Inverse Indexing" pattern:
1.  **Collection:** It scans the `DpdHeadword` table, specifically targeting `meaning_1` and other definition fields.
2.  **Cleaning:** English meanings are sanitized and broken down into semi-colon separated keywords or short phrases.
3.  **Mapping:** Each unique English term is mapped to a list of corresponding Pāḷi lemmas, along with their parts of speech and case information.
4.  **Integration:** The final mappings are "packed" into the project's `Lookup` table, which serves as the high-speed index for all search interfaces.

## Relationships & Data Flow
- **Source:** Pulls data from `DpdHeadword` and `DpdRoot` in **db/models.py**.
- **Output:** Populates the `epd` column in the `Lookup` table.
- **Consumption:** The **WebApp** and **Exporters** use this index to provide "English search" functionality.

## Interface
- **Compile:** `uv run python db/epd/epd_to_lookup.py` (Usually called as part of the full DB build process).
