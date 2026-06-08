# Spec: lookup_sync — DRY refactor of the Lookup add/update/clear/delete mechanism

## GitHub issue
#157 Refactoring

## Overview
The `Lookup` table (~1.29M rows, 19 data columns, `lookup_key` PK) is populated by
many build scripts. Each writes **one column** from a `{lookup_key: value}` dict and
re-implements the same add / update / clear / delete logic by hand. Two patterns exist
today:

- **Slow** — `query(Lookup).all()` loads the whole table, then loops with
  `update_test_add` + `is_another_value`. Used by grammar, epd, family_root,
  inflections→headwords, suttas→headwords, deconstructor. ~77% of the scan is a no-op
  (only 22.5% of rows have grammar; sparser columns waste 95%+).
- **Fast (scoped)** — `db/variants/add_to_db.py`: clear/delete over
  `filter(col != "")`, chunked `in_(900)` update, insert the rest, per-chunk
  `commit` + `expunge_all`. Never loads the full table. **This is the template.**

Extract one shared helper — `tools/lookup_sync.py :: sync_lookup_column()` — that
copies the scoped variants pattern, and migrate the canonical scripts onto it.

## Decisions (confirmed with user, 2026-06-08)
1. **Approach:** scoped-query helper (fixes both DRY and the full-table-scan waste).
2. **Rollout:** incremental, one script at a time, all under #157. Not a big-bang.
3. **`spelling_mistakes.py`** gets the same fix as `see.py` (stale entries now cleared).
4. **Scope for this thread:** the six canonical clear-or-delete scripts first. The
   three awkward ones (`suttas_to_lookup`, `transliterate_lookup_table`,
   `help_abbrev_add_to_lookup`) are deferred — "then we look at the others".

The six canonical scripts (column in brackets):
- `db/grammar/grammar_to_lookup.py` (`grammar`) — has golden master for data-gen
- `db/epd/epd_to_lookup.py` (`epd`)
- `db/families/family_root.py::update_lookup_table` (`roots`)
- `db/inflections/inflections_to_headwords.py` (`headwords`)
- `scripts/build/deconstructor_output_add_to_db.py` (`deconstructor`)
- `db/lookup/see.py` (`see`) + `db/lookup/spelling_mistakes.py` (`spelling`)

`db/variants/add_to_db.py` is the existing template; it may adopt the helper last so the
pattern has a single home, but is not a behaviour change.

## The helper

```python
def sync_lookup_column(
    db_session: Session,
    column: str,
    data: dict[str, Any],
    *,
    pack_attr: str | None = None,
    clear_stale: bool = True,
    chunk_size: int = 900,
) -> LookupSyncResult
```

Behaviour:
1. **Stale pass** (when `clear_stale`): query `filter(getattr(Lookup, column) != "")`.
   For each row whose `lookup_key` is **not** in `data`: if `is_another_value(row, column)`
   set `column = ""` (clear) else `db_session.delete(row)` (delete). Rows whose key **is**
   in `data` are skipped here (handled by the update pass). Commit.
2. **Update + insert pass**: batch `data` keys by `chunk_size` (`itertools.batched`).
   Per chunk: query existing rows `in_(chunk)`, re-pack the found ones, build new `Lookup`
   rows for the not-found keys, `add_all`, commit, `expunge_all`.
3. Packing uses `getattr(row, pack_attr)(value)` where `pack_attr` defaults to
   `f"{column}_pack"`. **`variant` needs `pack_attr="variants_pack"`** (only irregular one).
4. Returns `LookupSyncResult(updated, inserted, cleared, deleted)` for the caller's printer.

Value prep (sorting, list/tuple/dict shape) stays **caller-side**: the caller builds the
`data` dict, the helper just writes it.

### Why `*_pack` is never used to clear
Every `*_pack` raises `ValueError` on empty input, so the helper clears by assigning
`""` directly and only calls `pack` with the non-empty values present in `data`.

## Intended, accepted behaviour differences vs the old slow loop
These follow directly from the scoped approach and match the variants template:
- The helper only ever touches rows that hold a value in the target column. The old
  full-load loop could incidentally **delete an all-empty orphan row** (every column "")
  whose key happened to land in `test_set`. The helper leaves such rows alone. Such rows
  should not exist in a healthy db, so this is safe.
- **`see` / `spelling` bug fix:** today both re-query only `in_(update_set)` then branch
  on `elif key in test_set:` — dead code, since the two sets are disjoint. Stale see/
  spelling values are therefore **never** cleared, and the whole step is skipped when
  `update_set` is empty. After migration, stale entries are correctly cleared/deleted.
  This is a deliberate, wanted change (confirmed).

## Constraints
- Modern type hints, `pathlib.Path`, no `sys.path` hacks.
- `tools.printer` for output, `tools.db_helpers.get_db_session`.
- Helper is ORM-only, scoped, never `query(Lookup).all()`.
- Reuse `tools.lookup_is_another_value.is_another_value`.
- `update_test_add` is retired **only when its last caller is migrated** (not this thread,
  since rollout is incremental — suttas still uses it).
- Do NOT run the heavy build scripts against the real `dpd.db` (per project rule — the
  user runs those). Verification is via fast in-memory-sqlite behavioural tests.

## Tests (test-first, no mocks)
- `tests/tools/test_lookup_sync.py` — behavioural test of the helper against an
  in-memory sqlite db (the `tests/gui2/test_roots_db.py` pattern): covers update of an
  existing row, insert of a new key, clear of a stale key that has another value, delete
  of a stale key with no other value, the `clear_stale=False` path, and `pack_attr`
  override for `variant`.
- A **real** `see` test (`tests/db/lookup/test_see_population.py` is currently fake —
  it reimplements logic in raw `sqlite3` and never calls `see.py`). Replace it with one
  that drives `see.py` against an in-memory db and asserts add / update / stale-clear.
- Per-script migrations keep existing golden masters green (grammar, suttas).
- Gate per file: `ruff check --fix` → `ruff format` → `pyright` → `pytest`.

## How we'll know it's done (this thread)
- `tools/lookup_sync.py` exists with full test coverage, all green.
- The six canonical scripts call `sync_lookup_column` instead of the hand-rolled loop;
  each is shorter and their existing tests still pass.
- `see` and `spelling` now clear stale entries; a real see test proves it.
- `uv run pytest tests/` passes; ruff + pyright clean on every touched file.

## Not included
- `suttas_to_lookup.py` (delete-orphans-only), `transliterate_lookup_table.py`
  (update-only, multiprocessing), `help_abbrev_add_to_lookup.py` (multi-column, N+1) —
  deferred to a follow-up under #157.
- Retiring `update_test_add` / `lookup_is_another_value` (keep until last caller migrates).
- No change to the packed JSON shapes or to `db/models.py`.
