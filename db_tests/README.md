# db_tests/

## Purpose & Rationale
`db_tests/` is the project's quality assurance layer. It exists to solve the problem of data decay and logical inconsistencies in a large, manually-edited lexicographical database. It ensures that every entry follows the rules required for the exporters to function correctly.

## Architectural Logic
This directory follows a "Continuous Validation" pattern. It contains a suite of tests that check for Relational Integrity (valid foreign keys), Data Standards (allowable characters, required fields), and Linguistic Consistency.

## Relationships & Data Flow
- **Audit:** Monitors the output of the **db/** build process and the **GUI** edits.
- **Correction:** Identifies issues that are subsequently fixed manually in the **GUI** or automatically via scripts in **scripts/fix/**.

## Interface
- **Relationship tests:** `just db-test` runs `db_tests_relationships.py`, a battery of cross-word relationship checks.
- **Column-rule tests:** `db_tests_manager.py` is a shared library (`DbTestManager`) running the rules in `db_tests_columns.tsv`; it is used live via gui2's Tests tab. Running it directly (`uv run db_tests/db_tests_manager.py`) is only a single-headword smoke demo.
- **Granular audits:** standalone interactive scripts in `single/`.
- **Interactive editors:** a Flet mini-app for bulk corrections in `gui/`.
