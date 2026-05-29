# Plan — Anki public deck feedback link

## Architecture Decisions
- **Date baked at build time, not a per-note field.** The whole `.apkg` is one release, so a FIELDS entry would duplicate the same string across ~50k notes. Instead `make_model()` string-replaces a `__RELEASE_DATE__` placeholder in the template. Mirrors the webapp's `{{app_name}}+{{date}}` pattern.
- **Reuse `tools.date_and_time.year_month_day_dash()`** — the webapp already uses it for its date; gives `YYYY-MM-DD`.
- **Placement after `{{pic}}`** — pic is always empty in the public deck, so hr+footer land at the visual bottom under the table.
- **Style `hr` via theme var, drop footer `border-top`** to avoid a double line.

**GitHub issue:** https://github.com/digitalpalidictionary/dpd-db/issues/159

## Phase 1 — Implement

- [x] Task 1: Add hr + feedback footer to `exporter/anki/templates/public_back.html` after `{{pic}}`. Link to the Correct-a-mistake form with `entry.438735500={{id}}%20{{lemma_1}}` and `entry.1433863141=Anki+__RELEASE_DATE__`; no grammar/area param.
  → verify: footer present, no `326955045`, placeholder `__RELEASE_DATE__` present.
- [x] Task 2: In `exporter/anki/anki_apkg_exporter.py` `make_model()`, import `year_month_day_dash` and replace `__RELEASE_DATE__` with its value after reading `public_back.html`.
  → verify: `uv run ruff check exporter/anki/anki_apkg_exporter.py` passes; replacement leaves no literal `__RELEASE_DATE__`.
- [x] Task 3: Add `.dpd-footer`, `.dpd-link`, themed `hr` CSS to `exporter/anki/templates/public_styling.html` using theme vars only.
  → verify: classes defined, theme vars only.
- [x] Phase verify: ruff clean; grep confirms link has id+lemma, source `Anki+__RELEASE_DATE__`, no `326955045`.
