# Plan: MW2 Cologne Export

## Phase 1: Foundation — Paths, CSS, Download
- [ ] Task 1.1: Write tests for mw2 path configuration
- [ ] Task 1.2: Add mw2 paths to `resources/other-dictionaries/vendor/dpd_tools/paths.py` and `tools/paths.py`
- [ ] Task 1.3: Write tests for auto-download logic (download, compare, unpack)
- [ ] Task 1.4: Create `mw_helpers.py` with `download_fresh_source()` function
- [ ] Task 1.5: Create `mw.css` from Cologne source CSS + additional classes for inline style replacement

## Phase 2: Data Loading — SQLite to Memory
- [ ] Task 2.1: Write tests for abbreviation loading from `mwab.sqlite`
- [ ] Task 2.2: Write tests for author tooltip loading from `mwauthtooltips.sqlite`
- [ ] Task 2.3: Write tests for entry loading from `mw.sqlite`
- [ ] Task 2.4: Write tests for headword key parsing from `mwkeys.sqlite`
- [ ] Task 2.5: Implement `load_mw_data()` in `mw_helpers.py` — load all 4 SQLite databases into `MwData` dataclass

## Phase 3: Renderer — XML Pre-processing
- [ ] Task 3.1: Write tests for SLP1 accent stripping (with XML slash escaping)
- [ ] Task 3.2: Write tests for `<lang>` → `<ab>` and `<s1 n>` → `<ab n>` conversions
- [ ] Task 3.3: Write tests for abbreviation tooltip injection
- [ ] Task 3.4: Write tests for literature tooltip injection
- [ ] Task 3.5: Write tests for lex tooltip injection
- [ ] Task 3.6: Create `mw_renderer.py` Phase A: implement all pre-processing transformations

## Phase 4: Renderer — Tag-to-HTML Conversion
- [ ] Task 4.1: Write tests for Sanskrit `<s>` → `<span class="sdata">` conversion with SLP1→IAST
- [ ] Task 4.2: Write tests for abbreviation `<ab>` → `<span class="dotunder">` rendering
- [ ] Task 4.3: Write tests for literature `<ls>`, homonym `<hom>`, grammar `<lex>` rendering
- [ ] Task 4.4: Write tests for foreign language tags (`<bot>`, `<gk>`, `<fr>`, etc.) → `.foreign`/`.greek` classes
- [ ] Task 4.5: Write tests for structural tags (strip `<info>`, `<pb>`, `<pcol>`, etc.)
- [ ] Task 4.6: Write tests for `<div>`, `<F>`, `<C>`, `<Poem>`, `<sup>` rendering
- [ ] Task 4.7: Implement `mw_renderer.py` Phase B: all tag-to-HTML conversions (zero inline styles)

## Phase 5: Entry Builder — Headword Assembly
- [ ] Task 5.1: Write tests for mwkeys data format parsing (`H1,startL,endL;H1A,startL2,endL2;...`)
- [ ] Task 5.2: Write tests for sub-entry grouping by lnum range
- [ ] Task 5.3: Write tests for entry HTML assembly (H1-H4 type labels, sub-entry indentation)
- [ ] Task 5.4: Write tests for page-column reference rendering
- [ ] Task 5.5: Write tests for synonym generation (IAST + niggahitas + SLP1)
- [ ] Task 5.6: Implement `build_mw_entries()` in `mw_helpers.py`

## Phase 6: GoldenDict/MDict Export
- [ ] Task 6.1: Write tests for GoldenDict export integration (entry count, dict name "mw2")
- [ ] Task 6.2: Create `mw_from_cologne.py` — main GoldenDict/MDict exporter using shared helpers
- [ ] Task 6.3: Update `export_all.py` — add mw2 import alongside existing mw
- [ ] Task 6.4: Conductor - User Manual Verification 'Phase 6: GoldenDict Export' (Protocol in workflow.md)

## Phase 7: Mobile Database Export
- [ ] Task 7.1: Write tests for mobile mw2 entry insertion (dict_id="mw2", CSS populated, page refs kept)
- [ ] Task 7.2: Add mw2 section to `mobile_exporter.py` alongside existing mw section

## Phase 8: Visual Fidelity Verification
- [ ] Task 8.1: Run full GoldenDict export, compare 10+ headwords against Cologne website
- [ ] Task 8.2: Verify: teal Sanskrit, red homonyms, gray references, brown foreign text, tooltips
- [ ] Task 8.3: Verify zero inline styles in HTML output
- [ ] Task 8.4: Verify existing "mw" export still works unchanged
- [ ] Task 8.5: Run mobile export, verify mw2 entries with CSS and page references
- [ ] Task 8.6: Update documentation (`docs/` folder, READMEs)
- [ ] Task 8.7: Conductor - User Manual Verification 'Phase 8: Visual Fidelity' (Protocol in workflow.md)
