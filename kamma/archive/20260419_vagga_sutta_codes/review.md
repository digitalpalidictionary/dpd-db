## Thread
- **ID:** 20260419_vagga_sutta_codes
- **Objective:** Add sutta-code ranges to every vagga headword in the DPD database (MN, SN, AN, and all KN sub-books).

## Files Changed
- `scripts/add/vagga_codes/shared.py` — shared helpers: TSV loader, format_range, chapter→vagga/section, normalize_family_set, TSV writer
- `scripts/add/vagga_codes/runner.py` — CLI dispatcher per book (no `.commit`)
- `scripts/add/vagga_codes/apply.py` — commits a preview TSV to DB; dry-run supported; APPLY_STATUSES expanded to cover span/no-chapter/chapter-not-in-cst
- `scripts/add/vagga_codes/mn.py`, `sn.py`, `an.py`, `kn.py` — per-book preview generators
- `scripts/add/vagga_codes/dhp_m2.py` — DHP sutta-range generator using TSV `sc_code`, with DHP7 hardcoded override for bad `dhp90-00`
- `scripts/add/vagga_codes/kn_suggestions.py` — suggestions for TH/THI/JA (no DPD headwords yet)
- `scripts/find/sn_samyutta_mismatch_finder.py` — SN cross-field consistency check
- `gui2/dpd_fields.py:755` — vagga `meaning_lit` autofill: "chapter on " → "section on "

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `scripts/add/vagga_codes/kn.py` | KN sub-book TSVs are written inside `process()` rather than by the runner | Inconsistent with other books where the runner writes the TSV; minor cosmetic | Leave as-is — the shape is intentional since KN dispatches to multiple sub-books |

## Fixes Applied
- None (only a nit)

## Test Evidence
- `uv run python -c "from scripts.add.vagga_codes.shared import load_vagga_ranges; ..."` → 56 keys loaded
- `uv run python -m scripts.find.sn_samyutta_mismatch_finder` → 0 mismatches across 2258 SN headwords
- `uv run python -m scripts.add.vagga_codes.apply --book SN --dry-run` → updates=0 (already committed), rolled back
- `uv run python -m scripts.add.vagga_codes.apply --book AN --dry-run` → updates=0, rolled back
- `uv run python -m scripts.add.vagga_codes.apply --book DHP --dry-run` → updates=0, rolled back
- Commits applied to DB: MN 25, SN 212, AN 208, DHP 26 (+ sutta-range rewrite 26), UD 11, SNP 6, PV 4, VV 7 = **499 rows**

## Verdict
PASSED
- Review date: 2026-04-20
- Reviewer: haiku subagent (via kamma)
