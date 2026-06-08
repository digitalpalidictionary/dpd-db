# Spec: rename variants_pack/variants_unpack → variant_pack/variant_unpack

## GitHub issue
#157 Refactoring (cleanup follow-up)

## Why
`Lookup` has one naming inconsistency: the column is `variant` (singular) but its
methods are `variants_pack` / `variants_unpack` (plural). Every other column matches
its methods (`grammar` → `grammar_pack`, `see` → `see_pack`, …). The lookup_sync helper
(`tools/lookup_sync.py`) defaults to `f"{column}_pack"`, so `variant` is the only column
that needs a `pack_attr="variants_pack"` override. Renaming removes that special case and
fixes a latent kobo template bug.

This is a **pure Python method rename** on `db/models.py::Lookup`:
- the column stays `variant`, stored JSON is unchanged
- **no DB schema change, no migration, no rebuild**

## Scope
Rename both methods and update every caller.

`variants_pack` (writer):
- `db/models.py` (definition, ~line 280)
- `db/variants/add_to_db.py` (2 call sites, ~lines 81, 114)

`variants_unpack` (readers, live):
- `exporter/variants/variants_exporter.py:67`
- `exporter/webapp/data_classes.py:71`
- `exporter/tpr/tpr_exporter.py:160`
- `exporter/tbw/tbw_exporter.py:186`

Archive (decide whether to touch — they are archived, currently reference old name):
- `archive/exporter/tpr/tpr_exporter.py:286`
- `archive/web_app_old/modules.py:69`

## Latent bug to fix in the same pass
`exporter/kobo/templates/lookup.html:20` already calls `i.variant_unpack` (singular) —
a method that does **not** currently exist, so Jinja resolves it to `Undefined` and the
kobo variant loop silently iterates nothing. After the rename to singular, this template
becomes correct automatically. Verify the kobo variant section then renders.

## After the rename
Drop the `pack_attr="variants_pack"` override at the variant call site in
`tools/lookup_sync.py` (and in `db/variants/add_to_db.py` once it adopts the helper) so
the default `f"{column}_pack"` covers `variant` like every other column.

## Constraints
- Behaviour-preserving rename only. No JSON shape change, no schema change.
- Gate per file: `ruff check --fix` → `ruff format` → `pyright` → `pytest`.

## Done when
- No reference to `variants_pack` / `variants_unpack` remains in live code.
- All exporters and the kobo template render variants correctly.
- `tools/lookup_sync.py` no longer needs the `variant` special case.
- `uv run pytest tests/` green.

## Not included
- The lookup_sync DRY refactor itself (separate thread: `20260608_lookup_sync`).
