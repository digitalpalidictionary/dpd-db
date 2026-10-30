## Thread
- **ID:** 20261023_contrib_2_edits_json
- **Objective:** Contributor saves go to per-user JSON only; they see "db + own edits"; user 1 still writes the db.

## Files Changed
- `gui2/save_router.py` — one save seam (user 1 → db, contributor → JSON).
- `gui2/database_manager.py` — overlay, own lemmas and ids in duplicate check / next id.
- `gui2/toolkit.py`, `gui2/paths.py` — overlay wiring; per-user paths for dictionary and four helper files.
- `gui2/pass1_add_controller.py`, `gui2/pass2_add_view.py` — use the seam; contributor delete.
- `gui2/additions_manager.py`, `gui2/corrections_manager.py` — `discard`; review fixes (atomic write, rollback, damaged file kept aside).
- `gui2/variants.py`, `gui2/spelling.py`, `gui2/sandhi_files_manager.py`, `gui2/mixins.py`, `tools/spelling.py` — per-user files.
- `tools/compound_type_manager.py`, `tools/phonetic_change_manager.py` — refuse TSV edit on the server.
- Tests under `tests/gui2/` and `tests/tools/`.
(The code was committed in 546557a2, 43d085fe and e1c0a185 before this review; the review fixes are uncommitted.)

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `gui2/main.py`, DB/Sandhi/Spelling/Roots tabs | Other tabs still write `dpd.db` for a contributor | Breaks the "contributor never writes db" goal | DEFERRED to contrib_5 (hides tabs); logged in problem_children #7 |
| 2 | major | `additions_manager.get_next_addition` etc. | Pass2 buttons pop a contributor's own edits | Data loss of the only record | DEFERRED (Pass2 hidden in contrib_5); problem_children #8 |
| 3 | minor | `database_manager.get_all_lemma_1_and_lemma_clean` | Own corrections' lemma missing from duplicate set | Duplicate lemma slips through | FIXED |
| 4 | minor | `pass2_add_view` save / discard | Duplicate set not refreshed | Same | FIXED |
| 5 | minor | both managers | Non-atomic write; failed write leaves unsaved edit; damaged file read as empty | JSON is the only record | FIXED |
| 6 | minor | `tests/gui2/test_variants_spelling_own_files.py` | User 1 tests used the no-argument form the app never uses | Would stay green on a regression | FIXED (added shared-path tests) |
| 7 | nit | `gui2/mixins.py` | Docstring named the shared file | Wrong for contributors | FIXED |
| 8 | minor/nit | various | Username mismatch, overlay rename edge, non-numeric id, missing header, browser button, CodeRabbit item on #273 code | See problem_children #9 | DEFERRED / out of scope |

## Fixes Applied
- Atomic JSON write, rollback on failed write and discard, damaged file kept as `.corrupt`.
- Own corrections join the duplicate-lemma set; Pass2 refreshes it after a contributor save and a discard.
- Docstring fix; 13 new tests.

## Test Evidence
- `uv run pytest tests/` (whole suite) → 2553 passed, 12 deselected.
- `just typecheck` (whole repo) → 0 errors.
- `ruff check` / `ruff format` on all touched files → clean. `pyright --project /dev/null` on touched files → 0 errors, except `pass2_add_view.py` (49 flet-typing errors, same kind as before this thread; gui2 is excluded from the pre-commit pyright).
- Guard check: removing the fixes failed 5 of the new tests; restored → pass.
- Live local web run as a contributor (plan 3.1) and a user 1 desktop run → pass, logged in plan.md.
- Reviewers: Sonnet subagent, DeepSeek v4-pro via pi (max reasoning), CodeRabbit on `gui2/` (1 minor finding, in #273 code, out of scope).

## Not Verified
- Edit of a plain db word and refusal to delete a db word were never run in the app (unit tests only).
- The browser clipboard error and headless `pyperclip` were not resolved.
- Whether the nightly push carries the new per-user files (server thread).
- CodeRabbit reviewed `gui2/` only, not `tools/`.

## Verdict
PASSED
- Review date: 2026-10-30
- Reviewer: Claude (Sonnet 5.5) with Sonnet subagent, DeepSeek v4-pro and CodeRabbit
