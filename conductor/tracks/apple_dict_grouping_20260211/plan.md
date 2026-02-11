# Implementation Plan - Grouped Headwords in Apple Dictionary

This plan implements the grouping of dictionary entries by `lemma_clean` for the Apple Dictionary exporter.

## Phase 1: Setup and Template Design
- [ ] Task: Create new Jinja2 template for grouped entries.
    - [ ] Create `exporter/apple_dictionary/templates/entry_grouped.html`.
    - [ ] Implement logic to display singletons vs groups differently as per spec.
    - [ ] Ensure `lemma_clean` is used as the main header and not repeated in the body.
    - [ ] Include loop for sub-entries with their specific data points (number, pos, meaning, etc.).
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Setup and Template Design' (Protocol in workflow.md)

## Phase 2: Grouping Logic Implementation
- [ ] Task: Create TDD tests for grouping logic.
    - [ ] Create `tests/test_apple_dictionary_grouping.py`.
    - [ ] Mock `DpdHeadword` objects with various `lemma_1` values (grouped and singletons).
    - [ ] Implement test cases to verify the grouper yields correct lists of headwords.
- [ ] Task: Implement `HeadwordGrouper` logic.
    - [ ] In `exporter/apple_dictionary/apple_dictionary.py`, create a generator function/class that consumes a sorted stream of headwords and yields them in groups based on `lemma_clean`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Grouping Logic Implementation' (Protocol in workflow.md)

## Phase 3: Integration and XML Generation
- [ ] Task: Refactor `generate_dictionary_xml`.
    - [ ] Update the main query to ensure strict sorting by `lemma_1`.
    - [ ] Replace the simple loop with the new `HeadwordGrouper`.
    - [ ] Iterate over *groups* instead of single headwords.
- [ ] Task: Update `create_dictionary_xml_entry`.
    - [ ] Modify signature to accept `list[DpdHeadword]` instead of single `DpdHeadword`.
    - [ ] Update index generation to merge inflections from all headwords in the group.
    - [ ] Update template rendering to use `entry_grouped.html` with the list of headwords.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Integration and XML Generation' (Protocol in workflow.md)

## Phase 4: Final Verification
- [ ] Task: Verify output validity.
    - [ ] Run the full export command.
    - [ ] Check `Dictionary.xml` for correct grouping of "dhamma" and correct singleton display for "gacchati".
    - [ ] Validate XML syntax.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final Verification' (Protocol in workflow.md)
