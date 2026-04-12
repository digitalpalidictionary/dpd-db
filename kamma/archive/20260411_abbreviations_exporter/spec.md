# Thread: Integrate abbreviations_other.tsv into the exporter pipeline

## Issue Reference
GitHub issue #77 — continuation of thread 20260411_abbreviations_other

## Context (read before starting)
- `shared_data/help/abbreviations_other.tsv` — 1089 rows, columns:
  `source | abbreviation | meaning | category | notes`
  Sources: `PTS`, `CPD`, `Cone`, `CST`, `General`
- `shared_data/help/abbreviations.tsv` — DPD's own abbreviations (untouched)
- `db/lookup/help_abbrev_add_to_lookup.py` — populates the `Lookup` table:
  - `Lookup.abbrev` column stores DPD abbreviations (JSON packed)
  - A new `Lookup.abbrev_other` column (or similar) is needed for other-source abbreviations
- `db/models.py` `Lookup` class — has `abbrev: Mapped[str]`, `abbrev_pack/unpack`
- `exporter/goldendict/export_help.py` — `add_abbrev_html()` reads the TSV and renders
  one `DictEntry` per abbreviation using `exporter/goldendict/templates/help_abbrev.jinja`
- `exporter/goldendict/data_classes.py` — `AbbreviationsData` wraps each row
- `exporter/webapp/toolkit.py` — reads `Lookup.abbrev` and renders
  `abbreviations.html` / `abbreviations_summary.html` templates
- `tools/paths.py` — `abbreviations_tsv_path` points to `shared_data/help/abbreviations.tsv`;
  a new `abbreviations_other_tsv_path` is needed
- WXT extension uses the webapp — no separate work required

## What it should do

### 1. Database / Lookup table
Add a new column `abbrev_other` to `Lookup` (mirroring the existing `abbrev` column).
Populate it via a new `add_abbreviations_other()` function in
`db/lookup/help_abbrev_add_to_lookup.py`.

Column is added at runtime via `ensure_abbrev_other_column()` (idempotent ALTER TABLE),
not via Alembic. DB version bumped via `tools/version.py` (`minor = 4`).

The packing format for `abbrev_other` differs from `abbrev`: instead of a flat
`{meaning: ..., pali: ..., example: ..., explanation: ...}` dict, each entry stores a
**list of source-meaning pairs**, so all sources for one abbreviation are grouped:
```json
[
  {"source": "PTS", "meaning": "Cambodian", "notes": ""},
  {"source": "Cone", "meaning": "Cambodian", "notes": ""},
  {"source": "CST", "meaning": "Cambodia; variant reading ...", "notes": ""}
]
```
Multiple rows in the TSV with the same `abbreviation` value → grouped into one lookup key.

Use `@property` (not `@cached_property`) for `abbrev_other_unpack` — `cached_property`
stores in `__dict__` which SQLAlchemy can interfere with on mapped objects.

### 2. GoldenDict export
Add `add_abbrev_other_html()` in `exporter/goldendict/export_help.py` (alongside the
existing `add_abbrev_html()`). It:
- Reads `abbreviations_other.tsv`
- Groups rows by `abbreviation`
- Renders one `DictEntry` per unique abbreviation using a new Jinja2 template
  `exporter/goldendict/templates/help_abbrev_other.jinja`
- The rendered layout:
  - `<h3>` abbreviation, `<h4>Other Abbreviations</h4>` subheading
  - Table rows: `source | meaning (notes)` — no "Abbreviation" header row
- The DictEntry `word` = abbreviation, `synonyms` = [] (no extra synonyms needed)

### 3. Webapp export
Add rendering of `abbrev_other` in `exporter/webapp/toolkit.py`. Placed at the **very
end** of both rendering blocks (last item in the summary list).

New templates `abbreviations_other.html` / `abbreviations_other_summary.html`:
- Summary: `ka other abbreviations. ►` — same pattern as `grammar: ka`, `variants: ka`
- Detail heading: `<h3 class="dpd" id="other abbreviations: ka">other abbreviations: ka</h3>`
- Table rows: `source | meaning (notes)` — no redundant heading inside the div
- Template paths added to `tools/paths.py` as `template_abbreviations_other_summary` /
  `template_abbreviations_other`

### 4. paths.py
Add `abbreviations_other_tsv_path = base_dir / "shared_data/help/abbreviations_other.tsv"`

## Constraints
- Do not modify `abbreviations.tsv` or the existing `abbrev` column/pipeline.
- Mirror existing patterns exactly — same class structure, same pack/unpack pattern.
- Do not run scripts. User runs them.
- Modern type hints, Path, no sys.path hacks.

## How we'll know it's done
- Looking up `ka` in GoldenDict shows a grouped table with rows for each source.
- Looking up `ka` in the webapp shows the same grouped table.
- Looking up an abbreviation that exists only in `abbreviations_other.tsv` (e.g. `AAWG`,
  `Be`, `SLTP`) works in both GoldenDict and webapp.
- Abbreviations only in `abbreviations.tsv` (DPD-only) are unaffected.

## What's not included
- Dropping `pos='abbrev'` from the database — user handles separately; `dpd_db` rows
  stay in `abbreviations_other.tsv` until then, then remove `load_dpd_db` from the
  compile script.
- Kindle, Kobo, mobile exporters — deferred.
- Docs-website update — deferred.
- Scraping new external sources (BJT, SYA, MST) — separate thread.
