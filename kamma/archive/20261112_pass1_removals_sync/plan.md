# Plan — Pass1 Auto: a word added on one machine leaves the queue on the other

**GitHub issue:** #215. Never comment on or close the issue. Never commit: the owner commits at the end (project rule). Spec: `kamma/threads/20261112_pass1_removals_sync/spec.md` — read it first; item numbers below refer to it.

## Architecture Decisions

- **Laptop deletes, server hides (owner decision, option A, 2026-11-12).** The pull physically deletes contributor-finished words from the laptop's tracked `gui2/data/pass1_auto_<book>.json`, so the owner sees them in his git diff and his data commit carries them to the server. The server keeps hiding words through the removed lists, now from every contributor, not one.
- **All list reading lives in `gui2/pass1_file_manager.py`.** Two new helpers (`_hidden_words(book)`, `all_removed_words()`) and one module-level parser `_valid_lists(folder)`; the controller and the pull use the manager, never parse the lists themselves. The pull re-checks shape separately (`_check_removed`) because it must reject a bad file loudly, where gui2 must ignore it quietly.
- **Pull-only file kind.** `PULL_ONLY_KINDS` in `scripts/server_contrib/contrib_pull.py`, not `DELIVERED_KINDS` in `tools/contrib_entry.py`, so `contrib_push.py`, `contrib_reconcile.py` and `merge_contrib_files.py` are untouched (spec item 2).
- **Book keys are untrusted.** A key is applied only if it is a `gui2.books.sutta_central_books` key AND the book file exists (spec item 4). The key is never joined into a path before that.
- **No pruning, no db check, no server git write** (spec "What's not included").
- **Not abstracted:** no shared validator between gui2 and the pull; the two rules differ in what they do on failure and are each a few lines.

## Constraints to preserve

- Project rules in `CLAUDE.md`: modern type hints, `pathlib.Path`, no `sys.path` hacks, no `__init__.py` re-exports, debug with `ic` not `print`.
- After editing a file, run in order: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, pyright, the related tests. For `gui2/` and `tests/` files use `uv run pyright --project /dev/null <file>` (plain pyright analyses nothing there). Touch a file = own all its lint and type errors, pre-existing ones included.
- Never run `git stash`, `git checkout -- <path>`, `git restore` or `git reset --hard` (shared working tree).
- Tests must never touch the real `gui2/data/` or the real shared files: use `tmp_path` and the existing `Setup`/`shared` fixtures in `tests/scripts/server_contrib/test_contrib_pull.py`.

## Model Strategy

| Phase | Tier | Suggested model | Reason |
|---|---|---|---|
| Planning (done) | Pro | Opus | design and review gates |
| Phase 1 — gui2 list reading and the Pass1 Auto guard | Fast | Sonnet | small, fully specified edits plus tests |
| Phase 2 — the pull fetches, checks and applies the lists | Pro | Opus | handles untrusted contributor input that ends in writes to tracked files |
| Phase 3 — docs and full verification | Fast | Sonnet | mechanical doc edits and running checkers |

## Phase 1 — gui2 list reading and the Pass1 Auto guard — *Fast*

- [x] 1.1 **Shared list parser and the server's union view (spec item 1).** In `gui2/pass1_file_manager.py`:
  - Add module function `_valid_lists(folder: Path) -> list[dict[str, list[str]]]`: for each `sorted(folder.glob("pass1_auto_removed_*.json"))`, load JSON with `encoding="utf-8"`; skip the file on `OSError`, `ValueError` (covers `JSONDecodeError`) or `RecursionError`, or if the top level is not a dict; keep only the entries whose key is a `str` and whose value is a `list` of which every item is a `str` (drop the whole entry otherwise). Return one cleaned dict per file.
  - Add method `_list_folder(self) -> Path`: `self.removed_path.parent` if `self.removed_path is not None`, else `self.gui2_data_path`.
  - Add method `_hidden_words(self, book: str) -> set[str]`: union of `lists.get(book, [])` over `_valid_lists(self._list_folder())`.
  - Change `_read_view`: when `self.removed_path is not None`, subtract `self._hidden_words(book)` (instead of the own list). When it is `None`, return the file unchanged and glob nothing.
  - Leave `_read_removed`, `remove`, `write`, `update` unchanged.
  - Tests in `tests/gui2/test_pass1_file_manager.py` (reuse `_contributor`, `_write_tracked`). The shared contributor folder is `tmp_path / "server_data"` (`_contributor` sets `DPD_GUI2_DATA_DIR` to it but does not create it): `mkdir(parents=True, exist_ok=True)` it, then write bob's list as `tmp_path / "server_data" / "pass1_auto_removed_bob.json"` and alice's as `pass1_auto_removed_alice.json` in the same folder:
    - `test_contributor_read_hides_every_contributors_words`: alice `read("vv")` hides a word in alice's list AND a word in bob's list; a word under another book key in bob's list stays visible.
    - alice `remove("vv", "x")` changes only `pass1_auto_removed_alice.json`; bob's file is byte-identical.
    - a list file holding `{not json`, `{"vv": "abc"}`, or `{"vv": [1]}` hides nothing and raises nothing (for `"abc"`, a word `"a"` in the tracked file stays visible).
    - user "1" (`_manager`) with a list written to `tmp_path / "gui2" / "data" / "pass1_auto_removed_alice.json"` (that is `fm.gui2_data_path`) returns the full file from `read`.
  → verify: `uv run pytest tests/gui2/test_pass1_file_manager.py -q` all pass; then temporarily change `_read_view` back to the own list only (`set(self._read_removed().get(book, []))`), run `test_contributor_read_hides_every_contributors_words`, confirm it fails on bob's word, then restore it in the same command; record the result in this plan.

- [x] 1.2 **`all_removed_words()` and the Pass1 Auto guard (spec item 5).**
  - In `gui2/pass1_file_manager.py` add `all_removed_words(self) -> set[str]`: every word of every book of `_valid_lists(self._list_folder())`.
  - In `gui2/pass1_auto_controller.py`: in `__init__` add `self.removed_words: set[str] = set()` beside `self.unknown_words`; in `load_auto_processed` add `self.removed_words = self.file_manager.all_removed_words()` before the dict load; in `is_missing` add `and word not in self.removed_words` to the condition. Add a one-line WHY comment in `is_missing`: a word a contributor finished is deleted from the book file by the pull but is in no db until the owner processes the addition.
  - In `tests/gui2/test_pass1_auto_controller.py`, `make_controller` builds the controller with `object.__new__`, so add `ctrl.removed_words = set()` there or every existing test that reaches `is_missing` raises `AttributeError`.
  - New tests in the same file: with `ctrl.removed_words = {"xyz"}`, `ctrl.is_missing("xyz")` is `False` and `ctrl.is_missing("abc")` is `True`. In `tests/gui2/test_pass1_file_manager.py`: `all_removed_words()` for user "1" returns the words of two list files in `gui2/data` across two books.
  → verify: `uv run pytest tests/gui2/test_pass1_auto_controller.py tests/gui2/test_pass1_file_manager.py -q` all pass.

- [x] 1.3 **Phase 1 checks.** Run ruff check, ruff format and `uv run pyright --project /dev/null` on `gui2/pass1_file_manager.py`, `gui2/pass1_auto_controller.py` and both test files; then `uv run pytest tests/gui2 -q`.
  → verify: zero ruff and pyright errors on all four files; `tests/gui2` passes with the same number of skips/fails as before the phase (note any pre-existing failure here).

## Phase 2 — the pull fetches, checks and applies the lists — *Pro*

All edits in `scripts/server_contrib/contrib_pull.py`; tests in `tests/scripts/server_contrib/test_contrib_pull.py` unless named.

- [x] 2.1 **Fetch and check the lists (spec items 2 and 3).**
  - Add near `JSON_KINDS`: `PULL_ONLY_KINDS: tuple[tuple[str, str], ...] = (("pass1_auto_removed_*.json", "pass1_auto_removed"),)` with a WHY comment (the push copies every `DELIVERED_KINDS` file to the `contributions` branch; these lists are gitignored), and `BOOK_KEY = re.compile(r"[a-z0-9&-]{1,32}")`, `MAX_WORD_LENGTH = 200`.
  - `glob_parts`: iterate `(*DELIVERED_KINDS, *PULL_ONLY_KINDS)`.
  - `check_content`: before the `JSON_KINDS` branch, `if kind == "pass1_auto_removed": return _check_removed(text)`.
  - Add `_check_removed(text: str) -> str | None`, returning these exact reasons: `"not valid JSON"` (`ValueError`/`RecursionError`), `"JSON top level is not an object"`, `"a book name is not allowed"` (key not a `str` or no `BOOK_KEY.fullmatch`), `"a book's words are not a list"`, `"a word is not text"` (item not `str`, empty, longer than `MAX_WORD_LENGTH`, or `CONTROL_CHARACTERS.search(item)`).
  - Tests: add `"pass1_auto_removed"` to `GOOD_NAMES` (`"pass1_auto_removed_alice.json"`) and `GOOD_CONTENT` (`json.dumps({"vv": ["saṅkha"], "nidd1&2": ["upāgato"]}, ensure_ascii=False).encode()`), so the parametrized name and content tests cover it. New tests: each of the five reasons, one input each (`b'{"a": '`, `b'[]'`, `b'{"../x": []}'`, `b'{"vv": "abc"}'`, `b'{"vv": [""]}'`); `delivered_files(folder)` on a folder holding `pass1_auto_removed_alice.json` returns no such path (push set unchanged); in `tests/scripts/server_contrib/test_contrib_reconcile.py`, `reconcile_all(repo, folder)` leaves a removed list in `folder` byte-identical.
  → verify: `uv run pytest tests/scripts/server_contrib/test_contrib_pull.py tests/scripts/server_contrib/test_contrib_reconcile.py -q` all pass.

- [x] 2.2 **Apply the lists to the laptop book files, and trace (spec items 4 and 6).**
  - Imports: `from gui2.books import sutta_central_books`, `from gui2.pass1_file_manager import Pass1FileManager`, `from tools.pali_sort_key import pali_sort_key`.
  - Add `apply_pass1_removals(scratch: Path, repo: Path, source: str, log_path: Path) -> int`:
    1. `wanted: dict[str, set[str]] = {}`; for each `sorted(scratch.glob("pass1_auto_removed_*.json"))` load JSON (already checked by `check_scratch`) and union each key's words into `wanted[key]`.
    2. `paths = Gui2Paths(repo)`; `fm = Pass1FileManager(paths)`; `removed = 0`.
    3. For each `book in sorted(wanted)`: if `book not in sutta_central_books` or not `(paths.gui2_data_path / f"pass1_auto_{book}.json").is_file()`: `_log(log_path, f"pass1 skipped book key: {redact(book[:40], source)!r}")` and continue. (Check membership first, so a bad key never reaches the path join. `redact` is kept for parity with the `ignored name` log line, so no log line ever bypasses it.)
    4. `present = wanted[book] & fm.read(book).keys()`; if empty, continue (never call `update`, which always rewrites).
       A book file that is not valid JSON reads as `{}` (`_read_file`), so nothing is deleted and `update` is never called; that is intended, since the word stays on the list and the next pull retries.
    5. `fm.update(book, lambda data: [data.pop(word, None) for word in present])`; `removed += len(present)`; `_log(log_path, f"pass1 removed {book}: {', '.join(sorted(present, key=pali_sort_key))}")`.
    6. Return `removed`. Catch nothing (spec item 4).
  - `Status`: add `pass1_words_removed: int = 0`; in `text()` add `f"pass1_words_removed: {self.pass1_words_removed}"` right after the `ignored_names` line.
  - `_pull`: right after the `merge_all(...)` call and before `status.lines_added` is computed, add `status.pass1_words_removed = apply_pass1_removals(scratch, repo, source, log_path)`. This places it after both `editor_running()` returns and after the dry-run return, so a skipped, partial or dry run never deletes; no extra editor check is added.
  - Tests (full runs through `setup.go()`; write the book file as `json.dumps(data, ensure_ascii=False, indent=4)` into `setup.data`, the server list into `setup.server`):
    - a list `{"vv": ["a"]}` and book file `{"a": {...}, "b": {...}}` → book file now holds only `"b"`, in the same format; `status.pass1_words_removed == 1`; the log holds `pass1 removed vv: a`; `setup.data / "pass1_auto_removed_alice.json"` exists.
    - a listed book whose file holds none of the words → book file byte-identical, count 0.
    - keys `"text"`, `"zz"` (unknown) and `"dn"` with no `pass1_auto_dn.json` → no file is created or changed, the log holds three `pass1 skipped book key:` lines.
    - two contributors listing the same word in `vv` → it is removed once, count 1.
    - editor open from the start (`monkeypatch.setattr(contrib_pull, "editor_running", lambda: True)`) → the book file is byte-identical.
    - editor opens after `copy_in` (copy the pattern of `test_an_editor_that_opens_before_the_merge_gives_a_partial_run`) → book file byte-identical, outcome `partial`.
    - a bad list (`{"vv": "abc"}`) beside a good `additions_alice.json` → alice skipped with `a book's words are not a list` in `status.contributors`, book file byte-identical.
    - dry run → book file byte-identical and the returned `status.text()` contains `pass1_words_removed: 0` (a dry run writes no status file; assert on the returned object).
  → verify: `uv run pytest tests/scripts/server_contrib -q` all pass; then temporarily replace the body of `apply_pass1_removals` with `return 0`, confirm the deletion tests fail (record the count here), and restore it in the same command.

- [x] 2.3 **Phase 2 checks.** Run `uv run ruff check --fix`, `uv run ruff format` and `uv run pyright` on `scripts/server_contrib/contrib_pull.py` (plain pyright works there); ruff and `uv run pyright --project /dev/null` on the two test files.
  → verify: zero errors on all three files; `uv run pytest tests/scripts/server_contrib tests/gui2 -q` passes.

## Phase 3 — docs and full verification — *Fast*

- [x] 3.1 **Docs.**
  - `scripts/server_contrib/README.md`, section "The daily pull": after step 5 add a step: "It also copies each contributor's `pass1_auto_removed_<user>.json` (the Pass1 Auto words they finished) and deletes those words from your `gui2/data/pass1_auto_<book>.json` files, so they show in your git diff. Your next data commit takes them off the server's queue. A word stays on the contributor's list for good; to bring it back into the queue, remove it from their list on the server first." Add `pass1_words_removed` to the "Reading `outcome:`" bullet as one sentence.
  - `kamma/tech.md`: one dated bullet (2026-11-12) under Constraints, after the "Contributor pull (2026-11-04)" bullet, stating spec items 1, 2, 4 and 5 in three sentences and pointing to this thread.
  - `CLAUDE.md` "Data" bullet that says to sweep drafts with `ls gui2/data/pass1_auto_*.json`: add "skip `pass1_auto_removed_*`, the pulled contributor lists".
  → verify: `rg -n "pass1_auto_removed" scripts/server_contrib/README.md kamma/tech.md CLAUDE.md` shows one hit in each file.

- [x] 3.2 **Whole-repo checks.**
  → verify: `just typecheck` reports no new errors; `uv run pytest tests/gui2 tests/scripts/server_contrib tests/tools -q` passes; `git status --porcelain` lists only this thread's files (`gui2/pass1_file_manager.py`, `gui2/pass1_auto_controller.py`, `scripts/server_contrib/contrib_pull.py`, the four test files, the three docs, this thread folder) plus files that were already dirty before the thread (`gui2/data/additions_bdhrs.json` at the start).

- [ ] 3.3 **Owner check after the next real pull (owner, after review).** The owner closes gui2 and runs `cd <repo root> && just contrib-pull`.
  → verify: `logs/contrib_pull_status.txt` shows `pass1_words_removed: <n>`; `git diff --stat gui2/data/pass1_auto_*.json` shows only deletions, and the deleted words match the `pass1 removed` lines in `logs/contrib_pull.log`. (Note: as of 2026-11-10 the server has test users only, so `n` may be 0.)
