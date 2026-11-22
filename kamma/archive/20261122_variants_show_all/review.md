## Thread
- **ID:** 20261122_variants_show_all
- **Objective:** Fold long variant lists behind a "show all" button. The website and `/gd` fold always, `/search_json` folds on request, and the browser extension and the GoldenDict/MDict variants dictionary fold too (issue #99, PR #299).

## Files Changed
- `exporter/webapp/data_classes.py`, `toolkit.py`, `main.py`, `static/app.js` — the `fold` flag. `/search_html` and `/gd` always fold; `/search_json` folds on `fold=1`; the website sends `fold=1`.
- `exporter/webapp/templates/variant.html`, `static/dpd.js`, `static/dpd.css`, `identity/css/dpd.css` — the PR's fold markup, click handler and button style.
- `identity/css/dpd-css-and-fonts.css` — regenerated with `just css`.
- `tools/css_manager.py` — the review fix was later reverted, because the link look needs only the variables the header already kept. The file is the same as on `main`.
- `exporter/variants/variants_exporter.py`, `variants_header.html`, `exporter/goldendict/javascript/variants.js` (new), `tools/paths.py` — the GoldenDict/MDict fold, the script, and its guarded loader.
- `exporter/wxt_extension/utils/variants.ts` (new), `utils/search.ts`, `components/dictionary-panel.ts`, `assets/styles/dpd.css`, `assets/styles/chrome-extension.css` — the extension asks for the fold and handles the button.
- Tests: `tests/exporter/webapp/test_variant_webapp.py`, `tests/exporter/variants/test_variants_exporter.py`, `exporter/wxt_extension/tests/utils/variants.test.ts` (new), `tests/utils/search.test.ts`, and `tests/fixtures/variants_folded.html` (new, real output).
- `docs/technical/api_endpoints.md` — documents `fold`, and that `/search_html` and `/gd` always fold.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `tools/css_manager.py:114` | The variants header dropped `--dark`, `--light` and `--shadow-*`, which the button uses. | Without a main DPD entry on the page, the button lost its text colour and its shadows. | **Fixed, then superseded.** After review the owner chose the link look (Phase 6). The button now uses `.dpd-link`, which needs only `--primary-text` and `--primary-alt`, so the extra variables were reverted. The test now checks the variables of the `.dpd-link` and button rules. |
| 2 | minor | `exporter/webapp/data_classes.py:87`; tests | No test sat on exactly 20 rows. | Changing `>=` to `>` would have passed every test, and 23 words would silently stop folding. | Added one 20-row test for the webapp and one for the exporter. **Fixed.** |
| 3 | minor | the four untracked files | `variants.js` and three new extension files are untracked. Both exporters skip a missing script without an error, and CI runs no pytest. | Leaving one out of the commit would ship 376 dead buttons. | Name all four in the explicit commit list. **Open: a commit-time action.** |
| 4 | nit | `test_header_loads_the_shipped_variants_script` | The test does not check `js_paths=[pth.variants_js_path]`. | Dropping that line would keep the tests green. | **Deferred.** There is no test seam without refactoring `main()`. Both builds were checked instead: stardict `res/variants.js` and the `.mdd` entry `\variants.js`. |
| 5 | nit | `docs/technical/api_endpoints.md` | It did not say that `/search_html` and `/gd` always fold. | `/gd` is public. | Added one line to each. **Fixed.** |

CodeRabbit (`--base-commit e75780fd --include-untracked`, 26 files, fresh): 0 findings.

## Fixes Applied
- Findings 1, 2 and 5. Each new test was reverted against its fix and failed: `>` instead of `>=` → 2 failed; the old variable list → 1 failed.
- The variants dictionary was rebuilt. The installed GoldenDict copy has all 6 button variables, 376 buttons and the script.

## Change After Review (Phase 6, owner's choice)
- The button now looks like the DPD links: `class="variants-more dpd-link"` plus a reset (no background, border or padding). The blue DPD-button rules no longer name it. Live checks on the website, `/gd`, the extension popout and the two-entry GoldenDict page all matched the docs link's colour and weight, and all toggled. The GoldenDict copy was rebuilt.
- In the extension, footer links are lighter and weight 500 (the extension's own `.dpd-footer a` rule). The button keeps the standard `.dpd-link` look.
- Re-review: CodeRabbit run fresh on the whole change → 0 findings. Not re-run by the subagent: the delta is CSS plus one class.

## Test Evidence
- `uv run pytest tests/exporter/webapp tests/exporter/variants tests/tools -q` (scope: all webapp, variants exporter and tools tests; the routes ran on the real dpd.db) → 1112 passed, 1 failed. The failure is pre-existing: the abbreviations golden master expects "three gender", and the data has "three genders". No file of this thread touches it.
- `npm test` in the extension (all 5 test files) → 33 passed. `npm run compile` → clean.
- `just typecheck` (pyrefly, whole repo) → 0 errors. `ruff` and `pyright` → clean on all 8 changed Python files and both test files.
- Whole-data comparison of the old and new GoldenDict HTML, over all 72,413 entries → 0 differences beyond the separator `<tr>` and the fold markup. 376 entries fold, each with exactly `row_count - 10` hidden rows. The reviewer reproduced this, and also found the webapp template and the exporter hide the same rows in all 376.
- Live checks: website `/?q=ca` and `/gd?search=ca` (click, Enter, Space); built extension popout `ca` and `paññā`; GoldenDict page with two entries and with the script loaded twice (the guard is proved by a run without it). The owner confirmed GoldenDict on the first build.

## Not Verified
- The in-page extension panel on a real host site. Only the popout was run. A site's own `button` CSS (width, text-transform) could leak into the panel.
- DictTango and other MDict readers. Only the `.mdx`/`.mdd` contents were read.
- Dark themes, and the owner's look at the rebuilt GoldenDict copy in the link look.

## Verdict
PASSED
- Review date: 2026-11-22
- Reviewer: an independent general-purpose subagent (fresh context), model: Opus 5.5, plus CodeRabbit CLI. The implementing session applied the fixes and wrote this file.
- Independence: full for the subagent review. Reduced for the fixes and this summary, which come from the same session as the implementation.
