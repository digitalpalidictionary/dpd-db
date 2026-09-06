# Spec: How to cite DPD

## GitHub issue
None — arose from discussion.

## Overview

DPD is a continuously revised dictionary. A citation of the form "DPD, accessed 6 Sept
2026" is unverifiable: the entry a reader looks up may no longer say what was quoted.
Every serious work-in-progress dictionary solves this by pinning the citation to a
**version**, and by giving each entry a **stable address**.

DPD already has both ingredients and uses neither for citation:

- a release version string (`v0.4.20260905`), generated monthly by `tools/version.py`,
  written to `config.ini` and to the `db_info` table
- a stable per-entry permalink, `https://www.dpdict.net/?tab=dpd&q=<id>`

This thread makes those citable: a recommended citation format, published where scholars
and downstream apps will find it, plus the repo metadata that makes GitHub and Zenodo
able to generate a citation automatically.

It also fixes two attribution inconsistencies found while surveying: the licence is
stated two different ways, and the author name is stated two different ways.

## Research summary — why this design

Four citation systems were investigated (full notes in the thread discussion):

1. **Version-in-the-citation.** What the Dictionary of Old English and the Middle
   English Dictionary do — name the fascicle/edition and access date. Free, no
   infrastructure, relies on the reader's diligence.
2. **Per-entry DOIs.** What the OED does since 2023 — every entry carries a DOI under
   Oxford's prefix (`https://doi.org/10.1093/OED/1042593202` for *sustainability*).
   Gold standard. Requires a paid registration agency membership.
3. **Release DOIs via Zenodo.** Free. Every tagged GitHub release is archived and gets
   its own DOI, plus a "concept DOI" that always resolves to the newest version. Also
   mirrors into Software Heritage.
4. **Citation metadata in the repo.** A `CITATION.cff` file; GitHub renders a
   "Cite this repository" button from it and Zenodo reads it for record metadata. Free.

**Costed and rejected: per-entry DOIs.** 89,528 headwords + 753 roots = 90,281 entries.

| Path | Up-front | Recurring |
|---|---|---|
| Crossref, registered as database components ($0.06/DOI) | ~$5,420 | $200/yr |
| Crossref, registered as book chapters ($0.25/DOI) | ~$22,600 | $200/yr |
| DataCite direct membership (100k DOIs/yr included) | €0 | €2,200–2,700/yr |
| mEDRA (€0.90–4.50 per DOI) | €150 setup | €81,000–406,000 |

Crossref removes back-year registration fees entirely in January 2027, which could drop
the backfile cost to near zero — but only if a continuously revised dictionary's entries
count as "produced more than two full years ago", which is a question for Crossref, not
an assumption to build on.

**Decision: free layer only.** Per-entry DOIs buy granularity over a working permalink
and nothing else, and commit the project to registering DOIs on every monthly release
forever. DPD's readers are scholars and translators who follow links, not an indexing
bureaucracy. Revisit if DPD starts being cited in journals often enough to matter, at
which point an institution will likely sponsor it.

## Established facts

Verified by reading the code and querying the live db, not assumed:

- **Headword ids are never reused.** `gui2/database_manager.py::get_next_id` returns
  `max(id) + 1`. The live db has `max(id)` 90,108 against 89,528 rows — 580 retired ids
  from deleted words, none recycled. This is what makes the permalink genuinely stable.
- **The numeric permalink already works.** `exporter/webapp/static/app.js` reads `tab`
  and `q` from the query string on load; when `q` is all digits it triggers an id search,
  and `exporter/webapp/toolkit.py:252` resolves it via
  `DpdHeadword.id == int(q)`. No new route or code is needed to make the permalink work.
- **The version string is already everywhere it needs to be.** `tools/version.py`
  writes it to `config.ini` `[version] version` and to `db_info.dpd_release_version`;
  the webapp already passes `dpd_release_version` into the home page template.
- **`db_info` is already a citation-metadata carrier.** It holds `author`, `email`,
  `website`, `docs`, `github`, `latest_release`, `license`. Downstream apps read it.
- **The licence is stated two ways.** `README.md`, `docs/license.md`, the PDF front
  matter and `exporter/webapp/toolkit.py` all say CC BY-NC-SA 4.0. `docs/index.md`
  lines 25–28 say CC BY-NC 4.0 (three occurrences: prose link, anchor href, badge img).
  A repo-wide `rg` for `by-nc` excluding `by-nc-sa` returns those three lines and nothing
  else. **User confirmed: BY-NC-SA is correct.**
- **The author name is stated two ways.** "Bodhirasa Bhikkhu" in the Kobo/Kindle/PDF
  metadata and the webapp licence line; bare "Bodhirasa" in `pyproject.toml`, the
  GoldenDict/deconstructor/variants/grammar dictionary metadata, `db_info.author`, the
  RSS managing editor, and the PDF title page. **User confirmed: "Bodhirasa Bhikkhu"
  everywhere.**
- **There is no `LICENSE` file and no `CITATION.cff`** at the repo root.
- **The offline dictionary already ships help entries.** `shared_data/reference/help.tsv`
  is a two-column quoted TSV (`help`, `meaning`); `exporter/goldendict/export_help.py`
  turns each row into a dictionary entry whose headword is the `help` column. This is how
  a citation reaches GoldenDict, MDict and DictTango users offline.

## The recommended citation

**Whole dictionary:**

> Bodhirasa Bhikkhu. *Digital Pāḷi Dictionary*. Version v0.4.20260905. https://www.dpdict.net/

**A single entry:**

> Bodhirasa Bhikkhu. "gacchati 1." *Digital Pāḷi Dictionary*, version v0.4.20260905.
> https://www.dpdict.net/?tab=dpd&q=24043

Once Zenodo is connected, the DOI replaces the bare URL in both.

Style-agnostic on purpose. The docs page shows the pattern and how it maps onto Chicago,
MLA and APA rather than picking a house style — the reader's journal decides that.

## Scope

### In scope

| Surface | Change |
|---|---|
| Repo root | new `CITATION.cff`, new `LICENSE` |
| `docs/how_to_cite.md` | new page, added to the mkdocs nav |
| `docs/index.md` | fix BY-NC → BY-NC-SA (3 lines), link the new page |
| `docs/license.md` | link the new page |
| `README.md` | "How to cite" section |
| `exporter/webapp/templates/home.html` | "how to cite" link **and the release version** in the DPD footer pane |
| `exporter/goldendict/export_help.py` | new generated `cite` entry, so the citation ships offline |
| `tools/version.py` | new `db_info` `citation` key; author → "Bodhirasa Bhikkhu" |
| `exporter/pdf/templates/front_matter.typ` | citation block; "Created by" → full name |
| `pyproject.toml` | author name |
| `exporter/goldendict/main.py` | dictionary author + description name |
| `exporter/deconstructor/deconstructor_exporter.py` | author + description name |
| `exporter/variants/variants_exporter.py` | author name |
| `exporter/grammar_dict/grammar_dict.py` | author name |
| `tools/rss_feed.py` | managing editor name |

**Sibling repo `../dpd-flutter-app`** (added at the user's request after the first pass):

| Surface | Change |
|---|---|
| `lib/providers/citation_provider.dart` | new — reads the `citation` row of `db_info` |
| `lib/widgets/secondary/citation_card.dart` | new — the citation, a copy button, a link to the docs page |
| `lib/widgets/info_popup.dart` | new `How to Cite` item in the info menu, new `InfoContent.citation` |
| `test/widgets/citation_card_test.dart` | new — renders the citation, and the fallback when absent |
| `README.md` | short "How to Cite" section |

### Out of scope, and why

| Thing | Why |
|---|---|
| Per-entry DOIs | costed above; rejected |
| Connecting Zenodo | needs the user's GitHub/Zenodo account; a checklist is delivered instead |
| A "copy citation" button on each entry | a UI change to the shared headword template, which also renders inside GoldenDict; not asked for. Deferred, noted below |
| `exporter/pdf/templates/thanks.typ`, newsletters | those "Bodhirasa" are sign-offs on a letter, not attribution metadata |
| The epub `file-as` metadata | that field is a sort key, and bare "Bodhirasa" is correct for sorting |
| Kindle/Kobo/Apple metadata | already says "Bodhirasa Bhikkhu" |

## Design decisions

- **One source of truth for the citation string, in `tools/version.py`.** The citation
  embeds the version, and the version is generated there. Building it anywhere else means
  a second place that goes stale the month after someone forgets. It lands in `db_info`
  alongside the licence and website that are already there, so every downstream consumer
  gets it for free.
- **A `LICENSE` file is added even though this is a citation thread.** `CITATION.cff`
  requires an SPDX licence id, and the reason `docs/index.md` drifted is that the repo
  never had a canonical licence file to check against. One file removes the class of bug.
- **The Zenodo DOI is left out rather than faked.** Everything is written to be correct
  without a DOI, with one clearly-marked line in `CITATION.cff` and one in the docs page
  to fill in once the user has connected Zenodo. A placeholder DOI in a published file is
  worse than no DOI.
- **The offline citation is generated at export time, not stored in `help.tsv`**
  (changed during implementation). `help.tsv` is static text, so an entry written there
  could not name the version — and a citation without a version is the exact failure this
  thread exists to fix. `add_citation()` in `exporter/goldendict/export_help.py` builds
  the entry from `make_citation()` and the version in `config.ini`, following the shape
  of the existing `add_bibliography` and `add_thanks`.
- **The app reads the citation, it does not compose one.** `db_info` is already copied
  verbatim into the mobile database (`PASSTHROUGH_TABLES` in `mobile_exporter.py`), so
  the `citation` row arrives without any exporter change, and the app cannot drift from
  what dpd-db decided. The card degrades to a "needs updating" message on an older
  database that predates the key.
- **No licence change in the app.** Its `LICENSE` (MIT, app code) and `LICENSE-database`
  (CC BY-NC-SA 4.0, the dictionary) are already correct and correctly separated.
- **The website shows the version, not only a link** (added during implementation).
  `dpd_release_version` already reached the browser, but purely as a cache-busting query
  parameter — it was displayed nowhere, so a reader could not cite the version in front
  of them. Telling people to cite a version they cannot see is not a citation scheme.
- **The website gets a link, not an inline citation block.** The results already carry a
  licence line from the previous thread; a second block on every search would be noise.

## Non-goals

- Any change to the licence terms themselves.
- Any change to how the version string is generated.
- Registering any DOI, with anyone, for money.
- Changing the permalink format (it already works; this thread documents it).

## Acceptance

- The repo landing page on GitHub shows a "Cite this repository" button.
- The docs site has a "How to cite" page in the navigation, reachable from the home page
  and the licence page.
- Looking up "cite" in GoldenDict/MDict/DictTango returns the recommended citation.
- `db_info` carries a `citation` key holding the current version's citation.
- The PDF's front matter states how to cite it.
- Every licence statement in the repo says Attribution-NonCommercial-ShareAlike.
- Every author attribution says "Bodhirasa Bhikkhu".
- The user has a short checklist for connecting Zenodo, after which one line in two files
  gets the DOI.

## Deferred (not doing, noted for the user to request)

- A per-entry "cite this entry" control in the dictionary display.
- Per-entry DOIs, should funding appear.
