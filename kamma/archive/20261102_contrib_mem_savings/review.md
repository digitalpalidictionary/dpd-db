# Review: 20261102_contrib_mem_savings

**Date:** 2026-11-02
**Verdict:** PASSED (after the fixes below)
**Reviewers:** CodeRabbit (`--agent --fresh --committed --base-commit 247a8429~1`), pi with DeepSeek `deepseek-v4-pro` at thinking `max`. Written after the fact by the agent that ran them; no `/kamma:3-review` session was run.

## Files Changed

- `gui2/database_manager.py`
- `tests/gui2/test_database_manager_corpus.py`
- `tools/hashed_words.py` (new)
- `tests/tools/test_hashed_words.py` (new)
- `kamma/threads/20261102_contrib_mem_savings/` (spec, plan, handoff, artifacts, server results)

## Findings

- CodeRabbit: 0 findings on 17 files.
- DeepSeek 1, major: the contributor inflection build queried the shared session without `_corpus_lock`. REAL. FIXED.
- DeepSeek 2, minor: a "refresh DB" during the build was overwritten by `_inflections_ready = True`. REAL. FIXED with `_stale_epoch`.
- DeepSeek 3, minor: NULL `meaning_1` rows dropped from the slim corpus. NOT REAL: the live db has 0 NULLs of 89,774 and the column is `Mapped[str]`.
- DeepSeek 4, minor: the `_load_contributor_corpus` docstring was wrong about the DB tab. REAL. FIXED.
- DeepSeek 5, minor: `_detector_rebuild_worker` full-loads the corpus. Real code, unreachable for contributors (they save to JSON, the DB tab is read-only). NOT TOUCHED.
- DeepSeek 6, nit: tests did not cover the api column. REAL. FIXED with a new test.

## Fixes Applied

- The contributor inflection build holds `_corpus_lock`.
- `mark_corpus_stale` bumps `_stale_epoch`; a build that saw a refresh does not mark its sets fresh.
- The docstring names the Tests tab as the other corpus reader.
- Three new tests: lock, stale during the build, api column.

## Test Evidence

- `uv run pytest tests/gui2 tests/tools/test_hashed_words.py`: 626 passed.
- Mutation check: lock removed, 1 fails. Epoch check removed, 1 fails. Api column dropped, 2 fail. A freq_data value test stayed green when the column was not loaded, so it was removed.
- `ruff check`, `ruff format`, `pyright --project /dev/null` clean on both touched files. `just typecheck`: 0 errors.
- Whole run `pytest tests/gui2 tests/tools`: 1,433 passed, 2 failed before the fixes. `test_configger.py::...[uposatha_reset]` fails on its own (code from commit 7a0d638b). `test_tipitaka_db_deadline.py` failed at load average 15 and passed alone.
- Server: warm 1,165.9 to 943.3 MB, one book 1,485.0 to 1,045.7 MB (`artifacts/results.md`). The review fixes change locking only, so they were not re-measured.
