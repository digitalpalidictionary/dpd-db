# Review: db_tests triage & refresh

## Thread
- **ID:** 20260711_db_tests_triage
- **Objective:** One-by-one triage of ~39 db_tests scripts (#157): user runs, verdicts, agent implements; survivors freshened, rest parked/archived.

## Files Changed (this session's uncommitted batch; earlier phases in commits 25b7a6fc…cbec6205)
- `db_tests/db_tests_manager.py` — freshen + hot-path short-circuit (~2.1× Tests-tab step), API unchanged
- `db_tests/single/test_gram_in_last_position.py` — behavior-preserving freshen
- `db_tests/single/test_sandhi_errors.py` + `.json` (new) — extracted from parked `sandhi_contraction_errors`; self-regenerating cache; hyphen-insensitive flagging
- `db_tests/db_tests_relationships.py` — parked function + import removed
- `tools/speech_marks.py` — `regenerate_from_db` rebuilds from scratch (ghost fix), gui2-identical tokenizer, Pāḷi-sorted save, empty-key guard
- `tools/speech_marks.json` — regenerated, sorted, ghost-purged (52,062 keys)
- `tools/paths.py` — `sandhi_errors_exceptions_path`
- `gui2/sandhi_find_replace_view.py` — strip toggle, focus-to-replace, Clear fix
- `gui2/dpd_fields_examples.py`, `gui2/dpd_fields_commentary.py` — empty-key guard
- `justfile` — `test-sandhi` recipe; 3 READMEs reality-synced; 30 stale `.pyc` deleted

## Findings
| # | Severity | Location | What | Fix |
|---|----------|----------|------|-----|
| 1 | nit | speech_marks collection ×3 sites | isolated `-` token → `""` ghost key (pre-existing, inert) | `if clean_word:` guard added, key purged |
| 2 | minor | handoff.md | file inventory incomplete; stale "awaiting confirmation" wording | corrected |
| 3 | — | test_gram_in_last_position.py | CodeRabbit claimed semantics change — verified false (rewrite ≡ original incl. its duplicate-append) | rejected with reason |

## Fixes Applied
- All of the above (1–2); finding 3 rejected after verification against the diff.

## Test Evidence
- `uv run ruff check` + `ruff format` + `pyright` on all changed files → clean (gui2 pyright-excluded by config)
- `uv run pytest tests/db_tests/ tests/tools/speech_marks/` → 46 passed
- `uv run pytest tests/` → 1719 passed, 3 pre-existing DB-content-drift failures (test_family_root ×2, test_export_txt ×1 — documented, unrelated)
- `just --list` → `test-sandhi` parses; gui2 modules import cleanly
- Reviewer traced `error_test_each_single_row` short-circuit through all 9 operator branches → semantically equivalent; DbTestManager API cross-checked at every gui2 call site; user confirmed `just db-test`, `test_sandhi_errors.py`, and the gui2 strip toggle live

## Verdict
PASSED
- Review date: 2026-07-13
- Reviewer: independent Sonnet subagent (zero-context) + CodeRabbit CLI, findings verified and applied by Fable 5 session
