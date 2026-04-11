# Thread: Integrate abbreviations_other.tsv into the exporter pipeline

## Issue Reference
GitHub issue #77 — continuation of the abbreviations master-list thread (20260411_abbreviations_other)

## Context
`shared_data/help/abbreviations_other.tsv` now exists with ~1089 rows from five sources
(pts, dpd_db, general, cone, cpd). The DPD's own abbreviations remain in
`shared_data/help/abbreviations.tsv`. The old `shared_data/abbreviations/` folder and
`scripts/find/abbreviations_finder.py` have been deleted.

The `pos='abbrev'` entries will be dropped from the DPD database (`dpd_headwords`).
Until that happens, `dpd_db` rows in `abbreviations_other.tsv` overlap with the live DB.

## What it should do
1. Update `db/lookup/help_abbrev_add_to_lookup.py` to also read `abbreviations_other.tsv`
   and populate the `lookup` table with entries from all external sources.
2. Decide on presentation: individual dictionary entries per abbreviation, OR a single
   grouped "Abbreviations" help page per source, OR extend the existing help page.
   **This decision must be made before implementation.** Ask the user.
3. Update the GoldenDict / MDict exporter to render the chosen format.
4. Update the webapp (`exporter/webapp/`) if it has an abbreviations help route.
5. Update the WXT browser extension if it consumes the lookup table for abbreviations.
6. Remove the `dpd_db` loader from `compile_abbreviations_other.py` once `pos='abbrev'`
   is dropped from the database.

## Constraints
- Do not touch `shared_data/help/abbreviations.tsv` (DPD's own list, separate pipeline).
- Follow existing exporter patterns — do not invent a new export format.
- Run `db/lookup/help_abbrev_add_to_lookup.py` via `uv run`, not directly.

## Key files to read before starting
- `db/lookup/help_abbrev_add_to_lookup.py` — current consumer of abbreviations
- `shared_data/help/abbreviations_other.tsv` — the new source
- `shared_data/help/abbreviations.tsv` — DPD's own list (for reference)
- `exporter/goldendict/` — GoldenDict export pipeline
- `exporter/webapp/` — webapp routes (check for abbreviations route)

## What's not included
- Scraping new external sources (BJT, SYA, MST) — separate thread
- Docs-website update — separate thread
- Deleting old abbreviations from the database — user handles this directly
