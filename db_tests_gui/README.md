# db_tests_gui/

## Purpose & Rationale
`db_tests_gui/` is the interactive counterpart to the project's data integrity suite. Its rationale is to provide a user-friendly, visual environment for running database tests and, more importantly, for managing the corrections they trigger. It solves the problem of tedious command-line auditing by allowing editors to review and approve bulk data updates (like adding antonyms or hyphenations) in a centralized Flet-based application.

## Architectural Logic
This subsystem follows an "Interactive Test and Propose" pattern:
1.  **Orchestration:** `main.py` provides a Flet-based multi-panel interface for selecting and running different audit routines.
2.  **Specialized Adders:** Scripts (e.g., `add_antonyms.py`, `add_hyphenations.py`) act as the "engine" for specific tests, identifying missing data and preparing proposed corrections.
3.  **Visual Approval:** The GUI allows the user to see the current state vs. the proposed change, ensuring high-quality human oversight for automated updates.
4.  **Local Storage:** Uses the `storage/` directory to manage temporary data or persistent test configurations.

## Relationships & Data Flow
- **Input:** Directly interacts with `dpd.db` and the version-controlled TSVs.
- **Consumption:** Used by lexicographers during major data-capture phases to ensure consistency and coverage.
- **Evolution:** Represents the project's transition toward more modern, responsive internal tooling (using Flet).

## Interface
- **Start Test Runner:** `uv run flet run db_tests_gui/main.py`
