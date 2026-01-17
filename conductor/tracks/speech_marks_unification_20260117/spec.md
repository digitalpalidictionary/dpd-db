# Specification: Speech Marks Unification

## Overview

Create a unified speech marks management system to consolidate two separate systems (`HyphenationFileManager` and `SandhiContractionManager`) into a single `SpeechMarkManager` with a unified `tools/speech_marks.json` file. 

**Key principle:** A single, type-agnostic master list where each clean Pāḷi word maps to ALL its marked variants (whether apostrophe-contractions OR hyphenations).

This unification will:
- Eliminate duplication in codebase
- Provide a shareable master list for GitHub contributions
- Simplify speech mark management across all use cases

**Branch strategy:** All work done on feature branch. No migration tools needed - direct replacement of old system with new system. Old managers remain on main branch until new system is ready, then merge directly to main.

## Functional Requirements

### 1. Unified JSON Structure

Create `tools/speech_marks.json` with following structure:

```json
{
  "akacchoti": ["akaccho'ti"],
  "akatañca": ["akatañ'ca"],
  "sāliyavagodhumamuggakaṅguvarakakudrūsake": ["sāli-yava-godhuma-mugga-kaṅgu-varaka-kudrūsake"],
  "āyasatā": ["āyasa'tā", "āya-satā"]
}
```

**Structure characteristics:**
- Simple key-value: `dict[str, list[str]]`
- Key: Clean Pāḷi word (no apostrophes, no hyphens)
- Value: List of ALL marked variants for that word (any combination of `'` or `-`)
- No type fields, no metadata
- A clean word with 1 or more variants is included in JSON
- A clean word with 0 variants (no speech marks) is NOT included in JSON
- Variants can include mixed types (e.g., both sandhi and hyphenation for same word)

**Example usage pattern:**
- Input: `akatañca` → Check in unified dict
- Found: `["akatañ'ca"]` → Replace with variant
- Input: `sāliyavagodhumamuggakaṅguvarakakudrūsake` → Check in unified dict
- Found: `["sāli-yava-godhuma-mugga-kaṅgu-varaka-kudrūsake"]` → Replace with variant

### 2. SpeechMarkManager Class

Create `tools/speech_marks.py` with following API:

**Type definitions:**
```python
SpeechMarksDict = dict[str, list[str]]
```

**Initialization:**
- `__init__()` - Load unified JSON from `tools/speech_marks_path`
- Store as internal `speech_marks_dict: SpeechMarksDict`
- Use `tools.paths.ProjectPaths` for file paths

**Core Methods:**
- `get_speech_marks() -> SpeechMarksDict` - Return complete unified dictionary
- `get_variants(clean_word: str) -> list[str] | None` - Get variants for a specific clean word
- `has_variants(clean_word: str) -> bool` - Check if word exists in speech marks
- `update_variants(clean_word: str, variant: str)` - Add or append variant to a clean word
- `save()` - Write entire unified dict to `tools/speech_marks.json`

**Sandhi regeneration:**
- `regenerate_from_db()` - Scan DpdHeadword table (example_1, example_2, commentary) and find all apostrophe-marked words
- Extract clean word by removing apostrophes
- Extract all variants (different ways same clean word is contracted)
- Merge into unified dict
- `_should_regenerate() -> bool` - Check if cache is older than 1 day
- `_make_from_db()` - Core DB scanning logic (migrate from existing `SandhiContractionManager._make_sandhi_contractions()`)

**Hyphenation loading:**
- On initialization, if old `tools/hyphenations.json` exists, load and merge into unified dict
- Store as clean_word → [hyphenated_variant] in unified dict

**Persistence:**
- `save()` - Write complete unified structure to `tools/speech_marks.json`
- Use `json.dump()` with `ensure_ascii=False, indent=2` for consistency

### 3. Text Replacement Updates

Update text processing functions to use unified manager:

**Files to update:**
- `tools/sandhi_replacement.py` - Rename and refactor `replace_sandhi()` to `replace_speech_marks()`
  - Accept `SpeechMarkManager` instance
  - Check if clean word exists in unified dict
  - If found, replace with first variant (or join with `//` if multiple, like current sandhi behavior)
- `gui2/dpd_fields_functions.py` - Update all text cleaning functions
  - `clean_sandhi()` → Use `SpeechMarkManager.get_variants()`
  - `clean_example()` → Use `SpeechMarkManager.get_variants()`
  - `clean_commentary()` → Use `SpeechMarkManager.get_variants()`

All functions should accept `SpeechMarkManager` instance and use unified dictionary lookups.

### 4. GUI Component Updates

Update GUI2 components to use `SpeechMarkManager`:

**Files to update:**
- `gui2/toolkit.py` - Initialize `SpeechMarkManager` instead of two separate managers
- `gui2/dpd_fields.py` - Store reference to unified manager
- `gui2/dpd_fields_examples.py` - Update `_handle_hyphens_and_apostrophes()` to call unified manager
  - Detect words with `'` or `-`
  - Extract clean word by removing both characters
  - Call `speech_marks_manager.update_variants(clean_word, variant)`
- `gui2/dpd_fields_commentary.py` - Same pattern as examples
- `gui2/pass1_add_view.py` - Update to use unified manager
- `gui2/pass2_add_view.py` - Update to use unified manager

All components must continue functioning during transition (old managers still available on main branch).

### 5. Exporter Updates

Update exporters to use speech marks from unified manager:

**Files to update:**
- `exporter/goldendict/export_dpd.py` - Load from `SpeechMarkManager.get_speech_marks()` or `SpeechMarkManager.get_variants()`
  - Continue adding sandhi contractions as synonyms for dictionary lookup
  - Filter variants that contain `'` (or check variant string) to maintain current behavior
- `exporter/deconstructor/deconstructor_exporter.py` - Load from `SpeechMarkManager`
  - Continue adding contractions as synonyms
  - Maintain existing synonym generation logic

### 6. Path Definitions

**File:** `tools/paths.py`

Add:
```python
self.speech_marks_path = base_dir / "tools/speech_marks.json"
```

Remove old paths (`sandhi_contractions_path`, `hyphenations_dict_path`) after merge to main.

### 7. Test Updates

**Files to update:**
- `db_tests/single/test_hyphenations.py` - Update to use `SpeechMarkManager`
  - Rename tests to reflect unified speech marks concept
  - Test both hyphenation and sandhi variant lookups
  - Test that clean words with multiple variants work correctly
- `db_tests/db_tests_relationships.py` - Update `sandhi_contraction_errors()` to use unified manager
  - Rename to `speech_mark_errors()` or similar
  - Test for conflicts or issues in variant lists

**New tests needed:**
- Test that clean word lookup returns all variants
- Test that updating variants appends to existing lists correctly
- Test `regenerate_from_db()` produces correct speech marks

All tests must continue passing with new system.

### 8. Branch Strategy

- Create feature branch from `main` (e.g., `feature/speech-marks-unification`)
- All development happens on feature branch
- Old managers remain unchanged on `main` branch
- Once verified and tested, merge directly into main (no PR needed)
- At merge point, archive old managers to `archive/` directory
- Old JSON files (`hyphenations.json`, `sandhi_contractions.json`) moved to `archive/` at merge

### 9. Shareable Master List

The unified `tools/speech_marks.json` will serve as a shareable master list that can be:
- Committed to GitHub repository
- Edited by other editors directly via PR or merge
- Used as single source of truth for ALL speech marks (apostrophes AND hyphens)
- No type differentiation needed - clean word simply maps to all its variants

### 10. Code Quality

- **Ruff:** Run `ruff check` and `ruff format` ONLY on newly created or edited files (never on entire project)
- **Type hints:** Use modern syntax (`dict[str, str]`, `list[str] | None`, `|` for unions)

## Non-Functional Requirements

- **Backward Compatibility:** Old managers (`HyphenationFileManager`, `SandhiContractionManager`) must remain functional on main branch during development and testing on feature branch
- **Performance:** No regression in lookup speed or memory usage
- **Type Safety:** All new code must include proper type hints using modern syntax
- **Code Style:** Follow project conventions
- **Type Agnostic:** System treats `'` and `-` identically - just marks that get stripped to find clean word
- **No Metadata:** JSON contains only speech marks data, no versioning, type fields, or other metadata
- **No Migration Scripts:** Direct replacement of old system with new system on feature branch

## Acceptance Criteria

- [ ] `tools/speech_marks.py` implements `SpeechMarkManager` with all required methods
- [ ] `tools/speech_marks.json` is created with merged data from both existing files
- [ ] Unified dict structure is `dict[str, list[str]]` with clean words as keys
- [ ] A clean word with 0 variants is NOT included in JSON
- [ ] A clean word with 1+ variants IS included in JSON with list
- [ ] All GUI components use `SpeechMarkManager` and function correctly
- [ ] All exporters use `SpeechMarkManager` and produce identical output
- [ ] All existing tests pass with new system
- [ ] Old managers (`tools/hyphenations.py`, `tools/sandhi_contraction.py`) remain functional on main branch during development
- [ ] Old managers and old JSON files moved to `archive/` directory after successful merge into main
- [ ] Feature branch is created and all work done on feature branch
- [ ] Unified `speech_marks.json` is ready for GitHub sharing (no type fields, just clean→variants mapping)
- [ ] Code passes all linting and type checking (ruff run only on new/edited files)

## Out of Scope

- Changing underlying speech mark data values (merging logic only)
- Adding new speech mark discovery features beyond existing DB scan
- Modifying DpdHeadword database schema
- Creating new user interface for editing speech marks (existing GUI workflows sufficient)
- Versioning or tracking metadata for speech marks
- Migration scripts (direct replacement on feature branch)
- Creating PRs (merge directly into main)
- Running ruff on entire project (only on new/edited files)
