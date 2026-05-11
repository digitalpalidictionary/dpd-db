# add_synonym_variant_del — laser-focused v1

## Overview
Rewrite `db_tests/single/add_synonym_variant_del.py` so it does one job:
walk every existing synonym relationship in the DB, find the ones that do
NOT meet the validity criterion used by `add_synonym_variant_single.py`
and `add_synonym_variant_multi.py`, and let the user delete them.

## What it should do
- Reuse `GlobalVars`, `_format_fields`, `_show_result`, `_pair_key`,
  `_entry_label` from `add_synonym_variant_multi.py`.
- Reuse `clean_meaning`, `grammar_signature`, `pos_class`, `split_field`,
  `assign_relationship` from `tools/synonym_variant.py`.
- Validity:
  - same `pos_class`, same `grammar_signature`
  - both `meaning_1` populated
  - both single-meaning → cleaned meanings equal
  - otherwise → ≥2 shared cleaned meanings
- Detection: build `lemma_clean → [DpdHeadword,...]`. For each `hw_a`
  and each `syn_clean` in `split_field(hw_a.synonym)`:
  1. `candidates = by_lemma_clean[syn_clean] - {hw_a}`
  2. `same_class = [c for c in candidates if pos_class(c.pos) ==
     pos_class(hw_a.pos)]`
  3. If `same_class` is non-empty:
     - Gating uses a SOFT rule (`_plausibly_valid_synonym`): same
       pos_class + ≥1 shared cleaned meaning. If any same-class
       homonym passes this, skip the whole `syn_clean`. Rationale: the
       synonym field stores lemma_clean only, so deleting collaterally
       breaks links to plausibly-valid sibling homonyms. Recall over
       precision here; strict validity belongs to the add scripts.
       Example: `ativiya.synonym = "bhusaṃ"` is intended for
       `bhusaṃ 1` even though strict ≥2-shared fails.
     - Else → flag only `same_class` candidates.
  4. If `same_class` is empty (no same-pos homonym exists): flag the
     cross-pos candidates so the user can clean up the dangling
     reference.
  Dedupe flagged pairs by frozenset edge id. Rationale: the synonym
  field stores `lemma_clean`, not a homonym id, but a cross-pos match
  is structurally impossible — restricting validity to same-pos
  candidates eliminates both the `akataññū 2.1` and the `bhaya 2 nt`
  classes of false positive.
- Exceptions: del has its OWN file at
  `db_tests/single/add_synonym_variant_del.json`, accessed via
  `ProjectPaths.syn_var_del_exceptions_path`. Implemented as a local
  `GlobalVars` subclass that overrides `_load_exceptions` /
  `_save_exceptions`. Rationale: a del-exception means "keep this
  synonym despite failing validity" — the opposite verdict of the
  single/multi exception ("don't propose as a new synonym"). Sharing
  the file would let "don't propose" verdicts silently mask future
  invalid synonyms. Pair-key shape (`pos:lemmas:sig`) is reused as-is.
- Prompt: `(d)elete, (e)xception, (pass), (r)estart, (q)uit`.
- Outer `while True: GlobalVars() → find → prompt` mirrors multi/single.

## Assumptions & uncertainties
- `assign_relationship(..., "delete")` removes the lemma from the field
  correctly (confirmed by existing usage).
- "Any-valid-wins" matches lemma_clean semantics. Reverted from the
  per-candidate variant once a real homonym example surfaced.
- `_pair_key` is symmetric across lemma order.

## Constraints
- Touch only `db_tests/single/add_synonym_variant_del.py`.
- No phonetic/textual scaffolding.
- Modern type hints; comments only for WHY.

## How we'll know it's done
- `uv run ruff check db_tests/single/add_synonym_variant_del.py` passes.
- `uv run python -m py_compile <file>` passes.
- User runs the script and confirms wrong pairs surface and the prompt
  actions work.

## What's not included
- Reclassifying wrong synonyms as phonetic/textual variants.
- Edits to multi/single scripts or `tools/synonym_variant.py`.
