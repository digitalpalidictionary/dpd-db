## Thread
- **ID:** 20260503_an_vaggas
- **Objective:** Create per-source AN vagga extractor scripts (DPD, CST, SC, BJT, DPR) producing TSVs for manual alignment — GitHub issue #236

## Files Changed
- `scripts/suttas/dpd/an_vaggas.py` — queries live DB, one row per DPD AN vagga code
- `scripts/suttas/cst/an_vaggas.py` — parses UTF-16 XML, splits sub-vaggas in AN1 ch14-16, captures page numbers at first bodytext
- `scripts/suttas/sc/an_vaggas.py` — groups bilara-data JSON on (folder, vagga); handles AN1/AN2 per-file and AN11 peyyāla `:0.3` promotion
- `scripts/suttas/bjt/an_vaggas.py` — collapses BJT an.tsv to one row per vagga; chapter_key fix unlocks AN1 ch14 sub-vaggas
- `scripts/suttas/dpr/an_vaggas.py` — parses listam.js amlist structure; detects multi-element sections for sub-vagga rows

## Findings
No blocking or major findings.

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `bjt/an_vaggas.py:38` | Comment describes an edge case | Only non-obvious WHY needed | Left as-is — genuinely non-obvious |

## Fixes Applied (during session)
- **CST:** page numbers empty for first vagga of each nipāta — pages were read at chapter heading before `<pb>` tags; fixed by snapshotting pages at first bodytext.
- **SC:** 196 rows (missing AN11 Rāgapeyyāla) — `:0.2` was paṇṇāsaka label not vagga in peyyāla files; fixed by detecting "paṇṇāsaka" and promoting `:0.3`.
- **DPR:** regex missed peyyāla range entries (`'22-29'`); fixed with `[\d-]+` and `.split("-")[0]`.
- **DPR:** sub-vagga sections not emitted; fixed by detecting `[section][1]` existence as multi-sutta marker.
- **BJT:** AN1 ch14 etadaggapāḷi — 7 sub-vaggas collapsed to 1; fixed by adding sutta code chapter prefix to group key.

## Test Evidence
- DPD: 197 rows ✓
- CST: 197 rows ✓
- SC: 197 rows ✓
- BJT: 187 rows ✓ (genuine structural difference; many peyyāla sections absent from BJT source)
- DPR: ~197 rows ✓ (user confirmed)

## Verdict
PASSED
- Review date: 2026-05-04
- Reviewer: kamma (inline)
