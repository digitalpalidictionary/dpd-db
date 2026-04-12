# abbreviations_other.tsv

Master list of abbreviations from external Pāḷi dictionary sources.

## Columns
- `source` — short code: `PTS`, `CST`, `General`, `Cone`, `CPD`
- `abbreviation` — exactly as it appears in the source
- `meaning` — plain-text expansion
- `category` — `text` | `grammar` | `symbol` | `edition` | `resource` | `other`
- `notes` — sub-section, ref codes, or context

## Sources (as of 2026-04-12)
| source  | rows | description |
|---------|------|-------------|
| PTS     | 558  | Pali Text Society abbreviations |
| CPD     | 306  | Critical Pāli Dictionary bibliography abbreviations |
| Cone    | 145  | Dictionary of Pāli (Cone) front-matter abbreviations |
| CST     | 57   | Chaṭṭha Saṅgāyana Tipiṭaka abbreviations |
| General | 23   | Edition/variant-reading codes curated by Bryan Levman |
| **Total** | **1089** | |

## Notes
- This file is the master list. Edit it directly — no extraction script.
- Populated into the `lookup` table via `db/lookup/help_abbrev_add_to_lookup.py`.
- Exported to GoldenDict and webapp via the standard exporter pipeline.

## Known gaps (tracked in issue #77)
- BJT abbreviations
- SYA abbreviations
- MST abbreviations (SuttaCentral)
