# Thread: Compile master list of abbreviations from other Pāḷi dictionaries

## Issue Reference
GitHub issue #77 — "Add all abbreviations from all Pāḷi texts to DPD"

This thread covers the first compilation step of that issue: gathering and normalising
abbreviations from sources currently available in the repository into a single master
TSV. Exporter integration and docs-website work remain out of scope for this thread.

## Overview
Pāḷi scholarship uses many overlapping and conflicting abbreviation systems. The goal of
this thread is to consolidate the in-repo abbreviation data used by the project into one
authoritative file at `shared_data/help/abbreviations_other.tsv` that can later be
consumed by the exporter pipeline.

The implemented source model for this thread is:
- `pts` — PTS abbreviations, originally sourced from
  `shared_data/abbreviations/abbreviations_pts.tsv`
- `dpd_db` — DPD abbreviations loaded from `dpd.db` where `pos='abbrev'`
- `general` — consolidated general / edition / resource abbreviations, originally
  curated in `shared_data/abbreviations/abbreviations_bryan.tsv`
- `cone` — Cone front-matter abbreviations from
  `resources/other-dictionaries/dictionaries/cone/source/cone_front_matter.json`
- `cpd` — CPD abbreviations from
  `resources/other-dictionaries/dictionaries/cpd/source/cpd_clean.db`

## What it should do
1. Compile abbreviations from the five implemented sources above into
   `shared_data/help/abbreviations_other.tsv`.
2. Preserve special symbols and notation used by those sources where they appear.
3. Normalise everything into a single TSV with columns:
   - `source`
   - `abbreviation`
   - `meaning`
   - `category`
   - `notes`
4. Leave a short `shared_data/help/abbreviations_other_README.md` describing the file,
   its source list, and how to rebuild it.
5. Retire the old `shared_data/abbreviations/` source folder as part of the final state,
   after consolidating its contents into the new master output.

## Output Shape
- `source` uses the implemented short codes: `pts`, `dpd_db`, `general`, `cone`, `cpd`
- `abbreviation` stores the abbreviation as emitted by the source
- `meaning` stores the plain-text expansion or definition
- `category` may include `text`, `grammar`, `symbol`, `edition`, `resource`, `other`
- `notes` stores free-text context such as section labels or reference codes

## Constraints
- Do not run scripts automatically — only the user runs scripts.
- Do not modify `.env` / `.ini` files.
- Do not commit anything in this thread.
- Follow project rules: modern type hints, `Path` from pathlib, no `sys.path` hacks.
- The extraction script lives under `scripts/extractor/`.
- TSV output must be deterministic so diffs are readable.
- Use BeautifulSoup for Cone and CPD HTML parsing.
- Do NOT attempt to scrape BJT / SYA / MST / external websites in this thread.

## How we'll know it's done
- `shared_data/help/abbreviations_other.tsv` exists and has the five columns above.
- It contains rows from the five implemented sources: `pts`, `dpd_db`, `general`,
  `cone`, `cpd`.
- Rows are sorted stably by `(source, abbreviation)`.
- No empty `abbreviation` rows remain.
- A one-off extractor script exists and produces the TSV deterministically.
- Row counts per source are reported.
- Spot-checks pass for Cone `AAWG`, PTS `A.`, and representative `dpd_db` and CPD rows.

## What's not included
- Exporter integration (GoldenDict, MDict, webapp, mobile) — deferred.
- Docs-website update — deferred.
- Scraping new external sources such as BJT, SYA, MST, or external websites.
- Resolving conflicts between systems. Variants are preserved.
