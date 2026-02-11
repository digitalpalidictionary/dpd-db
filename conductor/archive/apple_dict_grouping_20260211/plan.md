# Implementation Plan - Grouped Headwords in Apple Dictionary

This plan implements the grouping of dictionary entries by `lemma_clean` for the Apple Dictionary exporter.

## Phase 1: Setup and Template Design
- [x] Task: Create new Jinja2 template for grouped entries.
    - [x] Update `exporter/apple_dictionary/templates/entry.html` (unified template for singletons and groups).
    - [x] Implement logic to display singletons vs groups identically (group of 1 = singleton).
    - [x] Ensure `lemma_clean` is used as the main header and not repeated in the body.
    - [x] Include loop for sub-entries with their specific data points (pos, meaning, etc.) in `<ol>` list.
- [x] Task: Add `lemma_number` property to `DpdHeadword` model (db/models.py).
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Setup and Template Design' (Protocol in workflow.md)

## Phase 2: Grouping Logic Implementation
- [x] Task: Create TDD tests for grouping logic.
    - [x] Create `tests/test_apple_dictionary_grouping.py`.
    - [x] Mock `DpdHeadword` objects with various `lemma_1` values (grouped and singletons).
    - [x] Implement test cases to verify the grouper yields correct lists of headwords.
- [x] Task: Implement `group_headwords_by_lemma_clean()` logic.
    - [x] In `exporter/apple_dictionary/apple_dictionary.py`, create a generator function that consumes a sorted stream of headwords and yields them in groups based on `lemma_clean`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Grouping Logic Implementation' (Protocol in workflow.md)

## Phase 3: Integration and XML Generation
- [x] Task: Refactor `generate_dictionary_xml`.
    - [x] Update the main query to sort by `lemma_1` using `pali_sort_key`.
    - [x] Replace the simple loop with the new `group_headwords_by_lemma_clean()`.
    - [x] Iterate over *groups* instead of single headwords.
- [x] Task: Update `create_dictionary_xml_entry`.
    - [x] Modify signature to accept `list[DpdHeadword]` instead of single `DpdHeadword`.
    - [x] Update index generation to merge inflections from all headwords in the group.
    - [x] Update template rendering with the list of headwords.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Integration and XML Generation' (Protocol in workflow.md)

## Phase 4: Final Verification
- [x] Task: Verify output validity.
    - [x] Run the full export command.
    - [x] Check `Dictionary.xml` for correct grouping of "dhamma" (16 entries) and correct display for "gacchati" (2 entries).
    - [x] Validate XML syntax with xmllint.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Final Verification' (Protocol in workflow.md)

## Summary

**Files Changed:**
- `db/models.py` - Added `lemma_number` property
- `exporter/apple_dictionary/templates/entry.html` - Updated to unified grouped template
- `exporter/apple_dictionary/apple_dictionary.py` - Added `group_headwords_by_lemma_clean()`, updated `create_dictionary_xml_entry()` and `generate_dictionary_xml()`
- `tests/test_apple_dictionary_grouping.py` - New test file (7 tests)

**Results:**
- 88,398 headwords grouped into 75,019 dictionary entries
- All 23 tests pass (7 new + 16 existing)
- XML validates successfully
