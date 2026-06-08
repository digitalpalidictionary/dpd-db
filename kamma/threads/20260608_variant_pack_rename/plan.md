# Plan: rename variants_pack/variants_unpack → variant_pack/variant_unpack

Status: **parked** — pick up after `20260608_lookup_sync`.

## Tasks
- [ ] Rename `variants_pack` → `variant_pack` and `variants_unpack` → `variant_unpack`
  in `db/models.py` (keep the `@property` on unpack; fix the `dict` param name shadowing
  while there if trivial).
- [ ] Update writer call sites in `db/variants/add_to_db.py` (2).
- [ ] Update live reader call sites: `exporter/variants/variants_exporter.py`,
  `exporter/webapp/data_classes.py`, `exporter/tpr/tpr_exporter.py`,
  `exporter/tbw/tbw_exporter.py`.
- [ ] Decide on archive files (`archive/exporter/tpr/tpr_exporter.py`,
  `archive/web_app_old/modules.py`) — likely leave, or update for tidiness.
- [ ] `exporter/kobo/templates/lookup.html` already uses singular `variant_unpack`;
  verify the variant loop now renders (was a silent no-op before).
- [ ] Drop the `pack_attr="variants_pack"` override in `tools/lookup_sync.py` /
  `db/variants/add_to_db.py` once the helper default `f"{column}_pack"` covers `variant`.
- [ ] Gate every touched file; run `uv run pytest tests/`.
