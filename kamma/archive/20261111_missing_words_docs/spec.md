# Missing Words page on the docs site, updated monthly

## Overview
The owner wants the per-book report of missing words (script `scripts/find/pass1_unknown_by_book.py`, recipe `just unknown`) published on the public docs site, so contributors can see where DPD has gaps and pick a book. It must refresh once a month, on the uposatha day, with the other docs updates.

## What it should do
1. A new docs page `docs/missing_words.md` holds the report: title `Missing Words in DPD`, the date, the column definitions, the tables, and the top-5 word lists per book. Its content is exactly what the script writes today.
2. A PDF of the same report, `docs/missing_words.pdf`, is built from the same data, and the page links to it near the top.
3. The page is in the mkdocs menu as its own item directly after the **Contributing** section (before **Other Dictionaries**), named `Missing Words`.
4. The script becomes a docs-update tool, like its siblings: `tools/docs_update_missing_words.py`, run from `just docs-update` (see `justfile`). It writes both files into `docs/` through `ProjectPaths`.
5. The monthly run is the owner's local docs routine on the uposatha day: run `just docs-update`, commit, push. Pushing `docs/**` triggers `.github/workflows/static.yml`, which rebuilds the site. No new GitHub workflow step.
6. `just unknown` stays and runs the same tool, so the owner can still run it alone.
7. Heading levels (owner feedback 2026-11-11): the page has one `#` title only. The theme's table of contents shows the headings under the first `#` heading and drops a second one, so the top-words section was missing. Levels: `##` What the columns mean, Missing words by book, Most frequent missing words. `###` under them: the four column names, then the eight groups (once in each of the last two). Each book in the top-words section is a bold line, not a heading, so the contents list stays short (owner, 2026-11-11). The PDF uses the same levels.
8. Tables (owner feedback 2026-11-11): all tables have the same full width. The page body sits in `<div class="missing-words" markdown>`, which needs the `md_in_html` extension in `mkdocs.yaml`. A rule in `docs/stylesheets/extra.css` sets full width and a 40% first column. The PDF tables use fixed column fractions (3:1:1:1:1). Measured live: every table 688 px wide, columns 274 and 4 x 103 px.
9. Contribution line (owner, 2026-11-11): directly under the title, in the page and in the PDF, both with a live link: "If you would like to contribute to the dictionary, please fill in the contribution form and let us know what you would like to help with." The link goes to the contribution (offer your help) form, `https://forms.gle/Z7ENe8CVFpe2yQqKA`, the same link as `docs/contributing/index.md`. The wording is the owner's sentence, lightly reworded; the owner approves it.

## Current behaviour (read from the repo 2026-11-11)
- `scripts/find/pass1_unknown_by_book.py` runs in about 9 seconds. It writes `scripts/find/pass1_unknown_by_book.md` and `.pdf` (untracked). The PDF comes from `typst compile`, which is a project dependency.
- `draft_release.yml` never commits docs files. Only `uposatha_day.ini` is committed. The website changelog is written in the runner and lost, so docs updates are a local routine.
- `just docs-update` runs `tools/docs_update_abbreviations.py`, `_bibliography`, `_thanks` and `_how_to_cite`. Each has a path attribute in `tools/paths.py` (`docs_*_md_path`) and a test in `tests/tools/test_docs_update_*.py`.
- `static.yml` builds on a push to `docs/**` or `mkdocs.yaml`.
- The script reads `dpd.db`, the CST text under `resources/dpd_submodules/cst/romn_txt`, the SuttaCentral text under `resources/sc-data`, the sandhi OK list, and the variant and spelling TSV files (Pass1 Auto drafts are not read: owner, 2026-11-11). The run stays local because the GitHub run does not hold the owner's current database.

## Assumptions & uncertainties
- Verified: all items under "Current behaviour".
- Assumed: mkdocs copies `docs/missing_words.pdf` to the built site, and a relative link from the page resolves. Checked by `mkdocs build` in the plan.
- Assumed: the owner is happy with a "Download as PDF" link on the page. It is one line of public text. The owner confirms the wording.
- Assumed: no date gate in the code. The sibling tools have none. The owner runs it on the uposatha day.
- Not verified: how the 800-line page looks in the mkdocs theme. The owner checks it with `just mkdocs`.
- The page names no money, no promise and no sign-up. Public page copy rules in `CLAUDE.md` apply: add no sentence the owner did not state.

## Constraints
- Keep the "KEEP IN SYNC WITH gui2/pass1_auto_controller.py" note in the tool's docstring.
- Move the file, do not copy it. Leave no stale copy in `scripts/find/`.
- Pre-commit gate on every touched file: `ruff check`, `ruff format`, `pyright` (tests need `--project /dev/null`), related tests.
- No git commands. The owner commits.

## How we'll know it's done
- `just docs-update` writes `docs/missing_words.md` and `docs/missing_words.pdf`, with today's date on top of both.
- `uv run mkdocs build` passes, the menu shows `Missing Words` after Contributing, and the built site holds the page and the PDF, with a working link.
- New tests pass, and fail when the abbreviation rule or the "needs a headword" rule is reverted.
- The owner opens the page with `just mkdocs` and approves how it looks.

## What's not included
- No change to the GitHub workflows.
- No example sentences, deconstructor splits or "claimed by" column.
- No change to Pass1 Auto, and no change to the Unknown button thread (`20261111_pass1_unknown_button`).

## Review changes (2026-11-11)
- Equal counts in the top-5 lists are now in Pāḷi order. A set made the order differ from run to run, so each monthly commit would have shown noise. This replaces the earlier "not included: tie-order fix".
- The last row of each table is labelled `All books added`, not `Total` (owner's choice): it sums the books, so a word in two books counts twice.
- Superseded: the first version subtracted the saved Pass1 Auto drafts in `gui2/data`. The owner removed that: the numbers must reflect the database, and they then do not move when Pass1 Auto runs. "Distinct words" counts a hyphenated compound and its parts; the page does not say so.

## SuttaCentral added (owner, 2026-11-11)
The first version counted CST text only. Pass1 Auto also adds the SuttaCentral Pāḷi words for a book, so the page missed them. Measured (SuttaCentral-only words that DPD lacks): Apadāna +699, Niddesa +693, Jātaka +285, Dhammapada +228, Buddhavaṃsa +44, Cariyāpiṭaka +38, Vimānavatthu +33, Petavatthu +13, Parivāra +62; Dīgha, Majjhima and Aṅguttara +0 or +1, Saṃyutta about +10. Commentaries and Abhidhamma have no SuttaCentral text.
- Decision (owner): the rows follow the SuttaCentral books, with the CST words of the matching CST books combined in. A row's words are the union of the CST and the SuttaCentral words.
- Rows: Vinaya = Vibhaṅga (Bhikkhu and Bhikkhunī: CST vin1, vin2; SC `vin1&2`, `vin-bi`), Khandhaka (vin3, vin4; `vin3&4`), Parivāra (vin5). Four Nikāyas = Dīgha, Majjhima, Saṃyutta, Aṅguttara (4 rows). Khuddaka = the Pass1 Auto books (khp, dhp, ud, iti, snp, vv, pv, th, thi, Apadāna = kn10+kn11, bv, cp, ja, Niddesa = kn15+kn16), then the CST-only Paṭisambhidāmagga, Milindapañha, Nettippakaraṇa, Peṭakopadesa. Abhidhamma and all commentaries stay one row per CST book.
- "Most frequent missing words" counts occurrences in the CST text; a word that only SuttaCentral has is counted in the SuttaCentral text. The two texts are not added together, because they hold the same suttas.
- Saved Pass1 Auto words are NOT subtracted (owner, 2026-11-11): the counts reflect what is in the database. A word Pass1 Auto has saved but the database lacks still counts as missing.
- If a SuttaCentral folder has no files (the `resources/sc-data` submodule not checked out), the tool stops with an error. It must not quietly count CST text only.
- The "Distinct words" definition on the page says "CST and SuttaCentral text".
