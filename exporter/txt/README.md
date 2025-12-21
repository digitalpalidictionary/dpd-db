# exporter/txt/

## Purpose & Rationale
`exporter/txt/` provides the project's simplest and most accessible export path. Its rationale is to transform the rich, multi-dimensional database into a plain human-readable text file. This format is ideal for users with visual impairments who rely on screen readers, for developers performing large-scale text analysis (grep/sed), and for archival purposes where long-term durability is prioritized over visual complexity.

## Architectural Logic
This subsystem follows a "Linear Text Serialization" pattern:
1.  **Iterative Rendering:** `export_txt.py` loops through every headword in the sorted database.
2.  **Summary Logic:** It condenses complex relational data (grammar, meanings, completions) into single lines or simple indented blocks.
3.  **Variant Versions:** It supports specialized logic for different audiences (e.g., the `aj_version` which prioritizes Sanskrit cognates for specific scholarly use).
4.  **Distribution:** The final large text file is typically zipped for efficient distribution.

## Relationships & Data Flow
- **Source:** Pulls from `DpdHeadword` in **db/**.
- **Consumption:** Used for accessibility tools, command-line searches, and as a raw data source for other linguistic experiments.
- **Tools:** Uses `tools/zip_up.py` for final packaging.

## Interface
- **Export:** `uv run python exporter/txt/export_txt.py`
