## Thread
- **ID:** 20260414_root_base_family_root
- **Objective:** Filter root_base by root_sign and auto-derive family_root from construction

## Files Changed
- `gui2/database_manager.py` — added root_sign filtering for root_base, construction-based family_root derivation
- `gui2/dpd_fields.py` — updated submit handlers to pass root_sign and construction

## Findings
No findings.

## Fixes Applied
None

## Test Evidence
- User tested root_base filtering with various root_signs → pass
- User tested family_root derivation from construction → pass

## Verdict
PASSED
- Review date: 2026-04-14
- Reviewer: kamma (inline)
