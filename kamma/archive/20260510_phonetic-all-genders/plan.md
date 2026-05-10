# Plan

## Architecture decisions
- Single change, single function: relax `phonetic_pos_class` to bucket all of `{masc, fem, nt}` as `"noun"`. Reuse the existing `NOUN_GENDERS` frozenset rather than inventing a new constant.
- Keep `pos_class` and `NOUN_GENDERS` untouched — they already do the right thing for synonym detection.
- Drop `_PHONETIC_MASC_NT` (now unused) rather than leaving it as dead code.

## Phase 1 — Relax phonetic pos-class

- [ ] Edit `tools/synonym_variant.py`:
  - Remove `_PHONETIC_MASC_NT` (line 139).
  - Rewrite `phonetic_pos_class` so `pos in NOUN_GENDERS` returns `"noun"`, else `pos`.
  - Update docstring to state all three noun genders are equivalent for phonetic matching.
  → verify: `uv run python -c "from tools.synonym_variant import phonetic_pos_class; assert phonetic_pos_class('masc') == phonetic_pos_class('fem') == phonetic_pos_class('nt') == 'noun'; assert phonetic_pos_class('adj') == 'adj'; print('ok')"`

- [ ] Lint + test gate.
  → verify: `uv run ruff check tools/synonym_variant.py` clean; `uv run pytest tests/db_tests/single/test_add_phonetic_variants.py -q` passes (skip cleanly if file not present).
