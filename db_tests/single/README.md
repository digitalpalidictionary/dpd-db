# db_tests/single/

## Purpose & Rationale
`db_tests/single/` is the project's collection of granular audit tools. Its rationale is to provide highly focused, individual tests for specific data columns, linguistic rules, or structural constraints. By breaking the massive task of database validation into "single" test units, the project ensures that even the most subtle logical errors (like incorrect vowel changes or numbering anomalies) can be detected and corrected.

## Architectural Logic
This directory follows a "Modular Audit" pattern:
1.  **Specialization:** Each script is designed to validate a single linguistic or data rule (e.g., `test_allowable_characters.py`, `test_family_compounds.py`).
2.  **Exception Handling:** Many tests are accompanied by `.json` or `.tsv` files that store legitimate exceptions, allowing the tests to be strictly accurate without reporting false positives.
3.  **Corrective Logic:** Some scripts (`add_...`) not only test but also provide logic for identifying and proposing corrections for missing data (like phonetic changes).
4.  **Decoupling:** These tests are intended to be run independently by the dictionary editor focusing on a specific data category.

## Relationships & Data Flow
- **Audit Target:** Runs directly against the live `dpd.db` using **db/** models.
- **Feedback:** Failures here are reported to the **GUI** or developer console to guide manual corrections.
- **Reference:** Acts as the executable "spec" for what constitutes valid data in the DPD project.

## Interface
Individual tests can be run as standalone scripts:
- `uv run python db_tests/single/test_allowable_characters.py`
- `uv run python db_tests/single/test_family_compounds.py`
(Refer to each script's docstring for specific details).
