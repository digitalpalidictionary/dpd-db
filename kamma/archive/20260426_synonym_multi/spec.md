# add_synonym_multi.py — multi-meaning synonym finder

## Overview
New interactive script `db_tests/single/add_synonym_multi.py` that finds DPD headwords with **multiple meanings** (where `meaning_1` contains `"; "`) sharing ≥2 cleaned meanings under the same `pos` and grammar signature, then lets the user promote the overlap into `synonym`, `variant`, or `var_phonetic`. Replaces the dual-meaning logic of legacy `add_synonym_variant.py`, mirroring the style of `add_synonym_single.py`.

## What it should do
- Iterate `DpdHeadword` rows.
- Skip rows where `meaning_1` is empty or has no `"; "`.
- For each surviving row, compute cleaned meaning set (split by `"; "`, run `clean_meaning`, drop empties) and `grammar_signature(hw.grammar)`.
- Bucket entries by `(pos, grammar_sig)`. Within each bucket, find every headword group sharing ≥2 cleaned meanings.
- Pronouns (`pos == "pron"`) and sandhis (`pos == "sandhi"`) are included — `grammar_signature` already enforces same grammar (case/person/gender), matching how the single script handles pronouns.
- For each group, build exception key `pos:m1|m2|...|mN:grammar_sig` (sorted shared meanings joined with `|`); skip if key in exceptions file.
- Reuse the prompt/commit pattern from `add_synonym_single.py`:
  - compute `syn_candidates`, `variant_candidates`, `phonetic_candidates` per headword
  - present group with rich-formatted lines
  - prompt `(s)ynonym, (v)ariant, (e)xception, (p)ass, (r)estart, (q)uit`
  - commit using set unions/differences identical to single script
- Reload-and-restart loop matching single script.

## Assumptions & uncertainties
- **Assumption:** the existing `syn_var_exceptions_path` is shared between single and multi scripts. Multi-meaning exception keys (with `|`) won't collide with single-meaning keys (no `|`).
- **Assumption:** "shared ≥2 meanings" means set intersection size ≥2, regardless of group size (≥2 headwords).
- **Assumption:** including `pron` and `sandhi` is acceptable because `grammar_signature` enforces matching grammar markers — be ready to revert by adding the filter back if it turns out noisy.
- **Uncertainty:** O(n²) pairwise grouping within a `(pos, sig)` bucket should be tractable since buckets are small; verified by inverted-index approach (meaning → headwords) followed by intersect.

## Constraints
- Must not modify `add_synonym_single.py` or `add_synonym_variant.py`.
- Must follow project rules: modern type hints, `Path` from pathlib, `pr` from `tools.printer`, no `sys.path` hacks.
- No execution by Claude — user runs the script.

## How we'll know it's done
- File exists at `db_tests/single/add_synonym_multi.py`.
- `uv run python -m py_compile db_tests/single/add_synonym_multi.py` succeeds.
- `uv run ruff check db_tests/single/add_synonym_multi.py` reports no errors.
- User confirms by running it and walking through a few groups.

## What's not included
- Refactoring shared helpers into a common module.
- Modifying `add_synonym_single.py` or `add_synonym_variant.py`.
- Changing the exceptions file format.
- Adding tests (the script is interactive and DB-mutating; no automated tests exist for the sibling scripts either).
