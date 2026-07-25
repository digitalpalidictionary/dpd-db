# Spec: move `variant` → `var_text`

**Thread:** 20260725_variant_to_var_text

## Overview

`DpdHeadword` carries three overlapping relationship columns plus `synonym`:

| column | rows populated (live `dpd.db`, 2026-07-25) |
|---|---|
| `synonym` | — |
| `variant` | 2,450 (2,865 tokens) |
| `var_phonetic` | — |
| `var_text` | 799 |

`variant` is the legacy column. `var_text` is its successor and means the same
thing — "variant readings of the headword found in other Pāḷi texts". The split
was made in the schema years ago but the data was never migrated. `db_tests`
already carries a rule named **`"variant: not empty, move"`**
(`db_tests/db_tests_columns.tsv:539`) whose entire purpose is to flag rows that
still have data in `variant`.

This thread does the migration: every token in `variant` moves into `var_text`,
merged with whatever is already there, Pāḷi-sorted, comma-space joined. After it,
`variant` is empty across the whole table and the gui2 field is gone.

## Everything needed already exists — nothing is being invented

- **`tools/synonym_variant.py:192` `assign_relationship(hw, other, target)`** is
  the canonical writer. Called with `target="var_text"` it, per token:
  - adds the token to `var_text`
  - discards it from `synonym`, `var_phonetic`, and `variant`
  - rewrites all four columns as `", ".join(pali_list_sorter(...))`

  The Pāḷi sort and the comma-space rendering the user asked for are already this
  function's built-in behaviour.
- **`just backup`** (`db/backup_tsv/backup_dpd_headwords_and_roots.py`) writes the
  tracked source of truth, `db/backup_tsv/dpd_headwords_part_*.tsv`. `dpd.db` is a
  build artifact; the TSVs are what gets committed.
- **`db_tests_columns.tsv:539`** already verifies the end state.
- **`scripts/fix/`** is the established home for one-off db repair scripts (see the
  sibling `scripts/fix/variant_cleaner.py`, which audits this very column).

## Verified pre-conditions

Measured against live `dpd.db` before writing this spec:

- **Zero token overlap** between `variant` and `synonym`, `var_phonetic`, or
  `var_text`. The merge cannot collide and cannot silently drop an existing
  assignment. `assign_relationship`'s exclusivity discards are therefore no-ops
  on this data.
- 74 rows have both `variant` and `var_text` populated — these are genuine merges
  and are the reason the move must union rather than overwrite.

## Directionality — decided: literal move, no backfill

`variant` links are largely one-way. At `lemma_clean` level:

| | count |
|---|---|
| directed edges | 2,790 |
| reciprocated | 752 (27%) |
| one-way | 2,038 (73%) |
| — target is not a headword at all (dead link) | 1,159 |
| — target exists, so backfillable | 879 |
| extra rows a backfill would edit | 1,272 |

Existing `var_text` data is itself already 37% one-way (353 of 943 edges), so
one-sidedness is the norm in the destination column, not something this move
introduces.

**Decision (user, 2026-07-25): no backfill.** The move is literal — one-way links
stay one-way. Reasons: a backfill would write 1,272 rows of unreviewed
assertions; it cannot fix the 1,159 dead links, which are a separate data-quality
problem `scripts/fix/variant_cleaner.py` already reports on; and symmetry can be
added later as a cheap follow-up pass over `var_text` if wanted.

## Scope

**In scope**

0. *(added mid-thread by user decision, 2026-07-25)* Normalise the 26 pre-existing
   `var_text` values that were not Pāḷi-sorted. These were hand-entered and never
   passed through `assign_relationship`; none were touched by the migration
   itself. Implemented as a second, idempotent pass in the same script.
1. One-off migration script `scripts/fix/variant_to_var_text.py`.
2. Run it, then `just backup`, committing the regenerated TSVs.
3. Remove the `variant` field and its handlers from gui2.
4. A `TODO` reminder on `DpdHeadword.variant` in `db/models.py` that the column
   is to be dropped at the next db-model change.

**Out of scope (decided by user)**

- Dropping the `variant` column from `db/models.py`. The user will do this when
  they next make other model changes; an empty column harms nothing meanwhile.
- Removing `variant` from exporters and templates
  (goldendict / webapp / tpr / kindle / kobo / pdf / anki / `export_txt.py`).
  Every one of them is guarded on the field being non-empty — the goldendict and
  webapp templates even read
  `{% if d.i.variant and not d.i.var_phonetic and not d.i.var_text %}` — so with
  the column emptied they render nothing. They come out with the column.
- `Lookup.variant`. Different column, different pipeline (`db/variants/`,
  textual variant readings from CST/BJT/SC/SYA). Completely untouched.
- Backfilling reciprocal links (see above).
- The 1,159 dead `variant` links whose target is not a headword. They migrate
  as-is into `var_text`; cleaning them is `variant_cleaner.py`'s job, a separate
  thread.

## Acceptance criteria

1. `select count(*) from dpd_headwords where variant != ''` returns **0**.
2. Total `var_text` tokens after = union of the before-sets, per row. No token
   lost, no token invented.
3. Every non-empty `var_text` value is Pāḷi-sorted and comma-space joined —
   guaranteed by going through `assign_relationship`.
4. `db_tests` rule `"variant: not empty, move"` reports zero rows.
5. gui2 starts, and the pass2 edit view shows no `variant` field; `synonym`,
   `var_phonetic`, `var_text` still work, including the `_add` transfer buttons.
6. `db/backup_tsv/dpd_headwords_part_*.tsv` regenerated and consistent with the db.
7. `ruff check`, `ruff format`, `pyright`, and the related tests pass on every
   touched file.

## Risks

- **Concurrent writers.** The row count moved 2451 → 2450 between two queries
  during investigation, i.e. something was writing to `dpd.db`. gui2 must be
  closed before the migration runs.
- **Irreversible in the db.** Mitigated by the TSV backup being committed
  separately from the migration, so the pre-state is recoverable from git.
