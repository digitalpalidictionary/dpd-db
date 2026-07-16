# Spec — Rearrange pass2add top button row

## Overview
The top button row of the gui2 pass2add tab (`gui2/pass2_add_view.py`) is cluttered. The user wants to (a) move the History dropdown to sit directly after "Clear All", and (b) collapse the two rarely-used action buttons — "Update Speech Marks" and "AiAutofill" — into a single dropdown action menu marked with a down-arrow symbol.

## What it should do
The top control row should render, left to right:

1. Enter ID/Lemma field
2. Clone
3. Split
4. P2A
5. New
6. Eg
7. Cor
8. Add
9. X
10. PRead
11. Clear All
12. **History dropdown** (moved from the end to here, immediately after Clear All)
13. **A dropdown action menu with a down-arrow icon**, containing two items:
    - "Update Speech Marks" → triggers the existing `_click_update_sandhi` logic
    - "AiAutofill" → triggers the existing `_click_update_with_ai` logic

Selecting either menu item must behave exactly as the old standalone buttons did (no change to the underlying handlers).

## Assumptions & uncertainties
- **Menu control choice:** "Update Speech Marks" and "AiAutofill" are *actions* (they trigger functions), not value selections. The semantically correct control is `ft.PopupMenuButton` (click → menu → on_click per item), **not** `ft.Dropdown` (select-a-value → on_change). The "down-arrow symbol" maps to `PopupMenuButton(icon=ft.Icons.ARROW_DROP_DOWN)`.
- The two existing handlers (`_click_update_sandhi`, `_click_update_with_ai`) both ignore their `e` argument, so they can be reused unchanged as `PopupMenuItem.on_click` callbacks.
- The standalone `update_speech_marks_button` and `_update_with_ai_button` member attributes are referenced only at their definition and in the current Row — nothing else in the codebase reads them — so they can be removed and replaced by the menu.

## Constraints
- Touch only `gui2/pass2_add_view.py`. No handler logic changes.
- gui2 is pyright-excluded but NOT ruff-excluded, so the file must pass `ruff check` + `ruff format`.
- Preserve the existing `spacing=10` and `alignment=ft.MainAxisAlignment.START` of the row.

## How we'll know it's done
- gui2 launches without error.
- Top row shows History dropdown right after "Clear All".
- A down-arrow menu button sits at the end of the row.
- Clicking the down arrow reveals "Update Speech Marks" and "AiAutofill".
- "Update Speech Marks" regenerates speech marks (message: "speech marks updated").
- "AiAutofill" loads AI suggestions into the _add fields (as before).

## What's not included
- No changes to other tabs (pass1, filter, etc.).
- No changes to the handlers' behaviour.
- No reordering of the other (queue) buttons — only History moves and two buttons collapse into the menu.
