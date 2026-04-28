## Thread
- **ID:** 20260411_phonetic_variant_detector
- **Objective:** Build a phonetic variant detection toolkit for DPD headwords (part 1 of #144)

## Files Changed
- `db_tests/single/add_phonetic_variants.py` — interactive CLI detector + DB editor (replaces planned `scripts/variants/` toolkit)
- `db_tests/single/add_phonetic_variants.json` — exception store for skipped pairs
- `tests/db_tests/single/test_add_phonetic_variants.py` — 30 unit tests using `SimpleNamespace` fakes
- `tools/paths.py` — added `add_phonetic_variants_exceptions_path`
- `.gitignore` — stale entry for `scripts/variants/phonetic_variant_candidates.tsv` (harmless)

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `plan.md`, `spec.md` | Spec/plan describe deleted `scripts/variants/` files; actual implementation is an interactive DB editor that writes to `var_phonetic`, `var_text`, `synonym` | Spec said read-only TSV reporter; implementation intentionally evolved to a full editorial tool during development | Intentional divergence — accepted by user, noted here |
| 2 | nit | `.gitignore:113` | Stale entry for `scripts/variants/phonetic_variant_candidates.tsv` | File will never be generated; the `scripts/variants/` directory was deleted | Leave or remove; harmless |

## Fixes Applied
None — spec divergence is intentional, accepted by user without code changes.

## Test Evidence
- `uv run pytest tests/db_tests/single/test_add_phonetic_variants.py -q` → 30 passed in 0.26s
- `uv run ruff check db_tests/single/add_phonetic_variants.py tests/db_tests/single/test_add_phonetic_variants.py` → All checks passed

## Verdict
PASSED
- Review date: 2026-04-28
- Reviewer: claude-sonnet-4-6
- Note: Implementation intentionally superseded the original spec (read-only TSV → interactive DB editor with 4 detection methods). Code quality is high; all tests pass; ruff clean.
