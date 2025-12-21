# db/variants/

## Purpose & Rationale
Different editions of the Pāḷi Tipitaka (e.g., Chaṭṭha Saṅgāyana, Buddha Jayanthi, Syāmaraṭṭha) often contain variations in spelling or word choice. The `variants/` directory exists to systematically harvest these differences. Its rationale is to ensure that DPD is not limited to a single edition, but acts as a comprehensive map of all authoritative manuscript readings, allowing users to find headwords regardless of the edition they are reading.

## Architectural Logic
This subsystem follows a "Corpus Variant Extraction" pattern:
1.  **Multi-Edition Processing:** Specialized scripts (e.g., `extract_variants_from_bjt.py`, `extract_variants_from_cst.py`) parse the specific formatting and markup used by different editions to identify variant readings.
2.  **Aggregation:** `main.py` orchestrates these extractions, combining them into a unified `VariantsDict`.
3.  **Refinement:** Logic within `variants_modules.py` handles the cleaning and categorization of the extracted variants.
4.  **Database Sync:** `add_to_db.py` updates the main project database with these consolidated variations.

## Relationships & Data Flow
- **Input:** Reads raw text resources from multiple editions located in **resources/**.
- **Output:** Updates the `variant` related fields in the `DpdHeadword` table.
- **Consumption:** The **exporter/variants/** module uses this data to generate standalone variant dictionaries.

## Interface
- **Full Process:** `uv run python db/variants/main.py`
- **Targeted Extraction:** Sub-scripts can be run individually to re-process specific editions.
