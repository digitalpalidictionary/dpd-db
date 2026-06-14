# Plan: remove_brackets() newline regression

## Tasks
- [x] 1. Identify the regressing commit — `ebdaf1f6` (#162); the three `\s`-based passes
      eat newlines.
- [x] 2. Fix `remove_brackets()` in `gui2/dpd_fields_functions.py`:
      - swap consuming `\s` → `[^\S\n]` in all three passes
      - add `[^\S\n]+\n` → `\n` (trim trailing spaces at end of line)
      - add `\n[^\S\n]+` → `\n` (trim leading spaces at start of line)
- [x] 3. Add regression tests to `tests/gui2/test_dpd_fields_functions.py`:
      newlines preserved, trailing-space-before-newline trimmed,
      leading-space-after-newline trimmed.
- [x] 4. Gate: 12/12 tests pass (all 9 original #162 tests still green), ruff clean.

## Checkpoint
- [x] Manual verification by user in the GUI — confirmed working.
