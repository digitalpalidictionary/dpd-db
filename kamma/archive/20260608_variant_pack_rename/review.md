## Thread
- **ID:** 20260608_variant_pack_rename
- **Objective:** Rename `variants_pack`/`variants_unpack` → `variant_pack`/`variant_unpack` on Lookup, drop the `pack_attr` override, fix latent kobo template bug. (#157)

## Files Changed
- `db/models.py` — rename methods + fix `dict` param shadowing → `data`
- `db/variants/add_to_db.py` — drop `pack_attr="variants_pack"` override
- `tools/lookup_sync.py` — update docstring (no longer lists variant as irregular)
- `exporter/webapp/data_classes.py` — `variants_unpack` → `variant_unpack`
- `exporter/variants/variants_exporter.py` — `variants_unpack` → `variant_unpack`
- `exporter/tpr/tpr_exporter.py` — `variants_unpack` → `variant_unpack`
- `exporter/tbw/tbw_exporter.py` — `variants_unpack` → `variant_unpack`
- `tests/db/variants/test_add_to_db.py` — all references updated
- `tests/tools/test_lookup_sync.py` — test updated to use new names

## Findings
No findings.

## Fixes Applied
None.

## Test Evidence
- `uv run ruff check --fix` → all passed
- `uv run ruff format --check` → 9 files already formatted
- `uv run pyright` → 0 errors, 0 warnings
- `uv run pytest tests/db/variants/ tests/tools/test_lookup_sync.py` → 79 passed
- `uv run pytest tests/` → 510 passed

## Verdict
PASSED
- Review date: 2026-06-08
- Reviewer: kamma (inline)
