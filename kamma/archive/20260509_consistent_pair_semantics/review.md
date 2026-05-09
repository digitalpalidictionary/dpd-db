## Thread
- **ID:** 20260509_consistent_pair_semantics
- **GitHub:** issue #144
- **Objective:** consolidate uncommitted python changes across synonym/variant detection — surface inconsistent pairs, broaden delete semantics, add (d)elete to phonetic prompt, plus ḍḍh→ddh rule and cluster-result printing.

## Files Changed
- `tools/synonym_variant.py` — new pair-consistent helpers replace four legacy already-related helpers; raw detectors no longer pre-filter; assign_relationship "delete" now clears all four fields; new PHONETIC_RULE `ḍḍh ↔ ddh`.
- `db_tests/single/add_phonetic_variants.py` — new `(d)elete` choice and updated prompt text.
- `db_tests/single/add_synonym_variant_multi.py` — uses `pair_consistently_related[_sets]`; `_all_pairs_related` now per-field; cluster `(s)`/`(p)` print every member's bucket fields after commit.
- `db_tests/single/add_synonym_variant_single.py` — uses `pair_consistently_related_sets`.
- `tests/db_tests/single/test_add_phonetic_variants.py` — two tests renamed and inverted to match new "surface inconsistent pairs" semantics.

## Findings

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `tools/synonym_variant.py` raw detectors | one-sided pre-filter removed → more candidates emitted, canonical-pair gate still trims them | runtime cost; `detect_by_rules` × `len(PHONETIC_RULES)` × matches | watch for slowness on full db; if material, re-add a same-field both-sides pre-filter (not the loose any-field one) |
| 2 | nit | `tools/synonym_variant.py` `assign_relationship_dict` "delete" | duplicates the new clearing logic of `assign_relationship` | two parallel implementations | acceptable — they're intentionally parallel (ORM vs dict) |

No blocking or major findings. Spec coverage complete: the originally-reported `vuḍḍha`/`vuddha` case is now surfaced via two complementary mechanisms — the new `ḍḍh→ddh` rule generates the candidate, and the new `pair_consistently_related` no longer hides the inconsistent recording.

Architecture decisions followed: legacy `already_related_*` helpers fully removed (no callers, confirmed via repo-wide rg). No backward-compat shims kept.

## Fixes Applied
- Inverted two tests in `test_add_phonetic_variants.py` to match the new semantics; both pass.
- Confirmed no external callers of the deleted helpers.

## Test Evidence
- `uv run ruff check tools/synonym_variant.py db_tests/single/add_phonetic_variants.py db_tests/single/add_synonym_variant_multi.py db_tests/single/add_synonym_variant_single.py tests/db_tests/single/test_add_phonetic_variants.py` → All checks passed.
- `uv run pytest tests/db_tests/single/test_add_phonetic_variants.py -q` → 28 passed.

## Verdict
PASSED
- Review date: 2026-05-09
- Reviewer: kamma (inline)
