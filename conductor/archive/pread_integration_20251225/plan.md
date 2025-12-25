# Plan: GUI2 Proofreader Integration ("PRead")

## Phase 1: ProofreaderManager Implementation
- [x] Task: Research and define `ProofreaderManager` structure in `tools/proofreader.py` (mimicking `AdditionsManager`).
- [x] Task: Write unit tests for `ProofreaderManager` (loading TSV, popping next, saving TSV).
- [x] Task: Implement `ProofreaderManager` class in `tools/proofreader.py`.
- [x] Task: Verify `ProofreaderManager` tests pass.
- [x] Task: Conductor - User Manual Verification 'Phase 1: ProofreaderManager Implementation' (Protocol in workflow.md)

## Phase 2: ToolKit & UI Integration
- [x] Task: Add `ProofreaderManager` to `ToolKit` in `gui2/toolkit.py`.
- [x] Task: Add `_pread_button` to `Pass2AddView` top section in `gui2/pass2_add_view.py`.
- [x] Task: Register the `_click_pread_button` handler in `Pass2AddView`.
- [x] Task: Conductor - User Manual Verification 'Phase 2: ToolKit & UI Integration' (Protocol in workflow.md)

## Phase 3: Logic & Verification
- [x] Task: Implement `_click_pread_button` logic in `gui2/pass2_add_view.py`.
    - Fetch next correction.
    - Load database headword by ID.
    - Update `meaning_1_add` with the correction.
    - Update messages and remaining count.
- [x] Task: Manual verification of the full "PRead" workflow in the GUI.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Logic & Verification' (Protocol in workflow.md)
