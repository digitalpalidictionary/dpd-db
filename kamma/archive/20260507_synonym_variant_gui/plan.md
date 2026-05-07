# Plan

## Architecture decisions
- New module `tools/synonym_variant.py` is the single home of detection
  rules, `assign_relationship`, and the `PhoneticVariantDetector`.
  Offline scripts and GUI both import from it. Reason: three near-
  identical copies today; any divergence becomes a silent bug.
- Detector lives on `DatabaseManager` as a cached attribute, built
  lazily and invalidated on commit. Reason: matches existing pattern
  (`all_lemma_clean`, `all_pos`, etc.) and keeps GUI startup cheap.
- "Live + _add" UX: write straight into the field AND into the `_add`
  field, so the user can edit freely without losing the original.
- GUI is one-sided. Bidirectional partner sync remains the offline
  scripts' job.

## Phase 1 — extract shared module
- [x] Create `tools/synonym_variant.py` containing: `clean_meaning`,
      `grammar_signature`, `_split_field`, `assign_relationship`
      (renamed from `_assign`, public), `PHONETIC_RULES`, `_SUFFIX_NORM`,
      `_construction_without_base`, `_already_related`,
      `_has_textual_occurrence`, `_same_families_if_present`,
      `_headword_identity`, `Pair` dataclass, `PhoneticVariantDetector`,
      and `find_synonym_candidates_for_hw(hw, ctx, *, mode)` extracted
      from the two syn scripts (single + multi).
      → verify: `uv run python -c "import tools.synonym_variant"` exits 0.
- [x] Refactor `db_tests/single/add_synonym_variant_multi.py` to import
      from the shared module; delete duplicated helpers.
      → verify: import test; run `uv run python -c "from db_tests.single.add_synonym_variant_multi import find_multi_meaning_pairs, GlobalVars; g=GlobalVars(); find_multi_meaning_pairs(g); print(len(g.pairs))"` and capture the count.
- [x] Refactor `db_tests/single/add_synonym_variant_single.py` similarly.
      → verify: import + count check as above.
- [x] Refactor `db_tests/single/add_phonetic_variants.py` similarly,
      keeping `PhoneticVariantDetector` in shared module.
      → verify: import + count check as above.

## Phase 2 — wire detector into DatabaseManager
- [x] Add `RelationshipDetector` (in `tools/synonym_variant.py`) that
      wraps `PhoneticVariantDetector` and adds `find_synonyms(hw)` /
      `find_phonetic_variants(hw)` per-headword methods returning
      `(candidates, rule_labels)`.
      → verify: small script in `temp/check_detector.py` opens db, builds
      detector, queries 3 known headwords, prints results.
- [x] Add `_relationship_detector` cached attr to `DatabaseManager`
      with a `get_relationship_detector()` accessor that builds on first
      call. Invalidate inside the commit/refresh path.
      → verify: import the manager, call accessor twice, second is
      instant.

## Phase 3 — GUI synonym flow
- [x] Replace `synonym_focus` body and add `meaning_1_blur` synonym
      computation. Use the new detector. Write into `synonym` (live)
      and `synonym_add` simultaneously. Subtract values already present
      in `variant`/`var_phonetic`/`var_text`.
      → verify: launch gui2, open a known multi-meaning headword, edit
      meaning_1, tab away → both fields populate.
- [x] Remove the wipe-synonyms branch from `meaning_1_blur` (lines
      777–785). New trigger replaces it.
      → verify: editing meaning_1 a second time triggers fresh
      computation that overwrites; no manual wipe.
- [x] Remove `DatabaseManager.get_synonyms`. Confirm no other callers.
      → verify: `rg "get_synonyms\(" .` returns no hits.

## Phase 4 — GUI phonetic-variant flow (new)
- [x] Add `var_phonetic_focus` handler that calls the detector. Write
      candidates live into `var_phonetic`, mirror into `var_phonetic_add`,
      set `helper_text` to the rule label(s).
      → verify: open a headword known to have a phonetic sibling
      (e.g. via construction match); focus `var_phonetic` → suggestion
      appears in both fields with rule label visible.
- [x] Wire the new handler into `FieldConfig` for `var_phonetic`
      (currently `on_change`/`on_blur` = `clean_pali_field` only).
      Add `on_focus=self.var_phonetic_focus`.
      → verify: focus the field, handler fires.
- [x] Suppress already-recorded candidates in detector
      `find_phonetic_variants` and `find_synonyms` based on the current
      headword's `synonym`/`var_phonetic`/`var_text`.
      → verify: with a headword that already has phonetic relationships
      saved, the suggestion list is correctly trimmed.

## Phase 5 — accept-time exclusivity
- [x] Route the `_add` ← transfer button (`transfer_add_value`) for
      `synonym`, `var_phonetic`, `var_text` through `assign_relationship`
      so the exclusivity rules apply on accept.
      → verify: with a lemma in `synonym`, accept it as `var_phonetic`
      via the ← button → it moves correctly.

## Phase 6 — end-to-end check
- [x] Open three real headwords in gui2 covering: multi-meaning synonym
      pair, single-meaning synonym pair, and phonetic pair. Confirm each
      surfaces correctly.
      → verify: described above; capture outcomes in review.md.
