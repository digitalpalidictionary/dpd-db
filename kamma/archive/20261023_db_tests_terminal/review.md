## Thread
- **ID:** 20261023_db_tests_terminal
- **Objective:** Replace the six db_tests Flet GUI tools with six standalone terminal scripts.

## Files Changed
- `db_tests/single/add_antonyms.py`, `add_antonyms_sync.py`, `add_family_compound_neg.py`, `add_family_compound_su_dur.py`, `add_family_compound_taddhita.py`, `add_hyphenations.py` — the six new scripts.
- `db_tests/single/*.json` (six) — one data file per script. Four seeded once from the TSV exception rows. Two moved from `gui/`.
- `tests/db_tests/single/test_add_antonyms_sync.py`, `test_add_hyphenations.py` — new tests.
- `db_tests/gui/` — deleted.
- `tools/paths.py`, `justfile`, `db_tests/run_all_tests.py`, `db_tests/README.md`, `docs/technical/project_folder_structure.md`, `db_tests/db_tests_manager.py`, `tools/goldendict_tools.py`, `tools/negative_to_positive.py` — references updated.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `add_hyphenations.py` stop check | A finished sweep saved `max_length` 0. | The next run would treat every word as long. | Fixed: stops at 1 without saving 0. |
| 2 | minor | all four `add_*` review scripts, sync | Unknown typed text is committed as the value (CodeRabbit). | A slip such as `Q` writes that letter. | Deferred by the user ("all the tests are like that"). Typed text commits by design. |
| 3 | minor | `add_antonyms.py` and three more, `EXCEPTIONS_PATH` | Path depends on the working folder (DeepSeek). | A wrong folder re-prompts excepted words. | Skipped: project rule runs from the root, and a red message prints when the file is missing. |
| 4 | nit | `add_antonyms_sync.py` meaning lines | Bold magenta breaks "no new colours" (DeepSeek). | Spec deviation. | Accepted: the user asked for it. Recorded in the spec. |

## Fixes Applied
- Finding 1.

## Test Evidence
- `uv run pytest tests/db_tests tests/tools -q` (scope: both folders) → 885 passed, 7 deselected
- `just typecheck` (scope: whole repo) → 0 errors
- `ruff check`, `ruff format`, `pyright` on each of the six scripts and both test files (scope: per file) → clean
- Revert checks (scope: the named tests) → the sync test fails without its fix, the re-flag, auto-approve and bold-tag tests fail without theirs
- `coderabbit review --agent --dir db_tests` (retry) → 1 finding. First attempts failed with "WebSocket closed". The tests folder was not reviewed by CodeRabbit.
- DeepSeek review (`deepseek-v4-pro`, max reasoning, whole diff) → approve with minors. First attempt failed with "Connection error", the retry worked.

## Not Verified
- The key wait in the hyphenations script needs a real terminal. The user used it live.
- `add_antonyms`, `add_family_compound_neg/su_dur/taddhita` print "nothing to do" on current data, so their item screen was never seen. Their logic was checked against the live database counts only.
- The speech marks rebuild on exit was not run by me. The speech marks file shows changes from the user's runs.
- The full test suite was not run, only `tests/db_tests` and `tests/tools`.

## Verdict
PASSED
- Review date: 2026-10-23
- Reviewer: Claude Sonnet 5.5, plus CodeRabbit CLI and DeepSeek (deepseek-v4-pro) as independent passes
