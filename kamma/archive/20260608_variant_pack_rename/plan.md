# Plan: rename variants_pack/variants_unpack → variant_pack/variant_unpack

## Tasks
- [x] Rename `variants_pack` → `variant_pack` and `variants_unpack` → `variant_unpack`
  in `db/models.py` (kept `@property` on unpack; fixed `dict` param → `data`).
- [x] Update writer call sites in `db/variants/add_to_db.py` (dropped pack_attr override).
- [x] Update live reader call sites: `exporter/variants/variants_exporter.py`,
  `exporter/webapp/data_classes.py`, `exporter/tpr/tpr_exporter.py`,
  `exporter/tbw/tbw_exporter.py`.
- [x] Decide on archive files — left as-is (archive is frozen).
- [x] `exporter/kobo/templates/lookup.html` already uses singular `variant_unpack`;
  rename makes it correct. Verify via exporters in testing.
- [x] Drop the `pack_attr="variants_pack"` override in `db/variants/add_to_db.py`
  and update comment in `tools/lookup_sync.py`.
- [x] Gate every touched file; `uv run ruff check --fix` → `ruff format` → `pyright` all pass.
- [x] `uv run pytest tests/` → 510 passed.
