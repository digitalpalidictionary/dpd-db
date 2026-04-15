## Thread
- **ID:** 20260415_db_tab_horizontal_scroll
- **Objective:** Enable horizontal scrolling and fix column widths in the DB tab DataTable

## Files Changed
- `gui2/filter_component.py` — removed fixed container width, replaced proportional column formula with per-column content sizing, raised minimum width to 120px

## Findings
No findings.

## Fixes Applied
- Raised minimum column width from 50px to 120px after user reported short columns ("origin", "pattern") were still being squeezed.

## Test Evidence
- User confirmed visually: "now its working. ok done. i'm happy"

## Verdict
PASSED
- Review date: 2026-04-15
- Reviewer: kamma (inline)
