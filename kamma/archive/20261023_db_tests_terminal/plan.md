# Plan: db_tests GUI to terminal scripts

**Thread:** 20261023_db_tests_terminal
**Spec:** `spec.md` in this folder. Read it first.
**GitHub issue:** none given (commits use `#157`, assumption). Never write to GitHub.

## Architecture Decisions (do not relitigate)

- Six standalone scripts in `db_tests/single/`. No shared module. The user rejected a helper (2026-10-23): "six totally separate tests".
- Model each script on the other interactive tests in `db_tests/single/` (`test_digu.py`, `test_verb_grammar_sync.py`): `pr.tic()`, `pr.yellow_title(...)`, `pr.summary(...)`, yellow-letter options line with `print(end="")` and `input()`, `pr.toc()`, `main()`, `if __name__ == "__main__"`.
- Keep the old classes' logic (selection, proposal, commit, exception) by copying it out of `db_tests/gui/*.py`. Drop all `ft.*`, `UiManager`, queues, `time.sleep`.
- Escape database text with `rich.markup.escape` before printing. Meanings can contain `[`.
- Prompt: `input()` after a yellow-letter options line. Enter commits the proposed value, typed text commits that text. `e`/`p`/`q` reserved. Empty with nothing proposed = pass.
- Screen layout: copy the house style exactly (see the spec). No panels, no new colours.
- A script's `main()` must return when the user quits, so `run_all_tests.py` moves on.
- Each script has its own JSON file with the same stem (user rule, 2026-10-23). Move the two existing JSON files with plain `mv` (not git).
- Option B (user, 2026-10-23): the four TSV-based scripts keep exceptions in their own JSON file (sorted id list), seeded once from the live TSV rows. They never read or write the TSV afterwards. See the spec.
- User change (2026-10-23): `add_antonyms_sync` drops `update_history`; proposed antonyms in bold cyan on their own line. Overrides task 3.2's keep-list and the "no new colours" rule for that line.
- Do all work at the end of a phase in one go. No commits. Report only.

## Phase 1 — Move data files and paths — *Fast*

- [x] 1.1 Move `db_tests/gui/add_antonyms_sync_dict.json` to `db_tests/single/add_antonyms_sync.json` (renamed to match its script) and `db_tests/gui/add_hyphenations.json` to `db_tests/single/add_hyphenations.json`.
  → verify: `ls db_tests/single/add_antonyms_sync.json db_tests/single/add_hyphenations.json` lists both; the first still has the uncommitted edit (`wc -c` equals 23016 or more).
- [x] 1.2 Edit `tools/paths.py` lines 142-148: `add_antonyms_sync_dict` points at `db_tests/single/add_antonyms_sync.json`, `add_hyphenations_config_path` at `db_tests/single/add_hyphenations.json`, comment `# db_tests/single`.
  → verify: `uv run ruff check tools/paths.py && uv run pyright tools/paths.py` clean; `rg -n "db_tests/gui" tools/paths.py` finds nothing.

## Phase 2 — The three family compound scripts — *Fast*

- [x] 2.1 Write `db_tests/single/add_family_compound_neg.py` from `gui/add_family_compound_neg.py` (see the spec table). Exceptions: `add_family_compound_neg.json`, a sorted id list, seeded once from the live TSV row `family_compound empty neg` (read the file; do not type ids). Drop `DbTestManager`.
  → verify: `uv run ruff check --fix`, `ruff format`, `pyright` on the file are clean. The yellow heading and the options line (e, p, q, Enter) appear before the first prompt. Start it with `printf 'q\n' | uv run python -m db_tests.single.add_family_compound_neg`: it shows item 1 and exits without a traceback. (Never `e` or a commit.)
- [x] 2.2 Write `add_family_compound_su_dur.py` (sorted by `pali_sort_key`). One `add_family_compound_su_dur.json`, seeded with the union of the TSV rows `family_compound empty su dur nir` and `family_compound empty sa`.
  → verify: same lint and `printf 'q\n'` run as 2.1.
- [x] 2.3 Write `add_family_compound_taddhita.py` and `add_family_compound_taddhita.json`, seeded from the TSV row `family_compound empty taddhita`.
  → verify: same lint and `printf 'q\n'` run as 2.1.
- [x] 2.4 Phase check: `rg -n "flet|ft\.|DbTestManager" db_tests/single/add_family_compound_*.py` finds nothing. Check each seeded JSON with a scratchpad script that loads the JSON and the TSV row(s) and asserts the JSON list equals the sorted TSV ids.
  → verify: the `rg` prints nothing; the scratchpad check prints equal for all three files.

## Phase 3 — The two antonym scripts — *Fast*

- [x] 3.1 Write `add_antonyms.py` and `add_antonyms.json` (seeded from the TSV row `antonym: empty`; spec table; show the 20 shortest words starting with the proposal, from the four wordlists in `ProjectPaths`).
  → verify: lint clean; `printf 'q\n' | uv run python -m db_tests.single.add_antonyms` shows item 1 and exits. `add_antonyms.json` equals the sorted ids of the TSV row `antonym: empty`. `db_tests_columns.tsv` is not changed by this thread.
- [x] 3.2 Write `add_antonyms_sync.py`. Keep `load/save_antonym_exceptions_dict`, `update_exceptions`, `commit_to_db`, `update_history`, `make_dest_antonyms`. Build the proposal from `dest.antonym.split(", ")`, never `dest.antonym_list`. No per-source print.
  → verify: lint clean; `printf 'q\n' | uv run python -m db_tests.single.add_antonyms_sync` shows candidate 1 in under 15 s and exits.
- [x] 3.3 Test the fix in `tests/db_tests/single/test_add_antonyms_sync.py`: in-memory SQLite, two sources naming one twin, call `make_dest_antonyms` and `commit_to_db` twice; assert the twin's `antonym` holds both lemmas. Use `uv run pyright --project /dev/null` for the test file.
  → verify: `uv run pytest tests/db_tests/single/test_add_antonyms_sync.py` passes. Then temporarily change `make_dest_antonyms` back to `dest.antonym_list`, rerun, expect the test to fail on the missing lemma (not on an import error), and restore at once in the same command.

## Phase 4 — The hyphenations script — *Fast*

- [x] 4.1 Write `add_hyphenations.py`: keep the `Data` class logic; replace `State`, `Controller`, `Gui` with a `main()` loop and the prompt in the spec. Stop when `max_length` reaches 0.
  → verify: lint clean; `printf 'q\n' | uv run python -m db_tests.single.add_hyphenations` shows item 1 and exits. `add_hyphenations.json` is unchanged afterwards (`wc -c` before and after).

- [x] 4.2 (user change) Hyphenations integration: regenerate speech marks once on exit if anything was committed; re-flag approved words whose text has a different form, listing the approved spelling. Test in `tests/db_tests/single/test_add_hyphenations.py`.
  → verify: lint clean; test passes; with the change reverted the test fails; `printf 'q\n'` run shows item 1 and leaves `add_hyphenations.json` and `speech_marks.json` unchanged.

- [x] 4.3 (user change, widened) Auto-approve words with one marked form, with or without the plain word. Tests in `tests/db_tests/single/test_add_hyphenations.py` (stub the save so no real file is written).
  → verify: lint clean; tests pass; with the change reverted they fail; `printf 'q\n'` run prints the auto-approved count and `add_hyphenations.json` is NOT used by the run beyond that (check the diff size reported to the user).

- [x] 4.4 (bug) List every marked form of a word; re-flag approved words that have a differing apostrophe-only form. Tests added to `test_add_hyphenations.py`.
  → verify: lint clean; tests pass; reverted they fail; read-only preview shows the word `nevasaññānāsaññāyatanasaṃyojane` back in the list with two numbered forms.

- [x] 4.5 (user change) On 0 replacements, print the forms plainly and wait for a key. No helper, no test (user rejected the raw-text version).
  → verify: lint clean; tests pass; a read-only scratchpad call prints the forms plainly.

- [x] 4.6 (user change, revised) After a pick, if an unchosen form has a bold tag inside it, show the forms plainly and wait for a key. The upfront skip was removed. Helper `has_bold_tag_inside` tested in `test_add_hyphenations.py`.
  → verify: lint clean; tests pass; reverted they fail; read-only scratchpad call on the live data counts how many listed words take the skip path.

## Phase 5 — Remove the GUI and fix references — *Fast*

- [x] 5.1 Delete `db_tests/gui/` (after 1.1, only the scripts, `main.py`, `README.md`, `__pycache__` remain).
  → verify: `ls db_tests/gui` fails; `ls db_tests/single/add_antonyms_sync.json db_tests/single/add_hyphenations.json` still lists both files.
- [x] 5.2 `justfile`: replace `db-tests-gui` with six recipes, each `cd`-free `uv run python -m db_tests.single.<name>` with a comment line. Use the names `add-antonyms`, `add-antonyms-sync`, `add-fc-neg`, `add-fc-su-dur`, `add-fc-taddhita`, `add-hyphenations`.
  → verify: `just --list | rg "add-"` shows the six.
- [x] 5.3 `db_tests/run_all_tests.py`: drop `LAST_MODULE` and the Flet words in the docstring; `find_modules` returns `[FIRST_MODULE, *singles]`.
  → verify: `uv run python db_tests/run_all_tests.py --list` lists the six new modules and no `gui`; ruff and pyright clean on the file.
- [x] 5.4 Update `db_tests/README.md` line 17, `docs/technical/project_folder_structure.md` (tree line 19, bullet line 108), and the docstrings in `db_tests/db_tests_manager.py` line 5, `tools/goldendict_tools.py` line 2, `tools/negative_to_positive.py` line 2.
  → verify: `rg --hidden -n -g '!.git' -g '!graphify-out' -g '!kamma' "db_tests[./]gui|db_tests/gui" .` prints nothing.

## Phase 6 — Final checks — *Fast*

- [x] 6.1 Run `just typecheck`, `uv run pytest tests/db_tests tests/tools`, and `rg -n "import flet" db_tests`.
  → verify: typecheck clean; tests pass; the `rg` finds nothing. Note any test that failed before this thread.
- [x] 6.2 Run each of the six with `printf 'q\n'` and read the first screen: the yellow heading matches the spec table and the options line lists every key. Then hand the user one command per script, each as `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && just <recipe>`, and ask them to run `add-antonyms-sync` live and compare with the old GUI's answers.
  → verify: the user confirms.
- [x] 6.3 Ask the user whether to run `coderabbit review --agent`. Suggest a commit message only: `#157 db_tests: replaced gui with terminal scripts, fixed antonym sync cache`.
  → verify: user answers.
