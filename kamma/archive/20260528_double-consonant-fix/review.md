## Thread
- **ID:** 20260528_double-consonant-fix
- **Objective:** Replace `-x-x` (hyphen, consonant, hyphen, same consonant)
  with `-xx` in `example_1`, `example_2`, `commentary` of `dpd_headwords`.

## Files Changed
- `scripts/fix/double_consonant_replacer.py` — new script with two patterns:
  plain `-x-x` → `-xx` and tag-wrapped `-x<b>-x` / `-x</b>-x` →
  `-x<b>x` / `-x</b>x`. Module-level `TAG_ONLY` flag to restrict to
  tag-pattern run.

## Findings
No findings. Plain pattern run committed to db by user. Tag pattern run
returned no matches.

## Fixes Applied
None.

## Test Evidence
- `uv run ruff check scripts/fix/double_consonant_replacer.py` → pass
- User-run dry-run + commit on plain pattern → committed
- User-run dry-run on tag pattern → nothing found

## Verdict
PASSED
- Review date: 2026-05-28
- Reviewer: kamma (inline)
