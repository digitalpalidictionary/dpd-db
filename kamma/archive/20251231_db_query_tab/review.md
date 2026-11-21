# Review: Database Query tab (#199, PR #297)

**Verdict: PASSED**

Reviewed 2026-11-21 on branch `webapp-db-query` (the contributor's two commits plus the
owner-side fixes below). The spec and plan were written as a conductor track
(`conductor/tracks/db_query_tab_20251231/`) and moved here at finalize; the contributor did
not tick the plan, but every acceptance criterion in `spec.md` is met. Reviewers: a full read
by the coordinating agent, an independent Claude subagent, DeepSeek flash through pi
(thinking off, one request, 62 KB) and CodeRabbit once per changed folder, twice. The owner
and the agent both ran the tab in a real browser.

## Files Changed
- `docs/technical/api_endpoints.md` (new `/dq_search` entry, licence and turn-taking lines)
- `docs/pics/dpdict.net/dpdict_dq_*_{dark,light}.png` (12 new screenshots)
- `docs/webapp/database_query.md` (new user guide page)
- `exporter/webapp/README.md`
- `exporter/webapp/db_query.py` (new)
- `exporter/webapp/main.py` (`/dq_search` route)
- `exporter/webapp/static/app.js` (tab switching from a map, fourth tab)
- `exporter/webapp/static/db_query.css` (new)
- `exporter/webapp/static/db_query.js` (new)
- `exporter/webapp/static/home.css` (tab row scrolls under 576 px)
- `exporter/webapp/templates/home.html`
- `mkdocs.yaml` (menu entry)
- `tests/exporter/webapp/test_asset_version.py`
- `tests/exporter/webapp/test_db_query.py` (new)
- `tools/search_deadline.py` (compile cache 4 -> 16)

## Findings
Fixed:
- No cap on filters per request (independent subagent, confirmed by probe): 999 filters gave
  a 500 ("Expression tree is too large"), and many heavy patterns filled the `regex`
  package's 500-pattern cache. Now at most 10, with a 400 and a readable message; the
  "+ filter" button disables at 10.
- The shared compile cache held 4 patterns, so OR queries with 5+ filters recompiled on every
  row: 4 filters 0.74 s, 5 filters 2.43 s, 10 hit the 4 s budget (median of 3 each). Raised
  to 16.
- Unknown-field validation left the old results exportable (CodeRabbit).
- An empty "or" row dropped its group boundary in the request (CodeRabbit).
- `ends_with` used `$`, which also matches before a final newline; 88,877 `freq_data`
  values end in one. Now `\Z` (CodeRabbit).
- A background DPD search finishing moved the cursor to the first query field (CodeRabbit).
- A blocked localStorage write cleared the preset name silently (CodeRabbit).
- Docs page: full address for `?tab=dq`, a wrong "grammar field mentions a root" example,
  and the case-sensitivity example now names its field (CodeRabbit and agent check).

Rejected with reasons:
- DeepSeek "cache test stays green on revert": the revert run failed with the timeout error.
- DeepSeek "other routes evict the patterns mid-query": only one regex search runs at a time.
- DeepSeek "`keyword` column gives a 500": no such column (`COLUMNS` equals `__table__.columns`).
- DeepSeek "`?tab=dq` is not read" and "Back restores stale dq state": `app.js` reads `tab`,
  and the real page opened on the tab; dq searches push no history entries.
- DeepSeek "busy should be 503": same 200-with-error shape as `/bd_search` and `/tt_search`.
- DeepSeek "header overflows at 600-750 px": measured at 7 widths, no overflow; the history and
  settings buttons are hidden below 750 px on `main` too.
- CodeRabbit "check busy before an unfiltered query": it reads 101 rows by id, cheap.
- CodeRabbit "preset load during a pending search": same as editing filters mid-search.

## Test Evidence
- `uv run pytest tests/exporter/webapp`: 207 passed.
- `test_the_most_filters_allowed_run_within_the_budget` fails with the cache put back to 4
  (timeout error) and passes at 16 (1.67 s).
- `uv run pytest tests/exporter/webapp tests/tools`: 1 failure, the abbreviations golden
  master, which reads live data ("three gender" vs "three genders") and nothing this thread
  touched.
- `just typecheck`: 0 errors. ruff, ruff format and pyright clean on every touched Python file.
  `node --check` clean on both scripts. `uv run mkdocs build --strict` passes.
- Real browser: five OR filters 0.67-0.70 s over 3 runs, all 100 rows match one of the five
  values; ten rows disable "+ filter"; the empty-"or" and stale-export fixes, the cursor fix
  and the blocked-storage message each checked on the live page.
