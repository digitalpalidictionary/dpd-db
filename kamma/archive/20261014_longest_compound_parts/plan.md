# Plan: longest_compound_parts

## Architecture Decisions
- One standalone script in `db_tests/single/`, following the interactive pattern of
  `test_family_compounds_have_meaning_1.py`. Pure functions (`parse_line`,
  `build_indexes`, `match_run`, `best_split`) take plain data so they are unit-tested
  without the db.
- Exceptions keyed by `lemma_1`, path added to `tools/paths.py`.

## Phase 1 — script
- [x] Write `db_tests/single/test_longest_compound_parts.py` and the path entry.
  → verify: `uv run pytest tests/db_tests/single/test_test_longest_compound_parts.py` — 7 passed (2026-10-14); ruff and pyright clean.
- [x] Tweaks from user runs (2026-10-14): skip `na` negatives (1,961 hits); open word in GoldenDict;
  arrow-part tie-break (test `test_sound_change_part_absorbed_on_tie`, fails on revert); `just test-compounds`.
  → verify: 8 tests pass; revert of tie-break fails 1.
- [x] User runs `uv run db_tests/single/test_longest_compound_parts.py` and reports wrong suggestions.
  → verify: each reported case gets a fixture copied from the real row and a fix.
- [x] Phase check: tests, ruff, pyright, `just typecheck` all clean.
  → 13 passed, typecheck 0 errors (2026-10-15).
- [x] Review fixes applied (see review.md).
