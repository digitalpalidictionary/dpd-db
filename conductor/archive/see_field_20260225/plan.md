# Plan: "See" Lookup Field

> **Note:** User handles all git commits manually. Agent runs all phases end-to-end without pausing for manual verification checkpoints or commit prompts.

## Phase 1: Data Layer & Manager

- [x] Task: Create `shared_data/deconstructor/see.tsv` with headers `see` and `headword`
- [x] Task: Add `see_path` to `tools/paths.py` following the `spelling_mistakes_path` / `variant_readings_path` pattern
- [x] Task: Create `tools/see_manager.py` with `SeeManager` class (load, update_and_save, get_see_dict) following `tools/variants_manager.py` pattern
- [x] Task: Write tests for `SeeManager` (load empty TSV, add entry, update entry, get dict)
- [x] Task: Conductor - User Manual Verification 'Phase 1: Data Layer & Manager' (Protocol in workflow.md)

## Phase 2: Database Model & Migration

- [x] Task: Add `see` column to `Lookup` class in `db/models.py` with `see_pack()` and `see_unpack` following the `spelling_pack`/`spelling_unpack` pattern
- [x] Task: Create migration function in `db/lookup/see.py` that runs `ALTER TABLE lookup ADD COLUMN see TEXT DEFAULT ''` (idempotent — checks if column exists first)
- [x] Task: Write tests for `see_pack` / `see_unpack` and migration idempotency
- [x] Task: Conductor - User Manual Verification 'Phase 2: Database Model & Migration' (Protocol in workflow.md)

## Phase 3: Lookup Table Population

- [x] Task: Create `db/lookup/see.py` population functions (`load_see_dict`, `add_see`) following `db/lookup/spelling_mistakes.py` pattern (three-tier: update/test/add)
- [x] Task: Integrate `see` population into the lookup build pipeline
- [x] Task: Write tests for see population (update existing, add new, clean stale)
- [x] Task: Conductor - User Manual Verification 'Phase 3: Lookup Table Population' (Protocol in workflow.md)

## Phase 4: GUI Integration

- [x] Task: Register `SeeManager` in `gui2/toolkit.py` following `spelling_mistakes` / `variants` pattern
- [x] Task: Add `add_see()` method to `gui2/sandhi_files_manager.py` following `add_spelling_mistake()` pattern
- [x] Task: Add "see" section (Section 6) to `gui2/sandhi_view.py` with two text fields ("Word", "Headword") and "Add" button following the spelling/variant row pattern
- [x] Task: Conductor - User Manual Verification 'Phase 4: GUI Integration' (Protocol in workflow.md)

## Phase 5: Webapp Export

- [x] Task: Add `SeeData` class to `exporter/webapp/data_classes.py` following `SpellingData` pattern
- [x] Task: Create webapp templates `see_summary.html` and `see.html` in `exporter/webapp/templates/` with display text "see ***headword***"
- [x] Task: Add template path constants (`template_see_summary`, `template_see`) to `tools/paths.py`
- [x] Task: Integrate see rendering into `exporter/webapp/toolkit.py` alongside spelling/variant checks
- [x] Task: Write tests for `SeeData` and template rendering
- [x] Task: Conductor - User Manual Verification 'Phase 5: Webapp Export' (Protocol in workflow.md)

## Phase 6: GoldenDict Export

- [x] Task: Add `SeeData` class to `exporter/goldendict/data_classes.py` following `SpellingData` pattern
- [x] Task: Create GoldenDict template `dpd_see.jinja` in `exporter/goldendict/templates/` with display text "see ***headword***"
- [x] Task: Add `generate_see_data_list()` function and integrate into `exporter/goldendict/export_variant_spelling.py`
- [x] Task: Add template path to `tools/paths.py`
- [x] Task: Write tests for GoldenDict see data generation
- [x] Task: Conductor - User Manual Verification 'Phase 6: GoldenDict Export' (Protocol in workflow.md)

## Phase 7: Documentation & Cleanup

- [x] Task: Update `docs/technical/dpd_headwords_table.md` with new `see` field documentation in the Lookup table section
- [x] Task: Run `uv run ruff check --fix` and `uv run ruff format` on all changed files
- [x] Task: Conductor - User Manual Verification 'Phase 7: Documentation & Cleanup' (Protocol in workflow.md)
