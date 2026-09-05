# Review: CC licence notice on DPD API output

## Reviewers
- **CodeRabbit** — two scoped runs (the webapp dir, then the tests dir; the first `--dir`
  did not reach the new test file, hence the second).
- **Independent agent audit** — from-scratch adversarial read, told not to trust the spec.

## Coverage
| Check | Scope actually covered |
|---|---|
| CodeRabbit run 1 | `exporter/webapp/main.py`, `exporter/webapp/README.md` — 0 findings |
| CodeRabbit run 2 | `tests/exporter/webapp/test_license_notice.py` — 1 finding |
| Agent audit | every `@app.get` in the webapp, all repo-wide FastAPI apps, every consumer of the three routes, CORS behaviour verified live, RFC 8288 syntax, test quality, repo conventions |
| `pytest tests/exporter/webapp/` | 48 passed (43 baseline + 5 new) |
| `just typecheck` (pyrefly, whole repo) | 0 errors |
| `ruff check` / `ruff format` / `pyright` | clean on both changed Python files |

**Not verified:** no live browser session. The site's own search was not loaded and
clicked. The frontend reads response keys by name, and the response shape is under test,
but that is reasoning rather than observation.

## Findings and resolutions

### 1. `Link` header invisible to cross-origin browsers — FIXED (severity: real gap)
`Link` is not a CORS-safelisted response header. `CORSMiddleware` was configured with
`allow_origins=["*"]` but no `expose_headers`, so page-context JS on another origin got
`null` when reading it. This mattered most for `/search_html` and `/gd`, whose HTML bodies
carry no in-band notice — the header is their only carrier, and both are consumed
cross-origin by `resources/fdg_dpd/assets/js/paliLookup.js` and
`resources/bw2/js/pali-lookup-standalone.js`.

Fixed by adding `expose_headers=["Link"]`. Verified live: an `Origin`-bearing request now
returns `access-control-expose-headers: Link`. A regression test covers it.

### 2. `docs/technical/api_endpoints.md` left stale — FIXED
The public API reference documented the `/search_json` body as exactly two keys. The
plan only accounted for the webapp README and missed this file, which is the one linked
from the docs site. Updated the response example and added a **Licensing** section stating
which endpoints carry the notice and which deliberately do not.

### 3. Test asserted an empty status check on the audio route — FIXED (CodeRabbit)
The negative test checked only for the header's absence without asserting the request
succeeded, so it would have passed for the wrong reason if the route started 404ing.
A hard `== 200` was not the right fix — the audio db is gitignored, so a clean checkout
legitimately 404s. The test now skips explicitly with a stated reason on 404 and asserts
200 otherwise.

### 4. Test enshrined a pre-existing quirk — RESOLVED BY DOCUMENTING
`/search_json` has long sent `Accept-Encoding: gzip` as a *response* header, which is
meaningless (it is a request header; `GZipMiddleware` does the real work). The change
correctly did not touch it, but the new test asserting its survival risked reading as an
endorsement. The assertion is kept — it genuinely guards that the licence header was
*merged* into the route's headers rather than substituted for them — with a docstring
saying it guards a pre-existing quirk and does not endorse it.

**Not fixed, deliberately:** the quirk itself. Removing it is unrelated to this thread and
would change response headers for existing consumers. Worth a separate look.

### 5. Negative test coverage was thin — FIXED
Originally only `/tt_search` and `/audio` were checked for absence. `/`, `/bd` and
`/bd_search` are now checked too, so a future middleware-based regression that blanket-
applied the header would be caught rather than half-caught.

### 6. Cosmetic: unannotated constants — FIXED
`LICENSE_URL` and `LICENSE_NAME` now carry `: str`, matching the two annotated dicts.

## Confirmed clean by the audit
- **Route coverage complete.** Every `@app.get` was read. Only three return dictionary
  content and all three carry the notice. `/` and `/bd` render the page shell with
  `dpd_results: ""`. The only other FastAPI apps in the repo are both under `archive/`.
- **No leak.** Verified live that `/`, `/bd`, `/bd_search`, `/status`, `/metrics`,
  `/openapi.json`, `/tt_search` and `/audio/dhamma` all return no `Link` header.
  `track_performance` passes responses through untouched; `GZipMiddleware` preserves the
  header alongside `content-encoding: gzip`.
- **Header is valid RFC 8288.** Angle-bracket URI-Reference, `license` is IANA-registered
  (RFC 4946), `title` is a legal target attribute, quoted-string needs no escaping, pure
  ASCII so no `title*` form required.
- **No consumer breaks.** Exhaustive search found four consumers of the affected routes —
  `static/app.js`, the wxt extension's search/api modules, and the GoldenDict/DictTango
  docs. All read `summary_html` and `dpd_html` by name. Nothing does strict-shape
  validation. No Go module, exporter, fixture or snapshot touches these routes.

## Outcome
Ready to finalise. Six findings, five fixed, one documented as an out-of-scope
pre-existing quirk.

---

## Addendum — post-review scope changes

Two rounds of user feedback after the first review.

### Round 1 — a footer line
Added a visible line in the dictionary tab's footer. **Wrong, and rejected by the user.**
A footer is not part of the results, so the notice did not travel with the data — the
exact property the whole thread exists to provide.

The user also saw the line render with the name and licence missing. That was a stale
server, not a code fault: jinja reloads templates from disk but uvicorn had not reloaded
the Python module, so the new template rendered against globals that did not yet exist.
Worth noting as a diagnosis trap — the symptom looked like a template bug.

### Round 2 — under the entries, with the CC marks
Moved to the single return point of the results builder, and added the four official
Creative Commons marks inline. See the spec addendum for the reasoning.

### Verification
- Rendered output inspected on `/search_html`, `/gd` and the JSON `dpd_html`: exactly one
  notice, four inline marks, correct attribution and deed URL, and it is the last thing in
  the results.
- Confirmed absent on "no results" for two different failing queries, and on the home
  page.
- Confirmed the notice is inline SVG with no `<img>`, so GoldenDict keeps it offline.
- `tools/css_manager.py` regenerates only `dpd.css`; the two stylesheets edited here are
  not regenerated, so the styling survives a server restart. Checked, not assumed.
- 53 webapp tests passing, 641 tools tests passing, `just typecheck` clean, `ruff` and
  `pyright` clean on every touched file.

### Verified in GoldenDict
User confirmed `/gd?search=dhamma` renders correctly in GoldenDict.

### Known gap (out of scope, not a defect)
The offline exported GoldenDict/MDict dictionaries are built by `exporter/goldendict/`,
which shares no code with the webapp and has its own templates. They carry no licence
notice. Most GoldenDict users install those rather than using the live API route, so this
is where the notice is most missing. Needs its own thread; the other export formats and
the mobile app are likely in the same position.
