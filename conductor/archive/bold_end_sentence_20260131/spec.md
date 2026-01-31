# Specification: Bold Definitions Extraction Bug Fix and Refactor

## Overview
The goal of this track is to fix a bug in the bold definition extraction process where bolded words at the end of sentences (followed by a full stop and/or being the last child of a paragraph) are not being captured. Simultaneously, the extraction logic will be refactored for improved readability and modularity, and unified to handle different XML structures more consistently. All work will be performed in a new directory `db/bold_definitions2` to allow for side-by-side comparison and ensure zero regression.

## Goals
- Fix the "end of sentence" bug where `<hi rend="bold">word.</hi></p>` or similar patterns are skipped.
- Refactor `extract_bold_definitions.py` into a modular, class-based structure in `db/bold_definitions2/`.
- Unify the extraction logic to remove the binary distinction between files with `soup.div` and those without.
- Create a comparison tool to verify that the new version captures all existing definitions plus the previously missed ones.

## Functional Requirements
1. **New Directory Structure**: Create `db/bold_definitions2/` and populate it with refactored versions of `extract_bold_definitions.py`, `functions.py`, and other necessary scripts.
2. **Data Model Class**: Implement a `BoldDefinitionEntry` class (using `dataclasses` or `Pydantic`) to represent an extracted definition, replacing raw dictionaries for better type safety and consistency.
3. **Unified Extraction Logic**:
    - Iterate through all `<p>` tags in the XML files.
    - Dynamically track context (`nikaya`, `book`, `title`, `subhead`) regardless of the presence of `<div>` tags by identifying heading patterns in paragraphs.
4. **Punctuation & End-of-Paragraph Handling**:
    - Remove the `if bold.next_sibling is not None:` constraint.
    - Ensure `get_bold_strings` correctly handles cases where punctuation is inside or immediately follows the bold tag.
5. **Comparison Tool**:
    - Implement a script (e.g., `compare_versions.py`) that:
        - Loads the TSV/JSON output from both `db/bold_definitions` and `db/bold_definitions2`.
        - Identifies "Lost" definitions (should be zero).
        - Identifies "Gained" definitions (should include the end-of-sentence cases).
        - Generates a summary report.

## Non-Functional Requirements
- **Zero Regression**: No existing valid bold definitions should be lost.
- **Maintainability**: Use modern Python type hints and modular functions in `functions.py`.
- **Readability**: Simplify complex regex and string cleaning logic where possible without changing behavior.

## Acceptance Criteria
- All definitions previously captured by the original script are present in the new script's output.
- Bold words at the end of sentences/paragraphs are successfully captured.
- The comparison report confirms the above and shows no unexpected changes.
- The refactored code is reviewed and approved for better readability and structure.

## Out of Scope
- Changes to the `BoldDefinition` SQLAlchemy database model.
- Changes to the search GUI or other downstream consumers of the bold definitions data (except for potential updates to the source file paths).
