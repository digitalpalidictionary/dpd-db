# scripts/archive/

## Purpose & Rationale
`scripts/archive/` is the project's historical vault. Its rationale is to preserve the wide variety of one-off, legacy, and experimental scripts that have shaped the Digital Pāḷi Dictionary over the years. It solves the problem of "losing" complex logic that was used for past data migrations, massive batch corrections, or specialized research projects.

## Architectural Logic
This directory follows a "Preservation and Reference" pattern:
1.  **Decommissioned Logic:** Contains scripts that were once essential but have been replaced by more modern subsystems (e.g., old DB rebuilders, legacy inflection finders).
2.  **One-Off Tasks:** Preserves scripts used for unique, non-repeating events, such as bulk renames or specific textual corrections (e.g., `theragatha_name_finder.py`).
3.  **Experimental Lab:** Stores various speed tests, memory analysis scripts, and prototyping code that informed the current high-performance Go and Python implementations.
4.  **No Guarantee of Execution:** Unlike the scripts in the main folders, these archived files are not expected to be compatible with the current environment or database schema without significant modification.

## Relationships & Data Flow
- **Source of Wisdom:** Acts as a library of techniques for developers looking to perform similar complex database manipulations in the future.
- **Provenance:** Documents the evolution of the project's operational workflows.

## Interface
These scripts are intended for **reading and reference only**. They should not be run in the production environment unless a developer is intentionally recreating a past migration or correction logic.
