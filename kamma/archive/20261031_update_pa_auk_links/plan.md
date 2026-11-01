# Plan: Update Pa Auk Society links to OpenTipitaka

## Architecture Decisions

- **Two static edits, no code.** The change is text/href edits in
  `exporter/webapp/templates/home.html` and
  `resources/tipitaka_translation_db/README.md`. No new code, helper, or
  refactor.
- **Target URL = `https://www.opentipitaka.org/`** (canonical host; bare
  `opentipitaka.org` 308-redirects to it). Confirmed live 200.
- **Link text = `OpenTipitaka`** (short form, per user).
- **Preserve `target="_blank"`** on the webapp link (external link in a tab
  that also holds an in-page search UI).
- **Download location does not move.** The translation databases are still on
  `dhamma.paauksociety.org`; the current, correctly-encoded URL (from
  OpenTipitaka's own `app.js`) is
  `https://dhamma.paauksociety.org/index.php?dir=Root/Tipitaka/SqlLite%20Database`
  — literal slashes in `dir=`, only the space encoded. This fixes the README's
  existing `dir=Root%2FTipitaka`, which the server treats as malformed.
- **Deliberately out of scope:** browser-extension theme/domain lists
  (`exporter/wxt_extension/`), `docs/install/browser_extension.md`,
  `docs_site/**`, and newsletters.

## Phase 1 — Update the translations tab link

- [x] Update the footer attribution link in `exporter/webapp/templates/home.html`
      (lines 383–384): change `href` from
      `https://tipitaka.paauksociety.org/index.php` to
      `https://www.opentipitaka.org/`, and change the link text from
      "Pa Auk Society Tipiṭaka Translations" to "OpenTipitaka".
  → verify: `grep -rniE "paauksociety|pa auk society" exporter/webapp/` returns
    no hits; `grep -n "opentipitaka" exporter/webapp/templates/home.html` shows
    the new `href` and the text `OpenTipitaka`; `target="_blank"` is still
    present on that `<a>`.
  → verify (live): `curl -sSI https://www.opentipitaka.org/ | head -1` returns
    `HTTP/2 200` (or `HTTP/1.1 200`).

## Phase 2 — Update the translation database source note

- [x] Update `resources/tipitaka_translation_db/README.md` line 9:
      - "Source" link: `https://tipitaka.paauksociety.org/index.php` →
        `https://www.opentipitaka.org/`
      - "More downloads" link:
        `https://dhamma.paauksociety.org/index.php?dir=Root%2FTipitaka` →
        `https://dhamma.paauksociety.org/index.php?dir=Root/Tipitaka/SqlLite%20Database`
  → verify: `grep -n "opentipitaka\|dhamma.paauksociety" resources/tipitaka_translation_db/README.md`
    shows `https://www.opentipitaka.org/` for the source and the new
    `dir=Root/Tipitaka/SqlLite%20Database` (literal slashes) for downloads;
    no `%2F` remains.
