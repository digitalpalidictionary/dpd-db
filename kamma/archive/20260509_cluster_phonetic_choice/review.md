## Thread
- **ID:** 20260509_cluster_phonetic_choice
- **Objective:** add (p)honetic-all-pairwise choice to cluster prompt in add_synonym_variant_multi.py

## Files Changed
- `db_tests/single/add_synonym_variant_multi.py` — extend `prompt_clusters` with `(p)` branch that writes `var_phonetic` pairwise across cluster members

## Findings
No findings. Diff is +30/-1, mirrors the `(s)` block exactly with target field and preserve-field swapped. `assign_relationship` enforces exclusivity, so no extra logic needed.

## Fixes Applied
None.

## Test Evidence
- `uv run ruff check db_tests/single/add_synonym_variant_multi.py` → pass
- User ran the script on a phonetic-variant cluster and confirmed bidirectional `var_phonetic` written

## Verdict
PASSED
- Review date: 2026-05-09
- Reviewer: kamma (inline)
