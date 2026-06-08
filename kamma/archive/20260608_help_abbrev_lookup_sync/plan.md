# Plan: migrate help_abbrev_add_to_lookup.py to sync_lookup_column

Status: **done**

## Tasks
- [x] `add_help`: build `data = {key: v["meaning"] for key, v in help_data.items()}`,
  replace clear loop + N+1 upsert with `sync_lookup_column(g.db_session, "help", data)`.
- [x] `add_abbreviations`: replace with `sync_lookup_column(g.db_session, "abbrev", abbrevs)`.
- [x] `add_abbreviations_other`: keep normalize + group into `grouped`, then
  `sync_lookup_column(g.db_session, "abbrev_other", grouped)`.
- [x] Remove unused imports (`is_another_value` if no longer used). Keep
  `ensure_abbrev_other_column` and its call in `main`.
- [x] Add `tests/db/lookup/test_help_abbrev_add_to_lookup.py` (in-memory sqlite):
  help + abbrev insert/update/stale-clear/stale-delete; abbrev_other dotted/undotted
  key collapse.
- [x] Gate touched files + `uv run pytest tests/`.

## Notes
- `abbrev_pack` / `abbrev_other_pack` use `indent=1`; the helper's default
  `f"{col}_pack"` resolves correctly for both — no `pack_attr` override needed.
- Pure DRY + N+1 fix; no intended behaviour change beyond removing the per-key queries.
