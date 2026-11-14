# Contributor Pass1: stop two contributors taking the same word, and split big books

No GitHub issue number was given. Add one here if there is one.

## Overview

Contributors on the web server add new words from the Pass1 queue of a book. Two contributors can work on the same book. Today a word that one contributor finishes can still be offered to the other, because the other contributor's screen holds a snapshot of the queue from when the book was opened.

This thread has two parts.

- **Part A.** When the next word loads, skip any word that another contributor has already finished.
- **Part B.** Split the largest Pass1 books into smaller parts, so contributors can take different parts by agreement. This part comes after Part A.

## Current behaviour (verified by reading the code, 2026-11-14)

- Each book has one draft queue file, `gui2/data/pass1_auto_<book>.json`. It is tracked by git. On a contributor server it is read-only (`Pass1FileManager._refuse_tracked_write`).
- A contributor who saves a word adds it to their own finished list, `pass1_auto_removed_<user>.json`, under the book key. The draft file stays as it is (`Pass1FileManager.remove`).
- `Pass1FileManager._hidden_words(book)` reads every `pass1_auto_removed_*.json` in the finished-list folder and hides those words. `_list_folder` returns the folder of the user's own finished list, which is the shared data folder.
- `Pass1AddController.process_book` calls `load_json`, which builds `auto_processed_iter` once from one copy of the queue. `get_next_item` only calls `next()` on that iterator. It never re-reads the finished lists.
- `Pass1AutoController.get_auto_processed_dict` caches the queue in `auto_processed_dict`. The cache is refreshed only after the user's own removal.
- So a word finished by another contributor after the book was opened stays in this contributor's iterator.
- Saving checks the main database for a duplicate `lemma_1` (`validate_no_duplicates`). It does not check other contributors' additions. This thread does not change that (see "What's not included").
- The nightly merge by the maintainer is where a duplicate would finally be caught.
- The daily pull (`contrib_pull.py`, `apply_pass1_removals`) deletes finished words from the draft files, one book at a time. It skips a finished-list key whose draft file is missing.

## What it should do

### Part A: skip finished words

1. `Pass1FileManager` gets one small method that returns the words finished in a book, read fresh from every finished list in the folder. It uses the same reading code and the same lock as `_hidden_words`.
2. `Pass1AddController.get_next_item` reads that set once per call. It skips any word in the set and moves to the next. When no word is left, it ends as it does today ("No more words to process.").
3. The "remaining" counter shows the count after finished words are removed.
4. A contributor never sees an error or a message about a skipped word. The word is simply not offered.
5. On the laptop, behaviour must not change. The new method returns an empty set there, because the existing test `test_the_laptop_read_ignores_pulled_lists` says the laptop ignores pulled contributor lists. (Changed 2026-11-14 during build; the first draft said the laptop would skip them too.)

### Part B: split books

Facts checked in the source (file counts, 2026-11-14):

| Book now | Words in queue | Source layout |
|---|---|---|
| `ap` (Apadāna) | 341 | CST: two books, `kn10` (Thera) and `kn11` (Therī). SuttaCentral: two folders, `tha-ap` (563 files) and `thi-ap` (40 files). |
| `nidd1&2` (Niddesa) | 702 | CST: `kn15`, `kn16`. SuttaCentral: folders `mnd` (16 files) and `cnd` (23 files). |
| `ja` (Jātaka) | 611 | SuttaCentral: 547 files, one per jātaka (`ja1` to `ja547`). CST: `kn14` is two files (`s0513m`, `s0514m`). |

Plan for each part:

1. **Apadāna and Niddesa.** Replace each combined book with two books, one per source part. New keys follow the SuttaCentral folder names: `tha-ap`, `thi-ap`, `mnd`, `cnd`. Each key points at its own CST book and its own folder.
2. **Jātaka root text only, five parts (decided by the user, 2026-11-14: "make a three-part or five-part split, your call. I want to spread the work across contributors").** The commentary (`jaa`) is not split. The cuts fall on whole nipātas, chosen so the draft words are about even. Measured with the draft words placed by CST story (`artifacts/jataka_split_options.md`):

   | New book | Nipātas | Stories | Draft words (measured 2026-11-14) |
   |---|---|---|---|
   | `ja-1` | 1 to 4 (Ekaka to Catukka) | 1-350 | 153 |
   | `ja-2` | 5 to 10 (Pañcaka to Dasaka) | 351-454 | 154 |
   | `ja-3` | 11 to 14 (Ekādasaka to Pakiṇṇaka) | 455-496 | 124 |
   | `ja-4` | 15 (Vīsati) | 497-510 | 89 |
   | `ja-5` | 16 to 22 (Tiṃsa to Mahā) | 511-547 | 137 |

   CST and SuttaCentral number the stories the same way (story 1 Apaṇṇaka, story 547 Vessantara, checked at both ends). A draft word goes into every part where it occurs in the CST text, so a word in two parts is in both files (44 words occur in more than one of these five parts; 1 word, `mavoca`, has no story and goes to `ja-5`; the five files hold 657 entries for 611 words). `SuttaCentralSource` gets one new optional argument, a range of story numbers, so a part reads only its own SuttaCentral files. `cst_books` stays `["kn14"]` for every part: CST gives a word's place only to the one-off split script, not to the book list.
   Known limit: if the laptop later runs Pass1 Auto on one part, the CST word list of the whole book is used, so it can re-add words that sit in other parts. The same already happens between books that share words.
3. **Existing draft files.** Each combined draft file is split by where each word occurs in the new parts (for Apadāna and Niddesa by the SuttaCentral text of each part, for Jātaka by the CST story number). A word that occurs in both parts goes into both files. This is done once, by a throwaway script in the thread's `artifacts/` folder, not by code that runs every time.
4. **Order of work on the live system.** Run the daily pull first, so finished words are deleted from the old draft files. Then split the files. A finished-list entry under an old key (`ap`, `nidd1&2`, `ja`) is not carried over to the new part files: the pull skips a key whose draft file is gone, and the new keys do not see it. Measured 2026-11-14: only two test users have such entries (18 distinct words under `ap`, all already absent from the new files) and none exist for `nidd1&2` or `ja`. A word finished under an old key between the split and the server switch would be offered again.
5. The other small books (all under 100 words) are not split.

## Assumptions and uncertainties

- **Verified in the code:** everything under "Current behaviour".
- **Verified by a test, not on the server:** all contributor instances share one data folder. `tests/scripts/server_contrib/test_add_contributor.py` asserts it for the add-contributor script. I did not check the live server (the dev clone cannot show it). Part A depends on this. Check on the live host before calling Part A done.
- **Measured 2026-11-14 (details in `artifacts/jataka_split_options.md`):** 610 of the 611 Jātaka draft words are in the first CST file, so CST cannot split the root text. SuttaCentral can place only 374 of the 611 draft words; 237 are not in the SuttaCentral word list.
- **Not verified:** whether adding new keys to the SuttaCentral book list changes the Pass2 tabs. `pass2_pre_controller`, `pass2_auto_control` and `tools/docs_update_missing_words.py` also read the book list. The plan includes a sweep.
- **Known limit:** a word that occurs in two parts stays in both queues. Part A does not catch it across books, because finished words are hidden per book.
- **Measured 2026-11-14 (dry run of the split script):** the Apadāna draft (341 words) splits into `tha-ap` 341 and `thi-ap` 17, so the Therī part is small. 481 of the 702 Niddesa words are fragments cut at SuttaCentral's bold quote tags (for example `dukkhan` from `<b>…dukkhan</b>ti`), made by an older word splitter. 478 of them are not in today's SuttaCentral or CST word list. **Decided by the user, 2026-11-14 ("remove the bold tag fragments"): the split script drops those 478.** It drops a word only when it has no home in today's texts and it matches a fragment of the old splitter. The other 3 stay, because they are also real words. The Niddesa draft then splits into `mnd` 158 and `cnd` 89, 23 words in both, 224 words in all.
- **Stale comment:** a comment in the file manager says two contributors on one book can corrupt the draft file. That is no longer true for contributors, who never write it. The project rule says to leave existing comments, so it stays.

## Constraints

- Contributors never write the tracked draft files. Keep that.
- Do not touch `.env` or `.ini` files. No git commands. The user commits.
- Type hints on everything, modern forms. `Path` not `os`. No `sys.path` tricks.
- Any tracked data file the code writes is saved in canonical sort order.
- Every touched file must pass `ruff check`, `ruff format` and `pyright`. Files under `gui2/` and `tests/` need `uv run pyright --project /dev/null <file>`. Run `just typecheck` before finishing.
- Do not run a full build or the live pull just to prove a fix (project rule). A guarding unit test is enough.

## How we'll know it's done

- **Part A.** A test with two file-manager instances on one shared folder: open a book, let the second instance finish a word, call the next-word step on the first, and the word is skipped. Reverting the change makes that test fail.
- **Part A.** `get_next_item` ends with "No more words to process." when every remaining word is finished by others.
- **Part A.** The remaining counter excludes finished words.
- **Part B.** The Pass1 book dropdown shows the new parts and no longer shows the combined books.
- **Part B.** The sum of the new draft files equals the old file plus the words that occur in both parts. The script prints both counts.
- **Part B.** `just typecheck` and the related tests pass. Pass2 tabs and the missing-words page still list the same books.

## What's not included

- A claim system, such as locking a word when it opens. That was option C and was not chosen.
- A save-time check for a headword already added by another contributor. That was dropped from option B by the user.
- Changing how finished words are hidden across different books.
- Cleaning bold tag fragments from any other book's draft file.
- Splitting the Jātaka commentary or any other commentary (dropped by the user, 2026-11-14).
- Splitting the books under 100 words, and the Dhammapada commentary (one CST file).
- Any change to the nightly merge or the daily pull.
