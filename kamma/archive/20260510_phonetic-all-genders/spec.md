# Phonetic variants: allow all three noun genders

## Overview
The offline `just add-variants-phonetic` flow (and the shared gui2 suggester) currently groups only `masc` + `nt` as a single phonetic-equivalence class (`noun_mn`) and keeps `fem` distinct. As a result, pairs like `bhāvana` (nt) ↔ `bhāvanā` (fem) are never surfaced as phonetic candidates, even though they are the same word with a gender-shifted ending. They tend to get routed as synonyms instead, which is the wrong field — these are spelling/gender variants, not synonyms.

## What it should do
Treat all three noun genders {masc, fem, nt} as one equivalence class for phonetic-variant matching, just as `pos_class` already does for synonym matching. Cross-gender candidates (a ↔ ā, etc.) should now appear when running `just add-variants-phonetic`, so the user can route them to `var_phonetic`.

## Assumptions & uncertainties
- "All three genders of nouns" means {masc, fem, nt}; tiliṅga (adj/pp/ptp/prp) is unchanged.
- Change applied to the shared function `phonetic_pos_class` in `tools/synonym_variant.py`, affecting both the offline script and the gui2 per-headword suggester. User's request was framed around the offline flow but consistency is desirable.
- No existing tests pin the current `noun_mn`-only grouping (verified with ripgrep over `tests/`).

## Constraints
- Touch only `phonetic_pos_class` (and the now-unused `_PHONETIC_MASC_NT` constant).
- Do not change `pos_class`, `NOUN_GENDERS`, the phonetic rule list, or any detector logic.
- Pre-commit gate: `uv run ruff check` + relevant pytest must pass.

## How we'll know it's done
- `phonetic_pos_class("masc") == phonetic_pos_class("fem") == phonetic_pos_class("nt") == "noun"`.
- `phonetic_pos_class("adj") == "adj"` (unchanged).
- Ruff + pytest for the affected paths pass.

## What's not included
- No changes to synonym detection.
- No changes to the substitution rule list.
- No data-side changes to existing rows.

## Repo context
- Function lives at `tools/synonym_variant.py:142`.
- Callers: `detect_canonical_pairs` (line ~628) and `find_phonetic_variants_for` (line ~677).
- Offline entrypoint: `db_tests/single/add_phonetic_variants.py`, invoked via `just add-variants-phonetic`.
