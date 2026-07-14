# Review

## Thread
- **ID:** 20260713_missing_meanings_dialog
- **Objective:** After every save in gui2 pass2add, surface missing dictionary words from
  examples/commentary in a dialog and feed them into a persistent "eg" queue processed via a
  new Eg button.

## Files Changed
- `gui2/pass2_add_view.py` — scan on save, missing-words dialog, Eg button + two-mode loading
- `gui2/pass2_eg_manager.py` — new queue manager (`pass2_eg_words.json`, atomic saves)
- `gui2/paths.py` — `pass2_eg_words_path`
- `config.ini` (gitignored) — `[gui2] missing_words_dialog = yes` toggle

## Findings
No blocking/major findings. Adversarial audit performed inline in the implementing session
(planned Sonnet subagent reviewer stalled ×3 on infrastructure; CodeRabbit run skipped per
user). Verified: no None crash in `unbold()` (`get_current_values` coerces to str), dialog
lifecycle matches the file's `delete_alert` pattern, no ORM mutation side effects, Eg-button
load order mirrors `_click_x_button`.

Accepted minor observations (not fixed, by design/deferral):
1. A just-saved new word's own inflected forms can appear as "missing" until the lookup table
   is rebuilt.
2. Words < 4 chars sort to the end of their section in appearance ordering (stem matching
   floor).
3. One small lookup query per unique word at save time — fine for SQLite at GUI scale.

## Fixes Applied
- None during review; several user-driven refinements were applied and spec-synced during
  implementation (unticked defaults, sentence grouping, appearance order, selectable text,
  no ignore list, commentary→example_1, bold-tag stripping, config gate, button placement).

## Test Evidence
- `uv run ruff check` / `ruff format` / `pyright` → clean on all three Python files
- Pass2EgManager scratchpad smoke (add/pop/persist across reload) → pass
- `uv run pytest tests/` → 1719 passed; 3 pre-existing failures unrelated to gui2 (stale
  golden data: tests/db/families/test_family_root.py, tests/exporter/txt/test_export_txt.py)
- Manual golden path exercised live by the user through several iterations → "ok i'm happy"

## Verdict
PASSED
- Review date: 2026-07-14
- Reviewer: Claude (implementing session; independence reduced — subagent reviewers failed on
  infrastructure, findings re-derived inline)
