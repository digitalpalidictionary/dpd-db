# Review: Missing Words docs page

**Verdict: PASSED** (2026-11-11)

## Reviewers
- CodeRabbit on `tools/` and on `tests/tools/`, run twice (before and after the SuttaCentral change).
- Independent from-scratch audit, run twice, in a fresh agent that read the files and the spec.
- Full test suite, ruff, pyright and pyrefly after the last change.

## Files changed
- `docs/missing_words.md` (generated page)
- `docs/missing_words.pdf` (generated PDF)
- `docs/stylesheets/extra.css`
- `justfile`
- `mkdocs.yaml`
- `tests/tools/test_docs_update_missing_words.py`
- `tools/docs_update_missing_words.py` (moved here from `scripts/find/`, which had it untracked)
- `tools/paths.py`

## Findings and fixes
1. CodeRabbit, tools, round 2 (minor): the page was written before the PDF compiled, so a typst failure left a new page and an old PDF. Fixed: the PDF is compiled to a temporary file first. Two tests guard it.
2. Audit round 1: the top-5 lists had a random order for equal counts, so each monthly run changed the file. Fixed: equal counts in Pāḷi order. A test fails with the old behaviour at three hash seeds.
3. Audit round 1: "Total" summed distinct words across books. Fixed by the owner's choice: the row is labelled "All books added".
4. Audit round 1: a dead branch in `classify_missing_words`. Fixed. Behaviour unchanged.
5. Audit round 1: no tests for the book mapping and the saved-file reading. Added, then removed with the Pass1 Auto subtraction (owner decision, below).
6. Own finding at the first full run: importing the tool changed the shared `cst_texts` dict and broke `test_every_xml_covered_exactly_once`. Fixed: the change moved into `main()`. A test guards it. Reverting it failed three tests.
7. Audit round 2: a half-missing SuttaCentral folder (Apadāna, Niddesa have two) was not caught. Fixed: every folder is checked. A test guards it.
8. Audit round 2: a stronger coverage test was needed. Added: each SuttaCentral row holds exactly the CST books of its SuttaCentral books.
9. Owner feedback: SuttaCentral words were missing. Added: rows follow the SuttaCentral books and combine the CST and SuttaCentral words. Measured effect on the Khuddaka books up to about 700 words.
10. Owner feedback: the numbers must reflect the database. Removed the Pass1 Auto subtraction completely. A test keeps a saved draft counted as missing.

Accepted, not fixed:
- "All books added" counts a word twice if it is in two rows. The label says it.
- "Distinct words" counts a hyphenated compound and its parts. The page does not say so.
- The count needs the SuttaCentral submodule. If a folder is empty the tool stops with an error.

## Checked and clean
- `md_in_html` extension: a build with and without it gave the same HTML for every page except the new one.
- All new CSS is scoped to `.missing-words`.
- The contribution form link matches the one on the Contributing page.
- No money request, no promise or sign-up on the page.
- CodeRabbit: 0 findings on the tests, both rounds.

## Test evidence (last run 2026-11-11)
- `uv run pytest tests/ -q`: 3232 passed, 12 deselected, 0 failed.
- `uv run ruff check`, `ruff format --check`: clean on the three Python files.
- `uv run pyright` (tools) and `pyright --project /dev/null` (tests): 0 errors.
- `uv run pyrefly check`: 0 errors.
- `uv run mkdocs build`: no warning about the page; page and PDF both in the built site.
- 25 tests in `tests/tools/test_docs_update_missing_words.py`. Each rule was reverted in turn and the matching test failed for the right reason.
- Two generator runs in a row gave byte-identical pages.
- The owner viewed the live page and approved the layout.
