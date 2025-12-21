# scripts/build/

## Purpose & Rationale
The `build/` directory contains the core automation logic for reconstructing and updating the DPD project's primary artifacts. Its rationale is to provide a reliable, repeatable pipeline for transitioning from raw data (TSVs, XMLs) to a fully populated, optimized database and ready-to-deploy archives.

## Architectural Logic
Scripts in this folder follow a "Transformation & Enrichment" pattern:
1.  **Reconstruction:** `db_rebuild_from_tsv.py` serves as the primary entry point for recreating the SQLite database from the version-controlled TSV files.
2.  **Enrichment:** Specialized scripts (e.g., `ebt_counter.py`, `root_has_verb_updater.py`) calculate and inject derived metadata into the database.
3.  **Linguistic Processing:** Handles complex transformations like transliterating corpora (`transliterate_bjt.py`) or parsing raw XML into usable text formats.
4.  **Artifact Preparation:** Logic for zipping and tarballing the resulting database and dictionary files for distribution (`tarball_db.py`, `zip_goldendict_mdict.py`).
5.  **Quality Gates:** `dealbreakers.py` performs final sanity checks before a build is considered "production-ready."

## Relationships & Data Flow
- **Input:** Consumes raw TSVs from **db/backup_tsv/** and external resources from **resources/**.
- **Output:** Populates the `dpd.db` SQLite file and generates the deployment archives.
- **Service Layer:** Heavily utilizes **tools/** for specialized Pāḷi processing and file management.

## Interface
Most build tasks are coordinated via the central build script:
- `uv run python scripts/build/db_rebuild_from_tsv.py`
Sub-tasks can be run individually as needed for maintenance.
