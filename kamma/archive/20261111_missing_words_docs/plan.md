# Plan: Missing Words page, updated monthly

## Architecture Decisions
- Follow the sibling pattern: `tools/docs_update_<name>.py`, a `ProjectPaths` attribute for each output, a recipe line in `just docs-update`, a test in `tests/tools/`.
- Move the script with its contents. Only the paths, the module docstring and the `main` wiring change.
- The monthly run stays local and manual. The release workflow is not touched.

## Model Strategy
| Phase | Tier | Suggested model | Reason |
|---|---|---|---|
| 1 — Move and wire | Fast | Sonnet | Mechanical edits |
| 2 — Tests | Fast | Sonnet | Small fixtures, copy the sibling test style |
| 3 — Menu and verify | Fast | Sonnet | Config edit and commands |

> Order changed 2026-11-11 at the owner's request: Phase 1 and the menu and page tasks of Phase 3 ran first, so the owner can see the page live (`just mkdocs` style serve) and give feedback. Phase 2 (tests) follows the feedback.

## Phase 1 — Move and wire — *Fast*
- [x] Add `docs_missing_words_md_path` and `docs_missing_words_pdf_path` to `tools/paths.py`, next to the other `docs_*` paths.
  → verify: `uv run pyright tools/paths.py` is clean.
- [x] Move `scripts/find/pass1_unknown_by_book.py` to `tools/docs_update_missing_words.py`. Write to the two new paths. Add a line near the top of the page: `[Download as PDF](missing_words.pdf)`. Keep the sync note.
  → verify: `ls scripts/find/pass1_unknown_by_book.*` shows no `.py`. Delete the old untracked `.md` and `.pdf` there by name.
- [x] Update `justfile`: add `uv run python tools/docs_update_missing_words.py` to `docs-update`, and point `unknown` at the new tool.
  → verify: `just --list` shows both recipes.
- [x] Lint: `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright` on `tools/docs_update_missing_words.py` and `tools/paths.py`.
  → verify: no errors.

## Phase 2 — Tests — *Fast*
- [x] Create `tests/tools/test_docs_update_missing_words.py`. Use an in-memory lookup table. Cases: an abbreviation-only row is in neither count; an `epd`-only row and an absent word are unrecognised; a deconstructor-only row needs a headword; a variant-only row is in neither; `missing_percent` rounds to one decimal and handles zero.
  → verify: `uv run pytest tests/tools/test_docs_update_missing_words.py` passes.
- [x] Add rendering tests: the markdown starts with the title and the date; each book has a `###` list heading under its group; a book with no missing words says `No missing words.`
  → verify: same file passes.
- [x] Prove the tests guard the rules: revert the abbreviation check in the tool by hand, run the file, expect the abbreviation test to fail for that reason. Restore at once.
  → verify: report the failing test names; after restore, all pass.
  (2026-11-11: three reverts, each failed one test for the right reason: abbreviation rule off and headword check off both failed `test_classify_splits_the_missing_words`; top words sorted ascending failed `test_count_book_lists_the_most_frequent_missing_words_first`. Restored, 12 pass.)
- [x] Lint the test file: `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright --project /dev/null`.
  → verify: no errors.

## Phase 3 — Menu and verify — *Fast*
- [x] Add `- Missing Words: "missing_words.md"` to the `nav:` in `mkdocs.yaml`, directly after the Contributing block.
  → verify: the line sits between `Resources: "contributing/resources.md"` and `Other Dictionaries`.
- [x] Run `uv run python tools/docs_update_missing_words.py` once to create `docs/missing_words.md` and `.pdf`.
  → verify: both files exist, both start with `Missing Words in DPD` and the date.
- [x] Run `uv run mkdocs build` and check the built site holds `missing_words/index.html` and `missing_words.pdf`.
  → verify: no warning about the page or the link; `ls site/missing_words*` shows both.
  (2026-11-11: `mkdocs build -d <scratchpad>` passed with no warning about the page; `missing_words/index.html` and `missing_words.pdf` both exist. Also seen live with `mkdocs serve`: link resolves to `../missing_words.pdf`.)
- [x] Check `docs/technical/project_folder_structure.md` for a tools list that names the other `docs_update_*` tools. If it does, add this one.
  → verify: `rg -n "docs_update" docs/technical/project_folder_structure.md`.
  (2026-11-11: that file names no `docs_update_*` tool, so no line added.)
- [x] Run `just typecheck` and the related tests: `uv run pytest tests/tools -k docs_update`.
  → verify: clean.
- [x] Ask the owner to run `just mkdocs`, open the Missing Words page after Contributing, and approve the look.
  → verify: owner confirms. Then the owner commits `docs/missing_words.md`, `docs/missing_words.pdf`, `mkdocs.yaml` and the code.

## Monthly routine (after this thread)
On each uposatha day, with the other docs updates: `cd <repo root> && just docs-update`, then commit `docs/` and push. The push rebuilds the site.

## Changes during the thread (owner feedback, 2026-11-11)
- Heading levels reworked so the contents list shows every section (spec item 7). Book names are bold lines, not headings.
- Tables full width through `md_in_html` in `mkdocs.yaml`, a wrapper div in the page and a rule in `docs/stylesheets/extra.css` (spec item 8).
- Review fixes: equal counts in Pāḷi order, `All books added` label, dead branch removed in `classify_missing_words`, three more tests (ties, auto-processed mapping, reading the saved files), the import-time `cst_texts` change moved into `main()`.
- Small refactor for tests: `lookup_has_data()` is a module function, used by the finder and by the tests.
- SuttaCentral added (spec, last section): rows follow the SuttaCentral books; tests for the union, the two-folder guard, the CST-wins count rule and the row/CST-code coverage.
- Second review (CodeRabbit: 1 finding, fixed; independent audit: 3 fixed, 2 accepted). The PDF is now compiled to a temporary file first, so a typst failure leaves both docs files untouched. Table CSS: first column 28%, no mid-word break in headings.
- Final checks 2026-11-11: ruff, pyright, pyrefly clean; full suite 3234 passed, 0 failed.
- Pass1 Auto drafts are no longer subtracted (owner, 2026-11-11): `auto_processed`, `auto_processed_for`, `_read_auto_processed` and `pass1_cst_code` removed, with their tests. A new test keeps a saved draft counted as missing.
