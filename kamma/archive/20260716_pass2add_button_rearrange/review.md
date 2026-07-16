## Thread
- **ID:** 20260716_pass2add_button_rearrange
- **Objective:** Rearrange the gui2 pass2add top button row — move History dropdown after Clear All and collapse Update Speech Marks + AiAutofill into a down-arrow action menu.

## Files Changed
- `gui2/pass2_add_view.py` — replaced the two standalone action buttons with one `PopupMenuButton(icon=ft.Icons.ARROW_DROP_DOWN)` and reordered the top Row (History now after Clear All, menu last).

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `gui2/pass2_add_view.py:170` | Added `tooltip="Actions"` beyond literal spec (spec only asked for the down-arrow icon). | Minor scope creep; harmless and arguably better UX for a now-hidden button. | None required — kept for discoverability. |
| 2 | nit | plan/file | No automated test added for the new menu. | Project testing rules say "mimic source structure". | Not applicable — pure GUI control arrangement, no new logic; gui2 layout isn't unit-tested elsewhere. Grep + ruff + pyright gate is appropriate. |

No blocking/major/minor issues.

## Fixes Applied
None — both findings are nits requiring no action.

## Test Evidence
- `uv run ruff check gui2/pass2_add_view.py` → All checks passed
- `uv run ruff format gui2/pass2_add_view.py` → 1 file left unchanged
- `uv run pyright gui2/pass2_add_view.py` → 0 errors, 0 warnings, 0 informations
- `rg -n "update_speech_marks_button|_update_with_ai_button" gui2/` → no matches (no dangling refs)
- `uv run pytest tests/` → 1582 passed, 17 deselected (0 failed)
- Manual (user): gui2 pass2add tab — History after Clear All, down-arrow menu at end, both items fire correctly. Confirmed working.

## Verdict
PASSED
- Review date: 2026-07-16
- Reviewer: kamma (inline) + independent "reviewer" subagent (zero-context)
