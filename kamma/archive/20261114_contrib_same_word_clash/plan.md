# Plan: contributor Pass1 same-word clash, and book split

Spec: `spec.md` in this folder. No GitHub issue number given.

## Architecture Decisions

- Part A adds one read method to `Pass1FileManager` and one loop in `Pass1AddController.get_next_item`. It reuses `_hidden_words` and the existing lock. No new file, no new class.
- Part A re-reads the finished lists on each next-word call (a few small files). No cache and no timer, so nothing can go stale again.
- Part B changes data and the book list, not the code paths. New book keys follow the SuttaCentral folder names (`tha-ap`, `thi-ap`, `mnd`, `cnd`).
- Existing draft files are split once by a throwaway script kept in this thread's `artifacts/` folder. The app does not carry migration code.
- Nothing is committed in this plan. The user commits at the end. Phase checkpoints are report-only.

## Model Strategy

| Phase | Tier | Suggested model | Reason |
|---|---|---|---|
| 1. Skip finished words | Fast | Sonnet | Small, well-specified code change with tests. |
| 2. Split Apadāna and Niddesa | Fast | Sonnet | Mechanical book-list edits and a one-off data split. |
| 3. Split Jātaka root text | Pro | Opus | Needs a reading of the data to choose split points, and corpus-wide checks. |
| 4. Docs and final checks | Fast | Sonnet | Notes, lint, type check. |

## Phase 1 — Skip finished words — *Fast*

Baseline before any edit (2026-11-14): `uv run pytest tests/gui2/test_pass1_file_manager.py tests/gui2/test_pass1_add_controller.py tests/gui2/test_pass1_auto_controller.py -q` gave 50 passed. No pre-existing failures.

- [x] 1.1 Add `finished_words(book: str) -> set[str]` to `Pass1FileManager` in `gui2/pass1_file_manager.py`. It takes the lock and returns `_hidden_words(book)` for a contributor, and an empty set on the laptop (`removed_path is None`).
  → verify: in `tests/gui2/test_pass1_file_manager.py` add a test with two `pass1_auto_removed_<user>.json` files in one folder. Run `uv run pytest tests/gui2/test_pass1_file_manager.py`, expect the words of both files for the right book, none for another book, and an empty set for the laptop manager.

- [x] 1.2 In `Pass1AddController.get_next_item` (`gui2/pass1_add_controller.py`), read `finished_words` once, loop over the iterator, and skip words in the set. Keep the "No more words to process." ending.
  Read `Pass1AutoController.get_auto_processed_dict` first. It caches the queue. Make the remaining counter come from the queue minus finished words. If that needs more than one call, use the file manager's `read(book)`.
  → verify: in `tests/gui2/test_pass1_add_controller.py` add a test. Open a book with words a, b, c. Write a finished list for another user that holds b. Call `get_next_item` twice and expect a, then c. A second test: all words finished by others, expect the "No more words to process." message and `False`.

- [x] 1.3 Prove the tests guard the change. Revert only task 1.2's edit in the one file, run the two new controller tests, report how many fail, then restore in the same command. The failing run must fail on the assertion, not on an import error.
  → verify: the report states the number of failing tests, and the file is restored (re-run the tests, expect pass).
  Result (2026-11-14): with the skip loop removed, 2 of the 3 new controller tests failed (`test_next_item_skips_words_finished_by_others`, `test_next_item_ends_when_every_word_was_finished_by_others`) on an assertion. The count test stays green because the count filter is separate code. Restored; file identical to the backup; 12 passed.

- [x] 1.4 Lint and type check every touched file: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright --project /dev/null <file>` for `gui2/` and `tests/`. Then `just typecheck`.
  Result (2026-11-14): ruff clean, pyright 0 errors, `just typecheck` 0 errors, 56 passed. Four old pyright errors in `tests/gui2/test_pass1_add_controller.py` (mock asserts on a typed attribute) were fixed with `cast(MagicMock, ctrl.db)`.
  → verify: all commands exit 0 with no errors. Run `uv run pytest tests/gui2/test_pass1_file_manager.py tests/gui2/test_pass1_add_controller.py tests/gui2/test_pass1_auto_controller.py`, expect all pass.

- [x] 1.5 Phase check. Confirm the live server uses one shared data folder: ask the user for the output of reading the `DPD_GUI2_DATA_DIR` value for two contributor units on the server.
  Result (2026-11-14): read-only check on the live server: all 8 unit env files hold the same folder, `/var/lib/dpd/contrib_data`.
  → verify: both units show the same folder. If they differ, stop and tell the user: Part A will not work.

## Phase 2 — Split Apadāna and Niddesa — *Fast*

- [x] 2.1 Sweep every use of the combined keys. Run `rg --hidden -F 'nidd1&2'` and the same for the `ap` key (`"ap"`) over the repo, excluding `kamma/archive` and `graphify-out`. Include `gui2/pass1_context.py`, `tools/docs_update_missing_words.py`, `scripts/server_contrib/contrib_pull.py`, `tests/`. Also check `pass2_pre_controller.py` and `pass2_auto_control.py` for any use of these books.
  → verify: the plan's task notes list every file found, and each is marked "change" or "no change, because …".
  Sweep result (2026-11-14), `rg --hidden`, excluding `kamma/archive`, `graphify-out`, `gui2/data`:
  - change: `gui2/books.py`, `gui2/pass1_context.py` (names), `tools/docs_update_missing_words.py` (two rows), `tests/gui2/test_books.py`, `tests/scripts/server_contrib/test_contrib_pull.py`.
  - change, not in the first plan: `tests/gui2/test_pass1_auto_controller.py`. Seven calls used the real key `ap` and four expected messages repeated it; they now use `tha-ap`.
  - no change: `tests/tools/test_docs_update_missing_words.py` (uses `ap` as a throwaway key with a mocked book list), `scripts/server_contrib/contrib_pull.py` (takes book keys from the contributor files), `tools/pali_text_files.py` and other `ap` hits (CST codes or unrelated words).
  - Pass2 side effect: the Pass2 Pre and Pass2 Auto book dropdowns read the same book list, so they show the four new keys instead of `ap` and `nidd1&2`. No Pass2 draft file exists for either book. No code change needed.
  - `tools/docs_update_missing_words.py` does not read the draft files, so the split does not change the missing-words page counts.

- [x] 2.2 In `gui2/books.py` replace `ap` with `tha-ap` (CST `kn10`, folder `tha-ap`) and `thi-ap` (CST `kn11`, folder `thi-ap`). Replace `nidd1&2` with `mnd` (CST `kn15`) and `cnd` (CST `kn16`). Update `BOOK_NAMES` in `gui2/pass1_context.py` and the book list in `tools/docs_update_missing_words.py` to match.
  → verify: update `tests/gui2/test_books.py` (it checks `ap` and `nidd1&2` today). Run `uv run pytest tests/gui2/test_books.py tests/tools/test_docs_update_missing_words.py`, expect all pass.

- [x] 2.3 Write a one-off script in `kamma/threads/<thread>/artifacts/split_drafts.py`. It splits `pass1_auto_ap.json` and `pass1_auto_nidd1&2.json` into the four new draft files by which part's word list holds each word. A word in both parts goes to both. It keeps each word's data. Files are written with `io.open(..., newline='')` and the source's line endings.
  Written (2026-11-14, at the user's request, without a fresh contributor pull first): `--write` created `tha-ap` 341, `thi-ap` 17, `mnd` 158, `cnd` 89, `ja-1` 153, `ja-2` 154, `ja-3` 124, `ja-4` 89, `ja-5` 137, and deleted the old `ap`, `nidd1&2` and `ja` draft files. Each new file loads as valid JSON with those counts.
  Status (2026-11-14, earlier): dry run done by the assistant at the user's request, nothing written. `ap` -> `tha-ap` 341, `thi-ap` 17; `nidd1&2` -> `mnd` 158, `cnd` 89, and 478 bold tag fragments dropped at the user's request; `ja` as in 3.4. The first dry run left 134 Apadāna and 548 Niddesa words with no home, because the script checked only SuttaCentral. It now checks the CST book of each part as well, and for Niddesa it keeps words cut at SuttaCentral's bold tags (see `spec.md`). Earlier status: the script is written at `kamma/threads/20261114_contrib_same_word_clash/artifacts/split_drafts.py`. It is a dry run by default and writes only with `--write`. It stops without writing if any draft word is in neither part. It has NOT been run; the user runs it.
  → verify: the script prints, for each old file, the old count, the two new counts, and the number of words in both. Check: new A + new B − both = old count. The user runs the script (project rule: the user executes scripts).

- [x] 2.4 Update `tests/scripts/server_contrib/test_contrib_pull.py` if it still uses `nidd1&2` as an example key (it does at line 59). The test only needs a book key, so a new key is fine.
  → verify: `uv run pytest tests/scripts/server_contrib/`, expect all pass.

- [x] 2.5 Lint, type check and run the phase tests as in 1.4 for every touched file.
  Result (2026-11-14): ruff clean, pyright 0 errors on every touched file, `just typecheck` 0 errors, `uv run pytest tests/gui2 tests/tools tests/scripts/server_contrib -q` gave 2057 passed, 7 deselected (slow). The first run had 6 failures from the old `ap` key in `test_pass1_auto_controller.py`; fixed by renaming the key in the test, not by loosening an assertion.
  → verify: all exit 0. `just typecheck` passes.

## Phase 3 — Split the Jātaka root text — *Pro*

The commentary is not split (user, 2026-11-14). Only the root text `ja`.

- [x] 3.1 Read the data and measure split points. Count the draft words per SuttaCentral number range, and per CST file. Put the table in `artifacts/jataka_split_options.md`.
  → verify: the table exists and its numbers come from the real files. Done 2026-11-14: 610 of 611 words are in the first CST file; per SuttaCentral range the counts are 13, 19, 36, 69, 150 and 123; 237 words are not in the SuttaCentral word list.

- [x] 3.2 The user chose five parts, cut by the assistant on the evidence (2026-11-14). The split is in `spec.md` (Part B, item 2): `ja-1` stories 1-350, `ja-2` 351-454, `ja-3` 455-496, `ja-4` 497-510, `ja-5` 511-547.
  → verify: the decision is written into `spec.md`. Done.

- [x] 3.3 Add an optional story-number range to `SuttaCentralSource` in `gui2/books.py` (a `range`, matched on the number in each file name, for example `ja123_root-pli-ms.json`). Replace `ja` with `ja-1` to `ja-5`, each with its own range, CST `["kn14"]`, and the same SuttaCentral folder. Add the five names to `BOOK_NAMES` in `gui2/pass1_context.py`. List the five keys in the Jātaka row of `tools/docs_update_missing_words.py`.
  → verify: in `tests/gui2/test_books.py` add (a) a test with fake files that a range keeps only the files inside it, and (b) a real-data test that the five parts together read exactly the 547 `ja` files, with no file in two parts. Run `uv run pytest tests/gui2/test_books.py tests/tools/test_docs_update_missing_words.py`, expect all pass.

- [x] 3.4 Extend `artifacts/split_drafts.py` to split `pass1_auto_ja.json` into the five files. Place each word by the CST story numbers where it occurs (same method as `artifacts/jataka_split_options.md`: headings `N. …jātakaṃ`, text cleaned with `clean_machine`). A word with no story goes to `ja-5`. Keep the dry-run default and the count check.
  Status (2026-11-14): `artifacts/split_drafts.py` now splits `ap`, `nidd1&2` and `ja`. I did not run the script. I imported its placement function in a scratch check (read-only) on the real draft and CST text: `ja-1` 153, `ja-2` 154, `ja-3` 124, `ja-4` 89, `ja-5` 137, 44 words in more than one part, 1 unplaced (`mavoca`, goes to `ja-5`), 657 entries in total.
  → verify: the dry run prints old, new, shared and unplaced counts. The new counts match the numbers above. The user runs it. Do not run `--write` myself.

- [x] 3.5 Lint, type check and run the phase tests as in 1.4 for every touched file. Sweep `rg --hidden` for any other use of the `ja` key as a Pass1 book (tests, docs, scripts) and fix each.
  Result (2026-11-14): ruff clean, pyright 0 errors on every touched file, `uv run pytest tests/gui2 tests/tools tests/scripts tests/exporter -q` gave 2908 passed, 12 deselected, `just typecheck` 0 errors. The `ja` sweep found only unrelated hits (`tests/db/test_sutta_info.py`, `db/`, `scripts/suttas`).
  → verify: all exit 0. `just typecheck` passes.

## Phase 4 — Docs and final checks — *Fast*

- [x] 4.1 Update `kamma/tech.md` (before the work lands, per the workflow) with one dated line: Part A re-reads finished lists on each next word, and the book split with the new keys. Also update `scripts/server_contrib/README.md` if it names the old book keys.
  Result (2026-11-14): the new `kamma/tech.md` line names `nidd1&2` once, as the old key it replaced; the README names the new keys only.
  → verify: `rg --hidden -F 'nidd1&2'` over `kamma/tech.md` and the README finds no stale key.

- [x] 4.2 Run `graphify update .` and prune old snapshots as the project rule says.
  Result (2026-11-14): graph rebuilt (38172 nodes), snapshots pruned, `ls -d graphify-out/20* | wc -l` printed 1.
  → verify: `ls -d graphify-out/20* | wc -l` prints 1.

- [x] 4.3 Order on the live system, for the user to follow: run the daily pull, split the draft files, push, let the nightly window pull. Write these steps, each as `cd <dir> && <command>`, in the thread's `artifacts/` folder.
  Result (2026-11-14): `artifacts/live_steps.md` written. `just contrib-pull` exists (`just --list`); the push step follows the README.
  → verify: the file lists the steps in that order, and each command exists in the justfile or README.

- [x] 4.4 Report that work is ready. Tell the user to run `/kamma:3-review`.
  → verify: every task above is `[x]`, and no file outside the list in the plan was changed (the user checks `git status`).

## Review results (2026-11-14)

CodeRabbit (free plan, one run per folder: gui2, tests, tools, scripts, kamma) and pi on DeepSeek flash (thinking off, one request of 61 KB). Findings were checked against the code before acting.

- Fixed: pi 3 (no test crossed from a finished list into `get_next_item`). Added `test_a_word_another_contributor_finishes_after_the_book_opened_is_skipped`, which uses two real contributors on one folder. With the skip loop removed, 3 of 13 controller tests fail, this one included.
- Fixed: pi 5 and 7 (tech note said "skips any word another contributor has finished" and did not mention the 478 dropped fragments). Both now in `kamma/tech.md`.
- Fixed: CodeRabbit kamma finding (live steps and spec called ignored old-key finished entries "harmless"). Measured instead: only two test users have such entries (18 words under `ap`, none left in the new files, none for Niddesa or Jātaka). Both files now say the entries are not carried over.
- Not real: pi 1 (a contributor cannot re-add a word through Pass1 Auto on the server: `update` raises PermissionError; and `read` already hides the contributor's own finished words). pi 4 (the laptop returns an empty set before reading any list).
- Skipped: pi 2 (counter refactor, no bug), pi 6 (empty range guard; the real-data test covers it).
- Not caused by this thread (NOTICED — NOT TOUCHING): CodeRabbit's six gui2 findings are about the content of single draft entries. All 1262 entries in the nine new files are identical to the old files. One draft key holds a Devanagari vowel sign (`abhisambhavैyyāti` in `mnd`), also in the old file.
- Docs (first build): `tools/docs_update_missing_words.py` was run alone on request. Only the date line changed; every row was identical.
- Docs (second build, at the user's request to split the rows): the page now has two Apadāna rows, two Niddesa rows and five Jātaka rows. The Jātaka rows are cut by CST story number with the new `make_cst_jataka_text_list` in `tools/cst_sc_text_sets.py` (the old `make_cst_text_list` returns identical output on 6 checks; the five ranges together give exactly the word counts of the whole book). Tests: `tests/tools/test_cst_sc_text_sets.py` (new) and three new tests in `tests/tools/test_docs_update_missing_words.py`; reverting the range branch fails the count test. Side effect: the "All books added" distinct-word total of the Khuddaka table rose from 163,221 to 185,883, because a word that occurs in several parts is counted in each part.
- Checks after the fixes: ruff clean, pyright 0 errors, `just typecheck` 0 errors, `uv run pytest tests/gui2 tests/tools tests/scripts -q` gave 2209 passed, 7 deselected.

## Second review (2026-11-14)

pi on DeepSeek flash (thinking off, one request of 23 KB) over the code changed after the first review: `tools/cst_sc_text_sets.py`, `tools/docs_update_missing_words.py`, the new and changed tests, `kamma/tech.md`.

- Not real: finding 1 (the opening lines of the second Jātaka file are counted as story 1). The running story number carries over from the end of the first file, so they go with story 520, which is in the `ja-5` range. The real file opens with a title, a part line and a nipāta heading before story 521. Pinned by `test_a_second_file_continues_the_story_the_first_file_ended_on`.
- Not real: finding 3 (counter disagrees on first paint). On the server `read` already hides every finished word when the book opens.
- Fixed: finding 2 (the refactor of `make_cst_text_list` had no pinned expectation). Four parametrized tests with exact lists, taken from the function before the refactor. With the dedupe step broken on purpose, 2 of them fail.
- Fixed: finding 4 (tech note said the Jātaka rows are split "like" the Pass1 books). The note now says the page counts only the CST stories of each range, and the Pass1 books still list the whole `kn14`.
- Skipped: finding 5 (nit, the laptop counter).
- Checks: ruff clean, pyright 0 errors, `just typecheck` 0 errors, `uv run pytest tests/gui2 tests/tools tests/scripts -q` gave 2220 passed, 7 deselected.
