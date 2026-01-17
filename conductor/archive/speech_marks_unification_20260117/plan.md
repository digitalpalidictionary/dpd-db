# Implementation Plan: Speech Marks Unification

## Phase 1: Foundation - Path and Type Definitions

- [x] Add `speech_marks_path` to `tools/paths.py`
  - Add: `self.speech_marks_path = base_dir / "tools/speech_marks.json"`
  - Keep old paths for migration period, mark deprecated in docstrings

- [x] Create type definitions in `tools/speech_marks.py`
  - `SpeechMarksDict = dict[str, list[str]]`
  - Import required modules: Path, json, dataclasses if needed

- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: SpeechMarkManager Implementation

- [x] Implement `SpeechMarkManager.__init__()`
  - Load from `tools/speech_marks_path` if exists
  - Initialize empty `speech_marks_dict: SpeechMarksDict` if file doesn't exist
  - Load old hyphenations if `tools/hyphenations.json` exists

- [x] Implement core getter methods
  - `get_speech_marks() -> SpeechMarksDict` - Return complete dictionary
  - `get_variants(clean_word: str) -> list[str] | None` - Get variants for specific word
  - `has_variants(clean_word: str) -> bool` - Check existence

- [x] Implement update and persistence methods
  - `update_variants(clean_word: str, variant: str)` - Add or append to list
  - `save()` - Write to JSON with `ensure_ascii=False, indent=2`

- [x] Implement DB regeneration methods
  - `regenerate_from_db()` - Scan DpdHeadword for apostrophe words
  - `_should_regenerate() -> bool` - Check cache age (1 day expiry)
  - `_make_from_db()` - Core DB scanning logic (migrate from `SandhiContractionManager`)

- [x] Write failing tests for `SpeechMarkManager`
  - Test initialization with and without existing JSON
  - Test loading old hyphenations
  - Test `get_variants()` returns correct list
  - Test `update_variants()` appends to existing lists
  - Test `regenerate_from_db()` produces correct data
  - Run tests and confirm they fail (Red phase)

- [x] Implement `SpeechMarkManager` to pass all tests (Green phase)
  - Write minimal code to make tests pass
  - Run tests and confirm they pass

- [x] Refactor `SpeechMarkManager` for clarity
  - Remove duplication, improve performance if needed
  - Ensure code follows project conventions

- [x] Run ruff on `tools/speech_marks.py`
  - `uv run ruff check tools/speech_marks.py`
  - `uv run ruff format tools/speech_marks.py`

- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Create Initial Unified JSON

- [x] Create initial `tools/speech_marks.json`
  - Manually merge existing `tools/hyphenations.json` data
  - Manually merge existing `tools/sandhi_contractions.json` data
  - Handle conflicts: merge variant lists for same clean word
  - Ensure structure: `dict[str, list[str]]` with only words having 1+ variants

- [x] Verify `SpeechMarkManager` loads initial JSON correctly
  - Test that both sandhi and hyphenation variants are loaded
  - Test that clean words with multiple variants work

- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
  - Test that both sandhi and hyphenation variants are loaded
  - Test that clean words with multiple variants work

- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Text Replacement Function Updates

- [x] Update `tools/sandhi_replacement.py`
  - Rename `replace_sandhi()` to `replace_speech_marks()`
  - Update to accept `SpeechMarkManager` instance
  - Use unified dictionary lookups for both types
  - Keep joining with `//` for multiple variants
  - **Renaming file to `tools/speech_marks_replacement.py` per user instruction**

- [x] Update `gui2/dpd_fields_functions.py`
  - Update `clean_sandhi()` to use `SpeechMarkManager.get_variants()`
  - Update `clean_example()` to use `SpeechMarkManager.get_variants()`
  - Update `clean_commentary()` to use `SpeechMarkManager.get_variants()`

- [x] Write failing tests for updated functions
  - Test `replace_speech_marks()` handles both types
  - Test GUI cleaning functions work with unified manager
  - Run tests and confirm they fail (Red phase)

- [x] Implement updated functions to pass tests (Green phase)
  - Write minimal code to make tests pass
  - Run tests and confirm they pass

- [x] Run ruff on modified files
  - `uv run ruff check tools/sandhi_replacement.py`
  - `uv run ruff check gui2/dpd_fields_functions.py`
  - `uv run ruff format` on both files

- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)

## Phase 5: GUI Component Updates

- [x] Update `gui2/toolkit.py`
  - Replace two manager initializations with `SpeechMarkManager`
  - Remove old manager imports if not needed elsewhere

- [x] Update `gui2/dpd_fields.py`
  - Store reference to `SpeechMarkManager`
  - Update all calls to use unified manager methods

- [x] Update `gui2/dpd_fields_examples.py`
  - Update `_handle_hyphens_and_apostrophes()` to detect both `'` and `-`
  - Extract clean word by removing both characters
  - Call `speech_marks_manager.update_variants(clean_word, variant)`

- [x] Update `gui2/dpd_fields_commentary.py`
  - Same pattern as examples field
  - Update auto-detection and updates

- [x] Update `gui2/pass1_add_view.py`
  - Update to use `SpeechMarkManager`

- [x] Update `gui2/pass2_add_view.py`
  - Update to use `SpeechMarkManager`

- [ ] Task: Conductor - User Manual Verification 'Phase 5' (Protocol in workflow.md)

## Phase 6: Exporter Updates

- [x] Update `exporter/goldendict/export_dpd.py`
  - Load from `SpeechMarkManager.get_speech_marks()`
  - Continue adding sandhi contractions as synonyms
  - Filter variants for `'` to maintain current behavior
  - Test output matches existing exporter

- [x] Update `exporter/deconstructor/deconstructor_exporter.py`
  - Load from `SpeechMarkManager.get_speech_marks()`
  - Continue adding contractions as synonyms
  - Test output matches existing exporter

- [x] Run ruff on modified files
  - `uv run ruff check exporter/goldendict/export_dpd.py`
  - `uv run ruff check exporter/deconstructor/deconstructor_exporter.py`
  - `uv run ruff format` on both files

- [ ] Task: Conductor - User Manual Verification 'Phase 6' (Protocol in workflow.md)

## Phase 7: Test Updates

- [x] Update `db_tests/single/test_hyphenations.py`
  - Rename tests to reflect unified speech marks concept
  - Update to use `SpeechMarkManager`
  - Test both hyphenation and sandhi variant lookups
  - Test that clean words with multiple variants work correctly

- [x] Update `db_tests/db_tests_relationships.py`
  - Rename `sandhi_contraction_errors()` to `speech_mark_errors()`
  - Update to use `SpeechMarkManager`
  - Test for conflicts or issues in variant lists

- [x] Write tests for GUI and exporter changes
  - Verify GUI components use unified manager
  - Verify exporters produce correct output

- [x] Run all tests and ensure they pass
  - `uv run pytest`

- [x] Run ruff on modified test files
  - `uv run ruff check db_tests/single/test_hyphenations.py`
  - `uv run ruff check db_tests/db_tests_relationships.py`
  - `uv run ruff format` on both files

- [ ] Task: Conductor - User Manual Verification 'Phase 7' (Protocol in workflow.md)

## Phase 8: Branch Creation and Final Testing

- [x] Create feature branch `feature/speech-marks-unification`
  - Ensure all changes are on this branch
  - Verify main branch still has old managers working

- [x] Run full test suite on feature branch
  - `uv run pytest`
  - Ensure all existing tests pass
  - Verify new tests pass

- [x] Manual testing of GUI2
  - Test example fields with apostrophes and hyphens
  - Test commentary fields
  - Verify speech marks are detected and saved correctly

- [x] Test exporters with unified system
  - Run GoldenDict export
  - Run Deconstructor export
  - Verify output matches expected

- [x] Task: Conductor - User Manual Verification 'Phase 8' (Protocol in workflow.md)

## Phase 9: Merge and Archive Old System

- [x] Merge feature branch into main
  - Direct merge (no PR)
  - Verify merge completes successfully

- [x] Archive old managers on main branch
  - Move `tools/hyphenations.py` to `archive/tools/`
  - Move `tools/sandhi_contraction.py` to `archive/tools/`
  - Move `tools/hyphenations.json` to `archive/tools/`
  - Move `tools/sandhi_contractions.json` to `archive/tools/`
  - Remove old paths from `tools/paths.py`

- [x] Verify final system works on main branch
  - Run `uv run pytest`
  - Test GUI2 startup and functionality
  - Test exporters

- [x] Commit changes for user
  - List all created/modified files
  - Propose commit message: `refactor(speech-marks): unify hyphenations and sandhi into single speech marks system`

- [x] Task: Conductor - User Manual Verification 'Phase 9' (Protocol in workflow.md)
