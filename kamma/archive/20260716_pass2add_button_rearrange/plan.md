# Plan — Rearrange pass2add top button row

## Architecture Decisions
- **Control type:** Use `ft.PopupMenuButton` (action menu) with `icon=ft.Icons.ARROW_DROP_DOWN`, not `ft.Dropdown`. The two items are *actions* (trigger handlers), not value selections; a Dropdown's `on_change` + string matching would be the wrong abstraction.
- **Reuse handlers:** `_click_update_sandhi` and `_click_update_with_ai` are reused as-is — both ignore their `e` arg, so they bind cleanly to `PopupMenuItem.on_click`.
- **Remove standalone button members:** `update_speech_marks_button` and `_update_with_ai_button` are deleted; their text now lives inside the menu. Nothing else references these attributes.
- **Row order:** History dropdown moves up to sit immediately after "Clear All"; the new menu button is appended last.

## Phases

### Phase 1 — Rebuild the top button row

- [x] Replace the two standalone action-button member definitions (`update_speech_marks_button`, `_update_with_ai_button`) with a single `_action_menu_button` member: a `ft.PopupMenuButton(icon=ft.Icons.ARROW_DROP_DOWN, items=[PopupMenuItem("Update Speech Marks", on_click=self._click_update_sandhi), PopupMenuItem("AiAutofill", on_click=self._click_update_with_ai)])`.
  → verify: file imports/defines cleanly; `uv run ruff check` passes. ✅
- [x] In the top-row `ft.Row` `controls` list, remove the two old buttons, move `self._history_dropdown` to immediately after `self._clear_all_button`, and append `self._action_menu_button` at the end.
  → verify: `uv run ruff check gui2/pass2_add_view.py` + `uv run ruff format gui2/pass2_add_view.py` clean. ✅

### Phase 2 — Verify

- [x] Confirm no dangling references to the removed button attributes (`rg "update_speech_marks_button|_update_with_ai_button" gui2/`).
  → verify: grep returns no matches. ✅
- [x] Smoke-gate: `uv run pyright gui2/pass2_add_view.py` (gui2 is pyright-excluded project-wide, but run anyway to catch gross errors) and `uv run ruff check gui2/pass2_add_view.py`.
  → verify: clean (or only pre-existing, unchanged gui2-style notes). ✅ ruff 0 issues, pyright 0/0/0, syntax OK.
