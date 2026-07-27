# Spec — Add DPPN and Apte to the mobile database

## Overview

Two dictionaries that already exist in the `other-dictionaries` collection are
not exported to the mobile database and therefore never reach the Flutter app:

- **DPPN** — G. P. Malalasekera's *Dictionary of Pāli Proper Names*, revised by
  Ānandajoti Bhikkhu (June 2025). 13,642 entries.
- **Apte** — Vaman Shivram Apte's *Practical Sanskrit-English Dictionary* (1890),
  built from the Cologne Sanskrit Lexicon. 34,277 entries.

Both already build to GoldenDict and MDict. This thread adds them to the mobile
SQLite export so they ship in every mobile database release, alongside CPD,
Monier-Williams, PEU, WordNet and BHS.

**Repos touched:** `dpd-db` (main), its `resources/other-dictionaries`
submodule, and `dpd-flutter-app` (one line).

---

## Current state

### Mobile export pattern

`exporter/mobile/mobile_exporter.py::export_other_dictionaries` contains one
self-contained block per dictionary (~35 lines each). Each block:

1. reads a source file,
2. builds `(dict_id, word, word_fuzzy, definition_html, definition_plain)` rows,
3. `executemany` into `dict_entries`,
4. inserts one row into `dict_meta` with `(dict_id, name, author, css, entry_count)`.

`word_fuzzy` is always `_strip_diacritics_mobile(word)`. CSS is passed through
`_sanitize_css()`. A missing source raises `_missing_source_error(name, path)`.

No schema change and **no `DB_SCHEMA_VERSION` bump** is needed — adding a
dictionary adds rows, not columns. Verified against commit `f0602dec`
(WordNet + PEU made unconditional), which bumped nothing.

### App side

`lib/providers/dict_provider.dart::initFromMeta` reads `dict_meta` and appends
any unseen `dict_id` to both `order` and `enabled` for existing users
(lines 115–133), and enables everything on a fresh install. `dict_settings_widget.dart`
builds its list from `dict_meta` too. **No app work is needed for discovery,
enabling, ordering or naming.**

`DictHtmlCard._buildEntryWidgets` already prints `entry.word` as a bold heading
above each entry, then renders `definition_html` through `HtmlWidget`.

`dict_meta.css` is stored in the database but **the app never applies it** — all
styling goes through `_buildStylesBuilder` in `dict_html_card.dart`, which keys
off HTML class names. We still populate `css` for consistency with the other
dictionaries.

---

## DPPN

### Source

- Path: `resources/other-dictionaries/dictionaries/dppn/source/DPPN.json`
  (`pth.dppn_source_path` — already defined in both `tools/paths.py` and the
  submodule's `vendor/dpd_tools/paths.py`).
- Restored automatically from the tracked `dictionaries/dppn/dppn.tar.zst` by
  `scripts/decompress_sources.py`, which is called by `scripts/prepare_sources.py`.
  The mobile release workflow already runs that step
  (`.github/workflows/mobile_release.yml` line 228–230) with recursive submodules.
  **No source-preparation work is needed for DPPN.**
- CSS: `resources/other-dictionaries/dictionaries/dppn/dppn.css` (`pth.dppn_css_path`).

### Data shape

A JSON list of `{"name": ..., "entry": ...}`. The two fields are two halves of
one HTML paragraph:

```json
{
  "name": "<p><span class=\"Head\"><b>Akataññujātaka</b> (<abbr title=\"Added\">Ja 90</abbr>). </span>",
  "entry": "A merchant is befriended by a colleague in another country but refuses to return the service. ... Ja.i.377-9. </p>"
}
```

Facts measured against the current source file:

- Every one of the 13,642 names contains at least one `<b>…</b>`; the **first**
  one is always the headword, and no headword contains nested tags.
- 1,414 names contain more than one `<b>` — the later ones are variant spellings
  inside the head line, e.g. `Akatti (<i>v.l.</i> <b>Akitti)</b>`.
- 13,604 names use `class="Head"`; the other **38 use `class="Heading3"`** and are
  alphabet section dividers (`A-An.`, `Ā.`, `Kh.`, `Mahā.` …) whose `entry` is just
  `" </p>"`. They are not dictionary entries.
- 249 names contain `ṁ`; **zero** contain `ṃ`.
- No `href` and no `<img>` anywhere in the entry bodies.

### How the existing exports display it

- **GoldenDict/StarDict** (`add_data` in `vendor/dpd_tools/goldendict_exporter.py`):
  the article body is `i["entry"]` only. The whole `name` HTML fragment is used
  as the lookup *key*, so the head material never appears in the article. The
  clean headwords are only findable because a separately computed synonym list
  is attached.
- **MDict** (`vendor/dpd_tools/mdict_exporter.py` line 68): prepends
  `<h3>{word}</h3>` — i.e. the raw head fragment — to the body, so the complete
  original paragraph is displayed.

Neither key format can be reused on mobile: `dict_entries` has a single `word`
column and no synonym mechanism, so the searchable word **must** be the clean
headword or nothing will be findable.

### Decision — headword and body (user-approved)

Follow MDict's *display* format (head line above body), but remove the bold
headword from the head line, because `DictHtmlCard` already prints the headword.
Everything else in the head line is kept, so source references and disambiguating
numbers survive.

- `word` = text of the first `<b>…</b>` in `name`, stripped, with `ṁ` → `ṃ`.
- `definition_html` = `name + entry` (the complete original paragraph, so the
  `<p>` open tag matches the trailing `</p>`), with the first `<b>headword</b>`
  removed, and with the head `<span>` removed entirely when nothing but
  whitespace and a full stop remains inside it. `ṁ` → `ṃ` throughout.
- Skip the 38 `class="Heading3"` entries.

Rendered result:

```
Akataññujātaka                 ← printed by DictHtmlCard from `word`
(Ja 90). A merchant is befriended by a colleague in another country…

Akatuññatāsutta
01. One who is of bad conduct in deed, word and thought…

Akatti
See Akitti.
```

### `dict_meta` row

| column | value |
| --- | --- |
| `dict_id` | `dppn` |
| `name` | `Dictionary of Pāli Proper Names` |
| `author` | `G. P. Malalasekera, revised by Ānandajoti Bhikkhu` |
| `css` | `_sanitize_css(pth.dppn_css_path.read_text())` |

---

## Apte

### Source

- Not stored in the repo. `dictionaries/*/source/` is gitignored, and Apte has no
  `.tar.zst` archive — unlike DPPN, and **exactly like Monier-Williams**.
- `dictionaries/apte/apte_helpers.py::download_fresh_source` fetches
  `ap90web1.zip` from `https://www.sanskrit-lexicon.uni-koeln.de/scans/AP90Scan/2020/downloads/ap90web1.zip`
  on every run, falling back to a previously downloaded local zip if the server
  is unreachable.
- The intermediate `source/apte.json` (~39 MB, `pth.apte_source_json_path` in
  `tools/paths.py` / `pth.apte_json_path` in the submodule) is written by
  `dictionaries/apte/apte_from_cologne.py::main`.

**The gap:** `scripts/prepare_sources.py` calls `build_mw_json(pth)` but has no
Apte equivalent, so `apte.json` does not exist in CI. Monier-Williams solved this
by extracting `build_mw_json(pth)` out of its `main()`
(`dictionaries/mw/mw_from_cologne.py` lines 18–47) and calling it from
`prepare_sources`. Apte must mirror that exactly.

### Data shape

`apte.json` is a list of `{"word", "definition_html", "definition_plain", "synonyms"}` —
the same shape as `mw.json`. Words are IAST (`aṃhatiḥ`). `definition_html` is a
full HTML document:

```html
<!DOCTYPE html><html><head><meta charset="utf-8"><link href="apte.css" rel="stylesheet"></head><body>
<p><strong>(H1)</strong> <span class="pcol-ref">[Printed book page <a href="…">0002-c</a>.]</span><br/>
<span class="sdata">aṃhatiḥ</span> … <span class="ls" title="Uṇādisūtras">Uṇ. 4. 62</span> …</p>
</body></html>
```

This is byte-for-byte the same idiom as Monier-Williams: DOCTYPE wrapper,
`(H1)` section markers, `class="ls"` spans carrying a `title` tooltip, and the
`sdata` / `dotunder` / `pcol-ref` / `hom` / `div-sep` / `foreign` classes.

### App handling

`prepareDictHtml` in `lib/widgets/dict_html_card.dart` already handles all of it
for `mw` via `_cleanMwHtml`: strips the document wrapper, strips the `(H1)`
markers, and rewrites `ls` tooltip spans into tappable `tooltip:` links.
`_buildStylesBuilder` already styles every class Apte uses.

So the app change is one line — route `apte` through `_cleanMwHtml` too. We do
**not** duplicate that cleaning in the exporter, to keep Apte and
Monier-Williams on one code path.

### `dict_meta` row

| column | value |
| --- | --- |
| `dict_id` | `apte` |
| `name` | `Apte Practical Sanskrit-English Dictionary, 1890` |
| `author` | `Vaman Shivram Apte` |
| `css` | `_sanitize_css(pth.apte_css_path.read_text())` |

---

## Added mid-thread (2026-07-27): case-insensitive exact match in the app

Manual testing surfaced a genuine app bug that DPPN is the first dictionary to
expose. The user asked for it to be fixed inside this thread.

### Symptom

Searching a proper name shows its Proper Names entry under **partial results**
even when the query is an exact match for the headword.

### Cause

`_dictRawResultsProvider` in `lib/providers/dict_provider.dart` lowercases the
query before every dictionary lookup:

```dart
exactRows = await dao.searchDictExact(query.toLowerCase());
```

`DictDao.searchDictExact` then does `word.equals(...)`, a binary comparison. The
stored DPPN headword is `Anāthapiṇḍika`, so the lowercased query never matches
and no exact row is produced. `searchDictPartial` uses `word LIKE 'query%'`, and
SQLite's `LIKE` folds case **for ASCII only**, so `a` matches `A` and the entry
lands in the partial tier instead.

The query is lowercased regardless of what the user typed, so typing the capital
does not help.

### Scale

Capitalised headwords per dictionary in the built database:

| dict | capitalised | total |
| --- | --- | --- |
| dppn | 13,330 | 13,604 |
| peu | 84 | 203,865 |
| mw | 44 | 194,084 |
| apte | 1 | 34,277 |
| bhs, cpd, wordnet | 0 | — |

### Second, worse half of the bug

ASCII-only case folding means names starting with an **accented** capital —
`Ānanda`, `Ñāṇamoli`, `Ṭhitañāṇa` — do not match the partial tier either. They
fall through to the fuzzy tier, which is a further degradation. Any fix must
handle these, which rules out SQLite's `lower()` and `LIKE` (both ASCII-only)
and requires Dart's Unicode-aware `toLowerCase()`.

### Decision (user-chosen)

The **airtight** option: a dedicated case-insensitive exact query, not a
reclassification of the already-fetched partial and fuzzy rows. Reclassification
was rejected because those two queries cap at 50 rows each, so a true exact match
for a common prefix could fall outside the window and still be missed.

Shape: match on the indexed `word_fuzzy` column to fetch a small candidate
superset, then filter in Dart with `word.toLowerCase() == query.toLowerCase()`.
`word_fuzzy` is produced by `_strip_diacritics_mobile` in the exporter, which
lowercases and strips diacritics, so it is case-blind and diacritic-blind — a
superset of any case-insensitive exact match, and highly selective.

**Gated on evidence.** The user required proof that the replacement costs no more
time than the current query before it is written. A benchmark against the real
604,000-row table is comparing: the current `word = ?`; `word_fuzzy = ?`;
a per-dict loop on `dict_id = ? AND word_fuzzy = ?`; and `word_fuzzy = ? AND
dict_id IN (…)`, with the existing fuzzy `LIKE` search as the accepted baseline.
Note that `idx_dict_entries_word` leads on `dict_id`, so the *current* query may
already be doing a full scan — the benchmark verifies this rather than assuming.
Results are recorded in `plan.md` Phase 4.

---

## What it should do

1. Every mobile database release contains DPPN and Apte in `dict_entries` and
   `dict_meta`.
2. Searching a proper name (e.g. `Anāthapiṇḍika`) in the app shows a
   *Dictionary of Pāli Proper Names* card with a readable entry.
3. Searching a Sanskrit word shows an *Apte Practical Sanskrit-English
   Dictionary, 1890* card rendered like the existing Monier-Williams card —
   no raw `<!DOCTYPE …>` text, no stray `(H1)`, tooltips tappable.
4. Existing users get both dictionaries switched on automatically after the
   database update; the display order and toggles work like every other
   dictionary.
5. The CI mobile release build produces both without manual steps.

---

## Assumptions & uncertainties

- **Both ship by default, no opt-in flag.** They follow CPD / MW / PEU / WordNet /
  BHS, not Cone (Cone is opt-in for licensing reasons that don't apply here).
  DPPN adds ~6.6 MB of raw text; Apte ~39 MB. The current mobile zip is 272 MB,
  which already includes the 191 MB `mw.json`, so the relative growth is modest.
  *If the size increase is unwanted, say so and Apte can go behind a flag.*
- **No variant/synonym rows.** DPPN's GoldenDict export splits the head line on
  `v.l.`/`also called`/`or`/… to generate synonyms, and Apte generates
  `generate_synonyms(slp1_key)`. The mobile schema has one word per row and no
  other dictionary carries synonyms, so we skip them. Alternative spellings will
  not be independently searchable. Deferred, not lost.
- **Apte depends on Cologne being reachable at build time.** Same exposure
  Monier-Williams already accepts. If Cologne is down and no local zip is
  present, the CI build fails loudly rather than shipping a partial database.
- Assuming `ṁ` → `ṃ` is the right canonicalisation for DPPN, matching the
  existing `_canonicalize_cpd_headword` and the PEU block.
- Assuming DPPN's 38 `Heading3` rows are unwanted. They are alphabet dividers
  from the printed layout with no content.
- Assuming Apte's Cologne page links should stay tappable, as they are for
  Monier-Williams.

---

## Constraints

- Do not bump `DB_SCHEMA_VERSION` (currently 7) or
  `AppDatabase.requiredDbSchemaVersion` — no schema change.
- Do not modify `exporter/mobile/mobile_exporter.py` beyond adding the two blocks
  and any helper they need. No refactor of the existing dictionary blocks.
- Submodule discipline: `resources/other-dictionaries` changes are a separate
  commit in that repo, then the submodule pointer is bumped in `dpd-db`.
- App changes limited to the single `prepareDictHtml` line.

---

## How we'll know it's done

1. `uv run python exporter/mobile/mobile_exporter.py` completes and reports
   ~13,604 DPPN entries and ~34,277 Apte entries.
2. Querying the built database:
   - `SELECT dict_id, name, entry_count FROM dict_meta` lists `dppn` and `apte`
     with correct names and non-zero counts.
   - `SELECT word, definition_html FROM dict_entries WHERE dict_id='dppn' AND word='Akataññujātaka'`
     returns a body starting with the `(Ja 90)` reference and containing no
     `<b>Akataññujātaka</b>`.
   - `SELECT COUNT(*) FROM dict_entries WHERE dict_id='dppn' AND word LIKE '%ṁ%'`
     returns 0.
   - No DPPN word is an alphabet divider (`A-An`, `Ā`, `Kh` …).
3. `cd resources/other-dictionaries && uv run python scripts/prepare_sources.py`
   exits 0 and reports `apte` present among the mobile-critical files.
4. In the app with the new database: a proper-name search and a Sanskrit-word
   search each show a correctly titled, correctly rendered card.

---

## What's not included

- Variant/alternative-spelling search rows for either dictionary.
- Any change to the GoldenDict or MDict exports.
- Any change to how DPPN cross-references (bold names inside entry bodies) behave —
  they stay plain bold text, not tappable links.
- Retiring the `--cone` flag or touching any other dictionary block.
- New tests for the mobile exporter (the repo has none for it today).
