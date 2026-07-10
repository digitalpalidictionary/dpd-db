# Review — gui2 Performance, Resource Use & Testability

## Thread
- **ID:** 20260710_gui2_perf_and_testing
- **Objective:** Measure-first refactor of gui2 speed, resource use, and testability (#157), phases 1–8.

## Files Changed
- `db/db_helpers.py` — cached Engine per db path (NullPool, lock, fork-PID guard)
- `gui2/database_manager.py` — single cached corpus + staleness, coalesced detector rebuild worker
- `gui2/filter_component.py` + new `gui2/filter_logic.py` — DB tab: paging, read-only cells with edit-on-demand, id-keyed batch save, off-thread apply
- `gui2/main.py` — lazy tab views via builder registry; db init off-thread; server start after first paint
- `gui2/toolkit.py` — 7 heavy managers/popups converted to `cached_property`
- `gui2/paths.py` — `Gui2Paths` injectable via `base_dir`
- `gui2/dpd_fields.py` — validations skip while corpus sets are still None
- `gui2/pass1_auto_controller.py`, `gui2/pass2_auto_control.py` — temp writes via `ProjectPaths`; dropped redundant re-read after `update()`
- `gui2/filter_tab_view.py`, `gui2/tests_tab_controller.py` — duplicate `new_db_session()` removed; tests tab uses `load_corpus()`
- `gui2/global_tab_view.py`, `gui2/pass1_add_view.py`, `gui2/sandhi_find_replace_view.py` — `mark_corpus_stale()` at write paths
- `tools/fast_api_utils.py` — dropped uvicorn `--reload`; `tools/spelling.py` — fast `has_misspellings()`
- 14 new test files (~330 tests), benchmark harness + before/after JSON results in the thread dir

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `gui2/filter_component.py:271` | Stale apply worker wrote `filtered_results`/paging state before the generation check; generation increment not atomic across Flet handler threads | Rapid re-applies could transiently render a superseded page | FIXED: results computed into locals; state+render inside `_apply_lock` after generation check |
| 2 | nit | `gui2/filter_component.py` | Pager stays disabled after a filter-validation error | Coherent (paging would re-run the invalid filter) | skipped |
| 3 | nit | `gui2/main.py:_ensure_tab_built` | Tab marked mounted before build; constructor error leaves a blank tab until restart | Strictly better than old eager crash-at-startup | skipped |
| 4 | nit | `gui2/filter_component.py` | Pending cell edits survive paging but display DB values when paging back | Deliberate id-keyed design; edits never lost | skipped |
| 5 | nit | thread `benchmarks/` | Empty untracked byproduct dirs (`exporter/`, `temp/`…) from bench runs | Untracked, harmless | left for cleanup |

CodeRabbit (4 minor, docs/bench only): spec.md stale `Status: planned` → FIXED (`implemented`); plan.md 7.2 "all 15 tabs lazy" contradiction → FIXED ("14 non-Global"); hardcoded bench baseline 347.19 → skipped (one-shot artifact, baseline documented in `results/3.2_startup.json`); `.gitignore` `*_sandbox` → skipped (bench scripts rmtree their sandboxes).

Verified independently: no db test targets a deferred corpus column; `has_misspellings` tokenizes identically to `check_sentence` (cell color and save gate agree); every headword write path calls `mark_corpus_stale()`; `Pass1FileManager.update()` returns the dict it writes; tab label order matches builder indices; no stale references to removed symbols (`_validate_data`, `_just_saved`, `tab_clicked`, …).

## Fixes Applied
- `gui2/filter_component.py` — apply-generation lock + late state assignment (finding 1)
- `spec.md` status, `plan.md` 7.2 wording (CodeRabbit)

## Test Evidence
- `uv run pytest tests/` → 1471 passed, 16 deselected (before AND after review fixes)
- `uv run ruff check` + `ruff format --check` on all 17 touched files → clean
- `uv run pyright` (db_helpers, fast_api_utils, spelling, filter_component) → 0 errors
- `coderabbit review --agent --type committed --base 08b38e5e` → 4 minor (2 fixed, 2 skipped with reasons)

## Verdict
PASSED
- Review date: 2026-07-10
- Reviewer: Claude (Fable 5), fresh session, independent of implementing sessions
