# Plan: Pass1 Auto, unknown words first

## Architecture Decisions
- Reorder `missing_words_dict` once, before the loop. The loop stays unchanged. This is the smallest change.
- The lookup check is one method on the controller (`find_unknown_words`). It uses the db session the controller already holds. No new class or file.
- The unknown set is kept on the controller (`self.unknown_words`) so the loop message can label each word.

## Model Strategy
| Phase | Tier | Suggested model | Reason |
|---|---|---|---|
| 1 | Fast (workhorse) | Sonnet | Small mechanical edit and one test file. |
| 2 | Fast (workhorse) | Sonnet | Run checks. |

## Phase 1 — Reorder and label — *Fast*
- [x] Add `find_unknown_words(words)` to `Pass1AutoController` in `gui2/pass1_auto_controller.py`. It returns the words with no `Lookup.lookup_key` row, or whose row has data only in `epd`. It queries in chunks of 900.
  → verify: unit test with an in-memory sqlite `Lookup` table (one row with a headword, one with only a deconstructor, one with only `epd`, one word absent) returns exactly the `epd`-only word and the absent word.
- [x] In `_auto_process_book`, after the two find-missing steps, set `self.unknown_words`, rebuild `missing_words_dict` unknown-first, and post the "Unknown words (not in lookup): N of M" message. Add " (unknown)" to the per-word "Processing" message for that group. Leave `_auto_process_text` alone.
  → verify: unit test runs `_auto_process_book` with fake words and shows the processed order is unknown group first, original order kept inside each group.
- [x] Test file: add the tests to `tests/gui2/test_pass1_auto_controller.py`. Revert the reorder line, run the tests, report how many fail, then restore it.
  → verify: with the reorder reverted the order test fails. With it restored, `uv run pytest tests/gui2/test_pass1_auto_controller.py` passes.
  (Done 2026-11-21: with the reorder neutralised exactly 1 test failed — the order test; restored, all 9 passed.)
- [x] Phase check: run `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright --project /dev/null` on the controller and the test file, then `just typecheck`.
  → verify: all four report zero errors.

## Phase 2 — Live check — *Fast*
- [x] Hand the user `cd . && just gui`. The user runs Pass1 Auto on one small book.
  → verify: the status line shows the "Unknown words" count, and the first words are labelled "(unknown)". The user confirms.
