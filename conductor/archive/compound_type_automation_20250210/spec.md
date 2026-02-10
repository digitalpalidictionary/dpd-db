# Compound Type Automation

## Overview

Create a CompoundTypeManager in `tools/` that encapsulates the compound type detection logic currently in `db_tests/single/add_compound_type.py`. The manager will:
- Load and parse the TSV file from `tools/compound_type_manager.tsv`
- Provide detection logic used by both the database test and the GUI
- Include a method to open the TSV for manual editing

## Functional Requirements

1. **Manager Location**: `tools/compound_type_manager.py`
2. **TSV Location**: `tools/compound_type_manager.tsv` (moved from `db_tests/single/add_compound_type.tsv`)
3. **Detection Trigger**: When `construction` field loses focus AND:
   - `meaning_1` is not empty
   - `pos` is not in ["sandhi", "idiom", "aor"]
   - `grammar` contains ", comp"
4. **GUI Integration**: Add `on_blur=self.construction_blur` to construction field in `gui2/dpd_fields.py`
5. **Auto-fill**: Detect and auto-fill `compound_type` dropdown if a match is found
6. **Edit Button**: Add button in GUI to open TSV in default editor

## Non-Functional Requirements

- Simple, not over-engineered
- Existing test file imports from manager
- Type hints on all code
- Pass ruff linting/formatting

## Acceptance Criteria

- [ ] Manager loads TSV and provides detection method
- [ ] GUI auto-fills compound_type when construction loses focus
- [ ] Database test refactored to use manager
- [ ] Button opens TSV for editing
- [ ] All code has type hints
- [ ] Passes ruff check --fix and ruff format

## Out of Scope

- Programmatic TSV updates (manual editing only)
- Complex caching mechanisms
- GUI tests for the auto-fill feature
- Public documentation (GUI is internal)
