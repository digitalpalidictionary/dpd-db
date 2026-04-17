## Thread
- **ID:** 20260417_add_spelling_bottleneck
- **Objective:** Fix slow response when using "Add spelling" in the meaning field

## Files Changed
- `gui2/dpd_fields_meaning.py` — skip redundant spell re-check after adding a word to dictionary

## Findings
No findings.

## Fixes Applied
None

## Test Evidence
- `uv run pytest tests/ -x -q` → 272 passed
- User confirmed instant response after "Add spelling"

## Verdict
PASSED
- Review date: 2026-04-17
- Reviewer: kamma (inline)
