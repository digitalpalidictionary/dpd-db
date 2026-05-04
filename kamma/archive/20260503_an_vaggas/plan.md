# Plan: AN vagga per-source extractors

**GitHub issue:** #236

## Architecture Decisions
- **One script per source, independent.** No shared helper module.
- **DPD reads the live DB.** Output reflects current state at extraction time.
- **CST reads UTF-16 XML directly.** BeautifulSoup, groups on `rend=chapter`; sub-vaggas in AN1 ch14-16 detected via `SUBVAGGA_RE` on `rend=subhead`.
- **SC reads JSON directly.** Groups on `(folder, vagga)` where vagga = `:0.2`; for peyyāla files where `:0.2` is a paṇṇāsaka label, uses `:0.3` as vagga name.
- **BJT reads `scripts/suttas/bjt/an.tsv`.** Collapses to one row per `(bjt_book, bjt_minor_section, bjt_vagga)`.
- **DPR reads `listam.js` from the DPR repo** at `../../2_Resources/Code/digitalpalireader`. Parses `amlist[book][pannasaka][vagga][section]`; emits one row per section that is a sub-vagga (section has >1 sutta element), otherwise only section 0.
- **`dpd_code` left blank for non-DPD sources.** Manual alignment happens after extraction.

## Phase 1 — DPD extractor
- [x] Create `scripts/suttas/dpd/an_vaggas.py`
- [x] Phase verification: 197 data rows. ✓

## Phase 2 — CST extractor
- [x] Create `scripts/suttas/cst/an_vaggas.py`
  - Fixed: sub-vagga splitting for AN1 ch14-16 (Etadaggavaggo, Aṭṭhānapāḷi, Ekadhammapāḷi)
  - Fixed: peyyāla range parsing (`157-163.` format)
  - Fixed: page numbers now captured at first bodytext not at chapter heading
- [x] Phase verification: 197 data rows. ✓

## Phase 3 — SC extractor
- [x] Create `scripts/suttas/sc/an_vaggas.py`
  - Fixed: AN1/AN2 grouped per file; AN3+ grouped on `(folder, vagga)`
  - Fixed: AN11 peyyāla — when `:0.2` is a paṇṇāsaka label, vagga taken from `:0.3`
- [x] Phase verification: 197 data rows. ✓

## Phase 4 — BJT extractor
- [x] Create `scripts/suttas/bjt/an_vaggas.py`
- [x] Phase verification: 181 data rows (genuine structural difference from other sources). ✓

## Phase 5 — DPR extractor (added during thread)
- [x] Create `scripts/suttas/dpr/an_vaggas.py`
  - Parses `DPR_G.amlist[book][pannasaka][vagga][section]` from `listam.js`
  - Detects sub-vagga sections via presence of element `[section][1]`
  - URL: `a.{book}.0.0.{pannasaka}.{vagga}.{section}.m`
- [x] Phase verification: ~197 data rows. ✓

## Phase 6 — End-to-end (user-driven)
- [x] User ran all scripts and confirmed output.
- [x] User added vaggas to Google Sheet; confirmed db/suttas pipeline (suttas_update.py → suttas_to_lookup.py → export).
