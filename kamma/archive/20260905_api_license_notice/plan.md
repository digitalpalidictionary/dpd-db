# Plan: CC licence notice on DPD API output

## Architecture Decisions
- **Two module-level constants in `exporter/webapp/main.py`.** `LICENSE_LINK_HEADER`
  (a `dict[str, str]` ready to splat into a response's `headers=`) and `LICENSE_NOTICE`
  (a `dict[str, str]` for the JSON body). Defined near the other module-level constants,
  above the routes. No new module — see spec.
- **Header applied per route, not by middleware.** The existing `track_performance`
  middleware runs on every path; using it would tag Tipiṭaka and audio responses too.
  Three explicit `headers=` arguments keep the scope exact and greppable.
- **`/search_json` merges the header into its existing `headers` dict** rather than
  replacing it — the `Accept-Encoding` entry already there must survive.
- **`license` added last** to the JSON response dict so it renders at the bottom.
- **New test file** `tests/exporter/webapp/test_license_notice.py`, following the
  `TestClient` pattern of `test_webapp_status.py`.

## Baseline
- [x] Record the pre-existing state: run `uv run pytest tests/exporter/webapp/` and note
      any failures that are already red before touching anything.
      → verify: 43 passed, 0 failed. Clean baseline — no pre-existing failures.

## Tasks

- [x] Add `LICENSE_LINK_HEADER` and `LICENSE_NOTICE` constants to
      `exporter/webapp/main.py`, placed with the other module-level state (near
      `history_list`), typed `dict[str, str]`.
      → verify: `uv run ruff check exporter/webapp/main.py` and
        `uv run pyright exporter/webapp/main.py` both clean.

- [x] `/search_json`: merge `LICENSE_LINK_HEADER` into the existing `headers` dict and
      append `"license": LICENSE_NOTICE` as the last key of `response_data`.
      → verified via TestClient rather than curl (no live server needed): `Link` header
        present, `Accept-Encoding: gzip` still present, `license` is the final key.

- [x] `/search_html`: pass `headers=LICENSE_LINK_HEADER` to its `TemplateResponse`.
      → verified: `Link` header present; only a `headers=` kwarg was added, the template
        context is untouched, so the rendered HTML cannot have changed.

- [x] `/gd`: pass `headers=LICENSE_LINK_HEADER` to its `TemplateResponse`.
      → verified: `Link` header present, template context untouched. GoldenDict rendering
        unaffected (header only; body identical).

- [x] Write `tests/exporter/webapp/test_license_notice.py`:
      - `Link` header present and naming CC BY-NC-SA 4.0 on `/search_json`,
        `/search_html`, `/gd`
      - `/search_json` body has a `license` key, it is the **last** key, and it holds the
        four expected sub-keys
      - `Link` header **absent** on `/tt_search` and on `/audio/{headword}`
      → verified: 5 tests, all passing. Hardened during review — the audio route now
        skips explicitly on 404 instead of passing vacuously, `/`, `/bd` and `/bd_search`
        joined the absence checks, and a cross-origin readability test was added.

- [x] Document the notice in `exporter/webapp/README.md` under the existing **Interface →
      API** bullet: one sentence saying DPD data responses carry a CC BY-NC-SA 4.0 `Link`
      header and that the JSON search response ends with a `license` object.
      → verified: added as a `**Licensing:**` bullet under Interface.

- [x] REVIEW ADDITION — `docs/technical/api_endpoints.md` was missed by this plan and is
      the reference actually linked from the public docs site. Updated the `/search_json`
      response example and added a **Licensing** section naming which endpoints carry the
      notice and which deliberately do not.
      → verified: the documented body now matches the real response.

- [x] REVIEW ADDITION — `expose_headers=["Link"]` on the CORS middleware. Without it the
      header is unreadable to cross-origin browser clients, which is exactly the audience
      for `/search_html` and `/gd` (no in-band notice in an HTML body).
      → verified live: an `Origin`-bearing request returns
        `access-control-expose-headers: Link`. Regression test added.

## Smoke
- [x] `uv run pytest tests/exporter/webapp/` — 48 passed (43 baseline + 5 new).
- [ ] Start the server, search a word on the site, confirm results still render.
      NOT DONE — needs a live browser check by the user. The frontend reads response keys
      by name (`data.summary_html`, `data.dpd_html`), so the extra key is inert by
      construction, and the test suite covers the response shape.
- [x] `just typecheck` clean — 0 errors.

## Deferred
Nothing. Bold definitions were considered and ruled out — dictionary data only.
