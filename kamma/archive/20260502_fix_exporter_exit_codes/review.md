## Thread
- **ID:** 20260502_fix_exporter_exit_codes
- **Objective:** Raise an error when a multiprocessing worker fails so the exporter does not continue silently.

## Files Changed
- `exporter/goldendict/export_dpd.py` — check `p.exitcode` after `p.join()`; raise `RuntimeError` on non-zero
- `tests/exporter/goldendict/test_export_dpd.py` — new test confirming crashing worker has non-zero exit code

## Findings
No findings.

## Fixes Applied
None.

## Test Evidence
- `uv run pytest tests/exporter/goldendict/test_export_dpd.py -v` → 1 passed
- `coderabbit review --agent` → 0 findings

## Verdict
PASSED
- Review date: 2026-05-02
- Reviewer: kamma (inline)
