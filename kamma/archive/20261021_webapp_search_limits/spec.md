# SPEC — Server-side limits for webapp searches
GitHub issue: https://github.com/digitalpalidictionary/dpd-db/issues/268 (read-only; do not comment or close)
Type: bug (resource limits)

## Overview
Four webapp search routes can use unbounded memory or CPU. The fix bounds every search by result count and by time. Only the webapp gets the new limits. The contributor GUI (gui2) keeps its current behaviour.

## Current behaviour (verified by reading the code)
1. `exporter/webapp/toolkit.py::make_dpd_html` matches `Lookup.lookup_key` with `.ilike(q)` and `.ilike(q + ".")`. `%` and `_` are LIKE wildcards, so q="%" matches every row. `.all()` loads them and every row is rendered. Used by `/search_json`, `/search_html`, `/gd`.
2. `exporter/webapp/main.py::db_search_bd` calls `BoldDefinitionsSearchManager.search(q1, q2, option)` with no limit, highlights every row with `re.sub(f"({q2}?)", ...)`, then trims to 100. The message shows `len(results)` before the trim.
3. Regex reaches SQLite through SQLAlchemy's own sqlite `REGEXP` (Python `re`, case-sensitive, no time limit). The engine-wide `REGEXP` listener in `tools/tipitaka_db.py::sqlite_engine_connect` (which says case-insensitive) is dead code: SQLAlchemy's function replaces it, so `'X' REGEXP 'x'` is 0 on both databases (verified). The highlight `re.sub` has no time limit either. Plain-search highlight does not escape q2.
4. `exporter/webapp/main.py::tt_search` runs `search_all_cst_texts` / `search_books` with no limit, then slices to 100. `total` in the JSON is the full count. Books are not deduplicated. An empty `q` is not rejected on the server (the browser rejects it).
   `tools/tipitaka_db.py::search_tables_union` wraps the UNION in `except Exception` and falls back to one query per table. `search_tipitaka` also swallows all errors and returns `[]`.
5. `exporter/webapp/toolkit.py::find_closest_matches` does `ascii_to_unicode_dict[q]` on a `defaultdict`. Each distinct miss adds an empty entry for the life of the process.

## What it should do
- Lookup: escape `\`, `%`, `_` in q before the LIKE match so they match themselves. No row cap (`lookup_key` is unique, so at most 2 rows).
- Failed lookups: read the map with `.get(q, [])`. Do not insert.
- Bold definitions: fetch at most 101 rows. Trim to 100 before highlighting. Show "100+ results found" when 101 come back. Escape q2 in the highlight for the plain option.
- Translations: strip q. An empty q returns an empty result. Deduplicate books, keeping order. Fetch at most 101 rows. `total` becomes 101 when more exist, and the browser shows "100+".
- Regex time limit: one budget per request of 4.0 s of the search's own CPU time (`time.thread_time`), with a 20 s wall-clock backstop. Waiting for a turn uses none of it. A wall-clock budget failed four ordinary full scans at once, all at 4.00 s (found by the pi test agent's finding and a follow-up measurement). A new `REGEXP` function is attached to each bold-definition and translation session (`tools/search_deadline.py::install_regexp`). Inside a deadline it uses the `regex` package with a compiled-once pattern and `timeout=` set to the time left. The highlight substitution does the same. Outside a deadline it copies SQLAlchemy's behaviour exactly (case-sensitive `re.search`), so gui2 is unchanged.
- On timeout, bold definitions show "The search took too long. Use a more specific search." in the existing message slot. Translations return JSON with an `error` text and the browser shows it. A timeout must never look like "no results".

## Assumptions & uncertainties
- Verified: the points above, by reading the code. The translation database is at `resources/tipitaka_translation_db/tipitaka-translation-data.db` (807 MB).
- The user chose a row cap for dictionary lookup in the question round. It was dropped because `lookup_key` is unique and escaping already bounds the rows.
- NOT verified: `regex.search(..., timeout=)` raises on a really slow pattern. A probe with `(a+)+$` finished without a timeout, so the engine may skip that case. The plan proves it with a pattern that does time out.
- NOT verified: the time budget. Starting guess was 2.0 s; measured value is 4.0 s (see plan). A legitimate all-books regex search may need more. The plan measures first.
- NOT verified: sync FastAPI routes keep a context variable inside the worker thread. The plan tests it.
- Python `re` and `regex` differ in rare syntax. The webapp uses `regex` only when the deadline is set, so the same pattern can behave differently in the webapp and in gui2. Verified in review: `[[:alpha:]]` matches nothing in `re` but letters in `regex`; `\p{L}`, `(?<=a+)b`, `[a-\d]` and a mid-pattern `(?i)` fail in `re` but work in `regex`.

## Constraints
- gui2 callers (`gui2/dpd_fields_commentary.py`, `gui2/translations_view.py`) must behave as before: default `limit=None`, no deadline.
- `uv add --no-sync regex`, then `uv sync --all-groups`. Run `just deps`.
- Each touched file must pass `ruff check`, `ruff format`, `pyright`.

## How we'll know it's done
- A search for `%` returns "no results" and loads no extra rows.
- A broad bold-definition search loads 101 rows, not all.
- A slow regex stops at the budget. A second request sent at the same time answers normally.
- A translation search with an empty q or duplicate books returns correctly. A broad one loads 101 rows.
- A run of 1000 distinct misses leaves the map at the same size.
- Tests fail with the fix reverted.

## What's not included
- Archive extraction hardening, HTML rendering of database text, status-page query history (the issue lists them as separate concerns).
- A length cap on q beyond the pattern limits below. Escaping `%` and `_` in the plain bold-definition SQL match (the row cap covers it).
- The per-table fallback in `search_tables_union` (reached only when the UNION query fails) still loads whole tables before the limit applies.

## Added after review (hardening round 2)
The user ruled that every server or memory problem is fixed in this thread, none deferred.
- Pattern guard: a pattern longer than 2000 characters, or whose `length x product of all {n}/{n,m} counts` exceeds 100,000, is refused before it is compiled. The `regex` package expands counted repeats, so `(?:a{3000}){3000}` (17 characters) needs 2.4 GB. A bad or refused pattern shows "That search pattern is not valid." or "That search pattern is too complex. Use a simpler pattern." in both the bold-definition and translation searches.
- Regex searches take turns: one runs at a time, up to three wait their turn (up to 10 s), anyone beyond that or still waiting after 10 s sees "The server is busy. Try again in a moment." Measured: one full scan costs 1.4 s alone, but two at once cost 3.8 s each, three 9.0 s and four 17.8 s, because the REGEXP callbacks fight over Python's global lock.
- Compiled patterns are cached 4 at a time, not 16.
- Tar extraction uses the `data` filter. The translation database unzip extracts only the database file.
- Not changed, with evidence: see the plan, Phase 5.
- Huge numbers: a dictionary query, a page address or an audio Range header with a very long digit string must not give a server error (measured: all three returned 500).
- The translation fallback path takes the same row cap as the main path.
- An adversarial battery of at least 20 hostile patterns must finish within 6 s each and within a 1 GB memory cap, in a child process.
- The translation search now passes the pattern to SQLite as a bound value. Before, it was pasted into the SQL text, and SQLAlchemy read a regex group such as `(?:abc)` as a missing parameter, so every such search fell back to the slow per-table path (found by a test in round 2).
- Recursion and group calls of the regex package (`(?R)`, `(?1)`, `(?&x)`, `\g<x>`) are refused: they run out of memory within half a second, faster than the time budget can stop them. Fuzzy matching (`{e<=1}`) is not refused: measured worst cases stay near 32 MB and the budget ends the slow ones.
- Not in scope, decided by evidence: see the plan, Phase 5.
- Dictionary lookups (`/search_json`, `/search_html`, `/gd`) take turns too: 2 run at a time, up to 20 wait up to 20 s (two heavy lookups finish together in about 1.9 s, so a 20 s wait drains about 20), anyone beyond that gets HTTP 503 with `Retry-After: 10`, the busy text, the normal JSON shape for `/search_json`, and the same cross-origin (`Access-Control-Allow-Origin`, `Access-Control-Expose-Headers`) and licence `Link` headers as a normal answer. Only GET requests take turns, so a browser preflight (OPTIONS) is answered at once. Measured: 8 lookups took 6.7 s one at a time and 16.7 s all at once; 40 at once held the server 115 s.

