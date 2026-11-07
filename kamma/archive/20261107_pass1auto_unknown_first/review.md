## Thread
- **ID:** 20261107_pass1auto_unknown_first
- **Objective:** Pass1 Auto (book run) sends completely unknown words to the AI first, then the rest as before.

## Files Changed
- `gui2/pass1_auto_controller.py` — `find_unknown_words` (chunked lookup check, NULL-safe, epd-only = unknown); `_auto_process_book` reorders `missing_words_dict` unknown-first, posts the "Unknown words" status, labels unknown words "(unknown)" (also in `compile_prompt`); `_auto_process_text` resets `unknown_words`; unknown query runs via `asyncio.to_thread`.
- `tests/gui2/test_pass1_auto_controller.py` — in-memory `Lookup` test (headword / deconstructor-only / epd-only / absent / NULL+epd rows) and full book-run order test (unknown first, group order kept, status line, labels).
- `kamma/threads/20261107_pass1auto_unknown_first/plan.md`, `spec.md` — checkboxes, revert-check result, contributor-host claim marked as assumption.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `gui2/pass1_auto_controller.py:144` (independent review) | `find_unknown_words` ran on the event loop | Frozen UI on big books; every other db step uses `to_thread` | Fixed: wrapped in `asyncio.to_thread`; test engine given `check_same_thread=False` + `StaticPool` to match `db_helpers` |
| 2 | minor | `compile_prompt` message (independent review) | "(unknown)" label overwritten within milliseconds | User never sees which word is unknown | Fixed: `compile_prompt` keeps the "(unknown)" tag |
| 3 | minor | `gui2/data/additions_alice.json:765,1758,1784` (CodeRabbit, pre-existing) | example mismatch, `"; ;"`, `derived_from` = pos | Data quality in contributor file | NOT TOUCHING — outside thread scope, per-word data is the editor's call |

Nits (accepted, not fixed): no chunk-boundary test (>900 words); two-step reorder style.

## Fixes Applied
- Findings 1 and 2 above; `unknown_words` reset in the paste-text run; spec's contributor-host claim marked unverified; revert-check result recorded in plan.md.

## Test Evidence
- `uv run pytest tests/gui2/test_pass1_auto_controller.py -q` (thread's controller behaviours) → 9 passed
- `uv run pytest tests/gui2/ -q` (whole gui2 suite incl. the concurrent books.py session's tests) → 710 passed
- Revert-check: reorder neutralised → exactly 1 failure (order test); restored → green
- `uv run ruff check` + `ruff format`, `uv run pyright --project /dev/null` (both files) → clean
- `just typecheck` (pyrefly, repo-wide) → 0 errors
- Live: user ran Pass1 Auto on a book via `just gui`; unknown words found first — confirmed

## Not Verified
- The live contributor host's `lookup` table (spec assumption marked); real-book unknown-vs-rest counts beyond the Apadāna simulation (8,328 missing → 808 unknown / 7,520 deconstructor-covered) and the user's one live book run.
- CodeRabbit ran on the shared tree diff (incl. the other session's `gui2/books.py`): no new findings.

## Verdict
PASSED
- Review date: 2026-11-21
- Reviewer: independent pi subagent "reviewer" + CodeRabbit CLI + user's independent review; consolidated by implementer session
- Independence: full (separate contexts) for both agent reviews
