## Thread
- **ID:** 20260607_search_result_cap
- **Objective:** Cap gui2 sutta/commentary search results to prevent UI freeze on broad terms like "sam".

## Files Changed
- `tools/bold_definitions_search.py` — added opt-in `limit: int | None = None` to `search()`; refactored 4 branches to build one query then apply optional `.limit()`.
- `gui2/dpd_fields_commentary.py` — `MAX_SEARCH_RESULTS = 100`; fetch `limit+1`, detect truncation, trim, show refine-search notice.
- `gui2/dpd_fields_examples.py` — `MAX_SEARCH_RESULTS = 100`; replaced `[:50]` literal, added refine-search notice when truncated.

## Findings
No blocking/major findings.
- nit: `commentary_truncated` is read via `getattr(..., False)` rather than initialized in `__init__`; safe (only set on the search path) and intentional, so the notice never shows for pre-filled commentary.

## Fixes Applied
- None (no blocking/major issues found).

## Test Evidence
- `uv run ruff check` (3 files) → pass
- `uv run ruff format --check` (3 files) → pass
- `uv run pyright` (3 files) → 0 errors
- `uv run pytest tests/db/bold_definitions/` → 7 passed
- Manual: user confirmed commentary "sam" search opens instantly with capped results + notice, no freeze.

## Verdict
PASSED
- Review date: 2026-06-07
- Reviewer: kamma (inline)
