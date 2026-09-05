# Spec: CC licence notice on DPD API output

## GitHub issue
#261

## Overview
Every response that carries **DPD dictionary data** should state the licence it is
released under — CC BY-NC-SA 4.0 — so that attribution and the non-commercial
restriction travel with the data instead of living only in the repo README.

Approach C from the discussion: a standards-based `Link` header on every DPD-serving
route (covers HTML and JSON alike, zero payload noise), **plus** a small `license`
object at the end of the DPD JSON body (the part a human actually reads).

The licence field does not create the restriction — CC BY-NC-SA 4.0 already binds
anyone who uses the data. What it buys is notice (nobody can claim ignorance) and
automatic attribution, which is the share-alike clause's practical failure point.

## Scope
"The API" here means the public FastAPI webapp behind dpdict.net
(`exporter/webapp/main.py`). `gui2/main.py` is a local editing GUI, not public, and is
out of scope.

### In scope — routes that return DPD dictionary data
| Route | Returns | Gets header | Gets body field |
|---|---|---|---|
| `/search_json` | JSON: `summary_html`, `dpd_html` | yes | yes |
| `/search_html` | HTML fragment of dictionary entries | yes | n/a (not JSON) |
| `/gd` | pure HTML for GoldenDict / MDict | yes | n/a (not JSON) |

### Explicitly out of scope
| Route | Why |
|---|---|
| `/tt_search` | Tipiṭaka translations — not DPD-licensed data |
| `/audio/{headword}` | audio recordings — separate licensing |
| `/bd_search` | bold definitions extracted from CST commentaries — not dictionary data, excluded (confirmed by user) |
| `/`, `/bd` | empty page shells, carry no dictionary content |
| `/status`, `/metrics` | operational endpoints |
| `/static/*` | assets |

## Established facts
- The project licence is **CC BY-NC-SA 4.0**, stated in the root `README.md` (line 55)
  and linked to `http://creativecommons.org/licenses/by-nc-sa/4.0/`.
- `/search_json` currently returns exactly `{"summary_html": ..., "dpd_html": ...}` and
  already passes a `headers` dict to `JSONResponse` — an extra header is a one-key add.
- `/search_html` and `/gd` return `TemplateResponse`, which accepts a `headers=` kwarg.
- The only consumer of `/search_json` in this repo is `static/app.js` (line 158), which
  reads `data.summary_html` and `data.dpd_html` **by name**. Adding a third key cannot
  break it.
- Python dicts preserve insertion order and FastAPI's JSON serialiser follows it, so a
  key added last genuinely renders at the bottom of the payload.
- `rel="license"` is the IANA-registered link relation for exactly this purpose
  (RFC 8288 / RFC 4946), so the header is a real standard, not a custom convention.
- The webapp already has one HTTP middleware (`track_performance`), but it fires on
  *every* path — using it would leak the notice onto Tipiṭaka and audio responses,
  which is the opposite of what is wanted. Per-route headers are the correct tool here.
- `tests/exporter/webapp/` already contains `TestClient`-based route tests
  (`test_webapp_status.py` is the pattern to copy).

## The notice content

**Header** (all three in-scope routes):
```
Link: <https://creativecommons.org/licenses/by-nc-sa/4.0/>; rel="license"; title="CC BY-NC-SA 4.0"
```

**Body field** (`/search_json` only, appended last):
```json
"license": {
  "name": "CC BY-NC-SA 4.0",
  "url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
  "attribution": "Digital Pāḷi Dictionary by Bodhirasa Bhikkhu — dpdict.net",
  "note": "Non-commercial use only. Derivatives must be shared alike."
}
```

Spelling is `license` (US), matching the root `README.md`.

Both values are defined once as module-level constants in `exporter/webapp/main.py` and
referenced from the three routes. No new module — a handful of constants used three times
in one file do not earn a file of their own.

**CORS.** `Link` is not a CORS-safelisted response header, so the middleware must also
send `expose_headers=["Link"]` or the notice is invisible to exactly the cross-origin
browser clients that consume `/search_html` and `/gd`. (Added during review — the original
spec missed it.)

## Design decisions
- **Per-route headers, not a middleware path allowlist.** An allowlist would duplicate
  route path strings in a second place and silently drift when a route is renamed. Three
  explicit `headers=` arguments are greppable and cannot go stale.
- **Once per response, not once per result.** A licence block repeated per entry is the
  thing developers strip out in irritation.
- **Four short keys.** Anything longer gets deleted by consumers.
- **No enforcement, no gating.** This is a notice. Nothing is blocked, rate-limited, or
  refused.

## Non-goals
- Any change to `robots.txt` or terms of service.
- Any CORS change beyond exposing the `Link` header for reading.
- Any licence notice on non-DPD data (Tipiṭaka translations, audio).
- A `/license` endpoint.
- Wrapping responses in a `data`/`meta` envelope (would break every consumer).

## Open questions
None. Bold definitions were considered and explicitly ruled out: the scope is dictionary
data only.

## Acceptance
- Requesting a DPD word through any of the three in-scope routes returns a `Link`
  header naming CC BY-NC-SA 4.0.
- The JSON search response ends with a `license` object.
- A Tipiṭaka translation search and an audio request carry no licence header.
- The website's own search still works unchanged.

---

## Addendum — visible licence line (added after first review)

The `Link` header is machine-readable only, so a person reading the site or a GoldenDict
entry saw nothing.

**Placement: appended to the rendered entries, not to a page footer.** The purpose of the
notice is that it travels *with the data*. A footer is not part of the results fragment —
when the two in-repo lookup scripts embed the HTML, or when someone copies entries, a
footer stays behind. Appending it at the single return point of the results builder means
one change covers every carrier at once: the site, the GoldenDict/MDict output, the JSON
`dpd_html` field, and any third-party embed.

**A "no results" page carries no notice.** The three fall-through branches that return
closest-match suggestions set a flag; the notice is appended only when real entries were
rendered. Stamping a licence on "No results found." is noise.

**Content.** The four official Creative Commons press-kit marks (cc, by, nc, sa), then
"Digital Pāḷi Dictionary by Bodhirasa Bhikkhu CC BY-NC-SA 4.0", the whole line linking to
the deed with `rel="license"`.

**The marks are inlined SVG, not linked images.** A remote image would break in offline
GoldenDict and would leak a request to a third party on every lookup. Their white
background discs were removed and they inherit `currentColor`, so they read in both light
and dark mode — the same technique as the GitHub icon already in the footer. The artwork
lives in a static file read once at import, following the pattern already used for the
webapp's CSS and JS assets. Cost is ~6KB raw, ~2.5KB gzipped, once per search response.

**Attribution** is "Digital Pāḷi Dictionary by Bodhirasa Bhikkhu CC BY-NC-SA 4.0", used
verbatim in the JSON body field, the link tooltip and the visible line, all built from one
set of constants so they cannot drift apart.
