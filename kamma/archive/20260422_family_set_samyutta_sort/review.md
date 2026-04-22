## Thread
- **ID:** 20260422_family_set_samyutta_sort
- **Objective:** Add "saṃyuttas of the Saṃyutta Nikāya" to natsort_exact so it sorts by meaning_1

## Files Changed
- `db/families/family_set.py` — added one entry to `SORT_STRATEGIES["natsort_exact"]`

## Findings
No findings.

## Fixes Applied
None.

## Test Evidence
- `uv run python3 -c "_get_sort_strategy('saṃyuttas of the Saṃyutta Nikāya')"` → "natsort" ✓
- `uv run python3 -c "_get_sort_strategy('previous Buddhas')"` → "natsort" ✓ (no regression)
- User ran `family_set.py` and confirmed correct sort output ✓

## Verdict
PASSED
- Review date: 2026-04-22
- Reviewer: kamma (inline)
