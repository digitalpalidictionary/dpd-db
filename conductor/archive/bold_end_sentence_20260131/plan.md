# Implementation Plan: Bold Definitions Extraction Bug Fix and Refactor

## Phase 1: Environment Setup & Research
- [x] Task: Create new directory `db/bold_definitions2/` and copy necessary scaffolding files.
- [x] Task: Research specific XML files identified (e.g., `s0101a.att.xml`) to find concrete examples of missing bold words at the end of sentences for test cases.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Environment Setup & Research' (Protocol in workflow.md)

## Phase 2: Refactoring & Unification
- [x] Task: Define the `BoldDefinitionEntry` class in `db/bold_definitions2/functions.py` to hold extraction data.
- [x] Task: Implement unified context tracking in `db/bold_definitions2/functions.py` (handling nikaya, book, title, subhead regardless of div structure).
- [x] Task: Implement the refactored `extract_bold_definitions.py` in `db/bold_definitions2/` using a single-pass `<p>` tag approach and the `BoldDefinitionEntry` class.
- [x] Task: Write unit tests in `tests/test_bold_extraction_logic.py` for context tracking and class-based extraction using sample XML snippets.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Refactoring & Unification' (Protocol in workflow.md)

## Phase 3: Bug Fix & Extraction logic
- [x] Task: Write failing tests in `tests/test_bold_end_of_sentence.py` that specifically target bold words at the end of paragraphs and sentences.
- [x] Task: Modify `get_bold_strings` and extraction logic in `db/bold_definitions2/` to remove the `next_sibling` constraint and correctly capture trailing punctuation.
- [x] Task: Implement refined cleaning and validation logic to ensure "substantial examples" are still prioritized and "useless endings" are handled correctly.
- [x] Task: Verify tests pass (Green phase).
- [x] Task: Conductor - User Manual Verification 'Phase 3: Bug Fix & Extraction logic' (Protocol in workflow.md)

## Phase 4: Verification & Comparison
- [x] Task: Create `db/bold_definitions2/compare_versions.py` to compare outputs between the old and new directories.
- [x] Task: Achieve zero "Lost" definitions by matching original heading and whitespace logic precisely.
- [x] Task: Run full extraction on both versions and generate a comparison report.
- [x] Task: Analyze "Gained" definitions to ensure they are the intended end-of-sentence captures.
- [x] Task: Ensure "Lost" definitions count is zero.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Verification & Comparison' (Protocol in workflow.md)

## Phase 5: Finalization
- [x] Task: Update `db/bold_definitions2/README.md` to reflect the new modular structure and improvements.
- [x] Task: Final code review and linting using `uv run ruff check .`.
- [x] Task: Conductor - User Manual Verification 'Phase 5: Finalization' (Protocol in workflow.md)
