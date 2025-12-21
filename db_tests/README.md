# db_tests/

## Purpose & Rationale
`db_tests/` is the project's quality assurance layer. It exists to solve the problem of data decay and logical inconsistencies in a large, manually-edited lexicographical database. It ensures that every entry follows the rules required for the exporters to function correctly.

## Architectural Logic
This directory follows a "Continuous Validation" pattern. It contains a suite of tests that check for Relational Integrity (valid foreign keys), Data Standards (allowable characters, required fields), and Linguistic Consistency.

## Relationships & Data Flow
- **Audit:** Monitors the output of the **db/** build process and the **GUI** edits.
- **Correction:** Identifies issues that are subsequently fixed manually in the **GUI** or automatically via scripts in **scripts/fix/**.

## Interface
Tests are run within **GUI** and as individual python scripts from this folder. 
The primary entry point is the test manager:
`uv run python db_tests/db_tests_manager.py`
