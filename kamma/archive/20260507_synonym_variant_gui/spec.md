# Synonym & phonetic variant suggestions in gui2

## Overview
Bring the gui2 headword editor to parity with the offline detectors in
`db_tests/single/` for synonym and phonetic-variant suggestions. Extract
the shared logic into a single module, fix the existing GUI synonym flow,
and add a new phonetic-variant flow that didn't exist before. The goal is
low-friction surfacing of candidates while editing — false positives are
acceptable because the user manually approves/edits.

## Repo context
- `gui2/dpd_fields.py` is the headword editor field controller.
  - `synonym_focus` (line ~1278) currently calls
    `db.get_synonyms(pos, meaning_1, lemma_1)` on focus and writes
    straight into `synonym`.
  - `meaning_1_blur` (line ~777) wipes `synonym` so it regenerates next
    focus — to be removed.
  - `var_phonetic` field has only `on_change`/`on_blur` = `clean_pali_field`.
    No focus handler. No suggestions today.
  - `_add` machinery: `update_add_fields`, `check_and_color_add_fields`,
    `transfer_add_value` already handle red-text suggestions for many
    other fields (`compound_type`, `phonetic`, `sanskrit`).
- `gui2/database_manager.py` `get_synonyms` (line ~714) — only caller is
  `dpd_fields.synonym_focus` (verify before deleting).
- `db_tests/single/add_synonym_variant_multi.py`,
  `add_synonym_variant_single.py`, `add_phonetic_variants.py` —
  three offline scripts with three near-identical copies of
  `_split_field`, `_assign`, `clean_meaning`, `grammar_signature`,
  `_already_related`, plus rule-specific detectors. The phonetic
  script also owns `PhoneticVariantDetector`, `PHONETIC_RULES`,
  `_construction_without_base`, `_SUFFIX_NORM`,
  `_has_textual_occurrence`, `_same_families_if_present`,
  `_headword_identity`.
- The exclusivity logic in `_assign`:
  - `synonym ↔ var_phonetic` mutually exclusive
  - `synonym + var_text` may coexist
  - `variant` is a legacy mirror of `var_phonetic ∪ var_text`,
    modified surgically — never recomputed wholesale.

## What it should do
- A new module `tools/synonym_variant.py` owns `clean_meaning`,
  `grammar_signature`, `_split_field`, `assign_relationship` (the
  exclusivity logic from `_assign`), `PHONETIC_RULES`,
  `_construction_without_base`/`_SUFFIX_NORM`, `PhoneticVariantDetector`,
  and a new `find_synonym_candidates_for(hw, ctx)` helper.
- All three offline scripts keep their current CLI behaviour but import
  the shared symbols.
- `DatabaseManager` exposes a lazily-built, session-cached
  `RelationshipDetector` that pre-indexes the db once and answers
  per-headword queries (`find_synonyms`, `find_phonetic_variants`).
  Rebuild on commit, like other cached sets.
- GUI synonym flow:
  - On `meaning_1` blur, compute candidates and write straight into
    `synonym` (live), and also into `synonym_add` so the original
    suggestion is preserved if the user edits.
  - Drop the "wipe synonyms when meaning_1 blurs" behaviour — superseded.
  - Use grammar_signature + cleaned meanings + single AND multi-meaning
    rules, matching the offline scripts.
  - `db.get_synonyms` is removed.
- GUI phonetic-variant flow (new):
  - On `var_phonetic` focus, run all four phonetic detection rules from
    `add_phonetic_variants.py` against the current headword.
  - Write candidates straight into `var_phonetic`, mirror into
    `var_phonetic_add`, and put the rule label in `var_phonetic`'s
    `helper_text`.
- Already-related suppression is one-sided: if the candidate is already
  in the current headword's `synonym`/`var_phonetic`/`var_text`, don't
  suggest it. The bidirectional sweep stays in the offline scripts.
- Accept-time exclusivity: the `_add` ← transfer button for `synonym`,
  `var_phonetic`, `var_text` routes through `assign_relationship` so
  the exclusivity rules apply.

## Assumptions & uncertainties
- Detector indexes ~80k headwords once at first use — assumed acceptable
  cost (offline scripts already do it per run). To be measured.
- `meaning_1` blur is the right trigger for synonyms.
- `var_phonetic` focus is the right trigger for phonetic variants.
- `helper_text` for rule labels — to be tried; may need tweaking.
- `database_manager.get_synonyms` is only called from
  `dpd_fields.synonym_focus` (verify by ripgrep before removing).
- GUI updates only the current headword; partner-side updates handled
  by re-running the offline scripts.

## Constraints
- Don't break the three offline scripts — verify by import + dry-run.
- Don't add heavy work to GUI startup; build the detector lazily.
- Preserve existing `_add` plumbing.
- Apply `assign_relationship` exclusivity only on accept (← button) or
  fresh suggestion, not on every keystroke.

## How we'll know it's done
- Offline scripts produce the same pair lists as before the refactor
  (spot-check by running each script's detection pass on a fixed db
  snapshot and counting pairs).
- Opening a headword with known synonym candidates in gui2 populates
  both `synonym` (live) and `synonym_add` (red) on `meaning_1` blur.
- Focusing `var_phonetic` on a headword with a known phonetic partner
  populates both `var_phonetic` and `var_phonetic_add`, with a rule
  label in helper text.
- Already-recorded relationships are not suggested again.

## What's not included
- Bidirectional partner-row updates from the GUI.
- A "skip" / exception store in the GUI.
- Refactoring `meaning_1`/`construction`/`stem` flows beyond what
  interacts with synonym wipe behaviour.
- Tests for the shared module beyond import smoke tests.
