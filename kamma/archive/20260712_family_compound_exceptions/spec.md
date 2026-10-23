# Spec: family_compound_exceptions

## GitHub issue
None yet. Likely under #157 (project cleanup). Not confirmed. Do not write to GitHub.

## Origin
Spun off from `20260711_db_tests_triage` (Phase 3, `db_tests/gui/`). Triage of
`add_family_compound_neg.py`, `add_family_compound_su_dur.py` and
`add_family_compound_taddhita.py` showed they need a working "Exception" button.
That is design work, so it was kept out of the triage thread.

## Problem
The three scripts in `db_tests/gui/` are near-identical Flet editors. Each finds
headwords with an empty `family_compound` and lets the user fill it in. Each needs a
skip list ("exceptions"). None has an Exception button. Each keeps its list differently:

- `add_family_compound_neg.py`: hardcoded `neg_exceptions` (9 ids). Stale. The live test
  row `family_compound empty neg` holds 17 ids.
- `add_family_compound_taddhita.py`: `get_exceptions()` reads the row
  `family_compound empty taddhita` (32 ids) straight from `db_tests_columns.tsv`. Read only.
- `add_family_compound_su_dur.py`: same read for `family_compound empty su dur nir` (3 ids).

## Findings (read live 2026-10-23)

1. The four rows are real column tests, run by `DbTestManager`
   (`db_tests/db_tests_manager.py`). `error_test_each_single_row` skips any id in the
   row's `exceptions`. So the TSV row is the one skip list that both the gui2 tests tab
   and these scripts should share.
2. The draft of this spec proposed new JSON files seeded once from the TSV. That is
   wrong. An id excepted in a script would not reach the TSV row. The gui2 tests tab
   would flag that id again. Two lists would drift apart.
3. A sibling already does it the right way. `db_tests/gui/add_antonyms.py` loads
   `DbTestManager`, reads `internal_tests_list` for the row's `exceptions`, and its
   Exception button calls `manager.add_exception("antonym: empty", id)`. That call writes
   the id to the TSV row at once.
4. Live bug in `add_family_compound_su_dur.py`: `should_process()` matches
   `^(su|dur|sa|nir)\b `, but `get_exceptions()` reads only `su dur nir`. The row
   `family_compound empty sa` (3 ids: 56543, 56544, 88846) is never read. Those 3 words
   come back on every run.
5. Dead line in `add_family_compound_su_dur.py`: `i.lemma_clean not in self.exceptions`
   compares a string with a list of ints. It is always true.

## Decision
Follow the `add_antonyms.py` pattern. No new JSON files. No new `tools/paths.py` entries.
This replaces the earlier constraint "never write to `db_tests_columns.tsv`". That
constraint came from the parent thread's refactor scope. It does not apply to a feature
whose whole purpose is to add exceptions, and the gui2 tests tab already writes this file.

The user said one file or three does not matter. This design needs none.

## What to build

For each of the three scripts:

1. Create `DbTestManager()` in `DataAndLogic.__init__`, as `add_antonyms.py` does.
2. Read exceptions from `manager.internal_tests_list`, not from the TSV by hand.
3. Add an "Exception" `ft.TextButton` after "Pass" in the button row. Queue an
   `"exception"` action. In the main loop, call `lx.add_exception(i.id)`, then `break`.
4. Delete `from tools.tsv_read_write import read_tsv_dot_dict` and `get_exceptions()`
   where they exist.

Per script:

- **neg**: row `family_compound empty neg`. Delete the hardcoded `neg_exceptions`. Its 9 ids
  are a subset of the row's 17.
- **taddhita**: row `family_compound empty taddhita`.
- **su_dur**: read the union of rows `family_compound empty su dur nir` and
  `family_compound empty sa`. This fixes finding 4. Write a new exception to the `sa` row
  if `construction` starts with `sa `. Otherwise write to the `su dur nir` row. Remove the
  dead line from finding 5.

## Risks to check in review

- **Stale overwrite.** `save_tests()` rewrites the whole TSV from the manager's copy in
  memory. If gui2 is open and adds an exception while a script runs, the next button
  press in the script could overwrite it. `add_antonyms.py` has the same risk. Decide
  whether `add_exception` in the scripts should reload the file first
  (`manager.internal_tests_list = manager.load_tests()`), or whether to accept the risk.
- **TSV line endings.** gui2 and `save_tests()` write the file with CRLF. Git restores LF
  on commit. Check the diff of `db_tests/db_tests_columns.tsv` before commit. It already
  shows as modified in the working tree before this thread starts.
- **Script rules differ from the test rows.** The `sa` row skips words whose
  `meaning_1` contains "in reference to". The su_dur script does not. This thread does not
  change detection rules.

## Constraints
- Standard gates on every touched file: `ruff check --fix`, `ruff format`, `pyright`.
- The user runs the GUI. The agent never launches it.
- Do not change which words each script detects.

## Done when
- Each of the 3 scripts has an Exception button. Pressing it adds the id to the right TSV
  row at once.
- The su_dur script no longer shows the 3 reviewed `sa` words.
- No script reads the TSV by hand or holds a hardcoded list.
- Ruff and pyright are clean on all three files.
- The user confirms each button in the real GUI.
