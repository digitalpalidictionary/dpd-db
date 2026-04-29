## Thread
- **ID:** 20260429_th_thi_chapter_verse_codes
- **Objective:** Add TH1.45 / THI2.3 synthetic lookup codes alongside TH45 / THAG1.45

## Files Changed
- `tools/sutta_codes.py` — 10-line block inside `make_list_of_sutta_codes` adds THAG→TH / THIG→THI synthetic alias

## Findings
No findings.

## Fixes Applied
None.

## Test Evidence
- `make_list_of_sutta_codes(TH45/THAG1.45)` → `['TH1.45', 'TH45', 'THAG1.45']` ✅
- `make_list_of_sutta_codes(THI73/THIG16.1)` → `['THI16.1', 'THI73', 'THIG16.1']` ✅
- SNP control: `['SNP4.7', 'SNP45']` — unchanged ✅
- DN control: `['DN1']` — unchanged ✅

## Verdict
PASSED
- Review date: 2026-04-29
- Reviewer: kamma (inline)
