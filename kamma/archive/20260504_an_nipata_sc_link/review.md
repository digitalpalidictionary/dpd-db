## Thread
- **ID:** 20260504_an_nipata_sc_link
- **Objective:** Add AN nipāta support to SuttaInfo, mirroring is_samyutta/is_vagga pattern

## Files Changed
- `db/models.py` — added `is_nipata` cached_property; added AN branch in `sc_vagga_link`
- `tools/sutta_codes.py` — added `not su.is_nipata` to sc_code exclusion guard
- `exporter/webapp/templates/dpd_headword.html` — is_nipata var, "nipāta" button label, "SC Nipāta Card" link
- `exporter/goldendict/templates/dpd_headword.jinja` — same three edits

## Findings
No findings.

## Fixes Applied
None.

## Test Evidence
- Smoke test: AN1–AN11 `is_nipata=True`, `sc_vagga_link` correct for all 11
- Negatives: SN1, MN1, DN1 `is_nipata=False`
- Variants (`tikanipāta 1`, `catukkaṅguttara`, `navaṅguttara`) resolve via alias map to correct canonical SuttaInfo
- `coderabbit review --agent` → 0 findings

## Verdict
PASSED
- Review date: 2026-05-04
- Reviewer: kamma (inline)
