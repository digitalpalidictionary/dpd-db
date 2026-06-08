# Spec: migrate help_abbrev_add_to_lookup.py to sync_lookup_column

## GitHub issue
#157 Refactoring (lookup_sync rollout, follow-up to `20260608_lookup_sync`)

## Overview
`db/lookup/help_abbrev_add_to_lookup.py` writes three Lookup columns — `help`,
`abbrev`, `abbrev_other` — via three functions (`add_help`, `add_abbreviations`,
`add_abbreviations_other`). Each already does the scoped clear the helper does
(`query(Lookup).filter(col != "").all()` → `is_another_value` clear-or-delete), but
its update/insert is **N+1**: one `query.filter_by(lookup_key=key).first()` per key.
Migrate all three onto `tools/lookup_sync.sync_lookup_column`, which replaces the N+1
upsert with chunked `in_(900)` update + batched insert.

This is the cleanest remaining fit — same clear-or-delete semantics as the six already
migrated, just with the N+1 fixed for free.

## What changes
For each column, build the `data` dict caller-side, then one helper call:
- `add_help`: `data = {key: values["meaning"] for key, values in help_data.items()}`
  → `sync_lookup_column(db, "help", data)`. (`help` values are strings; `help_pack`
  stores `json.dumps(string)`.)
- `add_abbreviations`: `data = abbrevs` (key → dict) → `sync_lookup_column(db, "abbrev", data)`.
  (`abbrev_pack` uses `indent=1`; default `f"{col}_pack"` = `abbrev_pack`, no override.)
- `add_abbreviations_other`: keep the existing normalize + group-by-key logic to build
  `grouped` (key → list[dict]), then `sync_lookup_column(db, "abbrev_other", grouped)`.

Drop the per-function clear loop and the N+1 upsert loop. Remove now-unused
`is_another_value` import (only if no other use remains). Keep the `rich`-based prints
or swap to `pr` as currently used — no behaviour change intended there.

## Keep untouched
- `ensure_abbrev_other_column` — a one-off `ALTER TABLE` that adds the `abbrev_other`
  column if missing. Unrelated to the sync; leave as-is, still called first in `main`.
- Value prep (key normalization, grouping, sorting) stays caller-side.

## Constraints
- `clear_stale=True` (default) — matches today's scoped clear.
- `*_pack` raise on empty input; the data dicts never contain empty values, so the
  helper only packs non-empty values and clears by assigning "" directly.
- Modern type hints, pathlib, `pr` printer. No `sys.path` hacks.

## Tests (none exist today — add them)
- `tests/db/lookup/test_help_abbrev_add_to_lookup.py` against in-memory sqlite:
  for at least `help` and `abbrev`, cover insert / update / stale-clear-with-other-value
  / stale-delete. For `abbrev_other`, cover the normalize+group path (dotted/undotted key
  collapse) producing one entry, then synced.
- Gate per file: `ruff check --fix` → `ruff format` → `pyright` → `pytest`.

## Done when
- All three functions call `sync_lookup_column`; the N+1 `filter_by().first()` loops are
  gone.
- New behavioural tests pass; `uv run pytest tests/` green.
- ruff + pyright clean on touched files.

## Not included
- No change to packed JSON shapes, to `db/models.py`, or to the abbrev_other schema
  migration.
- suttas / transliterate (separate threads).
