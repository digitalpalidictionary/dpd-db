## Thread
- **ID:** 20260608_suttas_lookup_sync
- **Objective:** Migrate `suttas_to_lookup.py` to `sync_lookup_column` and retire `update_test_add`

## Files Changed
- `db/suttas/suttas_to_lookup.py` — replaced bespoke loop with `sync_lookup_column(..., clear_stale=False)`; dropped `lookup_db` from `GlobalVars`; added ordering-dependency docstring
- `tools/update_test_add.py` — deleted (no live callers remain)
- `tests/scripts/build/test_deconstructor_output_add_to_db.py` — removed `TestUpdateTestAdd` class and `update_test_add` import
- `tests/db/suttas/test_suttas_write.py` — new: 4 in-memory SQLite behavioural tests for the write path

## Findings
No findings.

## Fixes Applied
None

## Test Evidence
- `uv run pytest tests/db/suttas/ tests/scripts/build/test_deconstructor_output_add_to_db.py -v` → 18 passed
- `uv run pytest tests/ -q` → 510 passed, 4 warnings
- `uv run ruff check --fix` → all checks passed
- `uv run ruff format` → 1 file reformatted (test_suttas_write.py), 2 unchanged
- `uv run pyright` → 0 errors, 0 warnings
- `rg update_test_add --type py` (excl. archive/) → only docstring mention in `tools/lookup_sync.py`; no live imports

## Verdict
PASSED
- Review date: 2026-06-08
- Reviewer: claude-sonnet-4-6
