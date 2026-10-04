# Spec: Wikipedia Buddhist Encyclopedia Dictionary (other-dictionaries)

> **Renamed 2026-10-04 after review:** `dictionaries/wikipedia` → `dictionaries/buddhist_wiki`, tests `test_wikipedia_*` → `test_buddhist_wiki_*`, output `buddhist-wiki.zip`, display name "Buddhist Wiki" (was "DPD Buddhist Encyclopedia"), export flag `--skip-buddhist-wiki`. Paths below are as they were during the thread.


## Overview

Add a `wikipedia` dictionary to `resources/other-dictionaries/`: a GoldenDict/MDict export of the English Wikipedia **Category:Buddhism tree** (full tree, user decision — size is not a constraint for these formats), following the exact module pattern of the existing dictionaries (`dictionaries/nyanatiloka/` etc.).

Each entry carries **extracted plain text** of the article. Internal Wikipedia links (`[[Article|label]]`) become **colored anchors** that GoldenDict/MDict resolve as lookups within the same dictionary:

- GoldenDict: `<a href="bword://Title">label</a>`
- MDict: `<a href="Entry://Title">label</a>`

License: English Wikipedia text is **CC BY-SA 4.0**. Attribution must be carried in the dictionary metadata (description field), plus a dedicated "About / License" entry, plus a per-entry link back to the online article. This is a different situation from PTS (see AGENTS.md attribution rules): CC BY-SA is explicitly designed for reuse, so inclusion is clean, but attribution + share-alike must be visibly honored.

> **Scope change (user decision, 2026-10-04):** the Category:Buddhism tree is walked to **depth 5 only** (`MAX_DEPTH = 5`), giving 23,840 articles, not the full tree. Measured: the full tree (29,249 categories, 177,254 articles) drifts off topic from depth 5 down — "Burmese expatriate footballers", Tamil Nadu politics, the 2006 Africa Cup of Nations. Classifying articles with Jev was considered and rejected as overkill. Every "full tree" statement below now means "depth ≤ 5".
>
> **Route change (user decision, 2026-10-04):** article text comes from the action API, not the pages-articles dump (~100 MB vs 25 GB at depth ≤ 5); redirects come from the `redirect` SQL dump.
>
> **Name and licence (user decision, 2026-10-04):** the Wikimedia trademark policy bars "Wikipedia" in a product name, so the dictionary is **"DPD Buddhist Encyclopedia"** (output `buddhist-encyclopedia.zip`), described as text adapted from English Wikipedia. CC BY-SA 4.0 requires a link to the licence text: it is in the description, the About entry and every entry's source line.

## Verified facts (checked in repo / online, 2026-10-03)

- Existing pattern: `dictionaries/<name>/<name>.py` loads a source file, builds `list[DictEntry]`, calls `vendor.dpd_tools.goldendict_exporter.export_to_goldendict_with_pyglossary` + `vendor.dpd_tools.mdict_exporter.export_to_mdict`, with a per-dict CSS file. Outputs go to `build/goldendict/` and `build/mdict/`.
- The vendor `DictEntry`/`DictInfo`/`DictVariables` contract is generic HTML-in, so link schemes and styling pass through unchanged; nothing in vendor hard-codes a link scheme.
- Full Category:Buddhism tree ≈ **28k subcategories, ~250k articles** (DBpedia SKOS count, 2026-10-03; noisy with maintenance categories — a cleaning pass is required). Measured 2026-10-04 from the dumps: 29,249 categories, 177,254 articles; shipped scope is depth ≤ 5 (23,826 listed).
- The Wikipedia action API rate-limits this machine's IP (429s observed during census attempts) — any API-based fetch must be resumable and aggressively polite, or dumps must be used instead.
- `dumps.wikimedia.org` serves `enwiki-latest-pages-articles` (~23 GB) and `enwiki-latest-categorylinks.sql.gz` (~2.5 GB) without rate limits.

## Phased delivery

The thread ships in **two phases**:

- **Phase 1 — Proof of concept**: a limited article set (~200–500 hand-picked Buddhist articles: core concepts, a few texts, a few biographies) taken end-to-end through the whole pipeline — fetch → wikitext→text+links cleaning → `bword://`/`Entry://` conversion → GD + MDict export → verified in GoldenDict. Goal: validate the link scheme, CSS, cleaning quality, and exporter wiring before any mass fetch.
- **Phase 2 — Full build**: generate the full cleaned article list (~150k–250k), run the chosen fetch strategy at scale (resumable, checkpointed), and produce the final GD + MDict builds.

Phase 1 must not need rework for Phase 2: the pipeline code, entry builder, and exporter wiring are identical; only the article list and fetch volume differ.

## What it should do

1. **Article list generation**: enumerate the mainspace articles of the Category:Buddhism subtree, excluding hidden/maintenance categories (e.g. "Articles containing...", CS1 errors). Source: Petscan export (manual, browser) or dump-based crawl (categorylinks). The list is stored as a tracked artifact (`dictionaries/wikipedia/source/article_list.txt` or equivalent) so the content fetch is decoupled and repeatable. Phase 1 uses a small fixed seed list instead (checked into the repo).
2. **Content fetch**: obtain per-article text **with links preserved** (plain-text extract APIs strip `[[links]]`, so the source must be wikitext or rendered HTML). Preferred: dump-based (download pages-articles once, stream-parse with a wikitext parser, keep only listed articles, map `[[Title|label]]` → anchors). Fallback: resumable API fetch of wikitext with checkpoint files. Stored in `dictionaries/wikipedia/source/` (gitignored if huge — decide during implementation, consistent with how `ap90web1.zip` is handled).
3. **Entry building**: headword = article title; definition = cleaned paragraphs as HTML, internal links as colored `bword://` (GD) / `Entry://` (MD) anchors; redirects pointing at an article become synonyms of that article's entry; external links, images, infoboxes, references stripped. Each entry ends with a small attribution line linking to the online article.
4. **Metadata & license**: bookname "Wikipedia Buddhist Encyclopedia (English)"; description carries CC BY-SA 4.0 attribution + source URL + build date; first entry is an "About Wikipedia Buddhist Encyclopedia" article covering license terms and how links work.
5. **Export**: via the existing vendor exporters, producing `build/goldendict/wikipedia.zip` and `build/mdict/wikipedia.zip`, with a `wikipedia.css` controlling link color and body typography.
6. **Registration**: add to `dictionaries/README.md` table and `scripts/export_all.py` (verify how dictionaries are registered there).

## Assumptions & uncertainties

- **Fetch strategy (dump vs API) is the main open decision.** Spec prefers dumps (robust, no rate limits, "size doesn't matter"), but a 23 GB one-time download is a real cost; plan should let the implementer fall back to resumable API wikitext fetch if the dump route stalls. Assumption: either is acceptable; the output artifact is identical.
- **Tree cleaning quality**: the ~250k figure includes some junk; the accepted list may end up anywhere between 150k–250k articles. Assumption: we ship whatever survives hidden-category exclusion and mainspace filtering, without hand-curating topical boundaries.
- Wikitext→text+links parsing via `wikitextparser` (new dependency in the sub-project's pyproject) is adequate for reading-quality output; template-heavy articles will read imperfectly. Accepted: this is a reading aid, not a Wikipedia mirror.
- Redirects: assumed resolvable from the same dumps/API; if awkward, redirect-as-synonym is dropped (links to redirects must still resolve — normalize through redirect table).
- GD/MD link schemes confirmed as `bword://` / `Entry://` from GoldenDict/MDict documentation knowledge; **verify empirically in GoldenDict during implementation** before mass-producing the build.

## Constraints

- Python 3.13 + `uv`, modern type hints, `pathlib.Path`, no `sys.path` hacks (project conventions).
- Follow existing `dictionaries/<name>/` module pattern and vendor exporter APIs — no new exporter framework.
- Fetch/build must be resumable and non-interactive (CI-friendly), with progress logging via `vendor.dpd_tools.printer`.
- Respect `.gitignore` conventions for large source artifacts (see Apte precedent).
- `ruff check` / `ruff format` / `pytest tests/` clean; pyright clean on new files (remember `tests/` pyright gotcha in tech.md).

## How we'll know it's done

**Phase 1 (PoC):**
- The ~200–500-article seed builds both formats from source without manual steps.
- GoldenDict loads the GD zip: entries appear; clicking a colored link jumps to that entry in the same dictionary; CSS colors apply. MDict equivalently (`Entry://`).
- "About" entry present; spot-checked entries carry the online-article link.
- `pytest tests/` passes including link-conversion/cleaning tests on a fixture wikitext sample.

**Phase 2 (full):**
- Full build runs from the stored article list without manual steps.
- Article count at build end matches the article list within small tolerance; redirects resolve.
- Same GoldenDict/MDict verification spot-checks as Phase 1, on randomly sampled entries.

## What's not included

- Flutter app changes (this dictionary is for GoldenDict/MDict only).
- Images, infoboxes, math, references, categories bar, or any non-prose content.
- Languages other than English Wikipedia.
- Incremental update machinery (rebuild is from-scratch, fetch step is resumable but not incremental).
- Curating/trimming the topical scope beyond the depth-5 cut (user decision 2026-10-04), minus hidden categories.