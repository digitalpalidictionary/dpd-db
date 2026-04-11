# abbreviations_other.tsv

Master list of abbreviations from external Pāḷi dictionary sources.

## Columns
- `source` — short code: `pts`, `dpd_db`, `general`, `cone`, `cpd`
- `abbreviation` — exactly as it appears in the source
- `meaning` — plain-text expansion
- `category` — `text` | `grammar` | `symbol` | `edition` | `resource` | `other`
- `notes` — sub-section, ref codes, or context

## Sources (as of 2026-04-11)
| source  | description |
|---------|-------------|
| pts     | Pali Text Society abbreviations (~561 rows) |
| dpd_db  | DPD database `pos='abbrev'` headwords (~57 rows) |
| general | Edition/variant-reading codes curated by Bryan Levman (23 rows) |
| cone    | Dictionary of Pāli (Cone) front-matter abbreviations (~158 rows) |
| cpd     | Critical Pāli Dictionary bibliography abbreviations (~306 rows) |

## Rebuild
```bash
uv run python scripts/extractor/compile_abbreviations_other.py
```

## Known gaps (tracked in issue #77)
- BJT abbreviations
- SYA abbreviations
- MST abbreviations (SuttaCentral)
- External PTS/Cone front-matter not yet scraped
