# Implementation Plan

## Phase 1: Setup and File Organization
- [x] Task: Move TSV file from `db_tests/single/add_compound_type.tsv` to `tools/compound_type_manager.tsv`

## Phase 2: Create CompoundTypeManager (TDD)
- [x] Task: Write tests for CompoundTypeManager
    - [x] Sub-task: Create `tests/test_compound_type_manager.py`
    - [x] Sub-task: Test TSV loading and parsing
    - [x] Sub-task: Test compound type detection logic
    - [x] Sub-task: Test exception handling (missing TSV, malformed data)
    - [x] Sub-task: Run tests and confirm they fail (Red phase)
- [x] Task: Implement CompoundTypeManager
    - [x] Sub-task: Create `tools/compound_type_manager.py`
    - [x] Sub-task: Implement `__init__` with TSV loading
    - [x] Sub-task: Implement `detect_compound_type()` method
    - [x] Sub-task: Implement `open_tsv_for_editing()` method
    - [x] Sub-task: Add type hints to all methods
- [x] Task: Run tests to verify implementation (Green phase)
- [x] Task: Run ruff check --fix and ruff format on new files

## Phase 3: Refactor Database Test
- [x] Task: Update `db_tests/single/add_compound_type.py`
    - [x] Sub-task: Import CompoundTypeManager from tools
    - [x] Sub-task: Replace inline detection logic with manager calls
    - [x] Sub-task: Update TSV path reference to new location
    - [x] Sub-task: Remove duplicate code (keep only CLI/interface logic)
- [x] Task: Run database test to verify it still works
- [x] Task: Run ruff check --fix and ruff format on modified file

## Phase 4: GUI Integration
- [x] Task: Add construction_blur handler in DpdFields
    - [x] Sub-task: Import CompoundTypeManager in dpd_fields.py
    - [x] Sub-task: Initialize manager in `__init__`
    - [x] Sub-task: Implement `construction_blur()` method
    - [x] Sub-task: Add validation checks (meaning_1, pos, grammar)
    - [x] Sub-task: Call detection and auto-fill compound_type if match found
- [x] Task: Update construction field configuration
    - [x] Sub-task: Add `on_blur=self.construction_blur` to construction FieldConfig
- [x] Task: Add Edit TSV button
    - [x] Sub-task: Create button in appropriate GUI view
    - [x] Sub-task: Connect button to manager's open_tsv_for_editing() method
- [x] Task: Test GUI auto-fill functionality manually
- [x] Task: Run ruff check --fix and ruff format on modified files

## Phase 5: Final Verification
- [x] Task: Run full test suite
- [x] Task: Verify all acceptance criteria are met
- [x] Task: Create final summary of all changes
- [x] Task: **MANUAL VERIFICATION** - Conductor User Verification (Protocol in workflow.md)
