# Gate 2 — spec review

Backend: pi, DeepSeek API (`deepseek-flash`, thinking off, tools read/grep/find/ls), streamed as JSON events (kept outside the repo; final answers in `raw/*.md`). Reviewers: 2 (comprehension, design critic). Both exited 0. No backend switch.

## Disposition

| # | Finding | Severity | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| C1 | Item 5 never says where the removed-word set lives or that it is independent of `read` | Blocker | Accept | read `pass1_auto_controller.py:115-139`, `:371-381` | spec item 5: `removed_words`, `all_removed_words()`, load point |
| C2 | "Not rewritten" contradicts `update`, which always writes | Major | Accept | read `pass1_file_manager.py:101-119` | spec item 4: membership test before `update` |
| C3 | `Pass1FileManager(Gui2Paths(repo))` gets a folder, not a paths object | Major | Reject | constructor takes `Gui2Paths` (`pass1_file_manager.py:18`); `Gui2Paths(repo)` is a paths object | — |
| C4 | If `DPD_GUI2_DATA_DIR` is unset the glob hits the repo's `gui2/data` | Major | Reject | always set on the server (`add_contributor.sh:99`); unset only for local contributor testing, where `gui2/data` is the right folder | spec defines "list folder" |
| C5 | Pull-only allowlist shape and consumers unspecified | Major | Accept | read `contrib_pull.py:94-120`, `:245-304`, `:434-450` | spec item 2: `PULL_ONLY_KINDS`, `glob_parts` |
| C6 | Book-key regex not given literally | Major | Accept | — | spec item 3: `BOOK_KEY` literal, fullmatch |
| C7 | User "1" `read` must not glob | Nit | Accept | read `pass1_file_manager.py:47-51` | spec item 1 |
| C8 | `redact` arguments and cut order unstated | Nit | Accept | read `contrib_pull.py:416-425`, `:468-470` | spec item 6 |
| C9 | `text` lists never arrive usefully on the laptop | Nit | Reject | consistent with item 4's skip; nothing to change | — |
| D1 | Server `read` trusts any dict in a list file; a string value becomes a set of letters | Blocker | Accept | `set(removed.get(book, []))` on a string iterates characters (`pass1_file_manager.py:50`) | spec item 1: "valid" values only + test |
| D2 | `is_missing` guard is global across books, unstated | Blocker | Accept | read `is_missing` and both finders | spec item 5: stated and justified |
| D3 | Behaviour of `reconcile_all` on the new kind in scratch unstated | Major | Accept | `delivered_files` globs `DELIVERED_KINDS` only (`tools/contrib_entry.py:24-33`) | spec item 2 + reconcile test |
| D4 | A deletion error after `merge_all` marks the run failed and re-merges next time | Major | Reject | rerun is idempotent: `merge_all` logs merged lines (`merge_contrib_files.py:290-300`), deleting an absent word is a no-op; laptop paths cannot raise `PermissionError` | spec item 4 states it |
| D5 | An unpruned list deletes a word the owner re-drafts on purpose, every day | Major | Accept (documented) | follows from F6 | spec "Owner rule" |
| D6 | A `partial` run copies lists in without deleting; item 5 then hides an undeleted word | Major | Reject | a word still in the book file is already skipped by `is_missing` via `auto_processed_keys`, so item 5 changes nothing for it; the next pull deletes it | — |
| D7 | Dry-run output of the new status line unstated | Nit | Accept | `Status.text()` `:372-385` | spec item 6: always printed, 0 on dry run |
| D8 | A user with only a list shows "1 files, 0 entries" | Nit | Accept | `_summarise` `:434-450` | spec item 3: intended |

Totals: 17 findings — 12 accepted (C1, C2, C5, C6, C7, C8, D1, D2, D3, D5, D7, D8), 5 rejected (C3, C4, C9, D4, D6), 0 escalated.

## Raw findings

### g2_comprehension

## Restatement

Two machines share a Pass1 Auto queue of AI-drafted words, per book, in `gui2/data/pass1_auto_<book>.json` (git-tracked). On the laptop (user "1"), finishing a word deletes it from that file; the commit + nightly `git pull` carries it to the server. On the server a contributor cannot write those files, so finishing a word only appends it to `pass1_auto_removed_<user>.json` in `DPD_GUI2_DATA_DIR`. The spec: (1) server `read` hides words listed by *any* contributor; `remove` still writes only own list; (2) `contrib_pull.py` now copies those lists (pull-only allowlist, not `DELIVERED_KINDS`); (3) a new content check for the list shape; (4) after `copy_in`/second `editor_running`/`merge_all`, the pull deletes the listed words from the laptop book files via `Pass1FileManager`; (5) `Pass1AutoController.is_missing` also consults all local lists; (6) new status/log lines.

## Findings

**1. Blocker — hidden words vanish from `auto_processed_keys`, so item 5's premise breaks.** `gui2/pass1_auto_controller.py:108-113` builds `layout_auto_processed_dict` from `file_manager.read(book)` and `load_auto_processed` copies its keys into `auto_processed_keys`; `is_missing` (`:364`) tests that list. Once item 1 hides other contributors' words and item 4 deletes them from the laptop file, the word is simply gone from `read`/`auto_processed_keys`, and item 5 says to add it "also" — but the spec never says which list (`removed_path` set? `self.gui2p`?) or that the laptop list set and the read-removal set must be *different objects*. A fresh implementer will plausibly merge them and re-draft. The spec's item 5 words ("also returns False for any word in any `pass1_auto_removed_*.json` in the laptop's `gui2/data/` (all books of all lists)") never say where the set lives or that `removed_path` is `None` on the laptop, so the natural implementation `self.file_manager.read` has nothing to hide. **Fix:** name the set field, the globbing folder, and the load point (`load_auto_processed`, before `get_auto_processed_dict`), and state it is independent of `read`.

**2. Major — item 4's "no rewrite if nothing to delete" contradicts `update`.** `gui2/pass1_file_manager.py:131-145` always opens the file for `"w"` after the callback, even when the callback changed nothing. The spec says "A book with nothing to delete is not rewritten" and the test plan says "byte-identical". **Fix:** say the pull must test membership before calling `update` (or add a no-op path), and say who owns that branch.

**3. Major — item 4 says "Gui2Paths(repo)" but the pull already computed a data dir.** `contrib_pull.py:422-424` uses `Gui2Paths(repo).gui2_data_path`; the spec's `Pass1FileManager(Gui2Paths(repo))` receives the *folder*, not a paths object. **Fix:** spell the exact construction and that `removed_path` is `None` there by default (`gui2/paths.py:73`).

**4. Major — undefined "all lists in the contributor folder".** `removed_path` is `data / f"pass1_auto_removed_{user}.json"` (`gui2/paths.py:145`), i.e. `DPD_GUI2_DATA_DIR` when set. The spec says "the folder of `removed_path`" — but if `DPD_GUI2_DATA_DIR` is unset on the server, that is `gui2/data/` inside the repo, i.e. the tracked folder. **Fix:** state the precedence and that `read` must not glob the repo when the env var is missing.

**5. Major — item 2's allowlist mechanism is unspecified.** `contrib_pull.py:65-72` (`glob_parts`, `kind_of`) and `select_names` (`:277`) drive selection entirely off `DELIVERED_KINDS` in `tools/contrib_entry.py:11`. "Added to a pull-only allowlist inside `contrib_pull.py`" gives no data shape (tuple of `(pattern, kind)`? bare patterns?) nor says `glob_parts`/`kind_of`/`user_of`/`ignored_names`/`check_scratch`/`remove_users`/`_summarise` must consult it. **Fix:** name the constant, its type, and each consumer.

**6. Major — key charset `[a-z0-9&-]{1,32}` is unchecked against reality.** `gui2/books.py:90-320` has `vin1&2`, `nidd1&2`, `jaa` — fine — but the spec never says the pattern is anchored/fullmatch or that `-` must be escaped/last in the class; `a-z0-9&-` is valid but a naive regex author may write `[a-z0-9-&]` and create a range. **Fix:** give the literal regex.

**7. Nit — "hides only that contributor's OWN listed words" vs. item 1.** `gui2/pass1_file_manager.py:37-42` reads `self.removed_path`; item 1's "every `pass1_auto_removed_*.json` in the folder of `removed_path`" needs the *glob*, and user "1" reaches `_read_removed` only via `removed_path is not None`, so `read` must not glob when `None`. Not stated. **Fix:** one sentence.

**8. Nit — item 6's `redact` call.** `contrib_pull.py:378` `redact(text, source)` needs `source`; the spec says "through the existing `redact`" without saying which arg, and 40-char cut happens before or after redaction is unstated.

**9. Nit — `pass1_auto_text.json` is gitignored (`.gitignore:108`) so `book == "text"` lists in item 5 will never arrive from the server; item 4 says `text` is skipped. Consistent, but the spec never says the item-5 guard for `text` is therefore always empty on the laptop.**


### g2_design

I've read the spec and the six referenced sources. Findings:

**Blocker — Item 1 re-reads *every* list on every `read`, and a corrupt/foreign list widens the hide silently.**
`gui2/pass1_file_manager.py:34-41` reads only `self.removed_path`; the spec extends this to a glob, but never says what a `pass1_auto_removed_*.json` that is valid-JSON-but-not-the-shape (e.g. `{"vv": "alice"}` or `{"vv": [1]}`) does on the server. `_read_removed` returns `{}` on `JSONDecodeError` but passes any dict through. On the laptop a file that fails item 3's check is *skipped and the contributor dropped*, yet `copy_in` copies all scratch files after `remove_users` — the check is on the scratch copy, so a bad list still lands in `gui2/data/` only if it was attributed to a good user… which it isn't. Ambiguity: the spec never states whether `read` applies the same validation before trusting a list. An implementer will invent one. Fix: state that `read` runs the item-3 shape check per file and ignores a failing file entirely.

**Blocker — The same word in two books, or in `pass1_auto_text.json`.**
Items 4/5 key only on `[book]` for deletion (item 4 is book-scoped, correct), but item 5's `is_missing` guard is *global across all books* (`gui2/pass1_auto_controller.py:371-378` checks one flat `auto_processed_keys`). A word `alice` finished in `vv` is also hidden from the `dn` run and the text run (`is_missing` is the single gate for `find_missing_words_in_cst`/`_in_sutta_central`, `:394-412`). That is a behaviour change not stated anywhere: the spec says "any word in any `pass1_auto_removed_*.json`, all books of all lists" as if harmless. Say plainly that a removal in one book suppresses the word in the text run, and justify it.

**Major — `contrib_pull`'s `prepare` runs `reconcile_all` on the new kind.**
`scripts/server_contrib/contrib_pull.py:298-301` calls `prepare` unconditionally; `reconcile_all` (`contrib_pull.py:290`) was written for `DELIVERED_KINDS` files and the spec says nothing about how it treats an unrecognised `pass1_auto_removed_*` in scratch. Constraint line "Do not change `contrib_reconcile.py`" combined with "the file is checked and copied" means an implementer must discover whether reconcile crashes or no-ops. Fix: state the expected reconcile behaviour and add a test for it.

**Major — Ordering: item 4 runs after `merge_all` but the merge output is committed/consumed before the deletion.**
`contrib_pull.py:376-390`: `merge_all` runs, `status.lines_added` is computed, then the new step would delete words. If the deletion raises (e.g. `PermissionError` from `update`'s `_refuse_tracked_write`, or `OSError`), `run` catches it at `:453` and marks the run `failed` — but `merge_all` already appended contributor lines and `status.outcome` is overwritten, losing `lines_added`. Partial failure is presented as total failure, and `last_success` is never set, so the retry runs the merge again on already-merged lines. Fix: specify that the deletion failure is caught, counted, and reported as `pulled with problems`, not allowed to escape.

**Major — The word the owner re-drafts on purpose.**
The `< 200 chars` / `[a-z0-9&-]{1,32}` check in item 3 applies to *keys*, but word strings have no character-class rule, only length and control characters. Meanwhile item 4 deletes by exact key match against the book file's word keys. A list word with combining marks, an uppercase letter, or a leading space validates but never matches, and is silently counted as "nothing to delete" — the contributor's word reappears forever and item 5 also fails to hide it. Worse: if the owner *re-drafts* that word deliberately (item 5's own scenario), the pull re-deletes it on the next run, because the list is never pruned (explicitly out of scope). Result: an owner-re-added word is removed again every day and the owner sees it vanish in git. The spec's "accepted cost" paragraph covers a hostile contributor but not this benign path. Fix: state that a word deleted from the book file but present in a list blocks any future re-draft, and set an owner-facing rule (e.g. owner deletes the entry from the list).

**Major — Editor opens mid-run between the two checks and the deletion.**
Spec item 4 says "after the existing second `editor_running()` check". In `contrib_pull.py:378-386`, if `editor_running()` is true after `copy_in`, the function returns `partial` *before* `merge_all` — so the deletion never runs, but `copy_in` has already written the list into `gui2/data/`. Item 5's guard then hides the word from Pass1 Auto permanently while the book file still holds it: a word becomes invisible but undeleted, with no trace line. The spec's "skipped run deletes nothing" test covers the early skip only, not this window. Fix: specify that a `partial` run must leave `gui2/data/`'s lists out (or delete them) so item 5 cannot latch onto an unapplied list.

**Nit — `pass1_words_removed` placement and dry-run.**
`Status.text()` (`contrib_pull.py:330-345`) is emitted for dry runs too (`:466`). Spec item 6 doesn't say whether a `--dry-run` shows `pass1_words_removed: 0` or omits the line; both are defensible and an implementer must guess. Say which.

**Nit — `_summarise` file count.**
`contrib_pull.py:405-414` counts files per user with `user_of(path.name)`; a user with only a removed-list now reports "pulled 1 files, 0 entries", which reads oddly but is technically right. Item 3 only rules out counting entries. Confirm the count is intended.
