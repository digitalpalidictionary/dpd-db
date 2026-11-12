# Spec — Pass1 Auto: a word added on one machine leaves the queue on the other

**GitHub issue:** #215 (Contributor Onboarding: Easy GUI Setup & Data Submission). Never comment on or close the issue (project rule).

## Overview

Pass1 Auto (laptop only) writes AI drafts into `gui2/data/pass1_auto_<book>.json`, one JSON object per book, `{word_in_text: {field: value}}`. These files are tracked by git and reach the contributor server through git. Pass1 Add shows the words of one book file, one at a time; after a committed save of the book word it removes that word from the queue.

Today the removal behaves differently on the two machines:

- **Laptop (user "1"):** `Pass1FileManager.remove` deletes the word from the tracked book file. The owner's "data update" commit carries the deletion to `main`, and the server's nightly window (`git pull --ff-only`) brings it to the server. This direction already works, with up to a day's lag. **No change.**
- **Server (a contributor):** the tracked files are read-only there. `remove` appends the word to the contributor's own list `pass1_auto_removed_<user>.json` (`{book: [word, ...]}`) in the shared contributor folder `DPD_GUI2_DATA_DIR` (`/var/lib/dpd/contrib_data`). `read` hides only that contributor's OWN listed words. The list never leaves the server: the daily laptop pull copies only the kinds in `DELIVERED_KINDS`, and this kind is not one of them.

Result: a word a contributor finishes stays in the owner's queue on the laptop (so the owner can add it a second time) and stays visible to every other contributor on the server.

The owner chose (2026-11-12, option A of the Gate-1 fork) that the laptop **physically deletes** a contributor-finished word from its book file, so the deletion shows in the owner's git diff and his normal data commit carries it to the server.

## What it should do

Terms: a **removed list** is one `pass1_auto_removed_<user>.json` file, shape `{book: [word, ...]}`. The **list folder** is the folder that holds the removed lists: for a contributor `paths.pass1_auto_removed_path.parent` (on the server `DPD_GUI2_DATA_DIR`, always set by `add_contributor.sh`); for user "1" `paths.gui2_data_path` (`gui2/data/`), where the pull leaves its copies. A **valid** list value is a list whose items are all strings; anything else is ignored wherever a list is read in gui2.

1. **Server — hide words every contributor has finished.** New `Pass1FileManager` helper `_hidden_words(book) -> set[str]`: the union of the valid `book` values of every `pass1_auto_removed_*.json` in the list folder (a file that is not valid JSON or not an object is skipped; a non-list value or a non-string item is ignored). For a contributor, `_read_view` subtracts `_hidden_words(book)` instead of the own list. `_read_removed` stays own-list only, because `remove` uses it to append to the contributor's own file, and `remove` still writes only that file. For user "1" (`removed_path is None`) `_read_view` is unchanged and never globs.
2. **Laptop pull — fetch the lists.** In `scripts/server_contrib/contrib_pull.py` add `PULL_ONLY_KINDS: tuple[tuple[str, str], ...] = (("pass1_auto_removed_*.json", "pass1_auto_removed"),)` and make `glob_parts` iterate `DELIVERED_KINDS + PULL_ONLY_KINDS`. Every name consumer (`kind_of`, `user_of`, `select_names`, `ignored_names`, `check_scratch`, `remove_users`, `_summarise`) goes through `glob_parts`/`kind_of`, so this one change covers them; the name rules stay (`USER_PATTERN`, no sub-folders, 5 MB cap, regular file, no `added` in the name). `DELIVERED_KINDS` in `tools/contrib_entry.py` is **not** changed, because `contrib_push.py` copies every `DELIVERED_KINDS` file to the `contributions` branch with `git add -f`, and these lists are gitignored on purpose (`.gitignore:106`). `reconcile_all` (called by `prepare` on the scratch folder) uses `delivered_files`, which globs `DELIVERED_KINDS` only, so it ignores the lists; a test pins that.
3. **Laptop pull — check the lists.** `check_content` sends this kind to a new `_check_removed(text) -> str | None`: the text is JSON (`ValueError`/`RecursionError` → "not valid JSON"); the top level is an object; every key fullmatches `BOOK_KEY = re.compile(r"[a-z0-9&-]{1,32}")`; every value is a list; every item is a string that is non-empty, at most 200 characters, and matches no `CONTROL_CHARACTERS`. A failing file is handled like any bad contributor file today (that contributor's files are all skipped for the run and the reason is named in the status). The kind is not added to `JSON_KINDS`, so `_summarise` does not count its books as entries; it still counts the file in "N files" (intended).
4. **Laptop pull — delete the words from the book files.** New function `apply_pass1_removals(scratch: Path, repo: Path, source: str, log_path: Path) -> int` in `contrib_pull.py`, called in `_pull` right after `merge_all` (so only on the path that passed both `editor_running()` checks), returning the number of words deleted:
   - It reads the checked lists from `scratch` (`pass1_auto_removed_*.json`), and builds `{book: set(words)}` over all contributors.
   - A book key is applied only if it is a key of `gui2.books.sutta_central_books` AND `Gui2Paths(repo).gui2_data_path / f"pass1_auto_{book}.json"` already exists. Any other key (`text`, an unknown book, a book with no file) is skipped and logged. The key never reaches a path before both checks pass.
   - For an applied book it reads the file through `fm = Pass1FileManager(Gui2Paths(repo))` (laptop paths: `removed_path is None`, so writes are allowed and `read` hides nothing) and computes `present = words & fm.read(book).keys()`. Only if `present` is non-empty does it call `fm.update(book, ...)` to pop those words; `update` always rewrites its file, so a book with nothing present is never passed to it and stays byte-identical. The format stays `json.dump(..., ensure_ascii=False, indent=4)`, so the git diff shows only the deleted entries.
   - Exceptions are not caught here; the existing handler in `run` turns them into `failed: ...`. A re-run is safe: `merge_all` logs every merged line in `contrib_lines_merged.json`, and deleting an absent word is a no-op.
   - The pulled lists stay in `gui2/data/` after `copy_in` (gitignored), because item 5 reads them.
5. **Laptop Pass1 Auto — never bring a deleted word back.** New `Pass1FileManager.all_removed_words() -> set[str]`: every valid word of every book of every removed list in the list folder. `Pass1AutoController` gets `self.removed_words: set[str] = set()`, refilled in `load_auto_processed` (the one loader both the book run and the text run call) from `self.file_manager.all_removed_words()`, and `is_missing` also returns `False` for a word in `self.removed_words`. This is global across books on purpose: a word a contributor finished in one book is covered wherever it appears (in another book or in the text run), because their addition becomes a headword whose inflections hold it once the owner processes it. Without this guard, a word deleted in item 4 but not yet in `dpd.db` is found again and re-drafted.
6. **Trace.** `Status` gets `pass1_words_removed: int = 0`, set from item 4's return value, and `Status.text()` always prints `pass1_words_removed: <n>` after `ignored_names` (0 on a dry run, where item 4 does not run). `logs/contrib_pull.log` gets, per applied book with deletions, `pass1 removed <book>: <word>, <word>, ...` (words in `pali_sort_key` order), and per skipped key `pass1 skipped book key: {redact(key[:40], source)!r}`, the same way `_pull` logs an ignored name today.

**Owner rule (not code):** a word stays on a contributor's removed list for good (no pruning), so Pass1 Auto never re-drafts it and every pull deletes it again from a book file. To bring such a word back into the queue, remove it from that contributor's list on the server first.

## Assumptions & uncertainties

Verified from source on 2026-11-12 (see `egm/brief.md` for file:line evidence):
- The per-user files of every contributor live in one folder (`add_contributor.sh:52`, `Gui2Paths.for_user`).
- A contributor's save never writes the server db (`gui2/save_router.py`); it goes to `additions_<user>.json`, which reaches the laptop by the daily pull.
- `Pass1AutoController.add_word` writes one word at a time (`pass1_auto_controller.py:127-134`); Pass1 Auto never rewrites a whole book file. Its `is_missing` (`:371-381`) skips words already in the file, so a deleted word not yet in the db would be re-found.
- `get_auto_processed_dict` caches per book (`:115-120`), so `read` runs on book load, not on every save.
- The pull runs at most once a day with a success (`run`: "skipped: already done today") and never while gui2 is open (`editor_running`).
- No code globs `pass1_auto_*.json`; nothing else will mistake a copied `pass1_auto_removed_<user>.json` for a book file. (The CLAUDE.md advice "sweep drafts with `ls gui2/data/pass1_auto_*.json`" will now also list the removed lists; the sweeper must skip `pass1_auto_removed_*`.)

Accepted Goldfish findings (Gate 1, full text in `egm/gate1.md`):
- **Blocker (F1):** `_check_json` demands dict values and would reject the list shape, and a rejected file drops all of that contributor's files → item 3 gives the kind its own check.
- **Blocker (F4):** book keys come from a contributor's file → item 4 applies a key only after it matches a known book with an existing file.
- **Major (F3):** `DELIVERED_KINDS` also feeds the push → item 2 uses a pull-only allowlist.
- **Major (F5):** a Pass1 Auto re-run would re-draft a deleted word → item 5.
- **Major (F8):** no trace → item 6.
- **Nit (F2):** `_summarise` would count books as entries → item 3 keeps the kind out of `JSON_KINDS`.

Assumptions not verified:
- Contributors are approved people; a contributor who edits their list by hand could delete any draft word of a known book from the owner's queue. The owner sees every deletion in the git diff and in the pull log, and git holds the old file. Accepted as the cost of option A.
- A crash during the book-file write (non-atomic, as `Pass1FileManager.update` is today) could truncate a tracked file; git restores it. Not changed here.
- Contributors normally work on different books. A contributor whose page is already open keeps the snapshot taken at book load until they reload the book; another contributor's removal shows only then (Gate-1 F9, rejected).

## Constraints

- Server: never write the tracked `pass1_auto_*.json` files (existing rule, `PermissionError` in `Pass1FileManager`).
- Laptop pull: never touch `gui2/data/` while gui2 is open (existing rule). The new step runs only on the path that already reached `merge_all`.
- Do not change `DELIVERED_KINDS`, `contrib_push.py`, `contrib_reconcile.py` or `merge_contrib_files.py`.
- Project rules: modern type hints, `pathlib.Path`, no `sys.path` hacks; touch a file = own its `ruff check`, `ruff format` and pyright (`--project /dev/null` for `gui2/` and `tests/`); `just typecheck` before finishing.
- The plan's `## Model Strategy` table is always generated.

## How we'll know it's done

- A contributor test: with lists for `alice` and `bob` in one folder, `read("vv")` for alice hides both users' words; `remove` writes only alice's list.
- Pull tests: a good `pass1_auto_removed_alice.json` is selected, checked, copied into `gui2/data/`, and its words are deleted from `gui2/data/pass1_auto_vv.json`; a book with nothing to delete is byte-identical afterwards; the keys `../x`, `text`, an unknown book, and a known book with no file delete nothing and create no file; a list with a non-list value, a non-string word, or a bad key skips that contributor and names the reason; a skipped run (editor open) deletes nothing; the status shows `pass1_words_removed`; the push's file set is unchanged (`delivered_files` does not return the lists).
- Server read test: a list file that is not JSON, or holds `{"vv": "abc"}` or `{"vv": [1]}`, hides nothing and raises nothing; user "1" `read` ignores lists in `gui2/data/`.
- Reconcile test: `reconcile_all` on a scratch folder holding a removed list leaves it byte-identical.
- Pass1 Auto test: a word in any removed list (any book) is not `is_missing`; `load_auto_processed` refills `removed_words`.
- `uv run pytest tests/gui2 tests/scripts/server_contrib` passes; ruff, ruff format, pyright clean on every touched file; `just typecheck` clean.
- After the next real pull, the owner's `git diff gui2/data/pass1_auto_*.json` shows only removed entries, matching the `pass1 removed` lines in `logs/contrib_pull.log`.

## What's not included

- Pruning the removed lists (Gate-1 F6): pruning lets item 5's guard lapse and brings words back. The lists grow by a few words a day under the 5 MB cap.
- Hiding words already in `dpd.db` from Pass1 Add (Gate-1 F12): a different problem (words added by other routes); it does not cover a contributor's word, which is in no db until the owner processes it.
- Refreshing a contributor's open snapshot when another contributor finishes a word (F9), and the "deleted" wording on the server (F10).
- Any server-side git write, any change to the `contributions` branch flow.

## Review record

Goldfish reviews live in `egm/`: `brief.md` (request, facts, hypothesis); `gate1.md` (idea: 3 reviewers on pi DeepSeek flash, 14 deduplicated findings — 6 accepted, 7 rejected, 1 escalated and decided by the owner as option A); `gate2.md` (spec: 2 reviewers on pi DeepSeek flash, 17 findings — 12 accepted, 5 rejected, 0 escalated); `gate3.md` (plan readiness: 1 reviewer on pi DeepSeek flash, 7 findings — 6 accepted, 1 rejected).
