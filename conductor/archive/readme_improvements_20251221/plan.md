# Plan: Project-Wide README Improvements

## Phase 1: Foundation & Template [checkpoint: c124848]
- [x] Task: Define README Template
    - [x] Sub-task: Create a markdown template (`conductor/templates/DIR_README_TEMPLATE.md`) with sections: Purpose, Key Components, Relationships, Usage/Commands.
    - [x] Sub-task: Document the template usage guidelines in `conductor/docs/documentation_standards.md`.
- [x] Task: Directory Enumeration Script
    - [x] Sub-task: Create a Python script `conductor/tracks/readme_improvements_20251221/list_dirs.py` to list all directories, respecting `.gitignore`.
    - [x] Sub-task: Test the script to ensure it excludes ignored folders and includes valid ones.
- [x] Task: Compliance Checker Tool
    - [x] Sub-task: Create a Python script `conductor/tracks/readme_improvements_20251221/check_readmes.py` that iterates through the list from `list_dirs.py`.
    - [x] Sub-task: The script should report missing READMEs and READMEs that don't match the required sections (basic heuristic check).
- [x] Task: Conductor - User Manual Verification 'Phase 1: Foundation & Template'

## Phase 2: Root & Critical Directory Documentation
- [x] Task: Document `db/`
    - [x] Sub-task: Create/Update `db/README.md` manually with high-quality "Why" and "Relationships".
    - [x] Sub-task: Fill in "Key Components" (models, definitions, etc.).
- [x] Task: Document `exporter/`
    - [x] Sub-task: Create/Update `exporter/README.md` manually.
    - [x] Sub-task: Focus on the export flow and different formats supported.
- [x] Task: Document `gui/`
    - [x] Sub-task: Create/Update `gui/README.md` manually.
    - [x] Sub-task: Explain the UI architecture (Flet/legacy).
- [x] Task: Document `tools/`
    - [x] Sub-task: Create/Update `tools/README.md` manually.
    - [x] Sub-task: Highlight frequently used scripts.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Root & Critical Directory Documentation'

## Phase 3: Hybrid Generation & Broad Execution
- [x] Task: Hybrid Generation Script
    - [x] Sub-task: Create a script `conductor/tracks/readme_improvements_20251221/generate_readme_draft.py` that uses the template.
    - [x] Sub-task: The script should accept a directory path and attempt to list files for "Key Components" (simple listing initially).
- [x] Task: Batch Generation
    - [x] Sub-task: Run the generation script for all missing READMEs.
- [x] Task: Manual Refinement (Iterative)
    - [x] Review and refine major subfolder READMEs.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Hybrid Generation & Broad Execution'

## Phase 4: Final Review & Standardization
- [x] Task: Global Consistency Check
    - [x] Sub-task: Refine remaining root-level READMEs (shared_data, docs, go_modules, identity).
    - [x] Sub-task: Run `conductor/tracks/readme_improvements_20251221/check_readmes.py` to ensure 100% coverage.
- [x] Task: Cleanup
    - [x] Sub-task: Remove auto-generated "junk" READMEs.
- [x] Task: Conductor - User Manual Verification 'Phase 4: Final Review & Standardization'

## Phase 5: Manual Deep-Dive Documentation
- [x] Task: Document all project subfolders manually with "WHY"-focused content.
    - [x] `db/` subfolders
    - [x] `exporter/` subfolders
    - [x] `gui/` and `gui2/` subfolders
    - [x] `scripts/` subfolders
    - [x] `db_tests/` and `db_tests_gui/` subfolders
    - [x] `identity/` subfolders
    - [x] `shared_data/` subfolders
    - [x] `go_modules/` subfolders
    - [x] `resources/` root
- [x] Task: Conductor - User Manual Verification 'Phase 5: Manual Deep-Dive Documentation'
