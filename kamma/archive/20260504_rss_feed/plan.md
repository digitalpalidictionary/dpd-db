# Plan: RSS feed for DPD newsletter updates

## Architecture Decisions
- Single feed at https://docs.dpdict.net/rss.xml. Webapp links to it, doesn't serve it.
- One module `tools/rss_feed.py`, no shared-module consumers — keeps it simple.
- `markdown` package for HTML rendering (transitive dep of mkdocs, already present).
- Hand-rolled XML via `xml.etree.ElementTree`.
- Docs site: `theme.custom_dir: overrides` + `overrides/partials/header.html` to place RSS icon left of repo info.

## Phase 1 — Generate the feed

- [x] Create `tools/rss_feed.py`: parse `docs/newsletters.md` by `## YYYY-MM-DD`
      headings, render via `markdown`, rewrite relative image paths to absolute
      `docs.dpdict.net` URLs, emit RSS 2.0 to `docs/rss.xml` when run as __main__.
      → verify: `python tools/rss_feed.py` writes `docs/rss.xml`;
      `xmllint --noout docs/rss.xml` exits 0; one `<item>` per dated section.
- [x] Add `tests/tools/test_rss_feed.py`: smoke test against real newsletters.md,
      assert ≥1 item with non-empty title and valid pubDate.
      → verify: `uv run pytest tests/tools/test_rss_feed.py` passes.

## Phase 2 — Wire into docs build

- [x] Add `Generate RSS feed` step to `.github/workflows/static.yml` between
      `Populate index folders` and `Build MkDocs site`.
      → verify: step is in correct position.
- [x] Confirm mkdocs copies docs/rss.xml to site root.
      → verify: `mkdocs build` produces `docs_site/rss.xml`.

## Phase 3 — Webapp RSS icon

- [x] Add RSS icon link after email-button in home.html.
- [x] Add `<link rel="alternate">` to home.html head.

## Phase 4 — Docs site RSS icon

- [x] Add `theme.custom_dir: overrides` to mkdocs.yaml.
- [x] Create `overrides/partials/header.html` with RSS icon left of source block.
- [x] Add `<link rel="alternate">` via the same override.
