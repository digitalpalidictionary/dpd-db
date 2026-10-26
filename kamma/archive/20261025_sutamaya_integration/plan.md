# Plan: add sutamaya to the software integrations

**Thread:** 20261025_sutamaya_integration · **Spec:** `spec.md` (read first)
**GitHub issue:** none given

## Architecture Decisions
- One new Markdown page, copying the shape of `docs/integrations/epitaka.md` (title,
  one-paragraph intro, feature list, lookup, settings, more info). No new helpers.
- Screenshots come from the live app via `playwright-cli` (installed at
  `~/.local/bin/playwright-cli`). Light and dark pairs use the `#only-light` /
  `#only-dark` suffix, as `epitaka.md` does. Dark mode: the app follows the browser's
  colour scheme, or Style panel > Theme > Dark.
- Nothing is invented. Store links, DPD version and "free" are left out on purpose.
- Docs-only thread. No tests apply. Verification is the docs build, a link check and
  a look at each screenshot.
- Project rule: no commit, no git, no GitHub writes. The user commits at the end.

## Phase 1 — Collect and confirm facts — *Fast*
- [x] Re-check for a store link and open questions
  → verify: `curl -sL https://sutamaya.org/ | grep -c -i -E "apps.apple|play.google"`
  prints 0, and README of `gbbr/sutamaya.org` still has no store link. If a link now
  exists, stop and tell the user.
- [x] Confirm "On tap" in the live app (open https://app.sutamaya.org/read/mn10,
  Style panel, Pali = On tap, tap an English line)
  → verify: record in this plan whether tapping a line shows its Pāḷi. If it does not
  work, word the page as "set Pāḷi to Always" only.
- [x] Check every link the page will use returns 200 (app, site, repo, translation
  changes doc, privacy, both YouTube URLs, `mailto` excluded)
  → verify: `curl -sL --limit-rate 300k -o /dev/null -w "%{http_code} %{url_effective}\n" <url>`
  prints 200 for each. YouTube may print 200 only; accept that.
- [x] Phase check: facts in `spec.md` still match the live app and repo
  → verify: list any changed fact here, or write "no change".

## Phase 2 — Screenshots — *Fast*
- [x] Take desktop screenshots to the scratchpad, light and dark: main view (MN10 with
  Pāḷi "Always"), lookup (dock open on "bhagavā"), Style panel
  → verify: Read each PNG. Pāḷi text and the DPD dock are legible, no cookie banner or
  half-loaded state.
- [x] Take one phone-width lookup shot, light and dark (390 wide)
  → verify: dock sits at the bottom, entries readable.
- [x] Copy the files to `docs/pics/sutamaya/` as `main-view_light.png`,
  `main-view_dark.png`, `lookup_light.png`, `lookup_dark.png`,
  `lookup-phone_light.png`, `lookup-phone_dark.png`, `settings_light.png`,
  `settings_dark.png`. Match the naming style in `docs/pics/epitaka/`.
  → verify: `ls docs/pics/sutamaya/` shows 8 files; `file` reports PNG for each.

## Phase 3 — Write the page and the listings — *Fast*
- [x] Write `docs/integrations/sutamaya.md` from the spec's "Page content". Sections:
  intro, "Sutamaya contains", Open it / Install (browser, web app), Looking Up a Word,
  Reading Settings, Offline, Get the Latest DPD, More Info (site, repo, MIT licence,
  issues, email, both videos). Plain tone, short sentences, no hype. Add an HTML
  comment for store links, like `epitaka.md`.
  → verify: read the page against the spec. Each sentence maps to a spec fact. The word
  "free" does not appear (`grep -c -i "free" docs/integrations/sutamaya.md` prints 0
  unless inside "freely available").
- [x] Add the nav line to `mkdocs.yaml` between "Simsapa Dhamma Reader" and
  "Sutta Central Website": `- Sutamaya: "integrations/sutamaya.md"`
  → verify: `grep -n -A1 -B1 sutamaya mkdocs.yaml` shows the line in that slot.
- [x] Add one line to the README integrations list before "Sutta Central", matching
  the existing `[Name](site) | [Docs](.../integrations/sutamaya/)` format
  → verify: `grep -n -B1 -A1 -i sutamaya README.md` shows alphabetical position.
- [x] Add one line to the Websites list in `newsletter/useful_links.md` before
  "SuttaCentral Voice", same format
  → verify: `grep -n -B1 -A1 -i sutamaya newsletter/useful_links.md` shows position.
- [x] Phase check: docs build
  → verify: run `uv run mkdocs build` (or the project's docs recipe: `just --list`
  first), expect no warning about `sutamaya.md` or a missing picture. If the user must
  run it, say so and hand over `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && <cmd>`.

## Phase 4 — Final check — *Fast*
- [ ] Open the built page and read it once top to bottom in light and dark mode
  → verify: images load in both modes; links work; tone matches `epitaka.md`.
- [x] Report the changed files for the user to commit. Suggest this commit message:
  `docs: add sutamaya integration page` (no issue number was given).
  → verify: `git status --porcelain` is user-run only. List the thread's files by hand:
  the new page, 8 pictures, `mkdocs.yaml`, `README.md`, `newsletter/useful_links.md`.
- [ ] Ask the user whether to email metta@sutamaya.org the page for a check before it
  goes live (per `add_your_app.md`). Do not send.
  → verify: the user's answer is recorded here.

## Results (2026-10-25)
- Phase 1: no store link on the site or in the repo README (0 matches each). All 9 links
  returned 200. "On tap" confirmed live: tapping an English line shows its Pāḷi under it,
  and "On tap" is the default. Facts in `spec.md` unchanged.
- Phase 2: 8 PNGs in `docs/pics/sutamaya/`. Deviation: named `-light`/`-dark` (hyphen),
  not `_light`, to match `docs/pics/epitaka/`. The Style panel's theme swatches did not
  draw in headless captures; the selected theme label still shows.
- Phase 3: page written; nav, README and newsletter lines added in alphabetical slots.
  `just mkdocs` built in 0.84 s with no warning about the new page or pictures. Two
  warnings existed before this thread (README.md vs index.md, and an unlisted
  `technical/style_guide_for_dpd_entries.md`).
- Phase 4: rendered page checked in light mode at http://127.0.0.1:8000/integrations/sutamaya/.
  Nav shows Sutamaya between Simsapa Dhamma Reader and Sutta Central Website.
  Dark-mode view of the rendered page was not checked.
- Files changed: `docs/integrations/sutamaya.md`, `docs/pics/sutamaya/*.png` (8),
  `mkdocs.yaml`, `README.md`, `newsletter/useful_links.md`.
- Suggested commit message: `docs: add sutamaya integration page`

## Change of direction (2026-10-25)
The user wants the page as a hidden draft to show the app maker, not a public listing.
- Removed the nav entry, the README line and the newsletter line.
- `docs/integrations/sutamaya.md` front matter now has `search: exclude: true` and
  `robots: noindex`.
- `scripts/build/mkdocs_overrides/main.html` now prints `<meta name="robots">` when a
  page sets `robots` in its front matter. No other page sets it.
- Checked with `uv run mkdocs build -d <scratchpad>`: page is built; noindex tag on it
  only; no link to it from other pages; 0 mentions in the search index.
- The spec's "listed in nav, README, newsletter" and "alphabetical order" goals are
  parked until the maker approves. To publish: add the nav line between Simsapa Dhamma
  Reader and Sutta Central Website, add the README and newsletter lines, and remove the
  `search` and `robots` lines from the page.
- Intro line for the page is pending: the user's message ended at "just want it el…".

## Finalized (2026-10-26)
- Closed by the user without `/kamma:3-review` and without CodeRabbit. No `review.md`.
- Left open on purpose: dark-mode look of the rendered page (docs server was stopped),
  the page intro line (user's message ended at "just want it el…"), and the email to the
  maker. The page stays a hidden draft: nav line commented out in `mkdocs.yaml`, page has
  `search: exclude` and `robots: noindex`.
