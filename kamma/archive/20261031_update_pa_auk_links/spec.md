# Spec: Update Pa Auk Society links to OpenTipitaka

## Overview

The Digital Pāḷi Dictionary web app (`exporter/webapp/`) has a **Tipiṭaka
Translations** tab. Its footer contains an attribution link to the project that
supplies the underlying translation database. That project has been renamed —
it used to be "Pa Auk Society Tipiṭaka Translations" and is now
**OpenTipitaka**, hosted at `opentipitaka.org`. The translation-related links
still point at the old Pa Auk Society website (`tipitaka.paauksociety.org`), so
they should be updated to point at the new OpenTipitaka website.

## What it should do

1. Update the attribution link in the Tipiṭaka Translations tab so it points at
   the OpenTipitaka website, and change the visible text to the new project
   name.
2. Update `resources/tipitaka_translation_db/README.md` so its "Source" link
   names the new project, and its "More downloads" link points at the current
   (and correctly-encoded) download folder.

## Confirmed decisions (from the user)

- **New URL (webapp attribution):** `https://www.opentipitaka.org/` (canonical
  host).
- **New link text:** `OpenTipitaka` (short form).
- **Scope:** translation-related surfaces only. **No** browser-extension,
  `docs/install/browser_extension.md`, or newsletter changes.

## Verified facts (read from the real source, not memory)

- **Exact link location:** `exporter/webapp/templates/home.html`, line 383–384.
  It is the only "Pa Auk" / `paauksociety` reference in the whole webapp
  (`grep -rniE "paauk|pa auk|pa-auk|paauksociety" exporter/webapp` returns only
  this one hit). The footer reads:
  > This page uses the database from [Pa Auk Society Tipiṭaka Translations]
  > (https://tipitaka.paauksociety.org/index.php).
- **The translations tab** is the "Tipiṭaka Translations" tab: nav entry at
  `home.html:44`, section header `id="tt-title-clear"` at line 330, footer at
  line 383. It is rendered by `home.html` only — `home_simple.html` and the
  per-headword templates do not contain this footer.
- **README source note:** `resources/tipitaka_translation_db/README.md` line 9:
  > [Source](https://tipitaka.paauksociety.org/index.php). More downloads
  > available [here](https://dhamma.paauksociety.org/index.php?dir=Root%2FTipitaka).
- **New website resolves:** `https://opentipitaka.org/` returns HTTP 308 →
  `https://www.opentipitaka.org/` (HTTP 200). Page title: "About the project |
  OpenTipitaka". The site's own canonical/self links all use
  `https://www.opentipitaka.org`.
- **`openpitaka.org` does NOT resolve** (the Todoist task title says
  "openpitaka", but the real domain is `opentipitaka.org`).
- **Where the downloadable translation databases now live** — verified from
  OpenTipitaka's own production config, `https://www.opentipitaka.org/about/app.js`
  (`SITE_EXTERNAL_LINKS`):
  - `manualDatabases: "https://dhamma.paauksociety.org/index.php?dir=Root/Tipitaka/SqlLite%20Database"`
    (this is the "Translation database download" link on the OpenTipitaka site).
  - `apkMirror: "https://dhamma.paauksociety.org/index.php?dir=Root/Tipitaka"`.
  - A comment in that config states the file server expects **literal slashes
    in `dir=` (not `%2F`)**, and only spaces should be percent-encoded (e.g.
    `SqlLite%20Database`).
  - **Conclusion:** the translation database downloads have **not** moved — they
    are still served from `dhamma.paauksociety.org`, and OpenTipitaka's own
    download button points there. The current README link
    (`dir=Root%2FTipitaka`) uses `%2F` and is therefore malformed per that
    server's own guidance.

## Assumptions & uncertainties

- None outstanding. The "More downloads" question is resolved: the files remain
  on `dhamma.paauksociety.org`, and the correct current URL is
  `https://dhamma.paauksociety.org/index.php?dir=Root/Tipitaka/SqlLite%20Database`.

## Constraints

- Webapp templates are Jinja2 under `exporter/webapp/templates/`. The change is
  a static `href`/text edit; no Python, JS, or DB change is required.
- The actual translation data still comes from the same upstream source — only
  the attribution link changes. No data or export pipeline is touched.

## How we'll know it's done

- `grep -rniE "paauksociety|pa auk society" exporter/webapp/` returns **zero**
  hits.
- The footer link in `home.html` renders as
  `<a href="https://www.opentipitaka.org/" target="_blank">OpenTipitaka</a>`.
- `resources/tipitaka_translation_db/README.md` names `opentipitaka.org` for the
  source and points "More downloads" at
  `https://dhamma.paauksociety.org/index.php?dir=Root/Tipitaka/SqlLite%20Database`
  (literal slashes, encoded space only).
- Opening the new link in a browser lands on the OpenTipitaka site (200).

## What's not included

- Any change to the browser extension (`exporter/wxt_extension/`) theme/domain
  lists.
- Any change to `docs/install/browser_extension.md` or
  `docs_site/install/browser_extension/index.html`.
- Any change to historical newsletters (`docs/newsletters.md`,
  `docs_site/newsletters/**`).
- Regenerating/republishing the built webapp or docs_site output.
