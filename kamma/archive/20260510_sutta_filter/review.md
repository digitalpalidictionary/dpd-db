## Thread
- **ID:** 20260510_sutta_filter
- **Objective:** Add a Sutta filter radio to the pass2_add tab with a reduced
  field set, prefill `-` into source_1/commentary, and keep the filter sticky
  across consecutive word loads.

## Files Changed
- `gui2/dpd_fields_lists.py` — added `SUTTA_FIELDS` list (user-trimmed during
  implementation to a tighter set than the spec proposed).
- `gui2/pass2_add_view.py` — imported `SUTTA_FIELDS`, added Sutta radio,
  added sutta branch in `_handle_filter_change` with prefill, made sutta
  filter sticky in `clear_all_fields`.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `pass2_add_view.py:520-525` and `:603-607` | Prefill loop duplicated in two call sites | DRY | Could extract a `_prefill_sutta_dashes()` helper, but only 4 lines × 2 sites. Per project guidance "Three similar lines is better than a premature abstraction" — leaving as-is. |

No blocking or major findings. Spec coverage complete.

## Fixes Applied
- None. Original implementation matched the (evolved) spec.

## Test Evidence
- `uv run ruff check gui2/dpd_fields_lists.py gui2/pass2_add_view.py` → pass
- User manual smoke on the running gui2 → confirmed

## Verdict
PASSED
- Review date: 2026-05-10
- Reviewer: kamma (inline)
