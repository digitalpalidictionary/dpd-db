# Plan: Pass2Pre exceptions on/off toggle

## Phase 1 — Implement

- [x] Add `self.exceptions_switch` (ft.Switch, label "exceptions", value=True)
      and place it in the button Row after `self.exceptions_field`.
- [x] Gate the exception regex in `_filter_examples()` with
      `self.exceptions_switch.value`.
- [x] Add `handle_exceptions_toggle()` (re-filter, update count, rebuild radio).

## Phase 2 — Quality gate

- [x] `uv run ruff check --fix gui2/pass2_pre_view.py` — passed
- [x] `uv run ruff format gui2/pass2_pre_view.py` — unchanged
- [ ] Hand off to user for GUI manual test.
