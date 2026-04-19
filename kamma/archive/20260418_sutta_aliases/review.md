## Thread
- **ID:** 20260418_sutta_aliases
- **Objective:** Allow multiple sutta names (SC variants) to resolve to the same `SuttaInfo` row via `dpd_sutta_var`.

## Files Changed
- `db/models.py` — replaced `su` relationship with alias-aware `cached_property`; fixed `sutta_info_count`; added `_load_sutta_alias_map()`
- `tools/cache_load.py` — `load_sutta_info_set()` now includes `;`-split variants from `dpd_sutta_var`
- `tools/sutta_name_cleaning.py` — new: `clean_sc_sutta` and `clean_bjt_sutta` cleaning functions
- `tests/tools/test_sutta_name_cleaning.py` — new: 28 unit tests for cleaning functions
- `scripts/suttas/find_sutta_alias_candidates.py` — new: candidate-finder manual tool writing two TSV outputs

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `find_sutta_alias_candidates.py:3,65` | Stale BJT references in docstring and duplicate note | BJT source was dropped | Fixed — updated docstring and note text |

No other findings. `.su` spot-checked manually in `scripts/session.py` and confirmed working. Two caches (`_load_sutta_alias_map`, `load_sutta_info_set`) are consistent: both read `dpd_sutta_var` from the same table; `needs_sutta_info_button` and `su` cannot diverge in normal use.

## Fixes Applied
- Updated docstring: "sc_sutta and bjt_sutta fields" → "sc_sutta field"
- Updated duplicate note: "sc and bjt cleaned to same value" → "duplicate sc cleaned value"

## Test Evidence
- `uv run pytest tests/tools/test_sutta_name_cleaning.py -v` → 28 passed
- `uv run pytest tests/` → 300 passed, 3 pre-existing warnings
- REPL: `upasenaāsīvisasutta` → `su.dpd_sutta == "upasenāasīvisasutta"`, `needs_sutta_info_button == True`, variant in `load_sutta_info_set()` ✓
- User confirmed `.su` working in `scripts/session.py`
- CodeRabbit: service unavailable (connection error)

## Verdict
PASSED
- Review date: 2026-04-19
- Reviewer: claude-sonnet-4-6 (same agent as implementation — less independent)
