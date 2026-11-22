# Fold long variant lists behind a "show all" button

**GitHub:** issue #99 (only its item "JavaScript 'Show more' button for long lists") and pull request #299 from an outside contributor. The PR comes from the fork `kirill-morozov-n/dpd-db`, branch `webapp-variants-show-more`, and the maintainer can push to it.

## Overview

A variants table lists every variant reading of a word. Some lists are very long: `ca` has 1,679 rows, `vā` 649, `te` 450. PR #299 folds long lists on the website. A table with 20 rows or more shows its first 10 rows and a **show all N variants** button. The button shows the rest and then reads **show fewer**.

The PR folds in every search answer. The browser extension shows the same answers, fetched live from dpdict.net, but has no code for the button. After a website deploy, extension users would see 10 rows and a dead button on 376 words. This thread keeps the PR's fold and its rule. It makes the fold opt-in for callers that handle the button, adds the button to the extension, and adds the same fold to the GoldenDict/MDict variants dictionary.

The phone app (dpd-flutter-app) already folds variant tables with its own rule. See "What's not included".

## Current behaviour (verified 2026-11-22)

- **Website.** `exporter/webapp/toolkit.py::make_dpd_html` renders `templates/variant.html` with `VariantData(lookup_result)` for each lookup row that has a `variant`. Three routes call `make_dpd_html`:
  - `/search_html` returns `home.html`, which loads `static/dpd.js`.
  - `/search_json` returns JSON. The website's `static/app.js` calls it with `lazy=1`, in one place only.
  - `/gd` returns `home_simple.html`, which inlines `dpd.js` in a `<script>`. GoldenDict and DictTango use it as a website dictionary.
- **The `lazy` precedent.** `/search_json?lazy=1` empties hidden panels and sends their content apart. `docs/technical/api_endpoints.md` says it is "used by the webapp. … Other callers can leave it out and get the full HTML." `lazy_panels.split_hidden_panels` acts only on a `<div>` with an id and the `hidden` class. Hidden `<tr>` rows are not touched.
- **Browser extension** (`exporter/wxt_extension/`).
  - `utils/search.ts::searchWord` calls `/search_json?q=…` without `lazy`. It puts `summary_html` + `dpd_html` into `DictionaryPanel` (`components/dictionary-panel.ts`).
  - The in-page panel (`entrypoints/content.ts`) and the popout (`entrypoints/popout/main.ts`) both use that function and that class.
  - `DictionaryPanel._setupEvents` handles clicks only on `.dpd-button[data-target]` and `.dpd-button.play`.
  - The extension's CSS copies (`assets/styles/dpd.css`, `assets/styles/chrome-extension.css`) are kept by hand. They hide `.hidden`. Every rule is scoped under `#dict-panel-25445`, sometimes as a dangling prefix on the line before a comment.
  - The extension uses a local server at `127.0.0.1:8080` when one answers. Otherwise it uses `https://dpdict.net`.
- **GoldenDict/MDict variants dictionary.**
  - `exporter/variants/variants_exporter.py` builds each entry's HTML by joining strings, with no Jinja. It uses the header `exporter/variants/variants_header.html` and the CSS file `identity/css/dpd-css-and-fonts.css`, and it sets `js_paths=None`.
  - Separator rows are a bare `<td colspan='100%'><hr class='dpd'></td>` with no `<tr>`.
  - The same `DictEntry` list goes to GoldenDict (pyglossary), to MDict and, as an option, to slob.
  - `tests/exporter/variants/test_variants_exporter.py` tests only the synonym lists, not the HTML.
- **Sibling pattern: a script in a separate dictionary.**
  - The grammar dictionary ships `exporter/goldendict/javascript/sorter.js` through `js_paths=[pth.sorter_js_path]`.
  - Its header (`exporter/grammar_dict/grammar_dict_header.jinja`) loads that script with `<link … class="load_grammar_js" rel="preload" as="script">` and an inline loader guarded by `grammar_js_already_loaded`. The script therefore runs once, even when many entries show on one page.
  - The main DPD dictionary uses the same guard pattern (`js_already_loaded`). Its `main.js` reacts only to clicks on `.dpd-button`.
- **CSS.** `identity/css/dpd.css` is the source. `tools/css_manager.py` (`just css`) writes three files:
  - `exporter/webapp/static/dpd.css`, which the webapp also rewrites on every start.
  - `identity/css/dpd-css-and-fonts.css`, which is tracked and which the GoldenDict exporters use.
  - The docs CSS variables.

  On `main`, `dpd-css-and-fonts.css` matches its source. PR #299 changes `identity/css/dpd.css` and the webapp copy, but not `dpd-css-and-fonts.css`.
- **Data.** 72,413 lookup keys have variants:
  - 376 have 20 rows or more, so they fold under the PR's rule.
  - 353 have more than 20 rows.
  - 1,056 have more than 10 rows.
  - The largest are `ca` 1,679, `ootnote` 828, `vā` 649, `te` 450 and `taṃ` 416.
- **PR checks run during planning.** These ran on PR head `430b5938`, in a scratch worktree:
  - The 4 new tests pass.
  - With the template change undone, the 2 fold tests fail.
  - `ruff check`, `ruff format --check` and `pyright` are clean on the changed Python files.
  - The full webapp suite has not run on the PR yet. It needs `dpd.db`, which the scratch worktree does not have.

## What it should do

1. **Fold rule, the same as the PR.** A variants table with 20 data rows or more (`2 × rows_shown`, `rows_shown = 10`) shows its first 10 rows. The later rows carry `variant-more hidden`, and so do the separator rows after the fold. After the table comes `<button type="button" class="variants-more dpd-link" aria-expanded="false">show all N variants</button>`. It looks like the DPD links (bold, in the primary text colour) and stays a real button for the keyboard (owner's choice after review, 2026-11-22: the blue DPD-button look stood out in the variants tables). A click shows every row and changes the text to **show fewer**. A second click folds the table again and keeps the button in view. A shorter table shows in full, with no button.
2. **Website: fold only when the caller can handle it.**
   - `VariantData` takes a `fold` flag, off by default. `make_dpd_html` takes a matching flag and passes it on.
   - `/search_html` and `/gd` always fold, because their pages load `dpd.js`.
   - `/search_json` folds only when the request has `fold=1`. Without it, the answer has every row and no button, as today.
   - The website's `app.js` sends `fold=1`.
   - `docs/technical/api_endpoints.md` documents `fold` next to `lazy`.
3. **Browser extension.**
   - `searchWord` sends `fold=1`.
   - In the panel, a click on `.variants-more` toggles that table's `.variant-more` rows, `aria-expanded` and the button text, the same way `dpd.js` does.
   - The button looks like the panel's DPD links in every theme, because it carries `dpd-link`. The extension's `dpd.css` adds a scoped reset for `#dict-panel-25445 button.variants-more`, covering background, border, padding and font.
4. **GoldenDict/MDict variants dictionary.**
   - Each entry uses the same fold rule and markup as the website. Rows past the fold and their separators are hidden. Every separator is wrapped in a `<tr>`. The same button follows the table.
   - A small script handles the click. It ships with the dictionary like the grammar dictionary's `sorter.js` and loads once per page, with its own guard.
   - A rerun of `just css` updates `dpd-css-and-fonts.css`, so the button reset reaches the dictionary. `.dpd-link` needs only `--primary-text` and `--primary-alt`, which the variants header already keeps.
5. **One rule in one place.** The variants exporter takes the threshold and the row count from `VariantData` (`exporter/webapp/data_classes.py`). The website and GoldenDict therefore cannot drift apart. `gui2/preview.py` already imports from that module.

## Assumptions & uncertainties

- **Assumed:** GoldenDict, GoldenDict-ng and DictTango run dictionary scripts. The main DPD dictionary's buttons already depend on this. A reader with scripts turned off would show only the first 10 rows of a long list, and its DPD buttons are already dead today.
- **Assumed:** the 1,679-row table for `ca` opens fast in the extension panel. The PR measured less than 0.1 s on the website.
- **Unverified:** whether the built extension loads into a throwaway Playwright Chromium for the live check. If it does not, the owner loads the dev build once.
- **Not run yet:** the full webapp test suite on the PR branch. The PR author reports 206 passed. The author also reports 4 failures that fail on a clean `main` too: `test_tt_search_limits` (3 tests) and `test_metrics_endpoint`. Phase 1 records the real baseline.
- The website deploy and the extension release stay manual, and both belong to the owner. With the opt-in, their order no longer matters. An old extension still gets full lists. A new extension that talks to an old server also gets full lists, because the server ignores an unknown `fold`.

## Constraints

- The work goes on the PR branch as maintainer commits on top, as was done for PR #297. Never rewrite or force-push the author's commit.
- Do not commit, push or merge until the thread is reviewed and finalized and the owner says go. The push uses the `/pr` dry-run gate: `git push --dry-run <fork-remote> HEAD:webapp-variants-show-more` must show an update to an existing branch, never `[new branch]`.
- Shared working tree: confirm `git status --porcelain` is empty before `gh pr checkout 299`. Return to `main` at the end. Never stash, restore or reset.
- Edit CSS only in `identity/css/dpd.css`, then run `just css`. Never edit a generated copy by hand. The extension's CSS copies are the exception, because they are kept by hand. Mind their dangling-prefix scoping.
- Python: use modern type hints. Run `ruff check`, `ruff format` and `pyright` on each changed file (`--project /dev/null` for files under `tests/`). Run `just typecheck` before you finish.
- Extension: run npm as `npm --prefix <repo root>/exporter/wxt_extension …`, never after a `cd`.
- No extension version bump. The owner runs `just wxt-bump` when releasing.

## How we'll know it's done

- `dpd_html` from `/search_json?q=ca` has no `variants-more` and no `variant-more`. `/search_json?q=ca&fold=1`, `/search_html?q=ca` and `/gd?search=ca` each have the button and 1,669 hidden rows. A word with a short list never folds.
- On the local website, a search for `ca` shows 10 rows and **show all 1679 variants**. Click, Enter and Space each toggle the table. **show fewer** folds it back.
- The extension, built from this branch and pointed at the local server, folds `ca`, and its button toggles. A word with a short list shows in full.
- The exported variants dictionary entry for `ca` has 10 visible rows, the button and the script. In a page with the dictionary's CSS and script, the button toggles. The owner sees the same in GoldenDict.
- `uv run pytest tests/exporter/webapp tests/exporter/variants` passes, apart from the baseline failures that Phase 1 records. `npm test` passes in the extension. `ruff`, `pyright` and `just typecheck` are clean.

## What's not included

- **The phone app.** It already folds. Over 10 rows it shows 10, "show more (N remaining)" adds 10 per tap, and "show less" folds. The owner chose to keep it as it is.
- Any change to the variants docs page (`docs/features/variants.md`).
- The extension release, its version bump and the website deploy.
- The lookup key `ootnote` with 828 variant rows. It is most likely `footnote` with its first letter lost during variant extraction (the owner agrees). This thread does not check or fix it. It is a candidate for its own thread.
- The other items of issue #99: page numbers, PTS variants, commentary variants, and columns by edition.
