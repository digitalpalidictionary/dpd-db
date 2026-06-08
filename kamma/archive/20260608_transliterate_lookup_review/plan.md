# Plan: review transliterate_lookup_table.py

Status: **done** — decision recorded, bug fixed, tested.

## Architecture Decisions
- **Leave write path as-is.** No migration to `sync_lookup_column`. This script is update-only,
  multi-column, full-table-load — none of which fit the helper. Documented as the explicit exception.
- **`is_another_value(i, "epd")` semantics:** returns True when the row has real non-EPD data.
  The old code's `not is_another_value(...)` matched **only** EPD-only rows — the inverse of
  the intended "skip English-only" filter. Fix removes the `not`.

## Tasks
- [x] Confirm the intended row-selection logic. User confirmed: always skip EPD-only rows.
- [x] Fix: extract `_should_transliterate()` pure function with corrected precedence
      `(not lookup.sinhala or regenerate_all) and is_another_value(lookup, "epd")`.
      → verify: 7 unit tests pass (`tests/db/lookup/test_should_transliterate.py`)
- [x] Decide migration disposition: (a) leave write path as-is.
- [x] Tidy: removed 4 dead commented lines.
- [x] Gate: ruff check + ruff format + pyright (0 errors) + pytest (517 passed).

## Notes
- Not part of the `update_test_add` DRY target — this script never used it.
- Full-table load is intrinsic (transliterates every key); scoping yields no perf win.
