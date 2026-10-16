# Plan: agent nouns family set

Spec: `kamma/threads/20261016_agent_nouns_set/spec.md`

## Architecture Decisions
- The data change is a one-off script in `scripts/fix/`. It copies the shape of
  `scripts/fix/sort_family_sets.py`: query, print old → new, ask y/n, commit.
  The user runs it, with gui2 closed.
- The script reuses `sort_family_set` from `scripts/fix/sort_family_sets.py` for
  ordering. It writes no new sort code, so the ordering matches gui2's "Add Set".
- The script's match (`pos == "masc"`, non-empty `meaning_1`, `\bagent\b` in
  `grammar`) is the same as the new db_test. So after one run, the test is clean.
- The script appends the TSV row with `csv` QUOTE_ALL. It does not go through
  `DbTestManager.save_tests`, which would re-serialise every row and risk
  diff noise. The git diff must show exactly one added line.
- Nothing is generalised. The set name is a module constant, not a CLI argument.

## Phase 1 — Add-set script
- [x] Write `tests/scripts/fix/test_add_agent_nouns_set.py` for a pure function
  `add_set(family_set: str, set_name: str) -> str`. Cases:
  empty → `"agent nouns"`; `"occupations"` → `"agent nouns; occupations"`;
  `"types of ascetics; types of monastics"` keeps both and adds the new set in
  order; a value that already has `agent nouns` comes back unchanged (no duplicate);
  `"epithets of the Buddha"` sorts case-insensitively.
  → verify: `uv run pytest tests/scripts/fix/test_add_agent_nouns_set.py` fails
  with ImportError (no module yet).
  → result: `ModuleNotFoundError: No module named 'scripts.fix.add_agent_nouns_set'`.
- [x] Write `scripts/fix/add_agent_nouns_set.py`:
  - `SET_NAME = "agent nouns"`.
  - `add_set`: if `set_name` is already in the split parts, return the value
    unchanged. Else return `sort_family_set(f"{family_set}; {set_name}")`.
  - `main()`: `get_db_session(ProjectPaths().dpd_db_path)`. Query `DpdHeadword` where
    `pos == "masc"` and `meaning_1 != ""`. Keep rows where
    `re.search(r"\bagent\b", i.grammar)`. Compute `add_set`, and assign only when
    the value changed. Print the counter, id, lemma_1, old (red) and new (green)
    for each row. Print the total. Ask y/n, then commit or don't.
  - Module docstring: purpose, "CLOSE gui2 BEFORE RUNNING", run command.
  → verify: the tests from the task above pass. Then revert-check: replace the
  `add_set` body with `return family_set` and run the tests. Expect every test
  except the "already present" one to fail. Restore in the same command, and
  record the counts here.
  → result: 5 passed. Body revert: 4 failed, 1 passed ("already present", as expected).
    A second revert removing only the duplicate guard: that test fails, 1 failed / 4 passed.
    Restored and byte-checked with `cmp`; 5 passed.
- [x] Lint gate on both new files: `uv run ruff check --fix`, `uv run ruff format`,
  `uv run pyright` (the test file needs `--project /dev/null`, see tech.md).
  → verify: all clean, and pyright `filesAnalyzed` > 0 for the test file.
  → result: ruff clean, format unchanged, pyright 0 errors with filesAnalyzed 1 on each.
- [x] Phase check: `uv run pytest tests/scripts/fix/` and `just typecheck`.
  → verify: all pass, and pyrefly shows no new errors.
  → result: 49 passed (44 baseline + 5 new); pyrefly 0 errors.

## Phase 2 — db_test row
- [x] Append one row to `db_tests/db_tests_columns.tsv` with a scratchpad
  Python script (`csv.writer`, `delimiter="\t"`, `quoting=csv.QUOTE_ALL`,
  `newline=""`, utf-8), with the values from spec item 2, in header column order.
  → verify: `git diff --stat db_tests/db_tests_columns.tsv` shows 1 insertion and
  0 deletions. Every line has 26 tab-separated fields. `file` still reports LF.
  → result: 1 insertion, 0 deletions. `csv.reader` gives 26 fields on all 552 rows; `file` reports no CRLF.
    Later, at 05:47, a gui2 test-exception save (not this thread) rewrote the file with CRLF and added
    exception 47140 to "source_1 -". The diff is now 2+/1-. git `text=auto` restores LF on commit.
    (A raw `awk` line count flags lines 464–465: the existing "sanskrit no plus" row has a newline inside a quoted field, already so at HEAD.)
- [x] Phase check (read-only): with a scratchpad script, load `DbTestManager()`.
  Assert `integrity_ok`. Find the new test by name, and run
  `run_test_on_all_db_entries` over all `DpdHeadword` in the live db.
  → verify: integrity OK. The new test fails on exactly 676 headwords. The
  existing `grammar: masc aka no agent` still fails on 64 (unchanged).
  Record both counts here.
  → result: integrity_ok True; new test 676; `grammar: masc aka no agent` 64.
    Run as `PYTHONPATH=. uv run <scratchpad>/check_rule.py` from the repo root.

## Phase 3 — Apply to the live db (user runs)
- [x] Hand the user this command, with gui2 closed:
  `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && uv run scripts/fix/add_agent_nouns_set.py`
  → verify: the user reports "676 rows to update" and commits with `y`.
  → result: user ran it 2026-10-16: "676 rows to update", answered y, "committed to db".
    (User asked why close gui2: gui2's save writes every on-screen field back, so a masc agent open
    during the run and saved afterwards would lose the set; its set dropdown loads once at start.)
- [x] Phase check (read-only):
  `sqlite3 -readonly dpd.db "select count(*) from dpd_headwords where family_set regexp '\bagent nouns\b'"`
  returns 676. Re-run the Phase 2 check script, and the new test fails on 0.
  A count of finished masc agents whose family_set contains a set other than
  `agent nouns` returns 250, so no existing set was lost.
  → verify: 676 / 0 / 250, recorded here.
  → result: 676 / 0 / 250. No row carries the set twice. integrity_ok True; aka test still 64.
    Occupations: 157 finished rows now `agent nouns; occupations`; the 18 unfinished keep `occupations` alone (out of scope).

## Smoke gate
- `uv run pytest tests/ -q`: 2086 passed, 12 deselected. `just typecheck`: 0 errors.
- NOTICED — NOT TOUCHING: `db_tests/db_tests_columns.tsv` row "sanskrit no plus" has a newline inside a quoted field (present at HEAD).
