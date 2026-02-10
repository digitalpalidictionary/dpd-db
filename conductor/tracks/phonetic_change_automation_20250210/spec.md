# Phonetic Change Automation

## Overview

Create a `PhoneticChangeManager` in `tools/` that encapsulates the phonetic change logic currently in `db_tests/single/add_phonetic_changes.py`. The manager will:
- Load and parse the TSV file from `tools/phonetic_changes.tsv`.
- Provide detection and processing logic used by both the database test and the GUI.
- Be integrated into the GUI to auto-fill or suggest phonetic changes when the `phonetic` field receives focus.

## Functional Requirements

1.  **Manager Location**: `tools/phonetic_change_manager.py`
2.  **TSV Location**: `tools/phonetic_changes.tsv` (moved from `db_tests/single/add_phonetic_changes.tsv`)
3.  **Core Logic**:
    -   The manager must replicate the existing logic: checking `initial`, `final`, `exceptions`, etc., against the headword's `construction`, `base`, and `lemma`.
    -   It should return structured data indicating if a change is "auto_update", "auto_add", or requires "manual_check".
4.  **GUI Integration**:
    -   **Trigger**: When the `phonetic` field receives focus.
    -   **Auto-fill**: If a single, unambiguous change is detected (corresponding to "auto_update" or "auto_add"), automatically update the `phonetic` field.
    -   **Suggestions**: If there is a conflict or multiple possibilities (corresponding to "manual_check" or ambiguous cases), populate the `phonetic_add` field (the field to the right) with the suggestions.
5.  **Test Script Refactor**:
    -   `db_tests/single/add_phonetic_changes.py` must be refactored to use `PhoneticChangeManager`.
    -   The test script must maintain its existing CLI behavior (interactive prompts, rich printing) by consuming the data returned by the manager.

## Non-Functional Requirements

-   **Code Deduping**: The core logic must exist in only one place (the Manager).
-   **Backwards Compatibility**: The existing test script behavior must remain unchanged from the user's perspective.
-   **Type Hints**: All new code must be fully type-hinted.
-   **Linting**: Must pass `ruff check --fix` and `ruff format`.

## Acceptance Criteria

-   [ ] `PhoneticChangeManager` is created and correctly loads the TSV.
-   [ ] `tools/phonetic_changes.tsv` exists and contains the data from the original file.
-   [ ] `db_tests/single/add_phonetic_changes.py` runs exactly as before, but imports logic from the manager.
-   [ ] GUI `phonetic` field auto-fills correctly when focused and a clear rule applies.
-   [ ] GUI `phonetic_add` field shows suggestions when a conflict or manual check is required.
-   [ ] All code passes `ruff` linting and formatting.

## Out of Scope

-   Changing the logic of how phonetic changes are determined (we are moving/refactoring, not redesigning the linguistic rules).
-   Adding new columns or data types to the TSV (unless required for the refactor).
