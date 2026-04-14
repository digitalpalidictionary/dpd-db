## Thread
- **ID:** 20260414_sn_peyyala_collapsed_vaggas
- **Objective:** Fix incorrect Saṃyutta Nikāya peyyāla source numbering in the CST sutta example pipeline by handling collapsed `vitthāretabbo` vaggas.

## Files Changed
- `tools/cst_source_sutta_example.py` — corrected SN49/SN50/SN53 peyyāla ranges and added narrow counter-advance handling for known collapsed SN vaggas.
- `kamma/threads/20260414_sn_peyyala_collapsed_vaggas/plan.md` — recorded implementation and verification status.

## Findings
No findings.

## Fixes Applied
- Added `sn_collapsed_vagga_counts` for the explicitly identified collapsed SN vaggas.
- Added a narrow `rend == "centre"` branch in `sn_samyutta_nikaya()` to advance `g.sutta_counter` when the text contains `vitthāretabbo` and matches a known case.
- Corrected the affected `sn_peyyalas` ranges for SN49, SN50, and SN53.

## Test Evidence
- `python - <<'PY' ...` direct CST traversal check for SN49/SN50/SN53 → pass
- `python -m compileall tools/cst_source_sutta_example.py` → pass
- `coderabbit review --agent` → pass, `findings: 0`

## Verdict
PASSED
- Review date: 2026-04-14
- Reviewer: kamma-3-review (inline; same agent as implementation, plus CodeRabbit)
