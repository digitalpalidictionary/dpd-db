## Thread
- **ID:** 20260512_book_translator
- **Objective:** Single source of truth + translator for CST book identifiers (4 input types ↔ each other).

## Files Changed
- `tools/cst_book_translator.py` — runtime module: `BookInfo` dataclass + `all_books / from_cst_filename / from_gui_code / from_dpd_code / from_cst_book_name / translate`.
- `tools/cst_book_translator.tsv` — canonical data (217 rows, one per CST `.xml`).
- `scripts/build/generate_books_tsv.py` — one-shot generator that merges `cst_texts`, `book_codes`, `file_list`, extracts book names from CST XMLs (with `-e`/`-o` → `-a` normalization, chapter/subhead fallback, SPV grouping).
- `tests/tools/test_cst_book_translator.py` — 17 tests covering round-trips, fan-out, case-insensitivity, unknown inputs, all four `translate()` dispatch paths, `cst_xml_path` existence.
- `kamma/threads/20260512_book_translator/{spec,plan}.md` — thread docs.

## Findings
No blocking or major findings.

Minor (noted, not fixed — TSV is hand-editable so user can polish):
- A handful of `.nrf` rows have empty `gui_book_code` / `dpd_book_code` because those identifiers do not exist in the source dicts (e.g. e1002n.nrf "Nītimañjarī" has no DPD code in `abbreviations.tsv`). The TSV row is still present, just with empty cells — correct behavior per spec.
- `BookInfo.cst_xml_path` instantiates `ProjectPaths()` on each access. Property is rarely called and `ProjectPaths()` is cheap, so no caching added.

## Fixes Applied During Review
None — all earlier round-trips of fixes (gui→dpd fallback for mul files, XML name extraction, case normalization, chapter-only fallback for `.nrf`, SPV grouping for e0901–e0907) were applied during implementation in response to user feedback.

## Test Evidence
- `uv run pytest tests/tools/test_cst_book_translator.py` → 17 passed
- `uv run ruff check tools/cst_book_translator.py tests/tools/test_cst_book_translator.py scripts/build/generate_books_tsv.py` → clean
- Spot checks: `s0101m.mul ↔ dn1 ↔ DN ↔ "Dīghanikāya, Sīlakkhandhavaggapāḷi"` round-trips; `from_dpd_code("DN")` → 3 rows; `from_dpd_code("VINa")` → 5 rows; `from_dpd_code("SPV")` → 7 rows; `from_gui_code("kn14")` → 2 rows; `cst_xml_path.exists()` True.

## Verdict
PASSED
- Review date: 2026-05-14
- Reviewer: kamma (inline)
