# Spec: KOReader integration — full lifecycle (#241)

**GitHub issue:** [#241 — Add to KOReader](https://github.com/digitalpalidictionary/dpd-db/issues/241).
This thread tracks the WHOLE lifecycle of the KOReader integration, ticking
off #241 checklist items as they are completed. Rule agreed with the user:
tick checklist items on the issue as work lands, but NEVER comment on the
issue or close it.

## Overview
Bring the KOReader integration to life end-to-end on the public docs site:
the integrations article (from the developer's filled questionnaire +
screenshots), a dedicated install page under the Installation Guide, a live
check of the deployed site, and — once the plugin actually releases — the
Coming Soon marker flip and the Uposatha-day release newsletter mention.

## Facts (verified from source, 2026-10-18)
- `/home/bodhirasa/MyFiles/1_Incoming/koreader.zip` (1.7 MB) contains:
  - `add_your_app.md` — questionnaire filled in for "Digital Pāḷi Dictionary
    for KOReader (dpd.koplugin)" by Nirodhavihāri (nirodhav on GitHub). The
    article's source of truth.
  - `add_your_app_screenshots/` — 10 PNGs, 5 light/dark pairs: `hero`,
    `main`, `lookup`, `database_status_menu`, `database_status`.
- Nav lives in root `mkdocs.yaml`: "Software Integrations" (six app pages,
  then "Add Your App") and "Installation Guide" (…Kindle, Kobo, Anki,
  ChromeBook, extension, Update).
- Screenshot convention: `docs/pics/<app>/<name>_light.png`/`_dark.png` with
  `#only-light` / `#only-dark` suffixes (tipitakapali.md; kamma archive
  20261012_integration_template).
- Markdown extensions: `attr_list`, pymdownx highlight/inlinehilite/
  snippets/superfences. **No admonitions** — plain markdown only.
- Published integration pages are SHORT and human (tbw.md ~8 lines,
  tipitakapali.md ~25 lines).
- `https://github.com/nirodhav/dpd.koplugin` returns 404 (curl + GitHub
  search, 2026-10-18); `nirodhav` account exists. Plugin not published yet —
  hence Coming Soon, and hence the release-day items stay blocked.
- Newsletters: `docs/newsletters.md`, one H2 per date, prose + images in
  `docs/pics/newsletters/`; written at release time.
- Committing `docs/` auto-rebuilds the public site (docs/README.md), so
  "test live" is possible only after the user commits/pushes.
- Issue #241 also carries an UPSTREAM request (StarDict entry in KOReader's
  `dictionaries.lua` via PR to the koreader repo + other-dictionaries) that
  lives outside this repo — tracked on the issue, not executable here.

## What it should do
1. **Install page** (user moved it here from Integrations, 2026-10-18) —
   copy 10 PNGs to `docs/pics/koreader/`; create `docs/install/koreader.md`
   (H1 "DPD for KOReader" — corrected from `KOReader` to match install-page
   house style "DPD for Kindle"/"DPD for Kobo eReader", deviation recorded
   at review 2026-10-18; `**--- Coming Soon ---**` marker at top, plain-English
   intro, features with `hero`/`main`/`lookup` pairs, install steps +
   KOReader v2026.07+ / ~1.1 GB / Kindle-jailbreak note, keeping DPD current
   with `database_status` pairs, links with `{target="_blank"}`); nav line
   in the Installation Guide after Kobo. Portrait screenshots constrained
   with `{width=...}` attr_list (phone-height problem, user request); the
   hero advert stays full-width; developer named as
   [Ven. Nirodhavihārī](https://github.com/nirodhav) with long ī.
   NO integrations page — #241's "Add to integration list" item stays
   untouched/open on the issue.
2. **Test live** — after the user commits/pushes, verify the deployed page
   on digitalpalidictionary.github.io (both palettes).
3. **Tick #241 items** as each lands (body edits only — no comments/close).
4. **Release-day items (blocked until nirodhav publishes the plugin):**
   flip the Coming Soon marker to a live announcement, add the newsletter
   section for the Uposatha release, then tick those items.

## Assumptions & uncertainties
- Assumed: distilled article, not questionnaire structure (user's words).
- Assumed: slug `install/koreader.md`, nav label "KOReader" (user moved the
  page out of Integrations on 2026-10-18 — "it shouldnt be in integrations.
  My mistake, it should be in install").
- Assumed: developer's claims kept verbatim; unverifiable until repo is
  public. Contact email verified developer-supplied; 8shield.net MX live
  (SimpleLogin).
- Blocked: release timing unknown; items 4 stay open in this thread until
  the plugin is out.

## Constraints
- Docs-only changes: one new markdown page (`docs/install/koreader.md`),
  10 PNGs, one nav line.
- Plain markdown only (no admonitions).
- Existing pages untouched.
- Issue #241 = single tag for all KOReader work; tick items, never
  comment/close.

## How we'll know it's done
- `docs/install/koreader.md` live locally (build green, serve correct in
  both palettes), in the Installation Guide nav after Kobo.
- After user push: deployed page verified.
- #241 checkboxes ticked for: webpage setup, install instructions, test live.
- At release: marker flipped, newsletter added, remaining items ticked.

## What's not included
- The upstream StarDict `dictionaries.lua` PR to koreader/koreader (tracked
  on #241, outside this repo).
- Any generator for filled questionnaires (deferred in
  20261012_integration_template).
- Changes to existing integration/install pages (the single nav line is the
  only touched line outside the new page and new pics).
