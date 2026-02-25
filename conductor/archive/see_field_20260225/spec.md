# Spec: "See" Lookup Field

## Overview

Add a new "see" field to the DPD lookup system for words that are neither spelling mistakes nor variant readings, but unusual forms found in occasional books that don't warrant a full `dpd_headwords` entry. When looked up, these words display "see **_headword_**", pointing the user to the correct main entry.

The feature follows the same end-to-end pattern as spelling mistakes: TSV data file -> manager class -> GUI capture -> database population -> webapp/GoldenDict export.

## Functional Requirements

### FR1: Data Storage
- New TSV file at `shared_data/deconstructor/see.tsv`
- Two columns with headers: `see` | `headword`
- One-to-one mapping: one unusual form maps to one headword

### FR2: Manager Tool
- New file `tools/see_manager.py` with a `SeeManager` class
- Follows the pattern of `tools/variants_manager.py`
- Provides `load()`, `update_and_save()`, `get_see_dict()` methods
- Uses `read_tsv_2col_to_dict()` / `write_tsv_2col_from_dict()` from `tools/tsv_read_write.py`

### FR3: GUI Integration
- Add a new "see" section row in `gui2/sandhi_view.py` (Section 6)
- Two text fields: "Word" and "Headword", plus an "Add" button
- Follows the identical pattern of the existing spelling/variant rows
- Add `add_see()` method to `gui2/sandhi_files_manager.py`
- Register `SeeManager` in `gui2/toolkit.py`

### FR4: Database Model
- Add `see` column to the `Lookup` table in `db/models.py`
- Add `see_pack(list)` and `see_unpack` property following the `spelling_pack`/`spelling_unpack` pattern
- Stores JSON-encoded list of headword references

### FR5: Database Migration
- Add a lightweight migration that adds the `see` column to the existing `lookup` table via `ALTER TABLE lookup ADD COLUMN see TEXT DEFAULT ''`
- This avoids requiring a full database rebuild
- The migration must be idempotent (safe to run multiple times)

### FR6: Lookup Table Population
- New file `db/lookup/see.py` following the pattern of `db/lookup/spelling_mistakes.py`
- Three-tier operation: UPDATE existing keys, TEST/clean stale keys, ADD new keys
- Integrate into the lookup table build pipeline

### FR7: Webapp Export
- New `SeeData` class in `exporter/webapp/data_classes.py`
- New Jinja templates for summary and detail views
- Display text: see ***headword*** (headword in bold italic)
- Integrate into `exporter/webapp/toolkit.py` alongside spelling/variant checks

### FR8: GoldenDict Export
- New `SeeData` class in `exporter/goldendict/data_classes.py`
- New Jinja template `dpd_see.jinja`
- Display text: see ***headword*** (headword in bold italic)
- Integrate into `exporter/goldendict/export_variant_spelling.py`

### FR9: Path Registration
- Add `see_path` to `tools/paths.py` pointing to `shared_data/deconstructor/see.tsv`
- Add template paths for webapp and GoldenDict see templates

## Non-Functional Requirements
- All new code must pass `ruff check --fix` and `ruff format`
- Follow existing naming conventions and code patterns precisely

## Acceptance Criteria
- [ ] A "see" entry added via the GUI appears in `see.tsv`
- [ ] Running the migration adds the `see` column to an existing database without data loss
- [ ] After database rebuild, the entry appears in the `Lookup.see` column
- [ ] The webapp displays "see ***headword***" for see entries
- [ ] GoldenDict export includes see entries with correct display text
- [ ] Existing spelling/variant functionality is unchanged

## Out of Scope
- Reverse lookups (finding all "see" entries for a given headword)
- Bulk import/migration of existing data into "see"
- Any changes to the `dpd_headwords` table
