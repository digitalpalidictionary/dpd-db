# shared_data/reference/

## Purpose & Rationale
This directory stores the hand-curated reference content that surrounds the core
dictionary data: help text, abbreviation keys, bibliographic sources, and
acknowledgments. It is the **canonical source of truth** for this content.

These files are intentionally kept as plain TSV in `shared_data/`, **not** as
database tables. They are small, hand-edited, and git-diffable, so a TSV is the
lowest-friction home for editors and reviewers. The database holds only a
*derived* copy (see Data Flow below); the TSVs remain authoritative.

## Files
- **`help.tsv`** — contextual help strings for the user interface.
- **`abbreviations.tsv`** — DPD's own abbreviations (abbrev, meaning, pāli,
  example, explanation, ru_abbrev, ru_meaning).
- **`abbreviations_other.tsv`** — external-source abbreviations
  (PTS, CPD, Cone, CST, General). See `abbreviations_other_README.md`.
- **`bibliography.tsv`** — authoritative source list for citations.
- **`thanks.tsv`** — acknowledgment of contributors and organizations.

## Relationships & Data Flow
- **Source of truth:** these TSV files, edited by hand.
- **Ingestion:** `db/lookup/help_abbrev_add_to_lookup.py` packs `help`,
  `abbrev`, and `abbrev_other` into the `Lookup` table (JSON columns) for fast
  runtime lookup by the webapp and browser extension.
- **Consumption:** the GoldenDict, Kindle, and PDF exporters read these TSVs
  directly; the webapp reads the derived `Lookup` columns.

## Interface
Managed via manual TSV edits. After editing, rebuild the `Lookup` data with
`db/lookup/help_abbrev_add_to_lookup.py` so the derived copy stays in sync.
