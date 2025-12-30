# Implementation Plan: Sutta Catalog Deduplication

## Phase 1: Research and Planning

- [~] Review existing natsort usage patterns in scripts/suttas/bjt/*.py files (uses natsorted with alg=ns.PATH)
- [~] Review existing dv_catalogue_suttas.py implementation
- [x] Design the duplicate detection algorithm for consecutive entries
  - Example duplicate entries for testing:
    ```
    Entry 1: AN1.1 | summary="Test summary" | key_excerpt1="Excerpt A" | key_excerpt2="Excerpt B"
    Entry 2: AN1.2 | summary="Different"    | key_excerpt1="Excerpt C" | key_excerpt2="Excerpt D"
    Entry 3: AN1.3 | summary="Test summary" | key_excerpt1="Excerpt A" | key_excerpt2="Excerpt B"
    Entry 4: AN1.4 | summary="Test summary" | key_excerpt1="Excerpt A" | key_excerpt2="Excerpt B"
    Entry 5: AN1.5 | summary="Different"    | key_excerpt1="Excerpt E" | key_excerpt2="Excerpt F"
    ```
    Expected: Entry 1, Entry 2, Entry 3, Entry 5 (Entry 4 is consecutive duplicate of Entry 3)
  - Example with unsorted codes:
    ```
    Entry 1: AN1.10 | summary="Summary A" | key_excerpt1="Excerpt 1" | key_excerpt2="Excerpt 2"
    Entry 2: AN1.2  | summary="Summary B" | key_excerpt1="Excerpt 3" | key_excerpt2="Excerpt 4"
    Entry 3: AN1.1  | summary="Summary A" | key_excerpt1="Excerpt 1" | key_excerpt2="Excerpt 2"
    ```
    Expected after natural sort: AN1.1, AN1.2, AN1.10 (Entry 3 moves to first position)
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Test Setup

- [x] Verify natsort is available in dependencies (already in pyproject.toml)
- [x] Create test fixture with sample TSV data containing unsorted and duplicate entries
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Write Tests

- [x] Write one test that verifies correct output to DB (sorted and deduplicated)
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Implement Sorting and Duplicate Removal

- [x] Add natsorted import: `from natsort import natsorted, ns`
- [x] Implement natural sorting of dataframe by suttacode column using natsorted(alg=ns.PATH)
- [x] Implement duplicate removal logic that filters out consecutive duplicates where summary, key_excerpt1, and key_excerpt2 are identical
- [x] Add logging to report number of duplicates removed
- [x] Integrate sorting and duplicate removal into read_dv_catalogue()
- [x] Run test to verify correct DB output
- [x] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)

## Phase 5: Integration and Documentation

- [x] Update docstrings for read_dv_catalogue() to document new behavior
- [x] Run linting and type checking
- [ ] Task: Conductor - User Manual Verification 'Phase 5' (Protocol in workflow.md)
