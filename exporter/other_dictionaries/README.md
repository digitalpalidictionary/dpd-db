# exporter/other_dictionaries/

## Purpose & Rationale
`other_dictionaries/` serves as the project's auxiliary export pipeline. Its rationale is to provide users with a "Complete Library" experience by packaging non-DPD dictionaries (such as Monier-Williams, Concise Pāḷi Dictionary, DPR, and Buddhist Hybrid Sanskrit) into the same optimized GoldenDict and MDict formats used for the main project. It solves the problem of disparate, hard-to-find dictionary files by offering a unified build process for external lexicographical resources.

## Architectural Logic
This subsystem follows a "Multi-Source Integration" pattern:
1.  **Specialization:** The `code/` directory contains sub-modules for each external dictionary, each with its own logic for parsing the original source (often HTML, JSON, or legacy formats).
2.  **Harmonization:** External data is transformed into the same structure used by the DPD exporters, allowing for shared minification and packaging logic.
3.  **Batch Processing:** `export_all.py` acts as the orchestrator, running the specialized exporters in sequence to produce a suite of auxiliary dictionary files.
4.  **Static Storage:** `json/`, `goldendict/`, and `mdict/` act as intermediate or final storage for the generated dictionary data and binaries.

## Relationships & Data Flow
- **Sources:** Pulls from a wide variety of external data sources (often pre-processed and stored in `json/` or specialized subfolders).
- **Consumption:** These dictionaries are intended to be installed by the user alongside DPD to provide comprehensive cross-referencing capabilities.
- **Tools:** Utilizes the project's standard `tools/goldendict_exporter.py` for final artifact generation.

## Interface
- **Export All:** `uv run python exporter/other_dictionaries/code/export_all.py`
- **Individual Exports:** Sub-exporters can be run from their respective directories within `code/`.
