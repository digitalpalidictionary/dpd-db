## Thread
- **ID:** 20261031_update_pa_auk_links
- **Objective:** Repoint the DPD webapp's Tipiṭaka Translations attribution link (and the translation-DB source note) from the old Pa Auk Society site to OpenTipitaka.

## Files Changed
- `exporter/webapp/templates/home.html` — footer link href → `https://www.opentipitaka.org/`, text → `OpenTipitaka`, `target="_blank"` preserved.
- `resources/tipitaka_translation_db/README.md` — "Source" → `https://www.opentipitaka.org/`; "More downloads" → `https://dhamma.paauksociety.org/index.php?dir=Root/Tipitaka/SqlLite%20Database` (literal slashes, fixing a malformed `%2F`).

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `resources/tipitaka_translation_db/README.md:9` | trailing space on the edited line (pre-existing) | lint churn | removed |

No blocking or major findings. Independent `reviewer` subagent returned **PASSED**.

## Fixes Applied
- Removed the trailing space on `README.md:9`.

## Test Evidence
- `grep -rniE "paauksociety|pa auk society" exporter/webapp/` (scope: whole webapp tree) → zero hits.
- `grep -n "opentipitaka" exporter/webapp/templates/home.html` (scope: the edited template) → new href + `OpenTipitaka` text present; `target="_blank"` intact.
- `grep -rniE "tipitaka\.paauksociety\.org|pa auk society" exporter/webapp resources/tipitaka_translation_db` (regression sweep) → zero hits; `dhamma.paauksociety.org` remains only as the correct download host.
- README checks → new source + download URLs present; no `%2F` remains.
- `curl -sSI https://www.opentipitaka.org/ | head -1` (live) → `HTTP/2 200`.

## Not Verified
- The `dhamma.paauksociety.org` download URL uses a cookie/redirect-based PHP file browser that `curl -L` cannot fully traverse (redirect loop). It was verified as the exact URL OpenTipitaka's production `app.js` (`SITE_EXTERNAL_LINKS.manualDatabases`) uses, not by following it to a directory listing.
- The `README.md` change lives in the `resources/tipitaka_translation_db` **git submodule**. Finalize must commit inside the submodule and update the submodule pointer in dpd-db, or the change will not land.
- Live webapp render not visually inspected (static Jinja2 text edit; no logic/JS/DB change).

## Verdict
PASSED
- Review date: 2026-10-31
- Reviewer: DeepSeek Pro Coder + independent `reviewer` subagent
