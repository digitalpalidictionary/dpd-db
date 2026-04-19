# Plan: family_set tab-away loop

## Phase 1 — Fix focus trap
- [x] Remove `textfield_control.focus()` at `gui2/dpd_fields_family_set.py:110` inside the `if unknown_parts:` branch of `_handle_blur`. Keep the `error_text` assignment.
  → verify: launch gui2, enter `xxxx` into family_set, press Tab — focus leaves, red error remains. (user-confirmed)
