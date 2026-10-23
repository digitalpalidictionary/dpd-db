# Plan: family_compound_exceptions

Spec: `spec.md`. Pattern copied: `db_tests/gui/add_antonyms.py`
(`DbTestManager`, `get_exceptions`, `add_exception`, the "exception" action).
Reviewed by the "family compound review" herdr agent on 2026-10-23: spec and plan
confirmed accurate. Its extra points are folded in below.

## Baseline
- [x] Read `add_antonyms.py` and copied its shape.
- [x] `db_tests/db_tests_columns.tsv` was already modified before this thread: 2 lines, the
  `antonym: empty` and `source_2 -` rows. Not this thread's work. Do not count them in the final diff check.

## Phase 1: neg script
- [x] Import `DbTestManager`. Delete the hardcoded `neg_exceptions`. Add `TEST_NAME`.
- [x] Read exceptions from the row `family_compound empty neg`. Use them in `should_process`.
- [x] Add the Exception button, handler, `add_exception` and the loop branch.
- [x] Reload the file before every save (review point: a save rewrites the whole file from memory).
- [x] `ruff check --fix`, `ruff format`, `pyright`: clean.

## Phase 2: taddhita script
- [x] Same changes. Row: `family_compound empty taddhita`.
- [x] Delete `get_exceptions()` body, the `json` import and the `read_tsv_dot_dict` import.
- [x] ruff and pyright clean.

## Phase 3: su_dur script
- [x] Read the union of rows `family_compound empty su dur nir` and `family_compound empty sa`.
- [x] `add_exception` writes to the `sa` row if `construction` starts with `sa `. Otherwise to the `su dur nir` row.
- [x] Delete the dead `i.lemma_clean not in self.exceptions` line, the `json` import and the `read_tsv_dot_dict` import.
- [x] ruff and pyright clean.

## Phase 4: checks
- [x] `rg` for `neg_exceptions|read_tsv_dot_dict|internal_tests_path|import json` in the three files returns nothing.
- [x] Live rows read through `DbTestManager`: neg 17, taddhita 32, su dur nir 3, sa 3. All ids are `int`.
- [ ] Run `just typecheck` (whole repo, pyrefly). Not run yet.
- [ ] User test in the real GUI, one button per script. Check that the row gains the id and the word does not return.
- [ ] After the user test, `git diff` of the TSV must show only id additions in the four `family_compound empty*` rows, plus the 2 older changed rows.

## Accepted, not fixed
- The `sa` and taddhita rows also skip words with "in reference to" in `meaning_1`. The scripts do not. Pressing Exception on such a word saves an id the test never flagged. Harmless.
- Id 88846 sits in both the `sa` row and the taddhita row. No conflict.
- `add_antonyms.py` has the same stale-overwrite risk. It is outside this thread.
