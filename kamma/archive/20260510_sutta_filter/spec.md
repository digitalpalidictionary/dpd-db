# Sutta filter button on pass2_add tab

## Overview
Add a new "Sutta" radio filter to the pass2_add tab in gui2. It shows a reduced
set of fields appropriate for sutta-style data capture, and prefills "-" into
source_1 and commentary on activation when those fields are empty.

## What it should do
- Add a `Sutta` radio option to the existing filter RadioGroup in
  `gui2/pass2_add_view.py` (alongside All / Root / Compound / Word / Pass1).
- Define a new `SUTTA_FIELDS` list in `gui2/dpd_fields_lists.py`.
- Selecting the Sutta radio filters fields to `SUTTA_FIELDS` via the existing
  `dpd_fields.filter_fields(...)` machinery.
- On selecting the Sutta radio, if `source_1` is empty, prefill it with `"-"`.
  Same for `commentary`. Never overwrite existing values.

## Field visibility rule
Show all fields in `SUTTA_FIELDS`. Additionally, any field outside that list
that already has a value must remain visible. Hide only empty fields that are
not in the list. (Inherited from existing `filter_fields()` in
`gui2/dpd_fields.py:500-515` — no code change needed.)

## SUTTA_FIELDS — derivation
Start from `COMPOUND_FIELDS` and remove:
- All root_* fields (already absent from COMPOUND_FIELDS)
- family_compound, family_idioms (family_set kept — user confirmed)
- sutta_1, source_2, sutta_2, example_2 (only source_1 from that group)
- example_1 (user confirmed: hide)
- antonym, synonym, variant, var_phonetic, var_text
- cognate, link

Resulting list (in original order):
id, lemma_1, lemma_2, pos, grammar, derived_from, neg, plus_case,
meaning_1, meaning_lit, meaning_2, non_ia, sanskrit, family_set,
construction, derivative, suffix, phonetic, compound_type,
compound_construction, source_1, commentary, notes, origin, stem,
pattern, comment

## Assumptions & uncertainties
- `family_set` retained per user confirmation.
- Prefill only on radio click (not on Clear All) per user confirmation.
- Sutta filter is for data capture only; it does not change save/db logic.

## Constraints
- Do not modify .ini/.env.
- No changes to db model, save, or test logic.
- Keep behavior of existing filters unchanged.

## How we'll know it's done
- Radio button "Sutta" appears on the pass2_add tab.
- Clicking it shows only the SUTTA_FIELDS list (plus any non-empty fields).
- Clicking it prefills source_1 and commentary with "-" when those are empty.
- `uv run ruff check` passes for changed files.

## What's not included
- No changes to other tabs.
- No persistence of the filter selection across sessions.
- No new tests (matches the convention for sibling filters which are untested).
