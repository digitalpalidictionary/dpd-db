# Plan: Variant Field Cleanup and Retirement

## GitHub Issue
Part of #144.

## Architecture Decisions

- **Dry-run by default.** The cleanup script must require an explicit
  `--apply` flag to mutate the db. This is a one-shot data migration; the
  cost of an accidental run with bad logic is high.
- **Place script in `scripts/find/`.** That folder already holds analysis
  and find-and-fix utilities, including the existing
  `variants_process.py` prototype the user referenced.
- **Use existing helpers.** `split_field` from `tools.synonym_variant`
  for parsing, `pali_list_sorter` for canonical output. Don't reinvent.
- **No new abstractions.** This is two short edits and one ~50-line script.
  Keep it boring.
- **Phases ordered by reversibility.** Cleanup first (data change, but
  logically idempotent — re-running does nothing more). Code-change second
  (alters new-write behavior; reversible by re-adding two lines if needed).

## Phase 1 — Cleanup script

- [x] Create `scripts/find/variant_dedupe.py`
  - Parse args: `--apply` (bool, default False), `--limit N` (cap dry-run
    output to N entries, default 50, `--all` for unlimited).
  - For each `DpdHeadword`: compute duplicates as
    `variant_set ∩ (syn_set ∪ var_phon_set ∪ var_text_set)`.
  - Print colored line per affected headword: `lemma_1` — removed
    `[duplicates]` — kept `[remainder]`.
  - Tally total headwords affected, tokens removed, headwords whose
    variant becomes empty.
  - On `--apply`: prompt once `"Apply N changes to db? (y/N)"`, then
    rewrite `hw.variant = ", ".join(pali_list_sorter(remainder))` and
    commit once at the end.
  → verify: `uv run scripts/find/variant_dedupe.py` runs without errors
    and prints a non-empty summary; no db changes (confirm by running
    twice and seeing identical output).

- [x] User-driven dry run (manual; user runs it)
  → verify: user inspects sample output, agrees the proposed deletions
    are correct.

- [x] Apply (manual; user runs `--apply` after dry-run review)
  → verify: re-run dry-run shows 0 affected headwords; existing
    `db_tests/db_tests_relationships.py synonym_equals_variant` reports
    zero violations (or near-zero — investigate any residue).
  → result: 10,316 headwords cleaned, 11,692 tokens removed, 9,814 had
    variant fully emptied. Re-run dry-run = 0 affected. 2,122 headwords
    retain genuine variant-only content for future triage.

## Phase 2 — Stop writing variant from var_phon / var_text

- [x] Edit `tools/synonym_variant.py` `assign_relationship`
  - Remove `var.add(other)` from the `var_phonetic` branch (line ~101).
  - Remove `var.add(other)` from the `var_text` branch (line ~106).
  → verify: `uv run ruff check tools/synonym_variant.py` passes; existing
    tests `uv run pytest tests/` still pass.

- [x] Edit `tools/synonym_variant.py` `assign_relationship_dict`
  - Same two removals on the dict-based variant.
  → verify: ruff clean; pytest clean.

- [x] Repair `tests/db_tests/single/test_add_phonetic_variants.py`
  - Fixed broken imports (`_assign` → `assign_relationship` from
    `tools.synonym_variant`); removed dead tests for `_base_differs_*`
    helpers that no longer exist; renamed `detect_base_iya_iiya` →
    `detect_base_ya_iya_iiya` and rule string accordingly.
  - Updated `test_assign_phonetic_*` and `test_assign_textual_*` to
    assert `hw.variant == ""` (the new behavior from Phase 2).
  - Added missing `synonym_list`, `freq_data_unpack`, `root_sign`
    attributes to the `make_hw` SimpleNamespace helper.
  - Made `meaning_1` default to non-empty (canonical-pairs filter now
    requires both sides to have it).
  - Made `test_canonical_pairs_drops_already_related` bidirectional
    (current logic only filters bidirectional already-related pairs).
  → verify: `uv run pytest tests/db_tests/single/test_add_phonetic_variants.py`
    25 passed.

- [ ] End-to-end smoke check
  - Run a single iteration of `add_synonym_variant_multi.py` and
    `add_phonetic_variants.py`, classify one item each as var_phon or
    var_text, verify in the db that `variant` was NOT touched on those
    headwords.
  → verify: query the headword post-classification, confirm `variant`
    column is unchanged from its pre-classification state.
  → status: deferred to user — interactive scripts the assistant can't
    drive. Behavior is unit-tested in
    test_assign_phonetic_removes_synonym_and_does_not_touch_variant and
    test_assign_textual_can_coexist_with_synonym_and_does_not_touch_variant.

## Phase 3 — Verification + commits

- [ ] Run full ruff and pytest
  → verify: `uv run ruff check tools/synonym_variant.py
    scripts/find/variant_dedupe.py` and `uv run pytest tests/` both clean.

- [ ] Commit Phase 1 (script + applied data change) and Phase 2 (write
  behavior change) as two separate commits with `#144` prefix per project
  convention.
  → verify: `git log -3` shows clean commit messages; working tree clean.
