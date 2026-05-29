## Thread
- **ID:** 20260529_anki-feedback-link
- **Objective:** Add a small, theme-styled feedback link with release-date stamp to the bottom of Anki public-deck card backs.

## Files Changed
- `exporter/anki/templates/public_back.html` — hr + feedback footer linking to the Correct-a-mistake form (id+lemma, no grammar field, source `Anki+__RELEASE_DATE__`)
- `exporter/anki/anki_apkg_exporter.py` — `make_model()` replaces `__RELEASE_DATE__` with `year_month_day_dash()` at build time
- `exporter/anki/templates/public_styling.html` — themed `hr.dpd-rule`, `.dpd-footer`, `.dpd-link` CSS

## Findings
No findings.

(Notes: `&` in the href is unescaped, matching the existing webapp grammar footer convention. `hr` style scoped to `hr.dpd-rule` so the existing `<hr id="answer">` separator is untouched.)

## Fixes Applied
- During implementation, scoped the new hr style to a `dpd-rule` class to avoid restyling the existing answer separator.

## Test Evidence
- `uv run ruff check exporter/anki/anki_apkg_exporter.py` → pass
- User built the deck, imported into Anki, confirmed hr + small themed link, prefilled form with id+lemma, source `Anki 2026-05-29`, no grammar field → pass

## Verdict
PASSED
- Review date: 2026-05-29
- Reviewer: kamma (inline)
