# Spec — Add Nyanatiloka's Buddhist Dictionary to other-dictionaries and the mobile app

## Overview

Nyanatiloka Mahathera's *Buddhist Dictionary: Manual of Buddhist Terms and
Doctrines* is a fixed, closed text — 4th revised edition, 1980, edited by
Nyanaponika Mahathera, published by the Buddhist Publication Society (BPS),
Kandy, ISBN 955-24-0019-8. Nyanatiloka died in 1957 and no edition has
appeared since 1980. This thread adds it as its own dictionary —
`dict_id = "nyanatiloka"` — to `resources/other-dictionaries` (GoldenDict +
MDict) and the mobile SQLite export, following the DPPN/Apte precedent in
`kamma/threads/20260727_dppn_apte_mobile/` (that thread's blocks are already
implemented, uncommitted, in `exporter/mobile/mobile_exporter.py` at the time
of writing — see "Thread dependency" below).

**Repos touched:** `resources/other-dictionaries` (new dictionary), `dpd-db`
(`tools/paths.py`, mobile exporter block, submodule pointer bump,
`docs/other_dicts.md`). No `dpd-flutter-app` change is needed — confirmed
below, not assumed.

**dict_id naming:** `nyanatiloka`, not an abbreviation. Existing ids mix
short acronyms (`mw`, `cpd`, `peu`, `bhs`) and longer names (`apte`, `dppn`,
`simsapa`, `cone`, `wordnet`). Unlike `apte`/`dppn` (abbreviations of a
title), "Nyanatiloka" is how everyone already refers to this dictionary — a
contrived acronym would be less recognizable, not more, so the full name is
kept.

---

## Source research

### Candidates checked

| Source | Verdict |
| --- | --- |
| **bps.lk** (publisher's own PDF) | Most authoritative, but PDF-only — no clean per-entry markup to parse without OCR/heuristics. Kept as the reference copy to spot-check against, not the extraction target. |
| **dhammatalks.net/Buddhist.Dictionary/** | **Selected** — see detailed structure analysis below. |
| **budsas.org/ebud/bud-dict/** | Same content, alternate mirror. Blocks automated fetches (HTTP 403) from this environment. Not needed since dhammatalks.net covers the same text. |
| **archive.org** (scanned 1970/BPS editions) | OCR-only text (djvu.txt), no per-entry structure, diacritics unreliable through OCR. Not used. |
| **`indic-dict/stardict-pali`** GitHub (StarDict/Babylon conversion) | Structured, but headwords are mixed with Devanagari script variants (`अब्भोकासिकङ्ग|abbhokaasikanga`) requiring extra cleanup, and the repo carries no license/attribution statement for the conversion. Rejected. |
| **`resources/other-dictionaries/dictionaries/simsapa/source/simsapa.json`** (already vendored) | 566 entries with no `[PTS]`/`[NCPED]`/`[DPPN]` tag (every other entry in that file carries one of those three tags), matching Nyanatiloka's dictionary in headword and style. **Rejected as the extraction source** — the Simsapa import ("init dictionary exporters", one commit) recorded no provenance for this subset. It also turns out to be a **partial excerpt, not the full dictionary** — see entry-count finding below — so it wouldn't even be a complete substitute. Left untouched; this thread adds a second, attributed, complete copy as its own card, it does not fix or split the Simsapa blob. |

### Licensing — resolved now, not deferred

Fetched `dic1-titel.htm` directly: the only notice present is `© 1980 by
Buddhist Publication Society`, with no reuse/reproduction restriction text on
the page or in its footer. This is the same posture DPD already accepts for
the other attributed-but-copyrighted dictionaries it ships (DPPN is © the
Ānandajoti Bhikkhu revision, CPD and MW/Apte are institutional works, none of
which carry an explicit redistribution license — DPD ships them with author
attribution in `dict_meta`, not under a verified open license). Nyanatiloka's
dictionary is treated the same way: shipped with full author/editor/publisher
attribution, consistent with existing project practice, not as a claim of an
open license that doesn't exist. **If this posture is wrong for this specific
case, say so before Phase 2 — this is a judgment call, not a verified legal
clearance.**

### Real HTML structure (fetched `dic3_a.htm` directly with `curl`, 99,720 bytes, decoded as `cp1252`)

This is a static, FrontPage-era site (`Saved: 05 November 2005` per the page's
own footer timestamp — confirms it hasn't changed in 20 years, consistent
with "static, not updated"). Concrete findings from the real markup, not
assumptions:

- Each entry is a `<p>` block: `<p><b>headword</b>: definition text…</p>`,
  e.g. `<p><b>abbhokāsik'anga</b>: 'living in the open air', is one of the
  ascetic means to purification (<i>dhutanga</i>, q.v.).</p>`.
- Diacritics are numeric HTML character references (`&#257;` = ā, `&#363;` =
  ū, etc.) — decode with `html.unescape`, independent of the page's declared
  `windows-1252` charset (numeric refs are already Unicode code points, no
  cp1252 mapping needed for them; only literal stray bytes, if any, need the
  `cp1252` decode).
- Cross-references use `s.` (see) or `q.v.` inside `<i>…</i>`; some are also
  wrapped in `<a href="dic2-abbrev.htm#...">` links to the site's own
  abbreviations page — these are dead links outside the site and **must be
  unwrapped to plain text** in the exporter (same treatment `simsapa_combined.py`
  already gives its own `<a>` tags via `soup.unwrap()`).
- `<a name="...">` anchors exist on only 14 of 197 entries on this page —
  inconsistent, not usable as the entry key. The headword is the first
  `<b>…</b>` inside each `<p>`, same idea as the already-working DPPN parser.
- **Malformed nesting exists** — spot-checked example: `<p><b>anabhirati-saññā:
  </b>s. <i>sabba-loke anabhirati-s.</p></i><p><b>Anāgāmī: </b>...` — the
  `</i>` closes *after* the `</p>`. A tolerant parser (BeautifulSoup, as
  already used by `simsapa_combined.py`) is required, not regex.
- Not every `<b>` is an entry boundary: of 213 total `<b>` tags on the page,
  16 are inline emphasis inside entry bodies (sub-terms, cross-references
  bolded mid-sentence) or page furniture (title, `-A-` alphabet header,
  footer nav bar uses `<strong>` not `<b>`, so that specific case is already
  excluded). Segmentation must be by `<p>` boundary (197 of them on this
  page), not by counting `<b>` tags.
- Preamble (`BUDDHIST DICTIONARY` title, `-A-` alphabet divider) and footer
  (nav links, "Saved: " timestamp) are excluded by only taking `<p>` blocks
  that begin with `<b>` and appear inside the main content `<blockquote>`,
  the same shape DPPN's `class="Heading3"` filter served for its own
  divider rows.

### Page list (fetched `index_dict.n2.htm` directly, not paraphrased)

26 letters map to 22 files: one page per letter **except** Q folds into
`dic3_r.htm` (no separate Q page, same as DPPN-style redirects), and W–Z
share `dic3_w-z.htm` plus a separate `dic3_y.htm`. Full file list:
`dic3_a.htm dic3_b.htm dic3_c.htm dic3_d.htm dic3_e.htm dic3_f.htm dic3_g.htm
dic3_h.htm dic3_i.htm dic3_j.htm dic3_k.htm dic3_l.htm dic3_m.htm dic3_n.htm
dic3_o.htm dic3_p.htm dic3_r.htm dic3_s.htm dic3_t.htm dic3_u.htm dic3_v.htm
dic3_w-z.htm dic3_y.htm`.

### Entry count — confirmed

All 22 pages fetched and parsed: **1,406 entries total** (per-page: a197 b46
c84 d92 e37 f35 g23 h21 i50 j12 k76 l24 m82 n61 o22 p122 r46 s167 t48 u52
v79 w-z17 y13). The 566 Simsapa-embedded entries are a **partial excerpt**
of the full dictionary, not a complete floor estimate — confirmed, not just
guessed.

### Authoring is inconsistent across pages — corrected from the single-shape assumption

Fetching all 22 pages (not just "A") showed at least three different hand-
edited HTML shapes for the same logical entry:

- **Shape 1** (page A): `<p><b>word</b>: definition…</p>` — well-formed,
  word and body in one `<p>`.
- **Shape 2** (page B): `<b><p>word: </b>definition…</p>` — the bold tag
  opens *before* the paragraph and closes partway through it; a browser-
  grade parser (BeautifulSoup) closes the `<p>` at the stray `</b>` and the
  actual definition text becomes a sibling of the `<blockquote>`, not a
  child of any `<p>`.
- **Shape 3** (page D): `<p><font face="Verdana"><b>word</b>…</p>` — an
  inline `<font>` wrapper sits between `<p>` and `<b>`.

The alphabet-divider row's own `<b>` sometimes stays open into the very next
real entry (`<b><font SIZE="5"><p ALIGN="CENTER">-B-</p></font><p>bahula-kamma:
</b>…`), producing a word like `-B-\n\nbahula-kamma` unless stripped. The
page's own title bold (`<b><a name="top">BUDDHIST DICTIONARY</a></b>`) also
matches the same tag-adjacency pattern used to detect entries and must be
explicitly excluded.

### Extraction rule (implemented, not just planned)

1. Segment the region between the page's first and second `<hr
   COLOR="#800000">` (header/footer boundary, confirmed present on every
   page) at every point matching either tag order, allowing optional
   `<font>`/`<a>` wrappers in between: `<p[^>]*>(?:\s*<(?:font|a)[^>]*>)*\s*<b>`
   or `<b>(?:\s*<(?:font|a)[^>]*>)*\s*<p[^>]*>`.
2. Parse each resulting raw slice with BeautifulSoup, take the first `<b>`
   tag's text as `word`, strip a leading alphabet-divider prefix
   (`^-[A-Za-z](?:-[A-Za-z])?-\s*`) and a leading colon, drop the entry if
   the word is empty or is exactly "BUDDHIST DICTIONARY".
3. Remove that first `<b>` node, unwrap every `<a>` and `<font>` tag (no CSS
   classes depend on them), and wrap the remaining content in `<p>…</p>` if
   it doesn't already start with a block tag — `definition_html`.
4. This naturally carries multi-paragraph entries (e.g. `Anāgāmī`'s 5-item
   numbered list) into one `definition_html`, since continuation `<p>`s
   don't match the entry-start pattern and stay part of the previous slice.

Verified: 0 unresolved `&#…;` entities, 0 leftover `<a>` tags, 0 near-empty
bodies, only 2 repeated headwords in the whole set (`conception` — two
genuinely distinct numbered sub-entries on the same page, not a parse
artifact) after the full 22-page run.

---

## Data shape (produced)

A JSON list of `{"word": str, "definition_html": str}`, one per headword —
1,406 total, built by the extraction rule above. `word` is `html.unescape`'d
and stripped; no synonyms table, same call as DPPN/Apte (`dict_entries` has
one `word` column; alternate spellings are not independently searchable;
duplicate headwords like `conception` above are kept as separate rows,
consistent with `word` not being a primary key elsewhere in `dict_entries`).
Source fetched with `curl` throughout, not `WebFetch` — `WebFetch`
paraphrases through a summarizing model and will not return verbatim markup,
which byte-for-byte parsing needs.

---

## Mobile export block

Mirrors the already-implemented DPPN/Apte blocks in
`exporter/mobile/mobile_exporter.py::export_other_dictionaries` (placed after
the Apte block, matching those two threads' insertion order):

```python
if not g.pth.nyanatiloka_source_path.exists():
    raise _missing_source_error("Nyanatiloka", g.pth.nyanatiloka_source_path)

with g.pth.nyanatiloka_source_path.open(encoding="utf-8") as f:
    nyanatiloka_data: list[dict[str, str]] = json.load(f)

nyanatiloka_css = _sanitize_css(g.pth.nyanatiloka_css_path.read_text(encoding="utf-8"))

batch = []
for entry in nyanatiloka_data:
    word = entry["word"]
    word_fuzzy = _strip_diacritics_mobile(word)
    batch.append(("nyanatiloka", word, word_fuzzy, entry["definition_html"], ""))
```

`dict_meta`: `("nyanatiloka", "Buddhist Dictionary: Manual of Buddhist Terms
and Doctrines", "Nyanatiloka Mahathera, ed. Nyanaponika Mahathera",
nyanatiloka_css, len(batch))`.

### `tools/paths.py` (dpd-db)

Add `nyanatiloka_source_path` and `nyanatiloka_css_path` to `RepoPaths`,
following the exact pattern of `_setup_dppn_paths` (`tools/paths.py:84-89` /
its mirror in the submodule's `vendor/dpd_tools/paths.py`):
`self.nyanatiloka_source_path = d / "source" / "nyanatiloka.json"`,
`self.nyanatiloka_css_path = d / "nyanatiloka.css"`.

## App side — confirmed, not assumed

Read `dpd-flutter-app/lib/widgets/dict_html_card.dart::prepareDictHtml`
(lines 55–61): it special-cases `cone`, `mw`/`apte`, and `cpd` only; every
other `dictId` — `nyanatiloka` included — falls through unchanged and is
rendered by `flutter_widget_from_html`'s `HtmlWidget`, which natively
supports `<p>`, `<b>`, `<i>`, `<blockquote>` with no custom CSS classes
required. Same conclusion DPPN reached (DPPN isn't in the special-case list
either). **No `dpd-flutter-app` code change is needed.** Phase 2 verification
loads the built database in the app and confirms this holds for real
scraped HTML, not just the plain-tag theory.

## GoldenDict / MDict export (`nyanatiloka.py`, mirrors `dppn.py`)

- GoldenDict (`export_to_goldendict_with_pyglossary`): `word=[d.word] +
  d.synonyms` (no synonyms here) is the lookup key, `defi=d.definition_html`
  is the article body verbatim — the headword is **not** repeated inside the
  body for GoldenDict, exactly as DPPN's `name`+`entry` construction removes
  its own leading bold headword.
- MDict (`export_to_mdict`, default `h3_header=True`, not overridden — same
  as `dppn.py`, which passes no `h3_header` argument): the exporter
  automatically prepends `<h3>{word}</h3>` to `definition_html` for every
  entry (`vendor/dpd_tools/mdict_exporter.py::add_h3_header`). No manual
  h3-prefixing needed in `nyanatiloka.py` itself.
- `DictInfo(bookname="Buddhist Dictionary: Manual of Buddhist Terms and
  Doctrines", author="Nyanatiloka Mahathera", description="4th revised
  edition, ed. Nyanaponika Mahathera, Buddhist Publication Society, 1980",
  website="https://www.dhammatalks.net/Buddhist.Dictionary/", source_lang="pi",
  target_lang="en")`.

## `other-dictionaries` submodule additions

- `dictionaries/nyanatiloka/source/nyanatiloka.json` (scraped data, committed
  + `.tar.zst` compressed via the existing `scripts/compress_sources.py`,
  which globs `dictionaries/*/source` with no per-dictionary list to update;
  restored automatically by `scripts/decompress_sources.py`, which globs
  `dictionaries/*/*.tar.zst` — confirmed by reading both scripts, no explicit
  registration needed for either).
- `dictionaries/nyanatiloka/nyanatiloka.css` — minimal (bold headword, italic
  Pali term; no special classes, matching the plain-tag markup).
- `dictionaries/nyanatiloka/nyanatiloka.py` — GoldenDict + MDict exporter,
  mirrors `dppn.py`'s shape exactly (see above).
- `dictionaries/nyanatiloka/README.md` — records the source URL
  (`dhammatalks.net/Buddhist.Dictionary/`), the page's own "Saved: 05
  November 2005" timestamp, the date this scrape was actually run, and the
  BPS edition/ISBN — closing the provenance gap the Simsapa import left open.
- Add `"nyanatiloka": pth.nyanatiloka_source_path` to `mobile_critical` in
  **`resources/other-dictionaries/scripts/prepare_sources.py`** (confirmed
  exact path — there is only one `prepare_sources.py`, in this submodule, not
  in `dpd-db`). Since the source is a committed, `decompress_sources`-restored
  static file (same as DPPN), this entry behaves as a **recording check that
  always passes**, not a live gate — same status as DPPN's own entry in that
  dict today.
- Register `nyanatiloka` in `scripts/export_all.py` (import + call), the
  "build everything" orchestrator — every other dictionary in this repo is
  listed there; omitting it would mean the one-shot build entry point
  silently skips the new dictionary even though `prepare_sources.py` and the
  mobile block are wired up.

## Docs

Every README/help/download-link location that lists dictionaries, in both
repos — not just the two below — per an explicit user request during
implementation (recorded in `plan.md`'s scope-addition note):

- `resources/other-dictionaries/scripts/export_all.py` — the "build
  everything" orchestrator; without registering `nyanatiloka` here it would
  never be built by the one-shot entry point even with `prepare_sources.py`
  and the mobile block wired up.
- `resources/other-dictionaries/.github/workflows/build-and-release.yml` —
  the actual GitHub Release notes table (real download links).
- `resources/other-dictionaries/README.md` — dictionary table.
- `dpd-db/docs/other_dicts.md` — GoldenDict table, MDict table, and a new
  description section alongside DPPN's, crediting Nyanatiloka and
  Nyanaponika and linking dhammatalks.net as the source.
- `dpd-db/docs/index.md` — one-line mention in the GoldenDict/MDict intro.
- `dpd-flutter-app/assets/help/bibliography.tsv` — bibliography row.

Checked and confirmed not applicable: `dict_settings_widget.dart` (dictionary
list is driven from `dict_meta` at runtime, no hardcoded list); `dpd-db`'s
root `README.md`.

## Thread dependency

`kamma/threads/20260727_dppn_apte_mobile/` has already implemented (but not
committed) the DPPN and Apte blocks in `exporter/mobile/mobile_exporter.py`
— confirmed by reading the current file, lines 691–774. This thread's mobile
block is written to insert immediately after the existing Apte block. If
that thread's changes are reverted or reordered before this one lands, the
insertion point in the plan's tasks will need re-checking against the file at
that time — flagged here so it isn't silently assumed still true.

## Constraints

- Do not bump `DB_SCHEMA_VERSION` — adding rows, not columns.
- Ships enabled by default (like DPPN/Apte/CPD/MW/PEU/WordNet/BHS) — not
  gated behind a flag like `--cone`.
- `dict_meta.author` must credit both Nyanatiloka (author) and Nyanaponika
  (editor of the 4th revised edition).

## What's not included

- Any fix to the existing Simsapa Combined Dictionary's untagged Nyanatiloka
  subset — flagged as a separate, optional follow-up, not part of this
  thread.
- Synonym/cross-reference rows.
- Any live re-fetch mechanism — committed as a static source, matching the
  DPPN pattern (dhammatalks.net's own footer timestamp shows it hasn't
  changed since 2005; nothing to keep in sync).

## Assumptions & uncertainties

- The 22-page set from `index_dict.n2.htm` is treated as the complete
  dictionary body; `dic2-abbrev.htm` (abbreviations, not headwords) is
  excluded. Confirmed by parsing all 22 pages (1,406 entries, no
  cross-letter duplicate headwords), not just assumed from page "A".
- The licensing posture above (attribute, don't claim an open license)
  matches how DPD already treats DPPN/CPD/MW/Apte — flagged explicitly as a
  judgment call for this specific case, not a verified legal clearance.
- BeautifulSoup's tolerant parsing correctly recovers the malformed
  `</p></i>`-style nesting and all three authoring shapes found across the
  22 pages — confirmed by spot-checking output from every letter during
  Phase 1, not assumed from one example.
