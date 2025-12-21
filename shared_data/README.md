# shared_data/

## Purpose & Rationale
`shared_data/` is the project's static data warehouse. It exists to solve the problem of managing large, version-controlled datasets that are not yet in the relational database or represent project-wide metadata (like abbreviation lists and correction histories).

## Architectural Logic
This directory follows a "Single Source of Truth for Raw Data" pattern. Files here are typically in human-readable formats (TSV, JSON, TXT) to allow for easy diffing in Git. They represent the "memory" of the project beyond the current database state.

## Relationships & Data Flow
- **Initialization:** Provides the source data for many **db/** build processes.
- **Persistence:** Stores the output of automated correction or deletion scripts from the **scripts/** folder.
- **Centralization:** Ensures that common mappings (like abbreviations) are defined once and used project-wide.

## Interface
Files in this directory are typically accessed programmatically via `tools/paths.py`.