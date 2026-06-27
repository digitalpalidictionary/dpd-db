## Thread
- **ID:** 20260627_pass2pre_exceptions_toggle
- **Objective:** Add an in-memory "exceptions" switch in Pass2Pre to turn exception filtering of example sentences on/off.

## Files Changed
- `gui2/pass2_pre_view.py` — add `exceptions_switch` (ft.Switch), place it in the button Row after the exceptions field, gate the exception regex in `_filter_examples()` on the switch value, add `handle_exceptions_toggle()` to re-filter and refresh list + count.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `gui2/pass2_pre_view.py:524` | blank line after handler docstring | cosmetic; consistent with sibling `add_exception`, `ruff format` leaves it | none needed |

No blocking, major, or minor findings.

## Verification (independent reviewer)
- `exceptions_switch` is defined in `__init__` before any call site of `_filter_examples()` (all call sites are event-driven, post-mount). No early-call risk.
- Refresh is live: `update_examples` and `update_examples_count` each call `self.page.update()`, so list and count repaint on toggle.
- Handler mirrors sibling `handle_search` (empty guard + three-call refresh) and the switch shape matches `pass2_auto_view.py::gd_switch`.
- Gate logic correct: switch off → `compiled_exception_regex` stays `None`, all examples survive; search filter untouched; default `True` preserves prior behaviour; no config write.
- Unused `e` arg matches every sibling handler; ruff default does not flag it.

## Fixes Applied
- None (review clean).

## Test Evidence
- `uv run ruff check --fix gui2/pass2_pre_view.py` → pass
- `uv run ruff format gui2/pass2_pre_view.py` → unchanged
- User manual GUI test → confirmed working (list and count update live on toggle)

## Verdict
PASSED
- Review date: 2026-06-27
- Reviewer: independent subagent (zero-context), orchestrated by implementing session
