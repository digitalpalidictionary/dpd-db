# Plan: Integrate abbreviations_other into exporter pipeline

Issue: #77

## Pre-flight (ask user before starting)
- [ ] P.0 Ask: how should external abbreviations be presented?
  - Option A: Extend existing help page (one big page, grouped by source)
  - Option B: Separate dictionary entry per source ("Cone Abbreviations", "CPD Abbreviations", etc.)
  - Option C: Individual entries per abbreviation (merged with DPD abbrevs)
  Wait for answer before Phase 1.

## Phase 1 — Drop dpd_db loader (after DB cleanup)
- [ ] 1.1 Confirm `pos='abbrev'` has been removed from `dpd_headwords` table.
- [ ] 1.2 Remove `load_dpd_db` function and its entry in `loaders` list from
      `scripts/extractor/compile_abbreviations_other.py`.
- [ ] 1.3 Re-run script, confirm `dpd_db` rows gone from TSV.
- [ ] 1.4 Update `shared_data/help/abbreviations_other_README.md` row counts.

## Phase 2 — Lookup table integration
- [ ] 2.1 Read `db/lookup/help_abbrev_add_to_lookup.py` in full.
- [ ] 2.2 Add logic to also read `abbreviations_other.tsv` and upsert rows into
      the `lookup` table with appropriate `lookup_key` and `headwords` JSON.
- [ ] 2.3 Run `uv run python db/lookup/help_abbrev_add_to_lookup.py` (user runs this).
- [ ] 2.4 Verify lookup entries exist for spot-check abbreviations (AAWG, Be, Ee, SLTP).

## Phase 3 — Exporter rendering (depends on P.0 decision)
- [ ] 3.1 Read relevant exporter files for the chosen format.
- [ ] 3.2 Implement rendering per the agreed presentation.
- [ ] 3.3 Build and spot-check output in GoldenDict.

## Phase 4 — Webapp & extension
- [ ] 4.1 Check `exporter/webapp/` for any abbreviations route and update if needed.
- [ ] 4.2 Check `exporter/wxt_extension/` for abbreviations consumption and update.

## Phase 5 — Verify & clean up
- [ ] 5.1 Run full exporter pipeline (user runs).
- [ ] 5.2 Spot-check rendered output for each source.
- [ ] 5.3 Update README with final row counts.
