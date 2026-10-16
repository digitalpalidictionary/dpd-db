# Agent nouns family set

## Overview
Add a new family set, `agent nouns`, to DPD. Put it on every finished masculine agent
noun in `dpd.db`. Add a db_test so that future masc agent nouns must carry the set.

## Current behaviour (verified against live dpd.db, 2026-10-16)
- 813 headwords have `pos = 'masc'` and the word `agent` in `grammar`
  (`\bagent\b` and `LIKE '%agent%'` give the same 813).
- 676 of these have a non-empty `meaning_1`. 137 are unfinished drafts.
- 250 of the 676 already have a `family_set` (mostly `occupations` 175,
  `types of monastics`, `types of ascetics`, `names of deities`, `animals`).
  These existing sets must be kept.
- No headword has `agent` anywhere in `family_set` today. The set is new.
- Other parts of speech also carry `agent` (fem 53, adj 1, nt 1). They are out of scope.
- `family_set` is a `"; "`-separated list in case-insensitive English order.
  Both the gui2 "Add Set" dropdown (`gui2/dpd_fields_family_set.py`) and
  `scripts/fix/sort_family_sets.py::sort_family_set` use that order.
- The family-set table (`db/families/family_set.py`) and the gui2 set
  dropdown (`gui2/database_manager.py::get_all_family_sets`) both build their
  set list from headword data. No hardcoded set list exists (checked with `rg`).
  So the new set needs no code change outside this thread.
- `db_tests/db_tests_columns.tsv` is a QUOTE_ALL TSV, 26 columns, read and
  written by `db_tests/db_tests_manager.py`. Criteria are ANDed.
  `contains word` wraps the string in `\b…\b`.
- The second requested test already exists as the last row of the tests file:
  `"grammar: masc aka no agent"` (pos equals masc, grammar does not contain
  agent, suffix contains `aka|\*aka`). It was committed in a "data update"
  commit. It fires on 64 words today, many of them not agents (kaṇṭaka "thorn",
  ovaraka "room", makasa "mosquito", modaka "sweet"). The user decided to leave it
  as is. The editor clears those hits in gui2.

## What it should do
1. A one-off script `scripts/fix/add_agent_nouns_set.py` (pattern:
   `scripts/fix/sort_family_sets.py`) does this:
   - Selects headwords with `pos == "masc"`, non-empty `meaning_1`, and
     `re.search(r"\bagent\b", grammar)`. This is the same match as the new db_test.
   - Adds `agent nouns` to `family_set` without removing any existing set.
     It re-sorts with the existing `sort_family_set`. A row that already has the
     set stays unchanged.
   - Prints old → new for each changed row and the total. It asks y/n before
     it commits.
   - The user runs it with gui2 closed. The agent does not run it.
2. Add one new row to `db_tests/db_tests_columns.tsv`:
   - name: `family_set: masc agent no agent nouns`
   - 1: `meaning_1` is not empty `-`
   - 2: `pos` equals `masc`
   - 3: `grammar` contains word `agent`
   - 4: `family_set` does not contain word `agent nouns`
   - error_column `family_set`; display `lemma_1`, `grammar`, `meaning_1`;
     exceptions `[]`; iterations `10`.
3. Unit tests for the pure "add set" function in
   `tests/scripts/fix/test_add_agent_nouns_set.py`.

## Assumptions & uncertainties
- The set name is exactly `agent nouns` (lowercase, plural). This is from the request.
- "Agent noun" means `agent` as a word in `grammar`. Masc agents with no `agent`
  in grammar are not found by this thread. The existing aka test is the
  user's tool for those.
- The family-set page lists all ~676 words in one set. Large sets already exist
  (`occupations`). I assume the size is fine.

## Constraints
- Never overwrite `family_set`. Only add to it.
- Edit the TSV with a scripted rewrite (csv QUOTE_ALL, tab). Check that every row
  still has 26 columns. Do not use the Edit tool.
- The agent never runs the db-writing script.
- Lint gate: `ruff check --fix`, `ruff format`, `pyright` on touched .py files.
  Then `just typecheck`.

## How we'll know it's done
- Before the script runs, the new db_test fails on exactly 676 headwords in the live db.
- The script's dry output lists 676 changes. Every one of the 250 rows with
  an existing set keeps that set.
- After the user runs the script, the new db_test fails on 0 headwords.
  Also, 676 headwords carry `agent nouns`.
- The unit tests pass, and a revert of the add function makes them fail.
- The TSV loads through `DbTestManager` and passes `integrity_check()`.

## What's not included
- Feminine, neuter and adjective agent nouns.
- The 137 unfinished masc agents. When an editor fills in `meaning_1`, the new
  test makes them add the set.
- Any change to the existing `grammar: masc aka no agent` test, or clearing its 64 hits.
- Any exporter or gui2 code change.
