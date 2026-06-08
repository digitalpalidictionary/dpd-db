# Spec: migrate suttas_to_lookup.py + retire update_test_add

## GitHub issue
#157 Refactoring (lookup_sync rollout, follow-up to `20260608_lookup_sync`)

## Overview
`db/suttas/suttas_to_lookup.py` is the last script still using the hand-rolled
`update_test_add` loop, and the special case flagged during the main refactor. It writes
the **`headwords`** column with `sutta_code -> {headword_id}` — the *same* column that
`db/inflections/inflections_to_headwords.py` writes with `inflected_word -> {id}`. The
two producers write **disjoint key sets** into one co-owned column.

Migrating it retires `update_test_add` entirely.

## The crux: why suttas must NOT clear stale
The canonical `clear_stale=True` would clear/delete every `headwords` row whose key is
not a sutta code — i.e. **it would wipe all the inflection rows**. So suttas must be
**purely additive**:

```python
sync_lookup_column(db_session, "headwords", sutta_data, clear_stale=False)
```

This is correct because of the **build order** (confirmed in
`scripts/bash/generate_components.py`):

```
47 inflections_to_headwords.py   (clear_stale=True — wipes all non-inflection headwords rows)
50 suttas_to_lookup.py           (clear_stale=False — re-adds current sutta codes)
```

Inflections runs first and deletes every non-inflection `headwords` row, *including last
build's sutta codes*. Suttas then re-adds only the current codes.

### Bonus: this fixes a pre-existing bug
The old suttas code never cleared stale sutta codes — its delete branch only fired for
fully-empty rows (`not is_another_value and not i.headwords`). After this change,
inflections deletes stale sutta-code rows first, so only current codes survive. Stale
sutta codes are cleaned for the first time.

### The cost: a documented ordering dependency
suttas is only correct when inflections runs immediately before it with
`clear_stale=True`. A standalone suttas run would let stale sutta codes accumulate.
We accept this and **document it loudly** (module docstring + this spec) rather than
engineer around it — sutta-code rows and inflection rows cannot be told apart by column
alone, so suttas genuinely cannot self-clean the shared column.

### Dropped behaviour (safe)
The old `not is_another_value(i, "headwords") and not i.headwords` orphan-delete branch
is dropped. Once every writer uses the helper (which deletes a row when clearing its last
value), fully-empty rows are never created, so there is nothing for this branch to reap.

## Retire update_test_add
With suttas migrated, `tools/update_test_add.py` has zero live callers (only an archive
file and a test reference remain).
- Delete `tools/update_test_add.py`.
- Remove the `TestUpdateTestAdd` class (and its `update_test_add` import) from
  `tests/scripts/build/test_deconstructor_output_add_to_db.py`. Keep `TestIsAnotherValue`
  and `TestDeconstructorPack` (those building blocks still live). `is_another_value`
  stays — still used by variants, help_abbrev, transliterate, and the helper itself.

## What changes in suttas_to_lookup.py
`add_to_lookup_table`: build `data = {code: sorted(ids) for code, ids in
g.sutta_info_dict.items()}` and call `sync_lookup_column(..., "headwords", data,
clear_stale=False)`. Drop the `update_test_add` + bespoke loop. Remove now-unused
imports (`update_test_add`; `is_another_value` only if unused here). `GlobalVars` no
longer needs the eager `query(Lookup).all()` for `lookup_db` (the helper queries scoped).

## Tests
- The existing golden master `tests/db/suttas/test_suttas_to_lookup.py` covers
  `make_sutta_info_dict` (data-gen) — unaffected, must stay green.
- Add a behavioural test for the write path (in-memory sqlite): an existing sutta-code
  row is updated; a new code is inserted; and crucially an existing **inflection**
  `headwords` row (a key NOT in sutta_data) is left untouched (proves `clear_stale=False`).
- After deleting `update_test_add`, confirm `tests/scripts/build/...` still passes with
  `TestUpdateTestAdd` removed.
- Gate per file: `ruff check --fix` → `ruff format` → `pyright` → `pytest`.

## Done when
- suttas uses `sync_lookup_column(..., clear_stale=False)`; bespoke loop gone.
- `tools/update_test_add.py` deleted; no live references remain.
- Ordering dependency documented in the suttas module docstring.
- New behavioural test + existing golden master pass; `uv run pytest tests/` green.

## Not included
- No change to `make_sutta_info_dict` / sutta-code generation.
- No attempt to make suttas self-clean the shared column (impossible by column alone).
