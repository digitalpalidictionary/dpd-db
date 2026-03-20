# Plan: MW2 Cologne Export

## Phase 1: Foundation — Paths, CSS, Download
- [x] Task 1.1: Write tests for mw2 path configuration
- [x] Task 1.2: Add mw2 paths to `resources/other-dictionaries/vendor/dpd_tools/paths.py` and `tools/paths.py`
- [x] Task 1.3: Write tests for auto-download logic (download, compare, unpack)
- [x] Task 1.4: Create `mw_helpers.py` with `download_fresh_source()` function
- [x] Task 1.5: Create `mw.css` from Cologne source CSS + additional classes for inline style replacement

## Phase 2: Data Loading — SQLite to Memory
- [x] Task 2.1: Write tests for abbreviation loading from `mwab.sqlite`
- [x] Task 2.2: Write tests for author tooltip loading from `mwauthtooltips.sqlite`
- [x] Task 2.3: Write tests for entry loading from `mw.sqlite`
- [x] Task 2.4: Write tests for headword key parsing from `mwkeys.sqlite`
- [x] Task 2.5: Implement `load_mw_data()` in `mw_helpers.py` — load all 4 SQLite databases into `MwData` dataclass

## Phase 3: Renderer — XML Pre-processing
- [x] Task 3.1: Write tests for SLP1 accent stripping (with XML slash escaping)
- [x] Task 3.2: Write tests for `<lang>` → `<ab>` and `<s1 n>` → `<ab n>` conversions
- [x] Task 3.3: Write tests for abbreviation tooltip injection
- [x] Task 3.4: Write tests for literature tooltip injection
- [x] Task 3.5: Write tests for lex tooltip injection
- [x] Task 3.6: Create `mw_renderer.py` Phase A: implement all pre-processing transformations

## Phase 4: Renderer — Tag-to-HTML Conversion
- [x] Task 4.1: Write tests for Sanskrit `<s>` → `<span class="sdata">` conversion with SLP1→IAST
- [x] Task 4.2: Write tests for abbreviation `<ab>` → `<span class="dotunder">` rendering
- [x] Task 4.3: Write tests for literature `<ls>`, homonym `<hom>`, grammar `<lex>` rendering
- [x] Task 4.4: Write tests for foreign language tags (`<bot>`, `<gk>`, `<fr>`, etc.) → `.foreign`/`.greek` classes
- [x] Task 4.5: Write tests for structural tags (strip `<info>`, `<pb>`, `<pcol>`, etc.)
- [x] Task 4.6: Write tests for `<div>`, `<F>`, `<C>`, `<Poem>`, `<sup>` rendering
- [x] Task 4.7: Implement `mw_renderer.py` Phase B: all tag-to-HTML conversions (zero inline styles)

## Phase 5: Entry Builder — Headword Assembly
- [x] Task 5.1: Write tests for mwkeys data format parsing (`H1,startL,endL;H1A,startL2,endL2;...`)
- [x] Task 5.2: Write tests for sub-entry grouping by lnum range
- [x] Task 5.3: Write tests for entry HTML assembly (H1-H4 type labels, sub-entry indentation)
- [x] Task 5.4: Write tests for page-column reference rendering
- [x] Task 5.5: Write tests for synonym generation (IAST + niggahitas + SLP1)
- [x] Task 5.6: Implement `build_mw_entries()` in `mw_helpers.py`

## Phase 6: GoldenDict/MDict Export
- [x] Task 6.1: Write tests for GoldenDict export integration (entry count, dict name "mw2")
- [x] Task 6.2: Create `mw_from_cologne.py` — main GoldenDict/MDict exporter using shared helpers
- [x] Task 6.3: Update `export_all.py` — add mw2 import alongside existing mw
- [x] Task 6.4: Conductor - User Manual Verification 'Phase 6: GoldenDict Export' (Protocol in workflow.md)

## Phase 7: Mobile Database Export
- [x] Task 7.1: Write tests for mobile mw2 entry insertion (dict_id="mw2", CSS populated, page refs kept)
- [x] Task 7.2: Add mw2 section to `mobile_exporter.py` alongside existing mw section

## Phase 8: Visual Fidelity Verification
- [x] Task 8.1: Run full GoldenDict export, compare 10+ headwords against Cologne website
- [x] Task 8.2: Verify: teal Sanskrit, red homonyms, gray references, brown foreign text, tooltips
- [x] Task 8.3: Verify zero inline styles in HTML output
- [x] Task 8.4: Verify existing "mw" export still works unchanged
- [x] Task 8.5: Run mobile export, verify mw2 entries with CSS and page references
- [x] Task 8.6: Update documentation (`docs/` folder, READMEs)
- [x] Task 8.7: Conductor - User Manual Verification 'Phase 8: Visual Fidelity' (Protocol in workflow.md)
