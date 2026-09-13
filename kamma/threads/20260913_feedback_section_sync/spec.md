# Spec: sync the feedback sections

## GitHub issue
(none yet)

## Status
Placeholder. Not planned, not started.

## Overview
The feedback section is written three times over, once per surface, and the three have
drifted apart. Bring them into line so that one editorial change lands everywhere.

## The three surfaces
- **Website** — the feedback block in `exporter/webapp/templates/dpd_headword.html`.
  The browser extension renders the site's HTML, so it inherits whatever this says.
- **GoldenDict / MDict** — built in JavaScript at
  `exporter/goldendict/javascript/feedback_template.js`.
- **App** — `lib/widgets/feedback_section.dart` in the `dpd-flutter-app` repo.

## Known divergences (2026-09-13)
- Website and GoldenDict offer *Help with coding* and *Help with Pāḷi* as two links; the
  app merges them into one *Get involved*.
- GoldenDict has a *Get updated* link naming the installed build's date; the other two
  have nothing equivalent.
- Website and GoldenDict say *Visit the DPD docs website*; the app says *Read the docs*.
- The *Correct a mistake* blurb differs: the app adds "Have something to add?".
- The app opens native form sheets; the other two link out to Google Forms.
- The ID line and the permalink line under it are the only part currently identical
  across all three (added 2026-09-13).

## Questions to settle before planning
- Is one shared source of wording feasible across Jinja, JavaScript and Dart, or is the
  realistic goal a single reviewed wording list that each surface copies?
- Should the app keep its native form sheets while matching the wording?
- Does the `Get updated` link belong on the website at all?

## Out of scope
PDF, Kindle, Kobo and txt exports have no feedback section.
