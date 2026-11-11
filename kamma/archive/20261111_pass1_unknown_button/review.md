## Thread
- **ID:** 20261111_pass1_unknown_button
- **Objective:** Pass1 Auto gets an "Unknown" button that runs only the completely unknown words of a book and stops; the rest runs later with Whole Book.

## Files Changed
- `gui2/pass1_auto_controller.py` — `unknown_only` argument on the book run, `unknown_only_run` flag, `progress_text()` counter that leaves out saved words in an Unknown run, flag reset in the text run.
- `gui2/pass1_auto_view.py` — Unknown button, `handle_unknown_click`, new row order (Book, AI Model, reload, Unknown, Whole Book, Process Text, ...), dropdown width 220, new labels and dialog title.
- `tests/gui2/test_pass1_auto_controller.py` — four new tests and a shared setup helper.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `tests/gui2/test_pass1_auto_controller.py:380` | Counter test calls `progress_text()` directly, not through the real save path. | A revert of the call site alone would stay green. | Deferred. |
| 2 | nit | `tests/gui2/test_pass1_auto_controller.py` | No Unknown-mode test for Stop or an error exit. | Confirmed by reading only. | Deferred. |
| 3 | nit | `gui2/pass1_auto_controller.py:180` | With no unknown words, the run still loads the prompt context before the early return (CodeRabbit). | Wasted work in a rare case. Moving it needs the status message in two places. | Deferred. |
| 4 | nit | `gui2/pass1_auto_controller.py:186` | Status text says "not in lookup"; epd-only words are also counted (CodeRabbit). | Text is pre-existing and fixed by spec item 6. | Skipped. |
| 5 | nit | `gui2/pass1_auto_view.py:131` | CodeRabbit proposed the labels "Unknown Only" and "All Missing". | The owner chose "Unknown" and "Whole Book". | Skipped. |

CodeRabbit also gave 11 findings on the saved Pass1 Auto result files in `gui2/data/`. These are the owner's per-word run output, not this thread's code. Not acted on.

## Fixes Applied
- None during review.

## Test Evidence
- `uv run pytest tests/gui2` (scope: whole gui2 test folder, run by the implementer) → 825 passed
- `uv run pytest tests/gui2/test_pass1_auto_controller.py` (scope: the one file, run by the independent reviewer) → 14 passed
- `uv run pytest tests/gui2 -k pass1` (scope: pass1 tests, independent reviewer) → 71 passed
- `ruff check`, `ruff format --check`, `pyright --project /dev/null` (scope: the 3 changed files, both agents) → clean
- `just typecheck` (scope: whole repo, implementer) → 0 errors
- Revert proofs (implementer): cut disabled → 3 new tests fail; counter change reverted → 1 fails; restored → all pass.
- Live runs by the owner: Buddhavaṃsa Unknown run ended `17 / 17 Finished unknown words in bv`; Apadāna counter read as expected; one-row layout confirmed.

## Not Verified
- The "no unknown words" message and Stop in Unknown mode were not run live. The first has a test; Stop was read only.
- The independent reviewer did not revert code; test strength was checked by reading.

## Verdict
PASSED
- Review date: 2026-11-11
- Reviewer: independent subagent (general-purpose) plus CodeRabbit CLI, model: Sonnet 5.5
- Independence: full (separate context) for the subagent review
