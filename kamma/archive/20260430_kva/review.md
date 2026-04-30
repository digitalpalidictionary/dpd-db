## Thread
- **ID:** 20260430_kva
- **Objective:** Add dvemātikāpāḷi + kaṅkhāvitaraṇī-aṭṭhakathā (KVA) handler and gui2 integration

## Files Changed
- `tools/pali_text_files.py` — registered `"kva": ["vin04t.nrf.txt"]` in `cst_texts`, `sc_texts` (empty), `bjt_texts` (empty), and `all_books`
- `tools/cst_source_sutta_example.py` — added `kva_dvemātikā_kaṅkhāvitaraṇī()` handler, wired into match block, updated `__main__` tests
- `gui2/dpd_fields_examples.py` — added `"KVA dvemātikāpāḷi + kaṅkhāvitaraṇī": "kva"` to `book_codes`
- `gui2/books.py` — added `SuttaCentralSource("kva", ["kva"], None, None)` to `sutta_central_books`

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `cst_source_sutta_example.py:2739,2755` | Missing `.lower()` on two `g.sutta` assignments in commentary chapter/title handlers | Inconsistent normalisation vs rest of function | Added `.lower()` |
| 2 | major | `pali_text_files.py` | `kva` absent from `sc_texts`, `bjt_texts`, `all_books` | Other pipelines that iterate these registries would skip the book | Added empty entries to `sc_texts`/`bjt_texts`, added to `all_books` |

Note: `kva` was deliberately NOT added to `atthakatha_books` — it contains both pātimokkha (mūla) and commentary, so it doesn't cleanly classify as purely aṭṭhakathā.

## Fixes Applied
- Added `.lower()` to two sutta assignments in commentary mode
- Registered `kva` in `sc_texts`, `bjt_texts`, `all_books`

## Test Evidence
- `uv run python tools/cst_source_sutta_example.py` → 8 `[PASS]` (bhikkhu/bhikkhunī pātimokkha + commentary cases)
- gui2 book dropdown shows KVA entry — confirmed working by user

## Verdict
PASSED
- Review date: 2026-04-30
- Reviewer: kamma (inline) + CodeRabbit
