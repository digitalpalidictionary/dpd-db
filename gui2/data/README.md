# gui2/data/

## Purpose & Rationale
The modern Flet-based GUI (`gui2`) relies on a robust local data layer. `gui2/data/` exists to manage the high-volume JSON data that fuels the "Pass 1" and "Pass 2" editorial workflows. Its rationale is to provide a fast, local cache for word additions, corrections, and automated processing results that are in transit between the raw corpora and the relational database.

## Architectural Logic
This directory follows a "Workflow Cache" pattern:
1.  **Automation Stages:** `pass1_auto_...` and `pass2_pre_...` files store the intermediate results of automated scans across different books of the Tipitaka.
2.  **User State:** `history.json` and `filter_presets.json` preserve the editor's individual preferences and recent activity.
3.  **Correction Logging:** `corrections.json` and `additions.json` act as the primary buffers for changes that have been proposed but not yet fully committed or synchronized.
4.  **Failure Analysis:** Files like `pass2_auto_failures.txt` provide debug information for automated tasks that require human intervention.

## Relationships & Data Flow
- **Input:** Populated by "Managers" and "Controllers" within the **gui2/** root.
- **Output:** Successful additions and corrections are eventually promoted to the **db/** subsystem or the **shared_data/** TSVs.
- **Sync:** Works in tandem with the logic in `gui2/additions_manager.py` and `gui2/corrections_manager.py`.

## Interface
This is an internal storage directory for the `gui2` subsystem. Files are managed programmatically and should typically not be edited by hand.
