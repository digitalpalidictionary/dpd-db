# Spec (PARKED) — Improve DPD in ePitaka

Status: parked 2026-10-06. Not planned. Run `/kamma:1-plan` on this thread
before any work. Depends on `20261006_epitaka_dpd_export` (the local daily
exporter) being finished.

## Overview
Recon done while planning the daily exporter showed several openings to
improve how DPD appears in the ePitaka app, and to add other dictionaries.
None are for public release until the user decides.

## Findings to build on (verified 2026-10-06)
- **`epd` already supported by the app, never filled.** The app checks
  `PRAGMA table_info(dpd_lookup)` for an `epd` column and shows an "English
  meaning" section from it (`epitaka/lib/core/database/dpd_dictionary_database.dart:121-137`,
  `lib/features/dictionary/widgets/dictionary_panel.dart:1001-1033`).
  `dpd.db` `lookup.epd` has the data. Data-only change, no app change.
- **Unused shipped fields.** `antonym`, `synonym`, `stem`, `pattern` are
  selected but never displayed. Showing them needs an app change.
- **Thin content.** `meaning_html` carries only grammar, sanskrit, root,
  compound and example_1. Missing vs DPD: example_2, sutta/source refs,
  inflection tables, word/compound families, notes, commentary,
  frequency, variants. All could be added inside `meaning_html` (data-only)
  as long as the app's `flutter_html` renderer copes (it ignores CSS
  classes; `<details>`/`<summary>` are stripped on expand).
- **Empty lookup rows.** ~89k `dpd_lookup` rows have neither headwords nor
  deconstructor (variant/spelling/grammar-only keys); the app shows nothing
  for them. Could carry spelling/variant notes.
- **Other dictionaries.** `epitaka.db` has TPR-style `dictionary(word,
  definition, book_id)` + `dictionary_books(id, name, user_order,
  user_choice)`; the app routes book 11 to `dpd-dictionary.db`, book 100 to
  `pali_definition`, everything else to `dictionary`
  (`dictionary_sheet.dart:1384-1401`). Users can also import `.mdx` files.
  DPD's other-dictionaries submodule could feed either route.
- **No in-app update.** The app downloads `dpd-dictionary.db` only when
  missing; the manifest `updated` date is never read. Public distribution
  of a fresher DPD needs an ePitaka app change or the maintainer's release.
- **Data quirks seen upstream:** `dictionary` has 22,727 rows for book 61
  (no `dictionary_books` row) and 11 rows whose `book_id` is text.

## Open questions for planning
- Data-only improvements first (epd, richer `meaning_html`), or app
  changes too (PRs to `dhammanana/epitaka_app` via `/epitaka-pr`)?
- Which other dictionaries, and through which route?
- Should a public `dpd-dictionary.zip` be offered to the maintainer?
