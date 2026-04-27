## Thread
- **ID:** 20260426_synonym_multi
- **Objective:** Build a multi-meaning synonym finder and modernise the entire synonym/variant workflow

## Files Changed
- `db_tests/single/add_synonym_variant_multi.py` — multi-meaning pair finder; added `_general_key`, general exception support; del/wrong-synonym code extracted to del file
- `db_tests/single/add_synonym_variant_single.py` — NEW: pair-based single-meaning synonym finder replacing old group-based add_synonym_single.py
- `db_tests/single/add_synonym_variant_del.py` — NEW: wrong synonym detector/remover, imports shared helpers DRY
- `db_tests/single/add_synonym_variant.json` — stripped 187 unrecognised legacy exception keys; kept 551 valid
- `justfile` — updated `add-synonyms-single` target, added `add-synonyms-del`
- `tools/paths.py` — removed dead `syn_var_exceptions_old_path`
- Deleted: `add_synonym_variant.py`, `add_synonym_variant_exceptions`, `add_synonym_variant_old.json`, `add_synonym_single.py`

## Findings
No findings. All critical bugs found during development (cached property staleness, variant data-loss, lemma_clean ambiguity, performance) were fixed before user testing confirmed the scripts working correctly.

## Fixes Applied
None during review — all fixes were applied during implementation.

## Test Evidence
- `uv run python -m py_compile db_tests/single/add_synonym_variant_multi.py` → pass
- `uv run python -m py_compile db_tests/single/add_synonym_variant_single.py` → pass
- `uv run python -m py_compile db_tests/single/add_synonym_variant_del.py` → pass
- `uv run ruff check db_tests/single/add_synonym_variant_{multi,single,del}.py` → all checks passed
- User ran all three scripts interactively and confirmed correct behaviour

## Verdict
PASSED
- Review date: 2026-04-27
- Reviewer: kamma (inline)
