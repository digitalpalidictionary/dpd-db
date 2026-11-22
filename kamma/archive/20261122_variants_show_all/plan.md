# Plan: fold long variant lists behind a "show all" button

**GitHub:** issue #99 ("Show more" item only) and pull request #299 (fork `kirill-morozov-n/dpd-db`, branch `webapp-variants-show-more`).

Read `spec.md` in this folder first. All facts it marks as verified were checked on 2026-11-22.

## Architecture Decisions

- **The fold is opt-in for each caller.** `VariantData(result, fold=False)` and `make_dpd_html(..., fold_variants=False)` are off by default. The routes whose page runs `dpd.js` (`/search_html`, `/gd`) always fold. `/search_json` folds only on `fold=1`. Reason: the extension and outside users of the JSON keep the full HTML until they handle the button. This is the same rule `lazy` follows.
- **`fold` is a new query parameter, and `lazy` stays as it is.** `lazy` means "empty the hidden panels", which the extension does not handle. The extension needs the fold without the panels.
- **The variants exporter reuses `VariantData`** for the threshold and the row count. One rule lives in one place. `gui2/preview.py` already imports from `exporter/webapp/data_classes.py`.
- **The GoldenDict script is a separate file**, `exporter/goldendict/javascript/variants.js`. It ships through `js_paths` and loads once through a guarded loader in the header, copying the grammar dictionary's `sorter.js` pattern. It is not added to `main.js`. Both dictionaries can show on one GoldenDict page, and two listeners would toggle twice, which leaves the table unchanged.
- **The extension's toggle code goes in a small `utils/variants.ts`,** so that vitest can test it. The panel calls it. The extension's existing tests cover only `utils/`.
- **No shared JS file across the website, GoldenDict and the extension.** Each runs in a different page and build. The handler is about 15 lines, copied three times, in the same way as the existing `.dpd-button` handler.

## Model Strategy

| Phase | Tier | Suggested model | Reason |
|---|---|---|---|
| 1 — Check out the PR and take a baseline | Fast | Sonnet | Commands and recording results |
| 2 — Website folds only on request | Fast | Sonnet | Mechanical changes, fully specified |
| 3 — Browser extension | Fast | Sonnet | Mechanical changes plus a live check |
| 4 — GoldenDict/MDict variants dictionary | Pro | Opus | The script runs in a page shared with other dictionaries. The load-once guard and the markup change need care. |
| 5 — Final checks | Fast | Sonnet | Run the checks, compare them with the baseline |
| 6 — Link look | Fast | Sonnet | CSS and markup change, plus live checks |

## Phase 1 — Check out the PR and take a baseline — *Fast*

- [x] 1.1 Check out PR 299 in the shared tree.
  - `git status --porcelain` must list nothing except this thread's untracked folder `kamma/threads/20261122_variants_show_all/`. If it lists anything else, stop and report it.
  - Run `gh pr checkout 299`. Record `git rev-parse HEAD` here (planning saw `430b5938`). Also record `git config --get-regexp 'branch\.webapp-variants-show-more\..*'`.
  → verify: `git branch --show-current` prints `webapp-variants-show-more`, and the HEAD and branch config are recorded below.
- [x] 1.2 Take a baseline of the webapp suite on the PR branch.
  - Run `uv run pytest tests/exporter/webapp -q`. Paste the summary line and the names of the failing tests below.
  → verify: every failing test is outside the variants code. These failures are the baseline that later phases compare against.

## Phase 2 — Website folds only on request — *Fast*

- [x] 2.1 Give `VariantData` a fold flag (`exporter/webapp/data_classes.py`).
  - `__init__(self, result: Lookup, fold: bool = False)`, and `self.folded = fold and self.row_count >= 2 * self.rows_shown`.
  - In `tests/exporter/webapp/test_variant_webapp.py`, give `_make_variant_data` a `fold: bool = True` parameter, so that the PR's tests keep their meaning. Add `test_long_list_without_fold_shows_every_row`: a 34-row list built with `fold=False` is not folded, has no button and has no `hidden`.
  → verify: `uv run pytest tests/exporter/webapp/test_variant_webapp.py -q` passes. Then change `fold and` to `True and`: the new test must fail. Report the count, then restore the line.
- [x] 2.2 Pass the flag through the search builder and the routes.
  - `exporter/webapp/toolkit.py::make_dpd_html` gets the keyword `fold_variants: bool = False` and calls `VariantData(lookup_result, fold=fold_variants)`.
  - `exporter/webapp/main.py`: `/search_html` and `/gd` pass `fold_variants=True`. `/search_json` gets the parameter `fold: bool = False` and passes `fold_variants=fold`. Check that no cache keyed on `q` alone sits in front of `make_dpd_html`.
  - `exporter/webapp/static/app.js` (the one `/search_json` call, about line 262): add `&fold=1`.
  - `docs/technical/api_endpoints.md`: add `fold` under the `/search_json` parameters, after `lazy`.
  - In `tests/exporter/webapp/test_variant_webapp.py`, add route tests with `TestClient(app)`. Copy the setup from `tests/exporter/webapp/test_webapp_status.py`. Check these four answers:
    - `/search_json?q=ca` has no `variants-more`.
    - `/search_json?q=ca&fold=1` has the button and at least one `variant-more hidden`.
    - `/search_html?q=ca` has the button.
    - `/gd?search=ca` has the button.
  → verify: `uv run pytest tests/exporter/webapp/test_variant_webapp.py -q` passes.
- [x] 2.3 Rebuild the generated CSS.
  - Run `just css`.
  → verify: `git diff identity/css/dpd-css-and-fonts.css` shows only the `button.variants-more` additions from the PR's `identity/css/dpd.css`. `git status --porcelain` shows no other changed CSS file. If one appears, read its diff and explain it below.
- [x] 2.4 Live check on the local website.
  - Start `just webapp` in the background on port 8080. Wait with a loop that has a timeout until `http://127.0.0.1:8080/` answers 200. Record the server PID.
  - With `playwright-cli` in its own headless browser (no login is needed), open `http://127.0.0.1:8080/` and search `ca`. Count the visible data rows of `table.variants` (expect 10) and read the button text (expect `show all 1679 variants`). Click: all rows show, and the text reads `show fewer`. Focus the button, press Enter, then Space, and confirm that each key toggles. Open `/gd?search=ca` and repeat the click check.
  - Search a word with fewer than 20 variant rows (pick one from `dpd.db`): it shows no button.
  - Leave the server running for Phase 3.
  → verify: paste the row counts and the button texts below.
- [x] 2.5 Phase 2 check.
  - Run `uv run ruff check --fix`, `uv run ruff format` and `uv run pyright` on `exporter/webapp/data_classes.py`, `exporter/webapp/toolkit.py` and `exporter/webapp/main.py`. Fix any error, old or new.
  - Run `uv run pyright --project /dev/null tests/exporter/webapp/test_variant_webapp.py`.
  - Run `uv run pytest tests/exporter/webapp -q`.
  → verify: the linters and type checks are clean, and the failures match the Phase 1 baseline exactly.

## Phase 3 — Browser extension — *Fast*

- [x] 3.1 Add the toggle code and its tests.
  - Create `exporter/wxt_extension/utils/variants.ts`, exporting `toggleVariants(button: Element): void`. Use the same logic as the PR's block in `dpd.js`:
    - Find the button's `.dpd` ancestor and its `table.variants`.
    - Toggle `hidden` on the `.variant-more` rows.
    - Flip `aria-expanded`.
    - Swap the text from `data-more` / `data-less`.
    - Call `scrollIntoView({ block: "nearest" })` when folding.
  - In `components/dictionary-panel.ts::_setupEvents`, at the top of the click listener, add: `const more = target.closest(".variants-more"); if (more) { toggleVariants(more); return; }`.
  - In `utils/search.ts`, change the endpoint to `'/search_json?q=' + encodeURIComponent(q) + '&fold=1'`.
  - Create `tests/utils/variants.test.ts` (happy-dom). Use real markup: the variants block from `http://127.0.0.1:8080/search_json?q=<word>&fold=1`, for a word with 20 to 30 rows taken from `dpd.db`. The tests check three things:
    - A click shows every row.
    - A second click folds the rows again.
    - `aria-expanded` and the text change each time.
  - In `tests/utils/search.test.ts`, assert that the endpoint sent includes `fold=1`.
  → verify: `npm --prefix <repo root>/exporter/wxt_extension test` passes. Then make the body of `toggleVariants` a no-op: the new tests must fail. Report the count, then restore the body.
- [x] 3.2 Style the button in the panel.
  - In `assets/styles/dpd.css` and `assets/styles/chrome-extension.css`, add `#dict-panel-25445 button.variants-more` to every selector list that styles `#dict-panel-25445 a.dpd-button`: the base rule, `:hover`, and the theme text-colour lists. Add `font-family: inherit` for the button.
  - Read each edit as a parsed selector, across comments and newlines, never line by line (see the dangling-prefix note in `spec.md`).
  → verify: `rg -n "variants-more" exporter/wxt_extension/assets/styles` lists each new selector with its `#dict-panel-25445` scope. The screenshot from 3.3 shows a styled button.
- [x] 3.3 Build the extension and check it live.
  - Run `npm --prefix <repo root>/exporter/wxt_extension run build`. The Chrome output goes to `.output/chrome-mv3`.
  - Keep the local webapp running. Load the build into a throwaway Chromium with Playwright: `launchPersistentContext` on a profile in the scratchpad, with `--disable-extensions-except=<build>` and `--load-extension=<build>`.
  - Open a local test page from the scratchpad that holds the word `ca`. Start a lookup the way users do; read `entrypoints/content.ts` to learn the trigger. Check that the rows go from 10, to all, to 10, and that the button is styled. Take a screenshot.
  - If this cannot be done in about 15 minutes, record why below, and add a 3-step owner check to the final report.
  - Stop the webapp by its PID.
  → verify: the counts and the screenshot path are recorded below.
- [x] 3.4 Phase 3 check.
  → verify: `npm --prefix <repo root>/exporter/wxt_extension test` passes, and `npm --prefix <repo root>/exporter/wxt_extension run compile` is clean.

## Phase 4 — GoldenDict/MDict variants dictionary — *Pro*

- [x] 4.1 Build the entry HTML with the fold.
  - In `exporter/variants/variants_exporter.py`, move the HTML build out of `main()` into `make_entry_html(header: str, d: VariantData) -> str`.
  - `main()` builds `VariantData(lookup, fold=True)` for each `Lookup` row, and keeps the synonym loop as it is.
  - The markup matches the website:
    - Each separator is `<tr><td colspan='100%'><hr class='dpd'></td></tr>`.
    - When `d.folded`, the rows and separators after the first `d.rows_shown` data rows carry `class='variant-more hidden'`.
    - The button follows `</table>` inside `div.dpd` and carries `data-more` and `data-less`.
  - Short lists stay as they were, except for the `<tr>` around the separators.
  - Add tests to `tests/exporter/variants/test_variants_exporter.py` and leave the synonym tests as they are:
    - A short list has no button and no `hidden`.
    - A long list has 10 visible data rows and hides the rest.
    - The separators after the fold are hidden.
    - The button text is right.
  → verify: `uv run pytest tests/exporter/variants -q` passes.
- [x] 4.2 Add the script and its loader.
  - Create `exporter/goldendict/javascript/variants.js` with one delegated `click` listener for `.variants-more`. Its body is the same as the PR's block in `dpd.js`.
  - (Added during work.) The script also sets a window flag and adds its listener only once. The header guard only holds when a reader runs each entry's scripts in page order. A reader that inserts all entries first would add one script per entry, and an even number of listeners leaves every click with no effect.
  - In `tools/paths.py`, add `self.variants_js_path` next to `sorter_js_path`.
  - In `exporter/variants/variants_header.html`, add `<link href="variants.js" class="load_variants_js" rel="preload" as="script">`. Add the guarded loader copied from `exporter/grammar_dict/grammar_dict_header.jinja`, with the guard `variants_js_already_loaded` and the class `load_variants_js`.
  - Set `DictVariables(js_paths=[pth.variants_js_path])`.
  → verify: a test asserts that the header holds the loader and the guard, and that `ProjectPaths().variants_js_path.exists()`.
- [x] 4.3 Check the page with real data.
  - In a scratchpad script, build the `ca` entry with `make_entry_html` from `dpd.db`. Write it twice into one page, in a scratch folder that also holds copies of `dpd-css-and-fonts.css` and `variants.js`.
  - Serve only that folder on 127.0.0.1 (`uv run python -m http.server --bind 127.0.0.1 --directory <scratch folder>`) and open the page with `playwright-cli`.
  - Expect three things:
    - The first table shows 10 rows.
    - One click shows all 1,679 rows. This proves the guard: with two listeners, the click would toggle twice and show nothing new.
    - A second click folds the table.
  - Stop the server by its PID.
  → verify: paste the counts below.
- [x] 4.4 Export the dictionary.
  - Read `[exporter] make_variants` with `config_read`. Never edit `config.ini`. If it is `no`, record that and skip this task.
  - Run `uv run python exporter/variants/variants_exporter.py`.
  - (Changed during work.) `make_variants` is `no` in `config.ini`, which must not be edited. A scratchpad script (`export_variants_to_scratch.py`) runs the exporter's own `main()` with only two things patched: that gate, and `share_dir`, which points into the scratchpad. Note: `export_to_goldendict_with_pyglossary` always runs `copy_dir`. That deletes `<GoldenDict dir>/dpd-variants` and copies the new build in its place. The owner's GoldenDict therefore now has the new build.
  → verify: list the new GoldenDict and MDict files that the exporter reports, and confirm that `variants.js` is inside each (the stardict resources and the `.mdd`). Record which file the owner loads in GoldenDict.
- [x] 4.5 Phase 4 check.
  - Run `ruff check --fix`, `ruff format` and `pyright` on `exporter/variants/variants_exporter.py` and `tools/paths.py`.
  - Run `pyright --project /dev/null tests/exporter/variants/test_variants_exporter.py`.
  → verify: everything is clean, and `uv run pytest tests/exporter/variants -q` passes.

## Phase 5 — Final checks — *Fast*

- [x] 5.1 Run the whole set.
  - `uv run pytest tests/exporter/webapp tests/exporter/variants -q`
  - `npm --prefix <repo root>/exporter/wxt_extension test`
  - `just typecheck`
  - `ruff` and `pyright` on every changed Python file.
  → verify: the failures match the Phase 1 baseline, and everything else is clean. `git status --porcelain` lists only this thread's files.
- [x] 5.2 Report to the owner.
  → verify: the report lists:
  - what changed;
  - the live numbers;
  - the GoldenDict file to load;
  - any owner check left over from 3.3;
  - the next step, `/kamma:3-review`.

## Phase 6 — Link look (owner's choice after review) — *Fast*

The owner tested GoldenDict and chose to show the button as a DPD link instead of a blue DPD button.

- [x] 6.1 Switch the button to the link look.
  - Add `dpd-link` to the button's classes in `exporter/webapp/templates/variant.html` and in `make_entry_html` (`exporter/variants/variants_exporter.py`).
  - In `identity/css/dpd.css`, remove `button.variants-more` from the `a.dpd-button` rule and from its `:hover` rule. Replace `button.variants-more { font-family: inherit; }` with a reset that sets `background: none`, `border: none`, `padding: 0`, `cursor: pointer`, `font-family: inherit` and `font-size: inherit`. Do not set colour or weight there: `.dpd-link` provides them. Then run `just css`.
  - Extension `assets/styles/dpd.css`: remove the button from the `a.dpd-button` base and `:hover` rules, and scope the same reset under `#dict-panel-25445`. In `assets/styles/chrome-extension.css`, remove the two button selectors from the theme text-colour rule.
  - Revert the review fix in `tools/css_manager.py`, because the link needs only `--primary-text` and `--primary-alt`. Change `test_header_defines_every_variable_the_button_uses` so that it reads the variables of the `.dpd-link` rules and the `button.variants-more` rules.
  - Update the exporter test's exact button string. Regenerate the extension fixture from the real `/search_json?q=aṭṭhikatvā&fold=1`.
  → verify: `uv run pytest tests/exporter/webapp tests/exporter/variants -q` and `npm test` pass. `rg "variants-more" identity/css exporter/wxt_extension/assets` shows no button selector left in a `dpd-button` rule.
- [x] 6.2 Live checks and a rebuild.
  - Website `/?q=ca` and `/gd?search=ca`: compare the computed styles of the button with those of the "read the docs" link (colour, weight). The background must be transparent, and the toggle must still work.
  - Extension popout `ca`: the same comparison and the toggle.
  - Rebuild the variants dictionary through the scratchpad export, and check the GoldenDict page as in 4.3.
  → verify: paste the computed styles and the row counts below.
- [x] 6.3 Re-review the change.
  - Run CodeRabbit fresh on the whole change. Rerun `just typecheck`, ruff and pyright on the touched Python files. Update `review.md`.
  → verify: `review.md` lists the look change and the results.

## After finalize — only on the owner's go-ahead

- Commit this thread's files on `webapp-variants-show-more`, staged by explicit path (`git add <files> && git commit -m "#99 webapp: …" -- <files>`).
- Run `git pull --ff-only`. If it does not fast-forward, stop.
- Read the fork remote from `git config --get branch.webapp-variants-show-more.pushremote`. Run the dry-run push. Go on only if it shows an update to an existing branch.
- Push, then run `gh pr merge 299 --merge --subject "#99 webapp: fold long variant lists behind a show all button (#299)"`.
- Run `git checkout main && git pull --ff-only`.
- Confirm that `gh pr view 299 --json state` says `MERGED` and that `git log origin/main..main` is empty.

## Records

(Fill in while working.)

- 1.1: branch `webapp-variants-show-more`, HEAD `430b593899283afb2549ee8d819fe90625f7d793`. Branch config: `remote` and `pushremote` = `https://github.com/kirill-morozov-n/dpd-db.git`, `merge` = `refs/heads/webapp-variants-show-more`.
- 1.2 baseline: `uv run pytest tests/exporter/webapp -q` → 211 passed in 33.59s. No failures. The 4 failures the PR author reported do not happen here.
- 2.1: `test_variant_webapp.py` 5 passed. With `fold and` changed to `True and`: 1 failed (`test_long_list_without_fold_shows_every_row`), 4 passed. Restored.
- 2.2: no cache in front of `make_dpd_html`. `test_variant_webapp.py` 9 passed (4 route tests on real `ca`). Fold forced off: 3 route tests failed. Fold forced on: the no-fold test failed. Restored.
- 2.3: `just css` changed only `identity/css/dpd-css-and-fonts.css`: the three `button.variants-more` hunks from `identity/css/dpd.css`. The webapp copy and the docs CSS were already current.
- 2.4 (headless playwright-cli, local `just webapp` on 8080):
  - Home `/?q=ca` (app.js, `lazy=1&fold=1`): 1679 rows, 10 visible, button `show all 1679 variants`, `aria-expanded=false`. Click → 1679 visible, `show fewer`, `true`, focus on the button. Enter → 10 visible. Space → 1679 visible.
  - `/gd?search=ca`: 10 visible → click 1679 → click 10. The button screenshot shows the blue DPD button style.
  - Home `/?q=paññā` (15 rows): 15 visible, no button.
- 2.5: ruff check and pyright clean on the 3 webapp files and the test (`--project /dev/null`). ruff format rewrote 1 file (small). `pytest tests/exporter/webapp` → 216 passed (baseline 211 + 5 new).
- 3.1: fixture `exporter/wxt_extension/tests/fixtures/variants_folded.html` = the real variants block of `/search_json?q=aṭṭhikatvā&fold=1` (20 data rows, 4 separators, 12 hidden rows). `npm test` → 33 passed. Toggle made a no-op: 2 toggle tests failed. `fold=1` dropped from the search: the endpoint test failed. Restored → 33 passed. The fixture is read through `__dirname`, because happy-dom gives `import.meta.url` a non-file scheme.
- 3.2: `dpd.css`: button added to the base rule and the `:hover` rule, plus `font-family: inherit`. `chrome-extension.css`: button and `:hover` added to the theme text-colour rule. Each selector carries `#dict-panel-25445` on its own line. CRLF/LF preserved (scripted rewrite with `newline=""`).
- 3.3: `npm run build` → `.output/chrome-mv3` (gitignored). A scratchpad Playwright script loaded it into a throwaway profile. The playwright-core 1.66 alpha wanted a newer browser, so the script used the installed Chrome for Testing 145 through `executablePath`. It opened `chrome-extension://<id>/popout.html?q=<word>`: the popout uses the same `DictionaryPanel`, `searchWord` and CSS as the in-page panel. The background used the local server on 8080.
  - `ca`: 1679 rows, 10 visible, `show all 1679 variants` → click → 1679 visible, `show fewer`, `aria-expanded=true` → click → 10 visible. Button background `rgb(0, 178, 255)` (the DPD button blue). The screenshot shows it styled like the DPD buttons above it.
  - `paññā`: 15 rows, 15 visible, no button.
  - The webapp was stopped by PID (exit 143 = SIGTERM).
- 3.4: `npm test` → 33 passed (5 files). `npm run compile` (tsc --noEmit) → exit 0.
- 4.1: `make_entry_html(header, d)` built. A whole-data comparison (scratchpad `compare_variants_html.py`, which copies the old loop verbatim) covered 72,413 entries: 72,037 short entries are identical apart from the separators now wrapped in `<tr>`, 376 folded entries are identical once the fold markup is removed, and each has `row_count - 10` hidden data rows and one button. 0 problems. `pytest tests/exporter/variants` → 15 passed (11 old + 4 new). `if d.folded` → `if False`: 3 fold tests failed. Restored.
- 4.2: `variants.js`, `ProjectPaths.variants_js_path`, header loader (`load_variants_js`, `variants_js_already_loaded`), `js_paths=[pth.variants_js_path]`. Header test added → 16 passed.
- 4.3 (scratch folder served alone on 127.0.0.1:8765, playwright-cli headless):
  - Page A, the real `ca` entry twice with its real header after `update_style`: 1 `variants.js` script loaded, both tables at 10 of 1679 rows. A click on the first button → first table 1679 and `show fewer`, second table still 10. A second click → 10.
  - Page B, the entry body with `variants.js` loaded twice on purpose: a click → 1679, a second click → 10. The script's own guard works.
  - Page C, the same as page B but with the guard removed: a click leaves 10 rows. This proves the guard is needed.
  - The server was stopped by PID (exit 143 = SIGTERM).
- 4.4: `make_variants = no`, so the export ran through the scratchpad script (7 s). Output: stardict `dpd-variants/` (with `res/variants.js` and `res/dpd-css-and-fonts.css`), `dpd-variants-mdict.mdx` and `.mdd`.
  - Stardict `.dict.dz`: 376 buttons, `show all 1679 variants` appears once, and all 72,413 entries carry the loader.
  - MDict, read with pyglossary's `readmdict`: the `.mdd` holds `\variants.js` (1200 bytes, with the guard) and `\dpd-css-and-fonts.css`. The `.mdx` has 166,302 keys (synonyms included) and 376 entries with a button. The one non-link `ca` entry has the button and the loader.
  - `copy_dir` replaced `<GoldenDict dir>/dpd-variants` with this build at 06:37. The old folder was a generated build from the same database, and it was not backed up. The owner was told.
- 4.5: ruff check and pyright clean on `variants_exporter.py`, `tools/paths.py` and the test (`--project /dev/null`). ruff format rewrote 1 file. `pytest tests/exporter/variants` → 16 passed.
- 5.1: `pytest tests/exporter/webapp tests/exporter/variants` → 232 passed. `npm test` → 33 passed. `just typecheck` (pyrefly) → 0 errors. `ruff check` and `ruff format --check` clean on all 7 changed Python files. `git status` lists only this thread's files, plus the gitignored `exporter/wxt_extension/.output/`. Branch `webapp-variants-show-more`.
- 5.2: report given. Owner check left: GoldenDict `ca` in DPD Variants (the build is already in the GoldenDict folder).
- Review fixes (2026-11-22). Reviews: an independent subagent, and CodeRabbit (0 findings).
  - `tools/css_manager.py`: the variants header keeps `--dark`, `--light` and `--shadow-*`, and drops `-shade`. The test `test_header_defines_every_variable_the_button_uses` fails with the old list.
  - Two tests at exactly 20 rows (webapp and exporter). Both fail if `>=` becomes `>`.
  - `docs/technical/api_endpoints.md`: `/search_html` and `/gd` always fold.
  - The variants dictionary was rebuilt through the scratchpad export. The installed GoldenDict copy has all 6 button variables, 376 buttons and `res/variants.js`.
  - `pytest tests/exporter/webapp tests/exporter/variants tests/tools` → 1112 passed, 1 failed. The failure is PRE-EXISTING — NOT CAUSED BY THIS THREAD: `tests/tools/test_docs_update_abbreviations.py::test_make_abbreviations_md_golden_master`; its frozen fixture has "three gender", and the live data has "three genders". `npm test` → 33 passed. `just typecheck` → 0 errors.
- 6.1: `dpd-link` added to the button in the template and in `make_entry_html`. The button selectors are removed from the `a.dpd-button` rules (the identity CSS, the extension's `dpd.css`, and `chrome-extension.css`, which is now back to `main`), and a reset rule is in their place. `tools/css_manager.py` is reverted to `main`. `just css` changed `dpd-css-and-fonts.css` (reset only) and the webapp `dpd.css`. The extension fixture was regenerated from `/search_json?q=aṭṭhikatvā&fold=1`. `pytest tests/exporter/webapp tests/exporter/variants` → 235 passed. `npm test` → 33 passed, and `npm run compile` is clean.
- 6.2: the computed style is shown as colour | weight | background | border.
  - Website `/?q=ca` and `/gd?search=ca`: the button is `rgb(26, 139, 219) | 700 | transparent | none`, the same as the variants block's "read the docs" link. The font size is 16px against 12.8px, because the link sits in the small-print footer and the button in a normal `<p>`, at table text size. The toggle goes 10 → 1679 → 10 on both pages.
  - Extension popout `ca`: the button is `rgb(26, 139, 219) | 700 | none`, with a transparent background, and it toggles. The extension's own `#dict-panel-25445 .dpd-footer a` rule (in `chrome-extension.css`) makes footer links lighter and weight 500. The button is not in the footer, so it keeps the standard `.dpd-link` look.
  - The variants dictionary was rebuilt into the GoldenDict folder: 376 `variants-more dpd-link` buttons, 0 old ones, and the reset is in `res/dpd-css-and-fonts.css`. The two-entry GoldenDict page: the button and the docs link both read `rgb(26, 139, 219) | 700 | transparent | none` with only the original variants variables. 1 script loaded, toggle 10 → 1679 → 10, and the second table was unaffected.
- 6.3: CodeRabbit run fresh (`--fresh --base-commit e75780fd --include-untracked`): 26 files, 0 findings, not reused. `just typecheck` → 0 errors. ruff and pyright are clean on the 5 changed Python files and the 2 test files. `pytest tests/exporter/webapp tests/exporter/variants tests/tools` → 1112 passed, 1 pre-existing failure (abbreviations golden master). `review.md` is updated.
