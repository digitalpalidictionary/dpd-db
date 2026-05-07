# Spec: RSS feed for DPD newsletter updates

## Overview
Publish an RSS 2.0 feed of monthly DPD newsletter updates. Source of truth is
`docs/newsletters.md`. Feed hosted at docs.dpdict.net/rss.xml. Both sites
advertise it with a visible icon and a `<link rel="alternate">` in their head.

## What it should do
- Parse `docs/newsletters.md` by `## YYYY-MM-DD` sections into feed items.
- Each item:
  - **title** — first `**...**` line of the section; fallback `DPD update YYYY-MM-DD`
  - **pubDate** — RFC 822 from the `## YYYY-MM-DD` heading at 00:00 UTC
  - **link / guid** — `https://docs.dpdict.net/newsletters/#YYYY-MM-DD`
  - **description** — section markdown rendered to HTML (CDATA); relative image
    paths rewritten to `https://docs.dpdict.net/...`
- Feed channel: title `Digital Pāḷi Dictionary — Updates`, link `https://www.dpdict.net/`,
  description `Monthly updates from the Digital Pāḷi Dictionary.`, language `en`,
  managingEditor `dpd@4nt.org (Bodhirasa)`
- Module at `tools/rss_feed.py`; run directly via `python tools/rss_feed.py`
  to write `docs/rss.xml`.
- GitHub Action step generates the file before `mkdocs build`; it is copied to
  site root as `docs_site/rss.xml`.
- Webapp adds `<link rel="alternate">` + visible RSS icon right of email button.
- Docs site: mkdocs header override adds RSS icon left of github repo info;
  plus `<link rel="alternate">` in head.

## Constraints
- No new Python dependencies. Use `markdown` (already pulled in by mkdocs).
- Hand-rolled XML via `xml.etree.ElementTree`.

## How we'll know it's done
- `python tools/rss_feed.py` writes valid `docs/rss.xml` with one item per section.
- Webapp home.html has alternate link and RSS icon.
- mkdocs build produces `docs_site/rss.xml` and index.html has alternate link.
- Feed validates at https://validator.w3.org/feed/.

## What's not included
- GitHub releases, corrections, blog posts, Atom format, email dispatch.
