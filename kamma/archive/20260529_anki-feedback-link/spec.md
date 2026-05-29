# Spec — Anki public deck feedback link

## Overview
Add a small, theme-styled feedback link to the bottom of the back of cards in the Anki **public** deck, mirroring the "Did you spot a mistake?" footer in the webapp's grammar tab — but without the grammar/area field, and stamped with the release date so feedback can be traced to a deck version.

## What it should do
- On the back of every public-deck card, below the data table, show a horizontal rule then a small footer: `Did you spot a mistake? Correct it here.`
- "Correct it here." links to the existing DPD "Correct a mistake" Google Form, prefilled with the word's id + lemma.
- The form's source field (`entry.1433863141`) is `Anki YYYY-MM-DD`, where the date is the deck build/release date.
- Styled small and themed with the Anki deck's CSS variables.

## Reference
Webapp grammar footer — `exporter/webapp/templates/dpd_headword.html:1202-1208`:
- Form id `1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ`
- `entry.438735500` = word identifier (`{{id}} {{lemma_1}}` for Anki)
- `entry.326955045` = area field — **omitted** (the "without the grammar field" requirement)
- `entry.1433863141` = source = `{{app_name}}+{{date}}` in webapp → `Anki+YYYY-MM-DD` here

## Assumptions & uncertainties
- `{{pic}}` is always empty in the public deck (`anki_apkg_exporter.py:160` passes `""`), so hr+footer placed after it sit directly under the table at card bottom.
- genanki bakes template HTML at build time; there is no native version/date field in the `.apkg`, so the date is injected via build-time string replacement of `__RELEASE_DATE__`.
- Build date = release date (deck is built per release). `tools.date_and_time.year_month_day_dash()` returns `YYYY-MM-DD`.
- Google Forms decodes `+` in a query param as a space, so `Anki+2026-05-29` displays as `Anki 2026-05-29`.

## Constraints
- Public deck only: touch `public_back.html` and `public_styling.html`, not `back.html`/`styling.html`.
- Anki theme vars only: `--label`, `--hl`, `--soft`, `--bg`.

## How we'll know it's done
- `make_model()` reads the template and replaces `__RELEASE_DATE__` with today's dash date.
- Back of public card shows an hr + small accent-colored "Correct it here." link opening the prefilled form with id + lemma, source `Anki YYYY-MM-DD`, and no grammar/area field.
- `uv run ruff check` passes on the edited Python file.

## What's not included
- The private/full deck (`back.html`, `styling.html`), the front, the export pipeline/query logic.
- Any new genanki FIELDS entry (date is baked into the template, not per-note).
