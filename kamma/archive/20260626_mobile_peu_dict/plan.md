# Plan — Add PEU to mobile exporter

## Phase 1 — Mobile exporter code
- [x] Add `_load_peu_dump(path) -> dict[str, str]` helper (JS-dump parser)
- [x] Add gated PEU section in `export_other_dictionaries` (`include_peu` param)
- [x] Add `--peu` flag in `main()` and thread it through
  - ✅ ruff check + format + pyright clean

## Phase 2 — Tests
- [x] Add `peu_source_path` to `_make_paths`; add `include_peu` to `_export`
- [x] Add PEU tests (skipped-by-default, exported-when-on, missing-source-raises)
  - ✅ `uv run pytest tests/exporter/mobile/` → 101 passed

## Phase 3 — Submodule (user commits)
- [x] Download latest source from `https://pm12e.pali.tools/dump`
- [x] Recompress PEU only (scoped tar+zstd, NOT compress_sources.py — that rebuilds all archives)
- [x] Rebuild goldendict/mdict: `uv run -m dictionaries.peu.peu`
- [x] Rebuild mobile db with `--peu` → `exporter/share/dpd-mobile-db.zip` (PEU = 203,865 entries)

## Review
- [ ] `/kamma:3-review`
- [ ] Address findings
- [ ] `/kamma:4-finalize`
