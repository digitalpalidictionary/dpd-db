# Spec: Pass2Pre exceptions on/off toggle

## Problem
In Pass2Pre, every example sentence is automatically filtered by the Pass2
exceptions set. There is no way to temporarily see the filtered-out examples
without removing the exceptions.

## Goal
Add a switch labelled "exceptions" that turns exception filtering on and off.
- ON (default) = current behaviour (examples matching exceptions are hidden).
- OFF = no exception filtering; all examples shown (search still applies).

## Scope (minimal)
- State is **in-memory only** — defaults to ON every time the GUI opens. No
  config.ini persistence.
- A single `ft.Switch` placed in the button Row, right after the exceptions
  textbox (which sits after the Pass button).

## Implementation
Three small edits in `gui2/pass2_pre_view.py`:

1. Create `self.exceptions_switch = ft.Switch(label="exceptions", value=True,
   on_change=self.handle_exceptions_toggle)` and add it to the button Row after
   `self.exceptions_field`.

2. In `_filter_examples()`, gate the regex build with the switch value:
   `if self.exceptions_switch.value and candidate_exceptions:`

3. Add `handle_exceptions_toggle()` mirroring the existing `_on_search_change`
   refresh trio: re-filter, update count, rebuild radio group.

## Out of scope
- Persisting toggle state across sessions.
- Any change to the exceptions manager or exceptions file.

## Verification
- GUI launch: switch shows after exceptions textbox, ON by default.
- Toggling OFF reveals examples previously hidden by exceptions; toggling ON
  hides them again.
- Search filtering works in both states.
- `ruff check`, `ruff format`, pass cleanly on the touched file.
