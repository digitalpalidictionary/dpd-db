# gui/stash/

## Purpose & Rationale
The `stash/` directory provides a local persistence layer for the GUI applications. Its rationale is to protect the editor's progress and maintain a seamless user experience by storing state, session metadata, and temporary "stashed" data that does not yet belong in the main relational database.

## Architectural Logic
This directory follows a "Local State Management" pattern:
1.  **GUI State:** Stores the window positions, active tabs, and field values to allow the editor to resume exactly where they left off.
2.  **Daily Record:** Logs the editor's daily activity and progress for personal tracking or auditing.
3.  **Examples Stash:** A temporary holding area for sutta examples or other curated snippets that are being reviewed before final ingestion.
4.  **Serialization:** Data is typically stored in simple formats like JSON or Pickle for fast read/write access during the GUI's lifecycle.

## Relationships & Data Flow
- **Interaction:** The **gui/** and **gui2/** systems write to this directory upon significant events (tab change, save, exit).
- **Persistence:** Ensures that "work-in-progress" is not lost between application restarts or system reboots.

## Interface
This folder is managed automatically by the GUI functions. Developers should not manually edit these files unless they are debugging state restoration issues.
