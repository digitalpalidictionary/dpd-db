# Spec — Add PEU dictionary to mobile exporter (+ update source, rebuild goldendict)

## Request
- Add the Burmese Abhidāṇa / PEU dictionary ("Pali English Ultimate" = Pali Myanmar Abhidhan) to the mobile DB exporter.
- Update the PEU source to the latest version.
- Rebuild the PEU GoldenDict/MDict export.
- Follow the same format as the other mobile dictionaries (cone / cpd).

## Decisions (from user)
- **Gating:** PEU is **flag-gated, default OFF** (like `--cone`), via a new `--peu` flag. Quality is poor and the user does not want it distributed; it is for local use only.
- **Submodule commits:** the user will commit any `resources/other-dictionaries` submodule changes themselves.
- Download link for the latest source: `https://pm12e.pali.tools/dump` → `dictionaries/peu/source/peu_dump.js`.

## Scope

### Main repo — `exporter/mobile/mobile_exporter.py`
- Add `--peu` CLI flag and thread `include_peu: bool = False` into `export_other_dictionaries`.
- Add a gated PEU section, mirroring the existing `--cone` block:
  - When off: `pr.green_tmr("skipping PEU dictionary")` / `pr.yes("off")`.
  - When on: parse the JS dump at `g.pth.peu_source_path`, replace `ṁ`→`ṃ` on word + html (matching `peu.py`), compute `word_fuzzy` via `_strip_diacritics_mobile`, insert into `dict_entries` + `dict_meta`.
  - `dict_id="peu"`, name `"Pali English Ultimate"`, author `"Pali Myanmar Abhidhan"`, css `""` (PEU has no stylesheet).
  - Missing source raises the standard `_missing_source_error("PEU", ...)`.
- Add a `_load_peu_dump(path) -> dict[str, str]` helper replicating `dictionaries/peu/peu.py::extract_peu_from_data_dump` parsing (strip `var x = {...};` wrapper, drop control chars, JS→JSON quote swap, `json.loads`).
- No `DB_SCHEMA_VERSION` bump — only rows added, Drift tables unchanged.

### Tests — `tests/exporter/mobile/test_mobile_exporter.py`
- Add `peu_source_path` to `_make_paths`.
- Add `include_peu` to the `_export` helper.
- Tests: PEU skipped by default; PEU exported (parsing + ṁ→ṃ + fuzzy + meta) when `include_peu=True`; missing PEU source raises.

### Submodule — `resources/other-dictionaries` (user commits)
- Download latest source from the link, recompress `peu.tar.zst` via `compress_sources.py`.
- Rebuild PEU goldendict + mdict via `dictionaries.peu.peu`.

## Out of scope
- `prepare_sources.py` `mobile_critical` is NOT modified — PEU is optional (off by default), like cone, so it is not a mobile-critical source.
- No schema/version changes.

## Notes / assumptions
- PEU html mirrors the goldendict export's minimal handling (only `ṁ`→`ṃ`); no link-stripping/DOCTYPE removal, since the source has none and `peu.py` does none.
