## Thread
- **ID:** 20260510_phonetic-all-genders
- **Objective:** Allow all three noun genders {masc, fem, nt} as one phonetic-equivalence class so cross-gender pairs (e.g. bhāvana ↔ bhāvanā) surface in `just add-variants-phonetic`.

## Files Changed
- `tools/synonym_variant.py` — `phonetic_pos_class` now buckets all noun genders as `"noun"`; removed unused `_PHONETIC_MASC_NT`; docstring updated.
- `tests/db_tests/single/test_add_phonetic_variants.py` — replaced `reject_masc_fem` / `reject_nt_fem` with `allow_masc_fem` / `allow_nt_fem` to match the new spec.

## Findings
No findings.

## Fixes Applied
- None.

## Test Evidence
- `uv run python -c "from tools.synonym_variant import phonetic_pos_class; ..."` → ok
- `uv run ruff check tools/synonym_variant.py tests/db_tests/single/test_add_phonetic_variants.py` → All checks passed
- `uv run pytest tests/db_tests/single/test_add_phonetic_variants.py -q` → 28 passed
- User confirmed `just add-variants-phonetic` now surfaces cross-gender pairs as expected.

## Verdict
PASSED
- Review date: 2026-05-10
- Reviewer: kamma (inline)
