## Thread
- **ID:** 20260423_contributor_flow
- **Objective:** Fix contributor additions/corrections flow so primary user processes contributor files non-destructively into _added.json

## Files Changed
- `gui2/additions_manager.py` — non-destructive multi-file load, origin + source_key tracking, key-based file deletion on process
- `gui2/corrections_manager.py` — same pattern as additions manager
- `gui2/pass2_add_view.py` — unpack 4-tuple from get_next_addition, store _current_addition_key, thread through to save_processed_addition
- `gui2/data/additions.json` — deleted (dead file; primary never uses queue)
- `gui2/data/corrections.json` — deleted (dead file)

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `pass2_add_view.py:738` | Stale comment referencing corrections.json | Source is now contributor file | Not fixed — comment only, out of scope |
| 2 | nit | both managers | `_remove_key_from_file` + `_contributor_from_origin` duplicated | Minor DRY violation | Not fixed — shared module not worth it for 2 helpers |

## Fixes Applied
- Bug during testing: `get_next_addition` returned 3-tuple; additions id in `word_data` didn't match file key because DB assigns a new id on commit. Fixed by returning `source_key` as 4th element and using it instead of `word_data["id"]` in `_remove_key_from_file`.

## Test Evidence
- `uv run python /tmp/test_managers.py` → 7/7 PASSED (including explicit key-mismatch scenario)
- `uv run pytest tests/ -q -k "addition or correction or gui2 or manager"` → 95 passed
- `python3 -c "import ast; ast.parse(...)"` → OK for all 3 changed .py files
- Manual: corrections_deva.json shrinks on process, _contributor field appears in _added.json ✓

## Verdict
PASSED
- Review date: 2026-04-23
- Reviewer: kamma (inline)
