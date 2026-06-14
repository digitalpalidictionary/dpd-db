## Thread
- **ID:** 20260614_cst_source_latent_bugs
- **Objective:** Resolve the output-changing latent bugs (A/B/C) + typing smell (D) carried over from the cst_source refactor. Does NOT close #157.

## Files Changed
- `tools/cst_source/parsers/misc.py` — `ApParser` `APP`→`AP`; `AptParser` drop dead `book = "AP"` overwrite (keeps `APt`)
- `tools/cst_source/parsers/abhidhamma.py` — `Abh2Parser` vagga-less subhead: `xxxxxxx`→`{self.section}` (mirrors `Abh1Parser`)
- `tools/cst_source/parsers/khuddaka.py` — delete unreachable `Kn17Parser` branch (referenced unbound locals)
- `tools/cst_source/parsers/base.py` — widen `sutta_counter`/`section_counter`/`vagga_counter` to `str | int` (Finding D, no runtime change)
- `tests/tools/cst_source/test_parsers.py` — NEW: 3 fast parser tests + 1 slow kn17 reachability test
- `dpd.db` (untracked) — 5 `source_1` migrations: `APP1`→`AP1`, `APP2.4`→`AP2.4`, `AP2.5`→`APt2.5`, `AP3.3`→`APt3.3`, `AP2.3`→`APt2.3`

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `dpd.db` (gitignored) | 5 `source_1` edits live only in local db; backup TSV still shows old codes | Data fix not in version control until TSV regen | Run normal db backup before commit |
| 2 | nit | `test_parsers.py:20-43` | Kn17 exclusion list duplicated verbatim | Could drift if parser list changes | Accepted for independent guard test |
| 3 | nit | `test_parsers.py:9-10` | Two import styles for `bs4` Tag | Cosmetic; ruff/pyright clean | Accepted |

No blocking or major findings.

## Fixes Applied
- None needed during review. (Finding 1 is a workflow step the user owns; findings 2-3 accepted as-is.)

## Test Evidence
- `uv run pytest tests/tools/cst_source/test_parsers.py` → 3 passed, 1 deselected
- `uv run pytest tests/tools/cst_source/test_parsers.py -m slow` → 1 passed
- `uv run pytest tests/tools/test_cst_source_refactor_parity.py tests/tools/cst_source/ tests/exporter/analysis/test_passage_by_code_parity.py -m "slow or not slow"` → 33 passed
- `uv run pytest tests/` → 2222 passed, 16 deselected
- `uv run ruff check` + `uv run pyright` on all touched files → clean
- db sweep → exactly 5 migrated codes, 0 `APP*` remaining, 424 apadāna (`APA`/`API`) codes untouched

## Verdict
PASSED
- Review date: 2026-06-14
- Reviewer: Claude (same agent as implementation — less independent; flagged)
