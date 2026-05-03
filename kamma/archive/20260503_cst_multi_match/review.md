# Review

## Thread
- **ID:** 20260503_cst_multi_match
- **Objective:** Fix multi-match overwrite in find_sentence_example (closes #232)

## Files Changed
- `tools/cst_source_sutta_example.py` — fixed overwrite bug in sentence example collection

## Findings
No findings.

## Fixes Applied
None (no review issues found).

## Test Evidence
- User confirmed: `an1` / `āvilattā` now returns both the `udakassa` and `cittassāti` sentences.

## Verdict
PASSED
- Review date: 2026-05-03
- Reviewer: kamma (inline)
