# Review: citation permalinks

2026-09-13. CodeRabbit plus an independent from-scratch audit, run in parallel.

## CodeRabbit
0 findings across all 15 files.

## Independent audit — fixed
- **major** — the app's permalink was the only tappable link not wrapped in
  `SelectionContainer.disabled`. The entry screen wraps the subtree in a
  `SelectionArea` that fires a lookup on selection change, so a tap could start a
  spurious tap-search instead of opening the browser. Wrapped like its siblings.
- **minor** — `q.isnumeric()` is the wrong predicate: `"½"` and `"²"` are numeric but
  `int()` rejects them, and `/search_json?q=½` returned 500. Both the new guard and the
  pre-existing branch now use `q.isdecimal()`. Test added.
- **minor** — the permalink redirect used the default 307. Changed to 308, since a
  citation link is permanent by definition.
- **minor** — the route was undocumented. Added to `docs/technical/api_endpoints.md`.
- **minor** — nothing pinned the behaviour change on the GoldenDict route. Test added.
- **minor** — the website's permalink anchor had no `target="_blank"`, unlike its
  siblings. Added on the editor's instruction: a permalink opens in a new tab.

## Independent audit — considered, not changed
- The docs page now leans on two placeholder images. Deliberate: the editor is taking
  the real screenshots and overwriting them at those filenames. The page still carries a
  one-sentence instruction, so it is not empty if an image fails to load.
- A path of several thousand digits returns 500 rather than 404, because Starlette's
  `int` converter has no length bound and CPython caps `int(str)` at 4300 digits. No
  leak, no crash, bot-triggerable only. Left as it is.
- `/0` and other dead ids redirect to a "no results" page rather than 404.

## Verified by the audit
- The digits-only route cannot shadow or be shadowed by `/metrics`, `/static`,
  `/status` or `/audio/...`.
- The redirect loses nothing: `tab` defaults to `dpd` in the SPA.
- The old long link form is fully swept — remaining hits are SPA history state, archived
  specs and historical newsletters.
- Regenerating the how-to-cite page reproduces the committed file byte for byte.

## Tests
`uv run pytest tests/` — 1847 passed, 12 deselected. `just typecheck` — 0 errors.
`flutter analyze` on the changed widget — no issues.

## Not verified
The GoldenDict/MDict feedback panel was not rebuilt, so its permalink line has not been
seen rendered. The app was not run.
