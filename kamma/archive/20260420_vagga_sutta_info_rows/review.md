## Thread
- **ID:** 20260420_vagga_sutta_info_rows
- **Objective:** Generate vagga rows matching the `sutta_info.tsv` column layout so the user can merge vagga metadata into the master TSV.

## Files Changed
- `scripts/suttas/vaggas/__init__.py` — package marker.
- `scripts/suttas/vaggas/compile_vaggas.py` — main generator (renamed from `generate.py`). Loads `sutta_info.tsv`, groups vagga headwords by `dpd_code`, resolves anchor rows (exact / SN-prefix / SN last-row-fallback), writes `compile_vaggas.tsv` with a trailing `status` column.
- `scripts/suttas/vaggas/extract_vaggas.py` — AN-only scraper: produces four source TSVs (DPD/CST/SC/BJT) to support manual alignment of AN1/AN2 vaggas that have no sutta_info rows.
- `scripts/suttas/vaggas/compile_vaggas.tsv` — generator output (451 rows: 401 ok, 50 miss).
- `scripts/suttas/vaggas/extract_vaggas_{dpd,cst,sc,bjt}.tsv` — AN source exports.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | blocking | `compile_vaggas.py:58,188` | `sutta_info.tsv` gained an `edited` column (now 45 fields incl. trailing empty from CRLF `\t\r\n`); `csv.DictReader` returned 45 headers with a trailing `''`, tripping `assert len(headers) == 44` and producing an empty-named output column. | Re-running the generator failed, so the thread could not be re-verified or safely regenerated. | Filter empty header names (`[h for h in fieldnames if h]`) so the real count stays 44 and the output omits the phantom column. |

## Fixes Applied
- Filtered empty trailing fieldname in `load_sutta_info`.
- Updated `plan.md` and `spec.md` to reflect the renamed script, new output path, and the added `extract_vaggas.py` scrapers.

## Test Evidence
- `uv run python scripts/suttas/vaggas/compile_vaggas.py` → exits 0; reports `401ok/50miss`.
- Run twice, `cmp` on output → byte-identical (deterministic).
- `wc -l compile_vaggas.tsv` → 452 (1 header + 451 rows).
- Status breakdown: 401 `ok`, 29 `miss:an1_not_in_sutta_info`, 1 `miss:dhp_verse_vs_chapter`, 20 AN2/AN3/AN7-11 tail-range misses — all matching previously-documented out-of-scope cases.

## Residual Risk
- Remaining misses (AN1 × 29, AN2 tail × 14, other AN tails × 6, DHP × 1) are expected — AN1/AN2 vaggas have no sutta_info anchor rows and need manual population using the `extract_vaggas_*.tsv` files.
- `extract_vaggas.py` output not independently re-verified against CST/SC source semantics; treated as scratch data for manual user alignment, matching the spec's throwaway posture.

## Verdict
PASSED
- Review date: 2026-04-21
- Reviewer: Claude Opus 4.7 (same agent as implementation — review is less independent; user requested finalize)
