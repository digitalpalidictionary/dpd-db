# Plan: citation permalinks

All phases complete, 2026-09-13.

## Phase 1 — the short link
- [x] Add `SHORT_WEBSITE` and `make_permalink()` to `tools/version.py`.
- [x] Add a digits-only route to `exporter/webapp/main.py` redirecting to `/?q=<id>`.
- [x] Make a bare number skip the lookup table in `exporter/webapp/toolkit.py`.
- [x] Tests: `tests/exporter/webapp/test_permalink.py`.

## Phase 2 — the permalink in every feedback section
- [x] Website: `permalink` attribute on `HeadwordData`, rendered in the feedback block of
      `exporter/webapp/templates/dpd_headword.html`.
- [x] GoldenDict/MDict: `exporter/goldendict/javascript/feedback_template.js`.
- [x] App: `lib/widgets/feedback_section.dart` in `dpd-flutter-app`.
- [x] Browser extension inherits the website's HTML — no change needed.

## Phase 3 — the docs
- [x] `tools/docs_update_how_to_cite.py`: short link in all four citation forms, and the
      build-it-yourself section replaced by light/dark screenshots.
- [x] Placeholder PNGs under `docs/pics/dpdict.net/` for the editor to overwrite.
- [x] `exporter/goldendict/export_help.py`: short link in the `cite` entry.
- [x] Tests updated to pin the screenshots and the absence of the old query form.
- [x] Regenerated `docs/how_to_cite.md`.

## Phase 4 — finalize
- [x] Placeholder thread `20260913_feedback_section_sync` for the wording divergences.
- [x] Review (CodeRabbit + independent audit) — see `review.md`.
