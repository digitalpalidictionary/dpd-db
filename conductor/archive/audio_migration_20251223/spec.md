# Specification: Audio Migration

## Overview
Migrate the audio development environment from `resources/dpd_audio/` (submodule) to a root-level `audio/` folder. This allows the Python scripts and logic to be version-controlled within the main `dpd-db` repository, while keeping the large data artifacts (MP3 files and the `dpd_audio.db` database) git-ignored and managed through external Releases.

## Functional Requirements
1.  **Code Migration:** Move all Python scripts and directory structures (e.g., `bhashini/`, `error_check/`) from `resources/dpd_audio/` to a new root `audio/` directory.
2.  **Path Synchronization:** Update `tools/paths.py` to point to the new root `audio/` location for all audio-related paths.
3.  **Data Isolation (Git-Ignore):**
    *   Update root `.gitignore` to strictly ignore `audio/mp3s/` and `audio/db/dpd_audio.db`.
    *   The data artifacts will be manually copied/linked to these locations for local processing but never committed to `dpd-db`.
4.  **Legacy Folder Maintenance:**
    *   Keep `resources/dpd_audio/` as a directory.
    *   Add a `README.md` to `resources/dpd_audio/` stating that this is the staging area for releases, and that logic has moved to the root `audio/` folder.
5.  **Submodule Decommissioning (Deferred):** The submodule removal will be the final step, performed ONLY after explicit user approval.

## Non-Functional Requirements
1.  **Code Integrity:** No logic changes; only path and organizational updates.
2.  **Repository Size Management:** Ensure large binary files are strictly git-ignored.

## Acceptance Criteria
- [ ] Root `audio/` folder contains all scripts and logic from the previous submodule.
- [ ] `git status` shows the `.py` files in `audio/` are tracked, but `audio/mp3s/` and `audio/db/dpd_audio.db` are ignored.
- [ ] `tools/paths.py` is updated and all audio scripts run without path errors.
- [ ] `resources/dpd_audio/README.md` is updated with current usage instructions.
