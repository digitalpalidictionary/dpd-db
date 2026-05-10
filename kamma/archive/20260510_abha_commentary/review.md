## Thread
- **ID:** 20260510_abha_commentary
- **Objective:** Wire up `abha` (Abhidhamma commentaries) with source prefix `ADha` into `cst_source_sutta_example.py` and gui2.
- **GitHub issue:** #150 (left open).

## Files Changed
- `tools/cst_source_sutta_example.py` — added `abha_abhidhamma_commentary()` parser + dispatcher case.
- `gui2/dpd_fields_examples.py` — added `"ADha Abhidhamma Commentary": "abha"` to book_codes.

## Findings
| # | Severity | Location | What | Fix |
|---|----------|----------|------|-----|
| 1 | minor | `abh03a.att.xml` | Spurious `<p rend="book">Abhidhammapiṭake` inside abh03a bumped `vagga_counter` from 3→4 | Guard added: only treat `book` headings containing "aṭṭhakathā" as volume boundaries. |

No other findings.

## Test Evidence
- `uv run ruff check tools/cst_source_sutta_example.py gui2/dpd_fields_examples.py` → all checks passed.
- `abha` + "cittuppād" → 71 examples, prefixes ADha1/2/3. ✅
- `abha` + "khandh" → 1035 examples, prefixes ADha1/2/3. ✅
- `abha` + "dhātukath" → 21 examples, prefixes ADha1/3. ✅
- `__main__` block unchanged (book = "vin5"). ✅

## Verdict
PASSED
- Review date: 2026-05-10
- Reviewer: kamma (inline)
