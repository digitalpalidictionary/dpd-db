# Plan: Sortable and Optimized Grammar Dictionary

## Phase 1: Performance and Caching
- [x] Task: Identify redundant grammatical data in the `lookup` table.
- [x] Task: Implement an HTML cache (dict) in `generate_html_from_lookup` to reuse generated HTML for identical grammar data.
- [x] Task: Measure and verify performance improvement.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Performance and Caching' (Protocol in workflow.md)

## Phase 2: HTML/CSS Refactoring
- [x] Task: Modify `generate_html_from_lookup` to restore HTML headers/footers for compatibility.
- [x] Task: Implement the `load_js` pattern in `grammar_dict_header.html` for GoldenDict/MDict support.
- [x] Task: Update the table generation logic to add a `class='col_empty'` to empty columns (2, 3, 4).
- [x] Task: Add CSS rules to `dpd.css` (or `dpd-css-and-fonts.css`) to hide empty columns.
- [x] Task: Conductor - User Manual Verification 'Phase 2: HTML/CSS Refactoring' (Protocol in workflow.md)

## Phase 3: JavaScript Development (TDD)
- [x] Task: Write unit tests for Pāḷi-aware sorting in JavaScript.
- [x] Task: Implement `paliSortKey` function in `sorter.js`.
- [x] Task: Implement table sorting logic with Reset state support.
- [x] Task: Implement Unicode arrow indicator updates.
- [x] Task: Conductor - User Manual Verification 'Phase 3: JavaScript Development (TDD)' (Protocol in workflow.md)

## Phase 4: Integration and Platform Testing
- [x] Task: Verify that `sorter.js` is correctly included in the GoldenDict and MDict export process via `DictVariables`.
- [x] Task: Fix HTML header and JS loading for GoldenDict/MDict compatibility.
- [x] Task: Test the generated dictionary in GoldenDict-ng and MDict.
- [x] Task: Verify Pāḷi sort order works as expected.
- [x] Task: Verify empty columns are hidden.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Integration and Platform Testing' (Protocol in workflow.md)

## Phase 5: Webapp Integration
- [x] Task: Refactor `exporter/webapp/templates/grammar.html` to use the 6-column structure (Pos, Gram1, Gram2, Gram3, Of, Word) matching the Grammar Dictionary.
- [x] Task: Update `exporter/webapp/data_classes.py` (or template logic) to split grammar strings into components.
- [x] Task: Ensure `sorter.js` is correctly loaded and initialized in the Webapp.
- [x] Task: Conductor - User Manual Verification 'Phase 5: Webapp Integration' (Protocol in workflow.md)
