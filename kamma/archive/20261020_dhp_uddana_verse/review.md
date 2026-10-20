## Thread
- **ID:** 20261020_dhp_uddana_verse
- **Objective:** The CST example finder returned nothing for the Dhammapada uddāna line "buddhavaggamhi ṭhārasa" because the verse walk required a `gatha1` start line; fix the verse start and end rules.

## Files Changed
- `tools/cst_source/examples.py` — new verse walk: `find_verse_start` (stops at `gatha1`, a `gathalast`, or a non-verse element), forward walk through gatha1/2/3 to a `gathalast` or non-verse element, final full stop, no 1-second stall
- `tools/cst_source/corpus_index.py` — `_resolve_gatha1` removed; cache keyed on `find_verse_start`; docstring updated
- `tools/cst_source/extractor.py` — `find_gatha_example(x)` call (unused argument dropped)
- `tests/tools/cst_source/test_examples.py` — 9 tests on real CST snippets (new file)
- `kamma/threads/20261020_dhp_uddana_verse/artifacts/verse_walk_diff.py` + `.txt` — whole-corpus old-vs-new comparison and report

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `test_examples.py` | Backward stop at `gatha1` and `find_verse_start` identity had no test | A regression there would pass silently; the index cache depends on the identity | Added Ud 30 line-5 test and a `find_verse_start` identity test |
| 2 | minor | `examples.py:54` | Verses ending without a `gathalast` ended in "," (321 of 1,114 changed verses) | Visible in pasted examples | Full stop restored after the loop; 2 tests |
| 3 | nit | `corpus_index.py:8` | Docstring said "cached per verse" | One verse can have two starts (mid-verse `gatha1`) | Now "cached per verse start" |
| 4 | nit | `spec.md`, `plan.md` | Empty-line count given as 7 / 6 | Real count is 10 (6 empty, 4 a single space), re-measured | Corrected |
| 5 | nit | `test_examples.py:parse` | Copies `make_cst_soup` cleanup steps | Fixtures could drift from the loader | Deferred: accepted as is |

## Fixes Applied
- Findings 1–4 fixed (plan tasks R1–R5). Finding 5 left as is.

## Test Evidence
- `uv run pytest tests/tools/cst_source/` (scope: cst_source package) → 52 passed
- `uv run pytest -m slow tests/tools/cst_source/` (scope: index-vs-live parity on kn1, parser checks) → 2 passed
- `uv run pytest tests/` (scope: whole project) → 2195 passed, 12 deselected
- `just typecheck` (scope: whole repo, pyrefly) → 0 errors
- ruff `--no-force-exclude` + `pyright --project /dev/null` (scope: the 4 changed files; plain runs skip `tools/cst_source`) → clean; same pyright command finds 14 errors in the old `examples.py`
- Revert checks: old function fails 4 of 5 original tests; each review test fails against the code it guards
- Whole-corpus diff (scope: all 217 CST files, every gatha line) → 0 changes among verses the old code handled correctly; final-stop change re-checked over all 183,225 lines: only 81 lines differ, each by "," → "."
- Live: kn2 "buddhavaggamhi ṭhārasa" → DHP423, full uddāna verse; index equals live search
- CodeRabbit `--uncommitted --fresh` on `tools/cst_source` and (with `--include-untracked`) `tests/tools/cst_source` → 0 findings

## Not Verified
- About 310 of the 444 cut run-ons were not read one by one (the rule only cuts at a non-verse element).
- The gui2 book+word search was not run in the real app; the user is asked to test it.
- `exporter/analysis/book_to_verses.py` was not run (user runs scripts); its DHP423 choice was checked by reading.
- Source-markup limits stay: back-to-back `gathalast` lines are not joined; a stray `gatha1` splits a verse when the search hits it.

## Verdict
PASSED
- Review date: 2026-10-20
- Reviewer: independent subagent (general-purpose) + CodeRabbit; fixes by the implementing session
