## Thread
- **ID:** 20260419_family_set_tab_loop
- **Objective:** Stop family_set field from trapping focus when entry is unknown.

## Files Changed
- `gui2/dpd_fields_family_set.py` — removed self-refocus in `_handle_blur` unknown-entry branch.

## Findings
No findings. Single-line deletion, error-text behavior preserved, unknown-entries branch still sets `error_text`, known-entries and empty-value branches untouched.

## Fixes Applied
- None.

## Test Evidence
- User-confirmed: typing bogus value + Tab → focus leaves, red error persists.

## Verdict
PASSED
- Review date: 2026-04-19
- Reviewer: kamma (inline)
