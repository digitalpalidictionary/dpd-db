# resources/

## Purpose & Rationale
The `resources/` directory is the foundational data layer of the project. Its rationale is to centralize all external, non-source-code dependencies required for the project to function. This includes vast Pāḷi text corpora (CST, SC, BJT), specialized fonts, audio recordings, and third-party documentation. It solves the problem of "missing dependencies" by ensuring all required datasets are part of the project's ecosystem.

## Architectural Logic
This directory follows an "External Data Foundation" pattern:
1.  **Corpora:** Subdirectories like `dpd_submodules/` (CST/BJT) and `sc-data/` store the raw text artifacts that form the basis of the dictionary's definitions and examples.
2.  **Specialized Submodules:** Git submodules (e.g., `bw2/`, `fdg_dpd/`) allow the project to integrate directly with external apps and websites while maintaining their independent development cycles.
3.  **Media Assets:** `dpd_audio/` provides the raw audio files for pronunciation.
4.  **Static References:** `flet-docs/` and other reference folders provide local copies of essential technical documentation for offline use.

## Relationships & Data Flow
- **Primary Input:** Acts as the raw input for the **db/** build processes and the **exporter/** rendering logic.
- **Independence:** While these resources are essential, they are generally treated as read-only artifacts that are updated via Git submodules or external downloads.

## Interface
Developers primarily interact with this folder by ensuring submodules are up-to-date or by referencing its paths in `tools/paths.py`.
