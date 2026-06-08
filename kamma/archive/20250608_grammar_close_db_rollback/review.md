# Review: Remove ORM mutation in grammar_to_lookup.py

**Verdict: PASSED**

## Files Changed
- `db/grammar/grammar_to_lookup.py`
- `tests/db/grammar/test_grammar_to_lookup.py`
- `AGENTS.md`

## Findings

### Minor (fixed)
- `generate_grammar_data` still wrote `i.stem = ""` on ORM objects — same mutation pattern the refactor was removing. Fixed with a local `stem` variable.
- Test coverage did not guard against stem mutation. Fixed by extending `test_modify_pos_does_not_mutate_headwords` to assert both `pos` and `stem` are unchanged after both functions run.

### Blocking
- None.

## Fixes Applied
- Replaced `i.stem = ""` with `stem = "" if i.stem == "*" else i.stem`; updated downstream references from `i.stem` to `stem`.
- Extended non-mutation test to cover stem as well as pos.

## Test Evidence
```
tests/db/grammar/test_grammar_to_lookup.py::test_modify_pos_does_not_mutate_headwords PASSED
tests/db/grammar/test_grammar_to_lookup.py::test_modify_pos_matches_fixture PASSED
tests/db/grammar/test_grammar_to_lookup.py::test_generate_grammar_data_matches_fixture PASSED
tests/db/grammar/test_grammar_to_lookup.py::test_bang_and_indeclinable_stems_produce_no_entries PASSED
tests/db/grammar/test_grammar_to_lookup.py::test_pattern_without_template_yields_no_entries PASSED
5 passed in 0.85s
```
ruff check, ruff format, pyright — all clean.
