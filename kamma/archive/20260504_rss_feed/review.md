## Thread
- **ID:** 20260504_rss_feed
- **Objective:** Publish RSS 2.0 feed of monthly newsletters on both DPD sites.

## Files Changed
- `tools/rss_feed.py` — parser + XML renderer, run as __main__ to write docs/rss.xml
- `docs/rss.xml` — generated feed (44 items), committed as a docs asset
- `tests/tools/test_rss_feed.py` — 4 smoke tests
- `.github/workflows/static.yml` — added Generate RSS feed step before mkdocs build
- `exporter/webapp/templates/home.html` — RSS alternate link in head + icon after email button
- `mkdocs.yaml` — added custom_dir: overrides
- `overrides/main.html` — extrahead block with RSS alternate link
- `overrides/partials/header.html` — RSS icon injected left of github repo source block

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `rss_feed.py:104` | Path traversal in __main__ | CLAUDE.md forbids parent-traversal path hacks | Fixed: use relative `Path("docs/...")` |

## Fixes Applied
- Path traversal → relative paths in `__main__` block.

## Test Evidence
- `uv run python tools/rss_feed.py` → `wrote 44 items → docs/rss.xml`
- `xmllint --noout docs/rss.xml` → valid
- `uv run pytest tests/tools/test_rss_feed.py` → 4 passed
- mkdocs serve confirmed `http://127.0.0.1:8000/rss.xml` serves the feed

## Verdict
PASSED
- Review date: 2026-05-04
- Reviewer: kamma (inline)
