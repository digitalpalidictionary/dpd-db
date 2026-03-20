# Plan: Apte Practical Sanskrit-English Dictionary from Cologne Source

## Phase 1: Project Scaffolding & Paths

- [x] Task 1.1: Create directory structure and boilerplate files
  - [x] Create `dictionaries/apte/` directory
  - [x] Create `dictionaries/apte/__init__.py` (empty file)
  - [x] Create `dictionaries/apte/source/` directory (for downloads)
  - [x] Create `dictionaries/apte/apte.css` — copy exact CSS from spec §5 (comment header: "Apte CSS"). MUST include `font-style: italic` on `.sdata` and `currentColor` on `.dotunder`
  - [x] Create `dictionaries/apte/README.md` — source info, run command (`uv run python -m dictionaries.apte.apte_from_cologne`), output paths

- [x] Task 1.2: Add Apte paths to `vendor/dpd_tools/paths.py`
  - [x] Add `self._setup_apte_paths()` call in `__init__` (after `_setup_mw_paths()`)
  - [x] Add `_setup_apte_paths` method with:
    - `self.apte_source_dir = d / "source" / "web" / "sqlite"`
    - `self.apte_zip_path = d / "source" / "ap90web1.zip"` (Cologne zip name is `ap90web1.zip`)
    - `self.apte_json_path = d / "source" / "apte.json"`
    - `self.apte_css_path = d / "apte.css"`
    - `self.apte_gd_path = self.goldendict_path`
    - `self.apte_mdict_path = self.mdict_path`
  - [x] Base directory: `d = self.dictionaries_dir / "apte"`

- [x] Task 1.3: Add Apte paths to `tools/paths.py` (dpd-db side)
  - [x] Add paths following the MW pattern:
    - `self.apte_css_path` → `resources/other-dictionaries/dictionaries/apte/apte.css`
    - `self.apte_source_dir` → `resources/other-dictionaries/dictionaries/apte/source/web/sqlite`
    - `self.apte_zip_path` → `resources/other-dictionaries/dictionaries/apte/source/ap90web1.zip`
    - `self.apte_source_json_path` → `resources/other-dictionaries/dictionaries/apte/source/apte.json`
    - `self.apte_gd_path` → `resources/other-dictionaries/build/goldendict/`
    - `self.apte_mdict_path` → `resources/other-dictionaries/build/mdict/`

- [x] Task 1.4: Write tests for paths
  - [x] Create `tests/test_apte_paths.py`
  - [x] Test that `RepoPaths()` has all 6 apte path attributes
  - [x] Test that `apte_css_path` filename is `apte.css`
  - [x] Test that `apte_zip_path` filename is `ap90web1.zip` (Cologne name)

- [x] Task: Conductor - User Manual Verification 'Phase 1: Project Scaffolding & Paths' (Protocol in workflow.md)

## Phase 2: Auto-Download

- [x] Task 2.1: Write download tests
  - [ ] Create `tests/test_apte_download.py`
  - [ ] Test `APTE_ZIP_URL` constant points to correct Cologne URL
  - [ ] Test download function signature accepts `zip_path` and `source_dir` params
  - [ ] Test that download skips when local file size matches `Content-Length` header (mock HTTP)
  - [ ] Test that download proceeds when sizes differ (mock HTTP)

- [x] Task 2.2: Implement auto-download in `apte_helpers.py`
  - [ ] Define `APTE_ZIP_URL = "https://www.sanskrit-lexicon.uni-koeln.de/scans/AP90Scan/2020/downloads/ap90web1.zip"`
  - [ ] Copy `download_fresh_source()` from `mw_helpers.py`
  - [ ] Adapt: change `MW_ZIP_URL` → `APTE_ZIP_URL`, change zip internal path references if needed
  - [ ] Logic: HEAD request → compare Content-Length to local file size → download if different → unzip

- [x] Task: Conductor - User Manual Verification 'Phase 2: Auto-Download' (Protocol in workflow.md)

## Phase 3: Data Loading

- [x] Task 3.1: Write data loading tests
  - [ ] Create `tests/test_apte_data_loading.py`
  - [ ] Test `ApteData` dataclass has 4 fields: `abbreviations`, `author_tooltips`, `entries`, `keys`
  - [ ] Test `ApteEntry` dataclass has fields: `key`, `lnum`, `data`
  - [ ] Test `ApteKeyEntry` dataclass has fields: `key`, `lnum`, `sections` (list of tuples)
  - [ ] Test abbreviation loading extracts `<disp>` content from raw data
  - [ ] Test key data parsing: `"H1,1.0,5.0;H1A,6.0,10.0"` → `[("H1", 1.0, 5.0), ("H1A", 6.0, 10.0)]`

- [x] Task 3.2: Implement data loading in `apte_helpers.py`
  - [ ] Define `ApteEntry` and `ApteKeyEntry` dataclasses
  - [ ] Define `ApteData` dataclass
  - [ ] Implement `load_apte_data(source_dir: Path) -> ApteData`
  - [ ] SQL queries use Cologne table names: `ap90`, `ap90keys`, `ap90ab`, `ap90authtooltips`
  - [ ] Abbreviation parsing: extract `<disp>` content via regex from raw data
  - [ ] Key data parsing: split on `;`, then split each segment on `,` → `(h_type, float(start), float(end))`

- [x] Task: Conductor - User Manual Verification 'Phase 3: Data Loading' (Protocol in workflow.md)

## Phase 4: Renderer — Preprocessing (Phase A)

- [x] Task 4.1: Write preprocessing tests
  - [ ] Create `tests/test_apte_renderer_preprocess.py`
  - [ ] Test broken bar replacement: `"a¦b"` → `"a b"`
  - [ ] Test SLP1 accent stripping protects XML slashes:
    - Input: `<s>a/b^c\\d</s>` → accents stripped, `</` and `/>` preserved
    - CRITICAL: verify `</s>` is NOT corrupted to `<_s>` or similar
  - [ ] Test `<lang n='X'>` → `<ab n='X'>` normalization
  - [ ] Test `<s1 n='X'>` → `<ab n='X'>` normalization
  - [ ] Test literature tooltip injection: `<ls>ABBREV.</ls>` gets `n='tooltip'` when found in dict
  - [ ] Test `<ls>ib.` special case → `<ls><ab>ib.</ab>`
  - [ ] Test abbreviation tooltip injection: `<ab>X</ab>` without `n=` gets tooltip from dict
  - [ ] Test `<ab n='existing'>` is NOT double-injected
  - [ ] Test lex tooltip injection: plain text inside `<lex>` → `<ab n='tooltip'>` tags
  - [ ] **CRITICAL test**: `inject_lex_tooltips` output still contains `<lex>` wrapper (MW mistake #6)

- [x] Task 4.2: Implement preprocessing in `apte_renderer.py`
  - [ ] Copy preprocessor functions from `mw_renderer.py`
  - [ ] Adapt function names: `preprocess_xml(xml, abbreviations, author_tooltips) -> str`
  - [ ] Execute preprocessing steps in EXACT order from spec §3 Phase A:
    1. Replace broken bar
    2. Strip SLP1 accents (with XML slash protection)
    3. Normalize `<lang>` and `<s1>` to `<ab>`
    4. Inject literature tooltips
    5. Inject abbreviation tooltips
    6. Inject lex tooltips (KEEP `<lex>` wrapper!)
  - [ ] `inject_lex_tooltips` MUST return `f"<lex>{''.join(result)}</lex>"` — NOT strip the wrapper

- [x] Task: Conductor - User Manual Verification 'Phase 4: Renderer — Preprocessing' (Protocol in workflow.md)

## Phase 5: Renderer — Tag-to-HTML (Phase B)

- [x] Task 5.1: Write tag rendering tests
  - [ ] Create `tests/test_apte_renderer_tags.py`
  - [ ] Test `<h>SLP1_CONTENT</h>` block is stripped entirely (content included) — MW mistake #2
  - [ ] Test H-type extraction: `<H1>` → `"H1"`, `<H1A>` → `"H1A"`
  - [ ] Test `<pc>` extraction and stripping
  - [ ] Test `<L>` extraction BEFORE stripping — MW mistake #3
  - [ ] Test `_render_s_tags`: `<s>agni</s>` → `<span class="sdata">agni</span>` (SLP1→IAST)
  - [ ] Test `_render_ab_tags` with and without `n=` attribute
  - [ ] Test `_render_ls_tags` with and without `n=` attribute (trailing space)
  - [ ] Test `_render_hom_tags`: `<hom>1</hom>` → `<span class="hom" title="Homonym">1</span>`
  - [ ] Test `_render_bot_bio_tags`:
    - `<bot n='X'>Y</bot>` → `class="foreign dotunder"` + `title="X"` — MW mistake #11
    - `<bot>Y</bot>` → `class="foreign"` only
    - `<zoo n='X'>Y</zoo>` → same as bot — MW mistake #9
    - `<bio>Y</bio>` → `class="foreign"`
  - [ ] Test `_render_foreign_lang_tags` for ALL 9 tags: `<gk>`, `<fr>`, `<ger>`, `<lat>`, `<tib>`, `<toch>`, `<arab>`, `<rus>`, `<mong>` — MW mistake #10
  - [ ] Test `_render_div_tags`: self-closing `<div .../>` → `<div class="div-sep"></div>`
  - [ ] Test `_render_footnote_tags`: `<F>X</F>` → `<br/>[<span class="fn-label">Footnote: </span><span>X</span>]`
  - [ ] Test `_render_c_tags`: `<C n="1">X</C>` → `<strong>(C1)</strong>X`
  - [ ] Test `_render_misc_tags`:
    - `<lex>f.</lex>` → `<strong>f.</strong>` (bold grammar labels — MW mistake #6)
    - `<b>X</b>` → `<strong>X</strong>`
    - `<i>X</i>` → `<em>X</em>`
    - `<etym>X</etym>` → `<em>X</em>`
    - `<lang>X</lang>` fallback → `<em>X</em>` — MW mistake #12
    - `<lb/>` → `<br/>`
  - [ ] Test assembly: primary headings (H1-H4) get label + page link, secondary (H1A etc.) do not — MW mistake #14
  - [ ] Test assembly: record ID appended as `[ID=VALUE]` — MW mistake #3
  - [ ] Test assembly: scan URL uses `dict=AP90` (Cologne code)
  - [ ] Test assembly: NO `<h3>` headword title — MW mistake #5

- [x] Task 5.2: Implement tag-to-HTML rendering in `apte_renderer.py`
  - [ ] Copy render functions from `mw_renderer.py`
  - [ ] Implement `render_xml_to_html(xml) -> str`
  - [ ] Step 1: Extract H-type, page-column, record ID BEFORE stripping
  - [ ] Step 2: Strip `<h>...</h>` blocks with `re.sub(r"<h>.*?</h>", "", xml, flags=re.DOTALL)` — strip CONTENT too
  - [ ] Step 2: Strip H-type tags, `<pc>`, `<L>`, self-closing tags, paired structural tags
  - [ ] Step 3: Render tags in EXACT order from spec §3 Phase B Step 3 (10 render functions)
  - [ ] Step 4: Assembly — primary headings get label with scan URL (`dict=AP90`), page link, record ID
  - [ ] `_SCAN_URL_BASE` = `"https://www.sanskrit-lexicon.uni-koeln.de/scans/csl-apidev/servepdf.php?dict=AP90&page="`
  - [ ] DO NOT add `<h3>` headword title

- [x] Task: Conductor - User Manual Verification 'Phase 5: Renderer — Tag-to-HTML' (Protocol in workflow.md)

## Phase 6: Entry Builder

- [x] Task 6.1: Write entry builder tests
  - [ ] Create `tests/test_apte_entry_builder.py`
  - [ ] Test entries are wrapped in `<p>` tags (not bare newlines) — MW mistake #4
  - [ ] Test full HTML document wrapper present: `<!DOCTYPE html>...<link href="apte.css"...` — MW mistake #1
  - [ ] Test CSS filename in wrapper is `apte.css` (not `ap90.css`)
  - [ ] Test synonym generation includes IAST + SLP1 variants
  - [ ] Test `build_apte_entries` returns list of `DictEntry` objects with `word`, `definition_html`, `definition_plain`, `synonyms`

- [x] Task 6.2: Implement entry builder in `apte_helpers.py`
  - [ ] Implement `build_apte_entries(data: ApteData) -> list[DictEntry]`
  - [ ] Copy structure from `build_mw_entries` in `mw_helpers.py`
  - [ ] HTML wrapper: `'<!DOCTYPE html><html><head><meta charset="utf-8"><link href="apte.css" rel="stylesheet"></head><body>'`
  - [ ] Each sub-entry wrapped in `<p>` tags
  - [ ] Synonym generation: IAST + niggahita variants + original SLP1, deduplicated via `set()`
  - [ ] Progress counter: display IAST via `slp1_translit()` — MW mistake #13
  - [ ] Use `bisect.bisect_left`/`bisect_right` for O(log n) range lookups

- [x] Task: Conductor - User Manual Verification 'Phase 6: Entry Builder' (Protocol in workflow.md)

## Phase 7: Main Exporter & Integration

- [x] Task 7.1: Write export tests
  - [ ] Create `tests/test_apte_export.py`
  - [ ] Test `main()` function exists and is callable
  - [ ] Test `DictInfo` uses bookname="Apte Practical Sanskrit-English Dictionary, 1890"
  - [ ] Test `DictVariables` uses `dict_name="apte"`

- [x] Task 7.2: Implement main exporter `apte_from_cologne.py`
  - [ ] Copy structure from `mw_from_cologne.py`
  - [ ] Update all references: `mw` → `apte` in function calls, paths, titles
  - [ ] `DictInfo`: bookname="Apte Practical Sanskrit-English Dictionary, 1890", author="Vaman Shivram Apte"
  - [ ] `DictVariables`: `dict_name="apte"`, `css_paths=[pth.apte_css_path]`
  - [ ] Save `apte.json` intermediate file
  - [ ] Export GoldenDict + MDict
  - [ ] pr.title: `"exporting apte (cologne source) to GoldenDict, MDict"`

- [x] Task 7.3: Add Apte to `scripts/export_all.py`
  - [ ] Add import: `from dictionaries.apte.apte_from_cologne import main as apte`
  - [ ] Add call: `apte()` (after `mw()` in the alphabetical list)

- [x] Task: Conductor - User Manual Verification 'Phase 7: Main Exporter & Integration' (Protocol in workflow.md)

## Phase 8: Documentation

- [x] Task 8.1: Update `docs/other_dicts.md`
  - [ ] Add row to GoldenDict table: `| Apte Sanskrit-English Dictionary | [apte-gd.zip](...) |`
  - [ ] Add row to MDict table: `| Apte Sanskrit-English Dictionary | [apte-mdict.zip](...) |`
  - [ ] Download link pattern: `https://github.com/digitalpalidictionary/other-dictionaries/releases/latest/download/apte-gd.zip`

- [x] Task 8.2: Update `resources/other-dictionaries/README.md`
  - [ ] Add row to dictionary table: `| apte | Apte (Cologne) | Sanskrit-English dictionary (from Cologne source) |`
  - [ ] Insert alphabetically (after `abt`, before `bhs`)

- [x] Task 8.3: Lint and format all changed files
  - [ ] Run `uv run ruff check --fix` on all new/changed files
  - [ ] Run `uv run ruff format` on all new/changed files

- [x] Task: Conductor - User Manual Verification 'Phase 8: Documentation' (Protocol in workflow.md)
