# Spec: sync the feedback sections

## GitHub issue
(none yet)

## Status
Done 2026-10-23. Wording applied to all three surfaces. Reviewed and passed.

## Overview
The feedback section is written three times over, once per surface. The three have
drifted apart. Bring them into line, and make each place name the other two, so a
wording change is never made in one place only.

## Decision: no single source of truth
One shared source across Jinja, JavaScript and Dart is not practical. Instead:
- The wording below is the reviewed reference.
- Each surface holds a copy.
- Each surface carries a comment that names the other two surfaces and says to change
  all three together.

## The three surfaces
- **Website** — the feedback block in `exporter/webapp/templates/dpd_headword.html`.
  The browser extension renders the site's HTML, so it inherits whatever this says.
- **GoldenDict / MDict** — built in JavaScript at
  `exporter/goldendict/javascript/feedback_template.js`.
- **App** — `lib/widgets/feedback_section.dart` in the `dpd-flutter-app` repo
  (`/home/bodhirasa/MyFiles/3_Active/dpd-flutter-app`).

## Current state (read from the files, 2026-10-23)
The 2026-09-13 divergence list was out of date. The website already matches the app on
the docs link and the "Get involved" link. Only GoldenDict differs.

Identical on all three already: the ID line, the permalink line, the intro line,
"Join the mailing list".

Still different after this thread (found in review, not agreed to align):
- "Add a missing word": website and GoldenDict add ". If you prefer to work offline, here
  is a spreadsheet to download, fill in and submit." The app stops after "other later
  texts."
- "How to cite": website and GoldenDict have it. The app's feedback section has no such
  link.

## Agreed wording
Four items change. Every other item keeps its current text.

1. **Correct a mistake** — drop "Have something to add?".
   Text: ". Did you spot a mistake in the dictionary? Please report it. It generally
   takes less than a minute and your corrections and suggestions help to improve the
   quality of this dictionary for everyone who uses it."
   Changes: website, app. GoldenDict already says this.
2. **Get updated** — stays on GoldenDict only. The website and the app each get a
   comment saying the absence is on purpose.
3. **Read the docs** — link text "Read the docs".
   Text: ". Get more detailed information about installation on your devices,
   upgrades, advanced settings and features."
   Changes: GoldenDict. Website and app already say this.
4. **Contribute to DPD** — replaces "Get involved" and GoldenDict's "Help with coding"
   and "Help with Pāḷi".
   Text: "Contribute to DPD" then ". Contribute your time, skills or resources to the
   project. Please use the form."
   Link target: the contributing page on the docs website, at its "Offer your help"
   heading, where the contribution form is embedded.
   Changes: all three. GoldenDict also merges its two links into one.

## Cross-reference comments
Each surface gets one comment next to its feedback block. The comment:
- names the other two surfaces and their files;
- says a wording change here must be made in all three;
- on the website and the app, says "Get updated" is GoldenDict-only on purpose.

## Settled by the decision above
- The app keeps its native form sheets. This thread only aligns wording.

## Out of scope
- PDF, Kindle, Kobo and txt exports have no feedback section.
- The form links and the form behaviour. Only wording and the contribute link change.

## Related
- `kamma/archive/20261022_contributions_form/spec.md` (#271) says every "get involved"
  link points at the contributing page. This thread keeps that rule.
- "Contribution form" means offer help. "Contribution website" means add Pāḷi entries.
  Do not mix the two names.
