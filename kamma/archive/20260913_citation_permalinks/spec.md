# Spec: citation permalinks

## GitHub issue
#262 how to cite DPD

## Overview
Stop telling readers how to build a permalink and just give them one. Shorten the link
itself, show it in the feedback section of every surface, and replace the
build-it-yourself instructions in the docs with a picture of where to find it.

Run as a `/kamma:quick` thread, so this record was written at finalize rather than up
front.

## Established facts (2026-09-13)
- The old permalink was `https://www.dpdict.net/?tab=dpd&q=<id>`.
- `tab` defaults to `dpd` in the webapp's URL handling, and the bare domain serves the
  site, so `https://dpdict.net/?q=<id>` already worked with no code at all.
- A bare number was already handled by the search function, but only in the branch that
  runs when the lookup table has no match.
- The lookup table holds exactly one all-digit key, `3`, the abbreviation "declined in
  all three genders", which shadowed headword id 3.
- Abbreviations are not clickable in the webapp, so nothing reaches that row by a click.
- The feedback section is written three times over: the website template, the
  GoldenDict/MDict JavaScript, and the app's Dart widget. The browser extension renders
  the site's HTML, so it inherits the website's version.
- The mkdocs how-to-cite page is generated, gated to uposatha days, and covered by tests.

## Decisions
- The permalink is `https://dpdict.net/<id>`, served by a digits-only route that
  redirects to the search.
- A bare number in the search always resolves to a headword id. The abbreviation `3`
  becomes unreachable by typing `3`; accepted, since it is reachable nowhere else and
  ids are the thing being linked.
- One shared helper builds the link on the Python side. JavaScript and Dart hardcode it,
  because they are separate codebases.
- Harmonising the rest of the feedback wording is deferred to
  `20260913_feedback_section_sync`.

## Out of scope
PDF, Kindle, Kobo and txt exports have no feedback section.
