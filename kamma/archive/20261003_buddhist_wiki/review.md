## Thread

> **Renamed 2026-10-04 after review:** `dictionaries/wikipedia` → `dictionaries/buddhist_wiki`, tests `test_wikipedia_*` → `test_buddhist_wiki_*`, output `buddhist-wiki.zip`, display name "Buddhist Wiki" (was "DPD Buddhist Encyclopedia"), export flag `--skip-buddhist-wiki`. Paths below are as they were during the thread.

- **ID:** 20261003_wikipedia_buddhist_dict
- **Objective:** GoldenDict/MDict dictionary of English Wikipedia's Category:Buddhism articles with in-dictionary links and CC BY-SA attribution.

## Files Changed (all in `resources/other-dictionaries`, uncommitted)
- `dictionaries/wikipedia/` — new: `wikipedia.py` (export), `entry_builder.py` (wikitext→HTML), `fetch_wikitext.py` (API fetch), `make_article_list.py` (linktarget category walk), `make_redirects.py` (dump redirects), `dump_rows.py` (SQL dump parser), `fetch_from_dump.py` (fallback XML extractor), `run_overnight.sh`, `wikipedia.css`, `source/seed_articles.txt`, `source/article_list.txt`
- `tests/test_wikipedia_{entry_builder,dump_rows,fetch_from_dump,fetch_wikitext,make_redirects,make_article_list}.py` — new
- `vendor/dpd_tools/paths.py`, `scripts/export_all.py`, `README.md`, `pyproject.toml`, `uv.lock`, `.gitignore` — registration, paths, wikitextparser dep
- dpd-db: `kamma/tech.md` (dated note), thread `spec.md`/`plan.md`/`handoff.md`

## Findings (independent Sonnet review + CodeRabbit, validated against code and data)
| # | Severity | Location | What | Fix |
|---|----------|----------|------|-----|
| 1 | major | `entry_builder.py` `_template_replacement` | Every unknown template collapsed to its last parameter: `{{convert\|150\|km}}`→"km", `{{nihongo\|Enni-bennen\|圓爾辨圓}}` lost the English name, `{{sfnp…}}`→"2003" (≈50k collapses in a 1/4 sample) | Per-template rules: first-param, date, convert, list-join, junk prefixes; last-param kept for lang/transl (Phase-1 decision) |
| 2 | major | `entry_builder.py` `paragraphs_to_html` | 5,562 empty `<li></li>`, headings over empty sections | Drop empty items; drop a heading followed by a same/higher heading or the end |
| 3 | major | `entry_builder.py`, `wikipedia.py` | No licence URL (CC BY-SA requires one); "Wikipedia" in the product name (trademark policy) | Licence link in footer/About/description; renamed "DPD Buddhist Encyclopedia", `buddhist-encyclopedia.zip`; changes + non-affiliation notice |
| 4 | major (CR) / minor | `make_article_list.py` reuse check | Row count can't tell a finished load from a killed one | `loaded` marker table per step; partial rows cleared; catmap rebuilt when its inputs reload |
| 5 | minor | `make_article_list.py` seed merge | Depended on untracked `redirects.json`; kept 14 dead titles | Seeds checked against the page dump |
| 6 | minor | `entry_builder.py` | `"` in titles broke `href`; `<nowiki/>` leaked (334) | `html.escape` href/footer, `quote` URL, regex nowiki |
| 7 | minor | `run_overnight.sh` | Step-1 download failure not fatal; `rm *.done` | Check markers after step 1; rm removed |
| 8 | minor | `make_redirects.py` | Docstring overstated ordering hazard | Reworded: never concurrently |
| 9 | nit | `debug_catgraph.py`, docstrings, test | Dead script on the wrong premise; stale "delete gz"; duplicate `webm`; vacuous assert | Deleted / fixed |

**Deferred (noted, not fixed):** generic `*_stubs` categories inside depth 5 (961 articles, a scope call for the user); `enwiki-latest-*` local names vs pinned URL; redirects to the 3 post-dump renames; `[[:Foo]]`/pipe-trick cosmetics; label text not HTML-escaped (escaping would break `&nbsp;` etc.); fetcher ignores `continue`/`Retry-After` (0 cut-offs observed); `missing.txt` can repeat lines; ~1% residue (119 entries with unbalanced `''''`, 40 Wikipedia-side broken links, ~25 nested tables/images). `fetch_from_dump.py` kept as the documented fallback.

## Fixes Applied
All of 1–9 above. Revert checks: old cleaner fails 17 of 37 entry-builder tests; page-id walk fails 2 of 4 walk tests; old fetch guard fails 1 of 2; old XML lookup fails 6 of 6.

## Test Evidence
- `uv run pytest tests/ -q` (scope: whole sub-project) → 309 passed, 1 failed = PRE-EXISTING `test_mw_data_loading::test_entries_count`
- `ruff check` + `ruff format --check` (scope: all 16 thread files) → clean; `uv run --with pyright pyright` same files → 0 errors
- `just typecheck` (scope: whole dpd-db repo, pyrefly) → 0 errors
- Full rebuild + whole-build scan (scope: every entry of both formats): 23,836 entries (one noise-only tree chart now correctly empty), 64,151 synonyms, 346,015 live links, 0 placeholder links, 0 empty `<li>`, 0 `nowiki`, 0 entries without a licence link
- Article list rebuilt: 23,826 = previous list minus exactly the 14 dead seed titles

## Not Verified
- MDict output opened in a real MDict reader (checked programmatically only).
- GoldenDict re-check after the review fixes (user's check was on the pre-review build).
- Legal reading is from Wikipedia's reuse guide and the Wikimedia trademark policy, not legal advice.

## Verdict
PASSED
- Review date: 2026-10-04
- Reviewer: independent Sonnet subagent + CodeRabbit CLI 0.7.6; fixes and validation by Claude Opus 5.5
