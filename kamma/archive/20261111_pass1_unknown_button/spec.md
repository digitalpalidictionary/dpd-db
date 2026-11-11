# Pass1 Auto: "Unknown" button (two-phase run)

## Overview
Pass1 Auto (`gui2/pass1_auto_view.py`, `gui2/pass1_auto_controller.py`) sends missing words of a book to the AI one by one. It already puts completely unknown words (no lookup row, or an `epd`-only row) first, then the words that only need a headword. The owner wants to run the two groups as two separate runs. A new **Unknown** button runs only the first group and stops.

Measured need (2026-11-11, distinct words per book, `dpd.db` lookup table): the Jātaka has 1,205 unknown words and 6,341 words that exist only in the deconstructor column. Running the groups apart lets the owner check the unknown words before the long tail.

## What it should do
1. A new button **Unknown** sits in the top row of the Pass1 Auto tab in this order: Book, AI Model (with its reload icon), **Unknown**, **Whole Book**, Process Text, Stop, Clear, GD. The order follows the user's steps: choose the book, choose the model, then choose unknown words only or the whole book.
2. Pressing it with a book chosen runs the normal book run, but only for the unknown words. The run ends when the last unknown word has been sent and saved. The message line then reads `Finished unknown words in <book>`.
3. A later press of **Whole Book** processes the rest. Words saved by the Unknown run are already in the book's saved results, so the normal run skips them. No new code is needed for phase two.
4. If the book has no unknown words, the run ends at once with the message `No unknown words in <book>`.
5. The counter shows `done / total` where total counts only the unknown words in this mode. Words saved by earlier runs are not added to either number: the counter starts at `0 / <unknown words>` and the total is the unknown words done plus the unknown words left. (Changed 2026-11-11 after the owner saw `15 / 964` on Apadāna. The run counts the Tipiṭaka text and the SuttaCentral text, so its total is larger than the docs table, which reads the Tipiṭaka text only.)
6. The first message of the run keeps the full picture: `Unknown words (not in lookup): N of M`, with M the count of all missing words.
7. Stop, the single-run lock and the error handling work as in the normal run.
8. Make room in the top row:
   - Book and AI Model fields: width 300 to 220.
   - `AutoProcess Book` button label to `Whole Book`.
   - `AutoProcess Text` button label to `Process Text`. The text dialog title `AutoProcess Text` also becomes `Process Text`.
   - Stop, Clear, the reload icon and the GD switch stay as they are.

## Current behaviour (read from code 2026-11-11)
- `_auto_process_book` builds `missing_words_dict`, calls `find_unknown_words`, stores the result in `self.unknown_words`, and reorders so unknown words come first. It then loops over the whole dict.
- `AutoProcess Text` sets `unknown_words` to an empty set. It is not affected.
- `is_missing` drops words in `all_inflections`, `sandhi_ok_list`, the auto-processed keys, variant readings and spelling mistakes. Words in the sandhi-OK list are therefore never sent in either phase.
- `find_unknown_words` treats a row with only `epd` data as unknown.

## Assumptions & uncertainties
- Verified: the code facts above, and that `tests/gui2/test_pass1_auto_controller.py` has a test of the unknown-first order that can be copied.
- Assumed: dropping the two fields to 220 and shortening the labels leaves room for one more button in the owner's window. Not measured. The owner confirms on a real run.
- Assumed: the Counter field in the second row needs no change, because the room problem is only in the top row.
- Assumed: the Pass2 Auto view also has an `AutoProcess Book` button (`gui2/pass2_auto_view.py`). It is a different tab and is left alone.
- Unknown: if one unknown word fails (bad AI reply), the loop skips it and goes on, as today. The Unknown run then ends with that word still unsaved. The owner sees it in the next normal run, because the word is still unknown and would come first.

## Constraints
- Minimal change: one new argument on the book run, one new button, width and label edits. No new class, setting or file.
- Pre-commit gate for every touched file: `ruff check`, `ruff format`, `pyright --project /dev/null` (the `gui2/` and `tests/` files are excluded from plain pyright), then the related tests. See `CLAUDE.md`.
- No git commands. The owner commits.

## How we'll know it's done
- A test shows the Unknown run sends only unknown words and then ends. It fails when the new argument is ignored.
- A test shows a normal run after an Unknown run sends only the other words.
- A test shows the no-unknown-words message.
- The existing tests in `tests/gui2/test_pass1_auto_controller.py` still pass.
- The owner runs `just gui`, opens Pass1 Auto, sees all buttons on one row with Unknown before Whole Book, after the AI Model field, and runs it on a small book.

## What's not included
- No change to Pass1 Process Text, Pass2 Auto, the AI prompt, or how words are found.
- No second "headwords" button. A normal run already does that.
- No new setting for the order of the two groups.
