# MW2: Monier-Williams Dictionary from Cologne Raw Source

## Overview

Build a new Monier-Williams Sanskrit-English Dictionary export pipeline that processes the
original Cologne Sanskrit Lexicon source files directly, producing a faithful reproduction
of the original Monier-Williams material as found in the printed books and on the Cologne
website. The output is exported as "mw2" to GoldenDict, MDict, and the mobile SQLite
database — coexisting alongside the current Simsapa-based "mw" export for fidelity comparison.

## Functional Requirements

1. **Auto-download fresh source data** from the Cologne Sanskrit Lexicon server every time
   the export runs. Download `mwweb1.zip`, compare against existing, unpack if changed.

2. **Load data from SQLite databases**: `mw.sqlite` (286,554 sub-entries), `mwkeys.sqlite`
   (194,083 grouped headwords), `mwab.sqlite` (424 abbreviations), `mwauthtooltips.sqlite`
   (literature tooltips).

3. **Render XML tags to HTML** faithfully replicating the Cologne website's PHP renderer
   (`basicadjust.php` + `basicdisplay.php`). All styling via CSS classes — zero inline styles.

4. **Pre-processing pipeline** matching `basicadjust.php`:
   - SLP1 accent stripping with XML slash escaping
   - `<lang>` → `<ab>`, `<s1 n>` → `<ab n>` conversion
   - Abbreviation tooltip injection from `mwab.sqlite`
   - Literature tooltip injection from `mwauthtooltips.sqlite`
   - Lex tooltip injection

5. **CSS derived from Cologne's actual CSS files** (`main.css` + `font.css`), plus
   additional classes (`.foreign`, `.div-sep`, `.fn-label`) to replace PHP inline styles.

6. **Shared helper module** (`mw_helpers.py`) used by both GoldenDict and mobile exporters
   directly — no intermediate JSON file.

7. **Page-column references** kept in both GoldenDict (`[p.X,Y]` text) and mobile DB.

8. **Dict name = "mw2"** everywhere — GoldenDict files, MDict files, mobile dict_id.
   Existing "mw" export untouched.

9. **SLP1 → IAST transliteration** via existing `slp1_translit()`. Synonyms include
   IAST + niggahita variants + original SLP1 key.

## Non-Functional Requirements

- ~194,083 output entries (matching mwkeys count)
- No inline styles in generated HTML
- CSS faithfully matches Cologne website appearance
- Fresh source data checked on every run

## Acceptance Criteria

1. Running `mw_from_cologne.py` produces ~194,083 GoldenDict + MDict entries with dict name "mw2"
2. Visual comparison of 10+ headwords matches Cologne website rendering
3. Sanskrit text in teal, homonyms in red, references in gray, foreign text in brown
4. Abbreviation tooltips appear on hover
5. Literature tooltips appear on hover
6. Zero inline styles in HTML output
7. Mobile exporter produces "mw2" entries with CSS and page references
8. Existing "mw" export remains unchanged and functional
9. Auto-download fetches fresh data when Cologne source has changed

## Commit Convention

All commits for this track must use the prefix `#221 mw2: `.

## Out of Scope

- Bundling font files (siddhanta1.ttf etc.) — GoldenDict has adequate Unicode support
- Replacing the existing "mw" Simsapa-based export (kept for comparison)
- Devanagari rendering mode (IAST/Roman mode only, matching current setup)
- Cross-linking between MW entries
