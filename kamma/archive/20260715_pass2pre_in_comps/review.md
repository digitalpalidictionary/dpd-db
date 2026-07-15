# Review

## Thread
- **ID:** 20260715_pass2pre_in_comps
- **Objective:** Pass2Pre "in comps" mode — surface compound components
  missing examples, one compound work item at a time.

## Files Changed
- `gui2/database_manager.py` — `make_compound_components_map()` +
  `compound_components_map`/`_components_gen` (corpus-gen-gated, lazy)
- `gui2/pass2_pre_controller.py` — in-comps queueing (`add_comps_entry`),
  per-entry headwords with source tracking, pair-keyed Nos, per-headword
  display, subword highlight, stale-index guard
- `gui2/pass2_pre_view.py` — "in comps" switch, guarded Yes/No handlers,
  per-headword display/highlight wiring
- `tests/gui2/test_database_manager_components.py` — new (6 tests)
- `tests/gui2/test_pass2_pre_components.py` — new (13 tests)

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `pass2_pre_controller.py` `find_words_with_missing_examples` | `comps_components`/`entry_headword_sources` never reset between runs | ON→OFF rerun leaked component headwords (violates "switch off = identical"); book switch kept stale component lists | Reset both at method start + regression test |
| 2 | minor | `pass2_pre_controller.py` `highlight_term_for` | end-shortening fallback applied to regular words too | absent word could highlight spurious fragment in off-mode | Shorten only for subwords + test |
| 3 | minor | within-session Yes on a component doesn't de-list it from later compounds in same run | converges on next PreProcess; consistent with pre-existing build-time gating | accepted as designed |
| 4 | nit | `handle_new_click` saves under compound while subword displayed | per spec ("New works unchanged") | accepted as designed |
| 5 | nit | shared inflection key in components map: last compound wins | any compound's components are valid work | accepted as designed |

## Fixes Applied
- #1: state reset in `find_words_with_missing_examples` +
  `test_rerun_with_switch_off_clears_comps_state`
- #2: early return for regular words in `highlight_term_for` +
  `test_highlight_term_for_regular_word_never_shortened`

## Test Evidence
- `uv run pytest tests/gui2/` → 245 passed
- `uv run pytest tests/` → full suite passed (1574 at wrap-up gate)
- `uv run ruff check` / `ruff format` / `pyright` → clean on all 5 files
- Manual: user ran live AN sessions throughout 2026-07-15 — compound work
  items, `[compound] subword` display, subword highlight, pair-keyed Nos,
  Yes/No/New/Pass all confirmed working
- CodeRabbit: 1 finding — identical to #1 (comps state reset), reviewed
  pre-fix snapshot; already resolved. No new findings.

## Verdict
PASSED
- Review date: 2026-07-15
- Reviewer: independent subagent (fresh context) + CodeRabbit; implementing
  agent applied fixes
