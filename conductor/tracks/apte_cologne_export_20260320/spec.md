# Spec: Apte Practical Sanskrit-English Dictionary from Cologne Source

## Overview

Build a new dictionary export pipeline for the **Apte Practical Sanskrit-English Dictionary, 1890** (Cologne code: AP90), processing raw source data from the Cologne Sanskrit Lexicon into GoldenDict and MDict formats.

The implementation follows a **copy-and-adapt** approach from the MW Cologne pipeline. All code lives independently in `dictionaries/apte/`. No mobile database export is needed.

All commits use the prefix `#222 apte: `.

**Naming convention**: Our dictionary code is `apte` everywhere (folder, files, classes, paths, dict_name). The Cologne source uses `ap90` internally (SQLite files/tables, zip filename, scan URL parameter) — these external names cannot change.

## Source Data

- **Download URL**: `https://www.sanskrit-lexicon.uni-koeln.de/scans/AP90Scan/2020/downloads/ap90web1.zip` (~9.7 MB)
- **Format**: Cologne standard SQLite databases inside zip
- **SQLite schema** (same as MW):
  - `ap90.sqlite` — sub-entries: `CREATE TABLE ap90 (key VARCHAR(100), lnum DECIMAL(10,2), data TEXT)`
  - `ap90keys.sqlite` — grouped headwords: `CREATE TABLE ap90keys (key VARCHAR(100), lnum DECIMAL(10,2), data TEXT)`
  - `ap90ab.sqlite` — abbreviations: `CREATE TABLE ap90ab (id VARCHAR(100), data TEXT)`
  - `ap90authtooltips.sqlite` — literature tooltips: `CREATE TABLE ap90authtooltips (key VARCHAR(100), data TEXT)`
- **Cologne scan URL**: `https://www.sanskrit-lexicon.uni-koeln.de/scans/csl-apidev/servepdf.php?dict=AP90&page=`

## Dictionary Identity

- **Dict code**: `apte` (used in file names, dict_name, folder name)
- **Display name**: "Apte Practical Sanskrit-English Dictionary, 1890"
- **Author**: "Vaman Shivram Apte"
- **Source language**: `sa` (Sanskrit)
- **Target language**: `en` (English)

## Functional Requirements

### 1. Auto-Download (`apte_helpers.py`)

- Compare `Content-Length` header from Cologne server against local zip file size
- Download `ap90web1.zip` only if sizes differ or local file missing
- Unpack into `dictionaries/apte/source/`
- Constant: `APTE_ZIP_URL`

### 2. Data Loading (`apte_helpers.py`)

Load 4 SQLite databases into an `ApteData` dataclass:

```python
@dataclass
class ApteData:
    abbreviations: dict[str, str]       # from ap90ab.sqlite
    author_tooltips: dict[str, str]     # from ap90authtooltips.sqlite
    entries: dict[float, ApteEntry]     # from ap90.sqlite
    keys: dict[float, ApteKeyEntry]     # from ap90keys.sqlite
```

- **Abbreviations**: Extract `<disp>` content from raw data. SQL: `SELECT id, data FROM ap90ab`
- **Author tooltips**: Direct mapping. SQL: `SELECT key, data FROM ap90authtooltips`
- **Entries**: Keyed by `lnum` (float). SQL: `SELECT key, lnum, data FROM ap90`
- **Keys**: Keyed by `lnum` (float). SQL: `SELECT key, lnum, data FROM ap90keys`
- **Keys data format**: `"H1,startL,endL;H1A,startL2,endL2;..."` — parse into `(h_type, start_lnum, end_lnum)` tuples

### 3. Rendering (`apte_renderer.py`)

Two-phase renderer copied and adapted from MW. Every detail below was learned through painful iteration on MW and MUST be implemented correctly from the start.

#### Phase A — Preprocessing (order matters!)

Execute in this exact order:
1. **Replace broken bar**: `xml.replace("¦", " ")`
2. **Strip SLP1 accents** from `<s>` and `<key2>` tags:
   - MUST protect XML slashes first: replace `</` → `<_`, `/>` → `_>`
   - Strip `/`, `^`, `\` characters
   - Restore: `<_` → `</`, `_>` → `/>`
3. **Normalize tags**: `<lang ...>` → `<ab ...>`, `<s1 ...>` → `<ab ...>`
4. **Inject literature tooltips**: Match `<ls>ABBREV. rest</ls>` pattern, lookup in author_tooltips dict, inject `n='tooltip'` attribute. Special case: `<ls>ib.` → `<ls><ab>ib.</ab>`
5. **Inject abbreviation tooltips**: For `<ab>` tags lacking `n=` attribute, lookup text in abbreviations dict, inject `n='tooltip'`
6. **Inject lex tooltips**: Convert plain text inside `<lex>` to `<ab n='tooltip'>` tags. **CRITICAL: KEEP the `<lex>` wrapper** so Phase B can convert it to `<strong>` for bold. If you strip `<lex>` here, grammar labels like "f.", "m.", "mfn." will lose their bold formatting.

#### Phase B — Tag-to-HTML Conversion

**Step 1: Extract metadata BEFORE stripping** (values needed for assembly):
- Extract H-type: regex `<(H[1-4][A-Z]?)\b` — determines primary vs secondary heading
- Extract page-column: `<pc>(.*?)</pc>` — needed for PDF scan link
- Extract record ID: `<L>(.*?)</L>` — needed for `[ID=X]` suffix

**Step 2: Strip structural content**:
- **Strip entire `<h>...</h>` blocks** with `re.sub(r"<h>.*?</h>", "", xml, flags=re.DOTALL)`. This prevents SLP1 key1/key2 text from leaking into the rendered output. Do NOT just strip `<h>` tags — strip the content too.
- Strip H-type tags: `</?H[1-4][A-Z]?>`
- Strip `<pc>`, `<L>` tags (already extracted)
- Strip self-closing: `<info/>`, `<pb/>`, `<pcol/>`, `<lbinfo/>`
- Strip paired tags (tags only, keep content): `info`, `pb`, `pcol`, `to`, `ns`, `shortlong`, `srs`, `key1`, `key2`, `body`, `tail`, `head`, `lbinfo`, `hwtype`, `vlex`, `edit`, `note`, `symbol`, `type`

**Step 3: Render tags to HTML** (execute in this exact order):
1. `_render_s_tags`: `<s>SLP1</s>` → `<span class="sdata">IAST</span>` (SLP1→IAST transliteration)
2. `_render_ab_tags`: `<ab n='tip'>X</ab>` → `<span class="dotunder" title="tip">X</span>`. Without `n=` → `<span>X</span>`
3. `_render_ls_tags`: `<ls n='tip'>X</ls>` → `<span class="ls" title="tip">X</span> ` (trailing space). Without `n=` → `<span class="ls">X</span> `
4. `_render_hom_tags`: `<hom>N</hom>` → `<span class="hom" title="Homonym">N</span>`
5. `_render_bot_bio_tags`:
   - `<bot n='X'>Y</bot>` → `<span class="foreign dotunder" title="X">Y</span>` (brown + dotted underline)
   - `<bot>Y</bot>` → `<span class="foreign">Y</span>` (brown only)
   - Same for `<zoo>` (MUST handle `<zoo>`, it was missed in MW initially)
   - `<bio>Y</bio>` → `<span class="foreign">Y</span>` (brown only)
6. `_render_foreign_lang_tags`: Each tag → `<span class="foreign" title="LANG_TITLE">X</span>`
   - `<gk>` → "Greek script"
   - `<fr>` → "French language"
   - `<ger>` → "German language"
   - `<lat>` → "Latin language"
   - `<tib>` → "Tibetan language"
   - `<toch>` → "Tocharian language"
   - `<arab>` → "Arabic script"
   - `<rus>` → "Russian language"
   - `<mong>` → "Mongolian language"
7. `_render_div_tags`: `<div .../>` → `<div class="div-sep"></div>`
8. `_render_footnote_tags`: `<F>X</F>` → `<br/>[<span class="fn-label">Footnote: </span><span>X</span>]`
9. `_render_c_tags`: `<C n="X">Y</C>` → `<strong>(CX)</strong>Y`
10. `_render_misc_tags`:
    - `<b>` → `<strong>`, `<i>` → `<em>`, `<etym>` → `<em>`
    - `<lex>` → `<strong>` (bold for grammar labels — works because Phase A preserved the wrapper)
    - `<lb/>` → `<br/>`, `<Poem>` → `<br/>`, `</Poem>` → (remove)
    - `<lang>` fallback → `<em>` (italic, for any `<lang>` not already normalized in Phase A)
    - `<alt>` → `<span class="alt-hw">(X)</span>`

**Step 4: Assembly**:
- Primary headings only (`H1`, `H2`, `H3`, `H4` — NOT `H1A`, `H1B`, etc.) get a label line:
  `<strong>(H1)</strong> <span class="pcol-ref">[Printed book page <a href="SCAN_URL">PAGE</a>.COL]</span>`
- Scan URL: `https://www.sanskrit-lexicon.uni-koeln.de/scans/csl-apidev/servepdf.php?dict=AP90&page=PAGE`
- Page-column: `<pc>` value has format `"page,col"` — replace `,` with `.`, split on first `.`
- Record ID appended: `<span class="record-id">[ID=VALUE]</span>`
- Join label + body with `<br/>\n`
- **Do NOT add an `<h3>` headword title** — GoldenDict already displays the headword. Adding one creates a duplicate.

### 4. Entry Assembly (`apte_helpers.py`)

- Each sub-entry wrapped in `<p>` tags (not bare `\n` — newlines are invisible in HTML)
- **Full HTML document wrapper for EVERY entry** (GoldenDict requires this for CSS to load):
  ```html
  <!DOCTYPE html><html><head><meta charset="utf-8"><link href="apte.css" rel="stylesheet"></head><body>BODY</body></html>
  ```
- The CSS filename in the `<link>` MUST match the actual CSS file name (`apte.css`)
- Synonym generation: IAST + niggahita variants + original SLP1 (deduplicated via `set()`)
- Progress counter displays IAST word (not SLP1) — use `slp1_translit()` on the key before displaying
- Use `bisect.bisect_left`/`bisect_right` for O(log n) range lookups on sorted lnum arrays

### 5. CSS (`apte.css`)

Copy from MW CSS with only the comment header changed. Exact content:

```css
/* Apte CSS — derived from Cologne main.css + font.css */

.sdata { color: teal; font-style: italic; }
.hom { color: red; }
.ls[title] { color: blue; font-size: 10pt; }
.ls { color: gray; font-size: 10pt; }
.gram { font-weight: bold; }
.divm { font-weight: bold; }
.greek { font-style: italic; }
.dotunder { border-bottom: 1px dotted currentColor; text-decoration: none; }
.lnum { font-size: smaller; background-color: rgb(240, 240, 240); }
.g { font-size: smaller; font-style: italic; }
.lang { font-size: smaller; font-style: italic; }
.pb { font-size: smaller; }
.footnote { font-size: smaller; }
.foreign { color: brown; }
.div-sep { margin-top: 0.6em; }
.fn-label { font-weight: bold; }
.pcol-ref { color: rgb(160, 160, 160); }
.record-id { color: rgb(130, 130, 130); }
.alt-hw { font-size: smaller; }
```

Key CSS rules that were missed/fixed during MW development:
- `.sdata` MUST include `font-style: italic` (was missing, Sanskrit text must be italic)
- `.dotunder` MUST use `currentColor` not `#000` (was `#000`, invisible on dark backgrounds)

### 6. Export (`apte_from_cologne.py`)

- Use `DictInfo` with bookname="Apte Practical Sanskrit-English Dictionary, 1890", author="Vaman Shivram Apte"
- Use `DictVariables` with `dict_name="apte"`, `css_paths=[pth.apte_css_path]`
- Save intermediate `apte.json` for potential future mobile use
- Export GoldenDict via `export_to_goldendict_with_pyglossary()`
- Export MDict via `export_to_mdict()`

### 7. Integration Points (ALL required)

| File | Change |
|------|--------|
| `dictionaries/apte/__init__.py` | Create empty file |
| `dictionaries/apte/README.md` | Create with source info, run command, output paths |
| `scripts/export_all.py` | Add `from dictionaries.apte.apte_from_cologne import main as apte` + call `apte()` |
| `vendor/dpd_tools/paths.py` | Add `self._setup_apte_paths()` call + method with: `apte_source_dir`, `apte_zip_path`, `apte_json_path`, `apte_css_path`, `apte_gd_path`, `apte_mdict_path` |
| `tools/paths.py` | Add: `apte_css_path`, `apte_source_dir`, `apte_zip_path`, `apte_source_json_path`, `apte_gd_path`, `apte_mdict_path` |
| `docs/other_dicts.md` | Add row to GoldenDict table + MDict table |
| `resources/other-dictionaries/README.md` | Add row to dictionary table |
| GitHub Actions | Automatic — `export_all.py` is called by CI workflow, which auto-picks up new dicts |

### 8. Files to Create

```
dictionaries/apte/
├── __init__.py              (empty)
├── apte_from_cologne.py     (main exporter)
├── apte_helpers.py          (download, data loading, entry building)
├── apte_renderer.py         (XML preprocessing + tag-to-HTML)
├── apte.css                 (styling)
├── README.md                (documentation)
└── source/                  (auto-populated by download)
    ├── ap90web1.zip
    └── web/sqlite/
        ├── ap90.sqlite
        ├── ap90keys.sqlite
        ├── ap90ab.sqlite
        └── ap90authtooltips.sqlite

tests/
├── test_apte_paths.py
├── test_apte_download.py
├── test_apte_data_loading.py
├── test_apte_renderer_preprocess.py
├── test_apte_renderer_tags.py
├── test_apte_entry_builder.py
└── test_apte_export.py
```

## Non-Functional Requirements

- Zero inline styles — all styling via CSS classes
- No mobile database export needed
- All commits prefixed with `#222 apte: `

## Acceptance Criteria

1. Running `apte_from_cologne.py` produces GoldenDict + MDict entries with dict_name "apte"
2. Entry count matches `ap90keys.sqlite` headword count
3. CSS applies in GoldenDict: teal italic Sanskrit, blue/gray references, red homonyms, brown foreign text, dotted underline tooltips
4. Clickable PDF page links open correct Cologne AP90 scans
5. All tests pass (`uv run pytest tests/test_apte_*.py`)
6. `export_all.py` includes apte and runs without error
7. Documentation updated in `docs/other_dicts.md`, both READMEs
8. `tools/paths.py` and `vendor/dpd_tools/paths.py` have all apte paths
9. No duplicate headword displayed (GoldenDict shows headword automatically)
10. Sanskrit text is italic (`.sdata` CSS)
11. Abbreviation underlines visible in dark mode (`currentColor`)

## Out of Scope

- Mobile database export
- Shared/extracted renderer code with MW
- Any changes to the existing MW dictionary
- Devanagari font handling (IAST only)

## Mistakes from MW Track — DO NOT REPEAT

| # | Mistake | Correct Approach |
|---|---------|-----------------|
| 1 | Entries had no CSS `<link>` tag — GoldenDict showed zero styles | Every entry MUST have full HTML doc wrapper: `<!DOCTYPE html><html><head><meta charset="utf-8"><link href="apte.css" rel="stylesheet"></head><body>...</body></html>` |
| 2 | `<h>` blocks stripped tags but left SLP1 content ("ADAraA-DAra") | Strip entire `<h>...</h>` block including content: `re.sub(r"<h>.*?</h>", "", xml, flags=re.DOTALL)` |
| 3 | `<L>` tag was in both `_STRIP_TAGS` and `_render_misc_tags` | Extract `<L>` value BEFORE stripping, then append `[ID=X]` in assembly step |
| 4 | Sub-entries joined with `\n` (invisible in HTML) | Wrap each sub-entry in `<p>` tags |
| 5 | Added `<h3>` headword title → duplicate in GoldenDict | Do NOT add headword title — GoldenDict displays it automatically |
| 6 | `inject_lex_tooltips` stripped `<lex>` wrapper → grammar labels lost bold | Return `f"<lex>{''.join(result)}</lex>"` to preserve wrapper for Phase B `<strong>` conversion |
| 7 | `.sdata` CSS had no `font-style: italic` | MUST include `font-style: italic` in `.sdata` rule |
| 8 | `.dotunder` used `border-bottom: 1px dotted #000` | Use `currentColor` not `#000` for dark mode compatibility |
| 9 | Missing `<zoo>` tag handler | Handle `<zoo>` same as `<bot>` (with/without `n` attr) |
| 10 | Missing foreign language tag handlers | Add ALL: `<gk>`, `<fr>`, `<ger>`, `<lat>`, `<tib>`, `<toch>`, `<arab>`, `<rus>`, `<mong>` |
| 11 | `<bot>` with `n` attribute only got brown, no dotted underline | With `n` attr → `class="foreign dotunder"` + tooltip; without → just `class="foreign"` |
| 12 | `<lang>` fallback stripped to plain text | Render as `<em>` (italic) |
| 13 | Progress counter showed SLP1 | Show IAST via `slp1_translit()` |
| 14 | No structural labels for entry types | Primary headings (H1-H4 only) get `<strong>(H-type)</strong>` + page link |
| 15 | XML slashes corrupted during accent stripping | Protect `</` and `/>` before stripping accent chars |
