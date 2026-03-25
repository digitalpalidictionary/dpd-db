# Plan: Compound Type Manager Tab (CT)

## Phase 1: Core Tab Scaffold and TSV Integration

- [x] Task: Create `gui2/compound_type_tab_view.py` with basic CT tab class inheriting from `ft.Column`
  - [x] Sub-task: Set up class with `__init__(self, page, toolkit)` matching existing tab patterns
  - [x] Sub-task: Register CT tab as the last tab in `gui2/main.py`
  - [x] Sub-task: Verify tab appears and is selectable in the GUI

- [x] Task: Write tests for TSV read/write operations
  - [x] Sub-task: Test loading rules from TSV
  - [x] Sub-task: Test adding a new rule to TSV
  - [x] Sub-task: Test editing an existing rule in TSV
  - [x] Sub-task: Test deleting a rule from TSV

- [x] Task: Implement TSV CRUD helpers in `CompoundTypeManager`
  - [x] Sub-task: Add method to append a rule to the TSV
  - [x] Sub-task: Add method to update an existing rule in the TSV
  - [x] Sub-task: Add method to delete a rule from the TSV
  - [x] Sub-task: Add method to get unique values for pos, position, and type fields

- [x] Task: Conductor - User Manual Verification 'Phase 1: Core Tab Scaffold and TSV Integration'

## Phase 2: UI Layout and Field Behavior

- [x] Task: Build Row 1 — word, pos, position, type fields
  - [x] Sub-task: Add `word` text field
  - [x] Sub-task: Add `pos` searchable dropdown populated from TSV values
  - [x] Sub-task: Add `position` searchable dropdown populated from TSV values
  - [x] Sub-task: Add `type` auto-fill text field with suggestions from existing TSV values

- [x] Task: Build Row 2 — exceptions field
  - [x] Sub-task: Add multiline text field that expands vertically and horizontally

- [x] Task: Build Row 3 — action buttons
  - [x] Sub-task: Add `Add`, `Search`, `Clear`, `Delete` buttons

- [x] Task: Implement word field pre-fill behavior
  - [x] Sub-task: On word field change, check TSV for matching rules
  - [x] Sub-task: If match found, pre-fill pos, position, type, and exceptions fields

- [x] Task: Implement Clear button
  - [x] Sub-task: Reset all fields and clear data display

- [x] Task: Conductor - User Manual Verification 'Phase 2: UI Layout and Field Behavior'

## Phase 3: Search and Data Display

- [x] Task: Write tests for database search logic
  - [x] Sub-task: Test position-based regex pattern generation (first, middle, last, any)
  - [x] Sub-task: Test pos filtering

- [x] Task: Implement Search button — query dpd_headwords
  - [x] Sub-task: Build position-based regex from word and position fields
  - [x] Sub-task: Query dpd_headwords where construction matches regex, filtered by pos
  - [x] Sub-task: Display results in data table with columns: #, lemma_1, meaning_1, compound_type, compound_construction

- [x] Task: Add "e" button to each result row for exception quick-add
  - [x] Sub-task: On click, append lemma_1 to the exceptions field (comma-separated)

- [x] Task: Conductor - User Manual Verification 'Phase 3: Search and Data Display'

## Phase 4: Add, Edit, Delete Operations

- [x] Task: Implement Add button
  - [x] Sub-task: Validate required fields (word, pos, position, type)
  - [x] Sub-task: Append new rule to TSV via CompoundTypeManager
  - [x] Sub-task: Auto-trigger Search after adding

- [x] Task: Implement Edit functionality
  - [x] Sub-task: When a pre-filled rule is modified, save changes back to TSV

- [x] Task: Implement Delete button
  - [x] Sub-task: Delete the currently loaded rule from TSV
  - [x] Sub-task: Clear fields after deletion

- [x] Task: Conductor - User Manual Verification 'Phase 4: Add, Edit, Delete Operations'

## Phase 5: Polish and Bug Fixes

- [x] Task: Code review bug fixes
  - [x] Sub-task: Fix `update_rule` dropping word modifications (added `new_word` param)
  - [x] Sub-task: Fix `e` button wiping unsaved table edits (added `_modified_cells` guards)
  - [x] Sub-task: Fix `e` button error when no rule loaded (guarded `_on_update` call)
  - [x] Sub-task: Fix stale iterator after Add and Update (refresh `_current_word_matches`)

- [x] Task: All tests passing (33/33)
