# Plan: KOReader integration — full lifecycle

**GitHub issue:** [#241 — Add to KOReader](https://github.com/digitalpalidictionary/dpd-db/issues/241).
This thread runs the whole integration lifecycle and ticks off #241 checklist
items as they complete. Rule: update the issue BODY (tick checkboxes) only —
never comment, never close.

## Architecture Decisions
- **Distil, don't dump.** Published integration pages (tbw.md ~8 lines,
  tipitakapali.md ~25 lines) are the house style. Questionnaire headings are
  submission format only; none survive into the article.
- **tipitakapali.md is the lead for the integrations article**; the existing
  e-reader install pages (kindle.md/kobo.md) are the lead for the install page.
- **Keep the developer's links and claims verbatim.** Repo verified 404 until
  release; the Coming Soon marker covers that gap — no invented placeholders.
- **Images flat in `docs/pics/koreader/`** per the
  `<app>/<name>_light|_dark.png` convention; zip's folder level dropped.
- **No tooling** — one-off pages need no generator (minimal-first).
- **Issue discipline:** tick checkboxes via `gh issue edit --body-file` only.
  No comments, no close, no label/assignee churn.
- **"Test live" is two-stage:** local serve now; deployed check after the
  user commits/pushes (docs/ commits auto-rebuild the site).

## Phase 1 — Screenshot assets

- [x] Extract `/home/bodhirasa/MyFiles/1_Incoming/koreader.zip` to a temp dir
      and copy the 10 PNGs into `docs/pics/koreader/`, flattening
      `add_your_app_screenshots/`, keeping `_light`/`_dark` names
  → verify: `ls docs/pics/koreader/` lists exactly 10 files — `hero`, `main`,
    `lookup`, `database_status`, `database_status_menu` × `_light`/`_dark` —
    byte sizes matching the zip listing

- [x] Phase 1 verification
  → verify: `file docs/pics/koreader/*.png` = "PNG image data" ×10;
    `ls docs/pics/koreader | wc -l` prints 10

## Phase 2 — Install page (moved from Integrations per user, 2026-10-18)

- [x] Write `docs/install/koreader.md` per spec: H1 `KOReader`;
      `**--- Coming Soon ---**` at top; plain-English intro (DPD inside
      KOReader, long-press a word, linked Ven. Nirodhavihārī); features with
      `hero`, `main`, `lookup` pairs; install steps + v2026.07+ / ~1.1 GB /
      Kindle-jailbreak note; keeping DPD current (replace db, delete
      `-wal`/`-shm`, restart) with `database_status_menu`/`database_status`
      pairs; bugs/feedback section; every external link `{target="_blank"}`;
      portrait/square screenshot pairs constrained `{width="360"/"400"}`,
      hero advert full-width
  → verify: voice/brevity in line with the house install pages; every image
    a `_light`+`#only-light` / `_dark`+`#only-dark` pair; zero questionnaire
    headings remain; email = developer-supplied dpd-koreader@nirodha.8shield.net

- [x] Add `- KOReader: "install/koreader.md"` to the Installation Guide block
      in `mkdocs.yaml`, after `Kobo`
  → verify: `rg -n "install/koreader" mkdocs.yaml` shows the line after Kobo

- [x] Phase 2 verification: internal consistency
  → verify: every `../pics/koreader/*.png` referenced resolves via `test -f`;
    no unreferenced PNGs in `docs/pics/koreader/`

## Phase 3 — Build & local serve

- [x] `uv run mkdocs build`
  → verify: exits 0; no new warnings mentioning koreader — RESULT: green
    (re-verified at review: only the pre-existing README-conflict WARNING;
    the style_guide line is INFO, not a warning)

- [x] `uv run mkdocs serve` and check the page
  → verify: RESULT — page serves 200; Coming Soon marker, H1 "DPD for
    KOReader", all 10 images, linked Ven. Nirodhavihārī; footer proves nav
    placement Previous: Kobo → Next: Anki (first serve ran against a stale
    instance on port 8000, hence the false alarm)

- [x] Tick #241 items "setup the webpage" and "Add installation instruction
      for KOReader" (convert the install bullet to a checkbox, then tick);
      body-only edit
  → verify: RESULT — both boxes `[x]` on the issue, no comments added
  → verify: `gh issue view 241` shows both boxes `[x]`, no new comments

## Phase 4 — Test live (after user commits/pushes)

- [ ] Deployed check of the page on digitalpalidictionary.github.io
  → verify: `curl -s https://digitalpalidictionary.github.io/install/koreader/`
    returns the page HTML (Coming Soon marker present); eyeball both palettes
    in a browser; then tick #241 "test live"

## Phase 5 — Release day (BLOCKED until nirodhav publishes dpd.koplugin)

- [ ] Flip the Coming Soon marker in `docs/install/koreader.md` to a
      short "now available" line linking the releases page
  → verify: marker gone; releases URL present and live (curl 200)

- [ ] Add the KOReader section to `docs/newsletters.md` for the Uposatha
      release (house newsletter voice, 1-2 screenshots)
  → verify: new H2 dated section reads like the 2026-07-29 entry; images in
    `docs/pics/newsletters/`

- [ ] Tick #241 "include in the uposatha day release newsletter"
  → verify: `gh issue view 241` shows the box `[x]`, no comments added
