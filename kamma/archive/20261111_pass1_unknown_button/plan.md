# Plan: Pass1 Auto "Unknown" button

## Architecture Decisions
- Add one argument `unknown_only: bool = False` to `auto_process_book` and `_auto_process_book`. The view passes `True` from the new button. A separate method would copy 90 lines.
- Cut `missing_words_dict` to the unknown words right after the reorder. The existing loop, counter and "finished" message then work without a new branch inside the loop.
- Phase two is the existing run. Saved unknown words are already skipped by `is_missing`. Nothing to build.

## Model Strategy
| Phase | Tier | Suggested model | Reason |
|---|---|---|---|
| 1 — Controller and tests | Fast | Sonnet | Small edit plus tests copied from an existing test |
| 2 — Button and layout | Fast | Sonnet | Mechanical UI edits |
| 3 — Verify | Fast | Sonnet | Run checks |

## Phase 1 — Controller and tests — *Fast*
- [x] Write the failing test first: `test_unknown_only_run_sends_only_unknown_words` in `tests/gui2/test_pass1_auto_controller.py`. Copy the setup of `test_book_run_processes_unknown_words_first`. Call `auto_process_book("ap", unknown_only=True)`. Assert `processed == ["m2", "m4"]`.
  → verify: run `uv run pytest tests/gui2/test_pass1_auto_controller.py -k unknown_only`, expect a failure (unexpected keyword argument). Paste the output here.
- [x] Add `unknown_only` to `auto_process_book` and `_auto_process_book` in `gui2/pass1_auto_controller.py`. After the reorder, if `unknown_only`, keep only the words in `self.unknown_words`. Compute the "N of M" message before the cut. Use `Finished unknown words in <book>` as the end message.
  → verify: the new test passes.
- [x] Add `test_unknown_only_then_normal_run_sends_the_rest`. Run the Unknown run, then a normal run with `auto_processed_keys` filled from the first run. Assert the second run sends only m1 and m3.
  → verify: `uv run pytest tests/gui2/test_pass1_auto_controller.py` passes.
- [x] Add `test_unknown_only_with_no_unknown_words_ends_at_once`. Assert nothing is sent and the message `No unknown words in ap` appears.
  → verify: same file passes.
- [x] Revert the controller change by hand for one run to prove the tests guard it: expect the three new tests to fail for the reason above, not for a syntax error. Restore at once.
  → verify: report the number of failing tests; after restore, all pass.
- [x] Phase check: `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright --project /dev/null` on the controller and on the test file.
  → verify: all three print no errors.

## Phase 2 — Button and layout — *Fast*
- [x] In `gui2/pass1_auto_view.py` add `handle_unknown_click`, like `handle_book_click`, passing `unknown_only=True`. Add `ft.Button("Unknown", on_click=self.handle_unknown_click)` directly before the Whole Book button, after the AI Model field.
  → verify: read the row in the file; Unknown comes before Whole Book, after the AI Model field.
- [x] Set the Book and AI Model dropdown widths to 220. Change the labels `AutoProcess Book` to `Whole Book` and `AutoProcess Text` to `Process Text`. Change the dialog title to `Process Text`.
  → verify: `rg -n "AutoProcess" gui2/pass1_auto_view.py` returns no match. The Pass2 view is untouched.
- [x] Phase check: `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright --project /dev/null` on the view. Run `uv run pytest tests/gui2/ -k pass1`.
  → verify: no errors; tests pass.

- [x] (Added 2026-11-11) Counter in an Unknown run: new `progress_text` method leaves out the saved words when `unknown_only_run` is set. Test `test_unknown_only_counter_counts_only_unknown_words`. Reverting the change fails that test (1 failed, 13 passed); restored, 14 pass.

## Phase 3 — Verify — *Fast*
- [x] Run `just typecheck` (pyrefly) and then `uv run pyright --project /dev/null` on both gui2 files.
  → verify: both clean.
- [ ] Ask the owner to run `just gui` from the repo root, open Pass1 Auto, and check the row and one Unknown run on a small book.
  → verify: owner confirms all buttons fit on one row and the run stops after the last unknown word.
