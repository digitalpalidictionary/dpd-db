## Thread
- **ID:** 20260601_link_br_fix
- **Objective:** Fix multi-link href rendering a URL-encoded `<br>` in webapp & GoldenDict

## Files Changed
- `exporter/webapp/data_classes.py` — removed `"link"` from `convert_newlines` column list
- `exporter/goldendict/data_classes.py` — removed `"link"` from `_convert_newlines` attr list

## Findings
No findings. The fix is minimal and targeted. Templates render links only via
`link_list` (splits on `\n`); the `\n`→`<br>` mutation was the sole cause, and
removing `link` from the conversion lists restores correct per-link splitting.

## Fixes Applied
- None beyond the planned change.

## Test Evidence
- `uv run ruff check` (both files) → pass
- `uv run pytest tests/exporter/webapp/test_dpd_headword.py` → 3 passed
- `uv run pytest tests/exporter/goldendict/test_dpd_headword.py` → 17 passed, 1 failed
  - Failure `TestVaggaRow::test_sc_sutta_and_title_hidden` is PRE-EXISTING
    (confirmed: fails identically on unmodified code), unrelated to links.
- Webapp: user confirmed two links now render as two clean anchors.
- GoldenDict: not re-exported by user; same code path (`link_list`), expected to work.

## Verdict
PASSED
- Review date: 2026-06-01
- Reviewer: kamma (inline)
