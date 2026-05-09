# Variant Field Cleanup and Retirement

## GitHub Issue
Part of #144 (synonym/variant detection work).

## Overview
The `DpdHeadword.variant` column is a legacy catch-all used historically to
record any kind of related-word relationship. The project has since split
relationships into three semantically meaningful fields: `synonym`,
`var_phonetic`, and `var_text`. Goal: stop using `variant` entirely, in a
phased way that doesn't break exporters or tests mid-flight.

This thread handles the first two phases:
1. One-off cleanup that removes any token from `variant` that already exists
   in `synonym`, `var_phonetic`, or `var_text`.
2. Stop new `variant` writes from `assign_relationship` and
   `assign_relationship_dict` when the target is `var_phonetic` or `var_text`.

A future thread will handle the final retirement (migrating remaining
`variant`-only entries via the existing `scripts/find/variants_process.py`
triage tool, then making the field unused).

## What it should do

### Cleanup script (`scripts/find/variant_dedupe.py`)
- Iterates every `DpdHeadword`.
- For each headword, removes from `variant` any token also present in
  `synonym_list`, `var_phonetic`, or `var_text`.
- Default mode = dry run. Logs changes (lemma_1, removed tokens, kept
  tokens). Does NOT commit.
- `--apply` flag commits the changes after a single confirmation prompt.
- Reports total headwords affected, total tokens removed, headwords whose
  `variant` becomes fully empty.

### Stop double-writing variant
- `tools/synonym_variant.py` `assign_relationship`: drop `var.add(other)`
  from the `var_phonetic` and `var_text` branches.
- Same for `assign_relationship_dict`.
- The `synonym` branch's `var.discard(other)` stays — it cleans up legacy
  entries when the user reclassifies as synonym.

## Assumptions & uncertainties

### Assumptions
- `DpdHeadword.variant` is purely informational. No code branches on its
  contents for behavior — only display, tests, and exports read it.
  (Audit confirms: kobo/tpr/tbw exporters use `Lookup.variant` which is a
  different column on a different table.)
- `db_tests/db_tests_relationships.py` `synonym_equals_variant` will go
  from "find overlap to fix" → 0 violations after cleanup. That's the
  intended outcome.
- Anki / mobile exporters that read `i.variant` will simply receive a
  smaller field — no schema change, no breaking.
- The field is scoped to `DpdHeadword`. The separate `Lookup.variant`
  column is unaffected.

### Uncertainties
- `gui2/dpd_fields.py:1422` has GUI behavior triggered by typing in the
  `variant` field. Not breaking, but contributors who relied on auto-fill
  from `variant` may notice less suggestion noise.
- The existing prototype `scripts/find/variants_process.py` is a richer
  interactive triage tool (classifies remaining variant tokens as
  syn/phon/text/delete). Left untouched — complementary to this dedupe.

## Constraints
- No interactive prompts in the cleanup script other than the apply
  confirmation. Default invocation should always be safe (dry run).
- Use `tools.pali_sort_key.pali_list_sorter` so the rewritten variant
  field stays in canonical order, matching the rest of the codebase.
- Modern type hints, `pathlib.Path`, no `sys.path` hacks.

## How we'll know it's done
- Cleanup script runs in dry-run mode and prints a clear summary.
- Cleanup script with `--apply` reduces `synonym_equals_variant` and
  `synonym_equals_variants` violations in `db_tests_relationships.py` to
  zero (or close — there may be one-sided cases).
- After the assign_relationship change, running the synonym/phonetic
  scripts no longer adds new tokens to `variant`.
- Existing test suite (`uv run pytest tests/`) passes.
- Linter (`uv run ruff check`) passes on changed files.

## What's not included
- Migration of remaining variant-only tokens (use the existing
  `variants_process.py` for that — separate thread).
- Removing `variant` from exporter outputs (Anki / mobile) — they can
  continue reading the field; it just gets thinner over time.
- Schema removal of the column itself.
- Any change to `Lookup.variant`.
