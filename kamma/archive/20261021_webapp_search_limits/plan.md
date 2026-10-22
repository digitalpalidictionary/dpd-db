# PLAN — Server-side limits for webapp searches
GitHub issue: https://github.com/digitalpalidictionary/dpd-db/issues/268

## Summary
- Dictionary lookup: `%` and `_` stop acting as wildcards. This removes the load-every-row case.
- Failed lookups: stop adding empty entries to the shared map.
- Bold definitions: load 101 rows at most, highlight only the 100 shown.
- Translations: check input on the server, drop duplicate books, load 101 rows at most.
- Regex: one time budget per request. A slow pattern ends with a clear message, never a silent "no results".
- gui2 is unchanged.

## Architecture Decisions
- One small module, `tools/search_deadline.py`, holds the context variable, the deadline check and a `regex`-based `sub`. Both `tipitaka_db.py` and the webapp use it. No change to gui2.
- Limits are fetch-limit-plus-one, so no second count query runs.
- A timeout raises a named error that is re-raised through the existing catch-all blocks.

## Phase 1 — Dictionary lookup and failed lookups
- [x] Write a failing test: with q="%" the lookup match returns 0 rows. Also a test that 1000 distinct misses leave `ascii_to_unicode_dict` the same size.
  → verify: run `uv run pytest tests/exporter/webapp/test_search_limits.py`; paste both failure outputs into this file before any fix.
    Failure output before the fix (6 failed, `tests/exporter/webapp/test_search_limits.py`):
    ```
    WildcardMatch: query '%' loaded key 'a'
    WildcardMatch: query '_' loaded key 'a'
    WildcardMatch: query 'd%' loaded key 'da'
    WildcardMatch: query '%%' loaded key 'a'
    WildcardMatch: query 'dhamm_' loaded key 'dhamma'
    AssertionError: assert ['kamma', 'zz...zzmiss4', ...] == ['kamma']  (1000 more items)
    ```
    The test aborts at the first non-exact key, so a failing run cannot fill memory.
- [x] In `toolkit.py`, escape `\`, `%`, `_` and pass `escape="\\"` to both `.ilike()` calls.
  → verify: the `%` test passes; searching "dhamma" and "kata 5" still return results via `TestClient` on `/search_json`.
- [x] In `find_closest_matches`, use `ascii_to_unicode_dict.get(q, [])`.
  → verify: the miss test passes.
- [x] Phase check: `ruff check --fix`, `ruff format`, `pyright` on both files; run the new test file.
  → verify: all clean, tests pass.

## Phase 2 — Deadline helper and bold definitions
- [x] `uv add --no-sync regex`, then `uv sync --all-groups`.
  → verify: `just deps` exits 0; `uv run python -c "import regex"` works.
    Result: `regex>=2026.5.9` added. `just deps` still exits 1 (8 findings), one of them `DEP002 regex unused` until Phase 2 code imports it. Recheck at the Phase 2 check.
- [x] Prove `regex` timeout with a pattern that really times out. Try patterns until one raises; record it in this file.
  → verify: the recorded pattern raises `TimeoutError` within 0.5 s.
    Result: `regex.search(r'^(a|a)+$', 'a'*60+'b', timeout=0.5)` raises `TimeoutError` after 0.5 s. Textbook nested repeats like `(a+)+$` and `^(a*)*$` finish instantly in `regex` (it optimises them), so they are not good test patterns.
- [x] Measure the slowest legitimate searches on the real data: one all-books translation regex, one broad bold-definition regex. Set the budget constant to at least 3× the slowest. Record the numbers (n, median).
  → verify: numbers are in this file; the constant is justified by them.
    Results (fresh process per run, machine load average about 3.4, so treat as upper bounds):
    - Bold definitions, broad regex returning 327,093 rows: 4.69, 4.80, 4.63, 4.60 s (n=4). Almost all of this is loading rows, which the 101-row limit removes.
    - Bold definitions, regex that matches nothing (full scan): 0.57, 0.58, 0.57 s (n=3).
    - Translations, all books, regex that matches nothing (full scan): 1.31, 0.94, 0.91 s (n=3).
    - Translations, all books, "dhamma" (43,555 rows, no limit): 5.98, 5.55, 5.82 s (n=3).
    RE-MEASURED under the deadline (load 0.9, n=3 each, fresh process): old `re` scan 0.27 s (bold) / 0.65 s (translations); `regex` with the pattern re-resolved on every row 1.5 s / 2.2 s (too slow); `regex` with the pattern compiled once (`lru_cache`) **0.53 s / 1.0 s**. The first set of numbers above was taken under load 3.4 and is inflated. Budget 4.0 s is about 4x the slowest scan under the deadline, so it stays.
    Slowest legitimate scan with a limit: about 1.3 s. Budget = 3 x 1.3, rounded up: **4.0 s**.
    Load note: `regex` holds the GIL while it matches unless `concurrent=True` is passed. Pass it, so a runaway pattern cannot starve other requests (the reported `/status` timeout).
- [x] Write `tools/search_deadline.py`: context manager `regex_deadline(seconds)`, `SearchTimeout` error, a `search` function and a `sub` function that use the time left.
  → verify: unit tests for deadline set, deadline unset (plain `re` path), deadline passed, and a context variable seen inside a sync FastAPI route.
    Result: `tests/tools/test_search_deadline.py`, 7 passed.
- [x] In `tipitaka_db.py`, make the `REGEXP` callback use the deadline when set.
    DEVIATION (found by probe): the engine-wide `REGEXP` listener in `tipitaka_db.py` is dead code. SQLAlchemy's own sqlite `REGEXP` replaces it, so `'X' REGEXP 'x'` is 0 on both databases and every regex search is case-sensitive today. The deadline function is therefore attached per session (`install_regexp`), copying today's case-sensitive behaviour. The dead listener is left as found (NOTICED — NOT TOUCHING). Re-raise `SearchTimeout` through `search_tables_union` and `search_tipitaka` instead of swallowing it. Detect it via a flag on the deadline, because SQLite wraps the error.
  → verify: test with a slow pattern and a tiny budget raises `SearchTimeout`, not an empty list; a gui2-style call without a deadline is unchanged.
- [x] In `db_search_bd`: wrap in `regex_deadline`, pass `limit=101`, trim to 100 before highlighting, escape q2 for the plain option, use the deadline `sub`, show "100+ results found" and the timeout message.
  → verify: `TestClient` tests: broad search returns 100 rows with the "100+" message; plain q2 `(` does not error; slow pattern returns the timeout message; a concurrent normal request answers.
    Result: `tests/exporter/webapp/test_bd_search_limits.py`, 5 passed. Emailed requests run live against the app: wildcard search 0.7 s, "No results found", peak memory unchanged at 688 MB; broad plain bold search 0.05 s with "100+ results found"; control regex 200; the starvation pattern finished in 1.5 s and a concurrent `/status` answered in 0.13 s.
    Note: against the real row, `regex` finishes the emailed `^(.+)+Z` instantly (it checks that the literal `Z` exists first), and Python `re` hung on it. The tests use `^(.|.)+[Z!]`, which makes `regex` time out too.
- [x] Phase check: lint, `pyright`, run tests/exporter/webapp and tests/tools/test_db_search_string.py.
  → verify: all pass.
    Result: ruff, ruff format and pyright clean on all 9 touched files; 83 tests pass. `just deps` now reports 7 findings, none about `regex` (the `regex` one cleared).

## Phase 3 — Translation search
- [x] Write a failing test: duplicate books are searched once; empty q returns empty; the search loads at most 101 rows.
  → verify: run the test file; paste failure output first.
    Failure output before the fix (`tests/exporter/webapp/test_tt_search_limits.py`, `tests/tools/test_tipitaka_db_deadline.py`; 6 failed):
    ```
    test_empty_query_is_rejected_by_the_server[]     calls == [] but search ran with {'books': ['dn1'], 'q': ''}
    test_empty_query_is_rejected_by_the_server[   ]  search ran with q '   '
    test_repeated_books_are_searched_once            ['dn1', 'mn1', 'dn1'] != ['dn1', 'mn1']
    test_search_asks_for_one_row_past_the_display_limit[dn1] / [all]   KeyError: 'limit'
    test_limit_stops_loading_rows                    TypeError: search_tables_union() got an unexpected keyword argument 'limit'
    ```
    `test_slow_regex_returns_an_error_not_an_empty_result` could not even finish on the unfixed code: the all-books search ran Python `re` on the slow pattern and the run had to be killed at 250 s. That hang is the reported bug.
- [x] Add an optional `limit` to `search_tables_union`, `search_all_cst_texts`, `search_books` (append `LIMIT n` to the UNION; stop in the per-table fallback). Default `None` keeps gui2 unchanged.
  → verify: the limit test passes; `tests` for gui2's translations view still pass.
    Result: `test_limit_stops_loading_rows` passes (600 rows unlimited, 101 limited). gui2's translations view calls `search_all_cst_texts` and `search_book` without a limit, so it is unchanged; checked in the full-suite run at the end.
- [x] In `tt_search`: strip q, return empty for empty q, deduplicate books, pass `limit=101`, wrap in `regex_deadline`, return `error` on timeout.
  → verify: `TestClient` tests for each case.
    Result: `tests/exporter/webapp/test_tt_search_limits.py`, 6 passed (slow-pattern case now ends at 0.5 s with the error text).
- [x] In `tipitaka_translations.js`: show "Found 100+ results, displaying the first 100." when `total` is over 100, and show `error` text when present.
  → verify: open the app, run a broad search, confirm the text and that the filter counter still reads correctly. Run a slow pattern, confirm the error text.
    Result (real browser via playwright-cli against a test server on port 8099 running the new code): broad search "dhamma" showed `Found 100+ results, displaying the first 100.` with 100 items; typing "bhikkhu" in the filter showed `Showing 62 / 100+ results.`; the slow pattern `^(.|.)+[Z!]` showed `The search took too long. Use a more specific search.` The test server was stopped afterwards.
- [x] Phase check: lint, `pyright`, tests; revert each fix in turn and report how many tests fail.
  → verify: each revert fails at least one test for the stated reason; restore each file by name.
    Result (each fix reverted alone, whole new test set run, file restored in the same script; `git diff --stat` identical afterwards):
    - lookup wildcard escape: 5 failed (all `test_wildcard_characters_only_match_themselves`).
    - failed lookups `.get`: 1 failed.
    - bold fetch limit: 1 failed. Bold plain-highlight escape: 1 failed.
    - bold REGEXP install and translation deadline wrapper: the slow-pattern test hung (killed at 90 s). That is the bug returning.
    - translation duplicate books: 1 failed. Empty query: 2 failed. Fetch limit: 1 failed. Union `LIMIT`: 1 failed.
    - union-level timeout re-raise: 0 failed. It was redundant with the per-table re-raise, so it was removed. Reverting the per-table re-raise fails `test_timeout_is_raised_not_swallowed`.
    Lint: ruff check, ruff format and pyright clean on every touched file.

## Phase 4 — Whole-change check
- [x] Run `just typecheck` and `uv run pytest tests/`.
  → verify: both pass; the repo's `graphify update .` runs clean.
    Result: `just typecheck` 0 errors. `uv run pytest tests/`: 2224 passed, 12 deselected (slow), exit 0. PRE-EXISTING — NOT CAUSED BY THIS THREAD: `just deps` reports 7 findings (conductor tests, icecream in dev group, starlette transitive). NOTICED — NOT TOUCHING: the dead case-insensitive `REGEXP` listener in `tools/tipitaka_db.py`.

## Phase 5 — Hardening round 2 (found after finalize began; user: fix everything that can hurt the server or its memory, defer nothing)
Findings behind this phase: an independent review plus the implementer's own probes.
- BUG INTRODUCED BY THIS THREAD: the `regex` package compiles a counted repeat by expanding it. `(?:a{1000}){1000}` (17 chars) used 277 MB, `(?:a{3000}){3000}` 2.4 GB, `(?:a{60000}){60000}` over 6.5 GB and a 500 error on the real `/bd_search` route. Python `re` compiled all of them in constant memory. The 4 s deadline cannot help: compile runs before the time check and `regex` has no compile timeout. The `lru_cache` of 16 compiled patterns would also keep each one in memory.
- Invalid regex: `/bd_search` returns a server error, `/tt_search` shows "No results found". `MemoryError`/`RecursionError` are also uncaught.
- No limit on how many regex searches run at once.
- Huge numbers give a server error (500), verified on the real routes: a 4000-digit query to the dictionary, a 5000-digit page address, and a 5000-digit audio Range header. Cause: the number overflows SQLite's integer, or Python's 4300-digit conversion limit.
- The fallback in the translation search (reached only if the combined query fails) loads whole tables with no row cap. Probed: a NUL character does not reach it (the combined query handles it), so it is unreachable today, but it is cheap to cap.
- Archive extraction: `tools/tarballer.py::extract_tarball` extracts members unfiltered (path traversal). `resources/tipitaka_translation_db/download_and_unzip_db.py::unzip_file` extracts everything into the downloader's own folder, so a bad zip can overwrite the downloader script.
Decisions on review items NOT changed (with evidence): per-request `Engine` creation in the tipitaka and audio helpers (reviewer measured 200 audio requests: file handles plateau at 5-15, memory flat — wasteful, not a fault); a lookup concurrency cap (40 concurrent `dhamma` lookups added 135 MB on a 625 MB base, so the "OOM on a 2 GB host" claim does not hold: 760 MB is far from 2 GB); `--limit-max-requests` (the start script runs one plain process with `nohup` and no supervisor, so the process would exit at the limit and stay down); `MALLOC_ARENA_MAX` (no measured benefit). HTML shown from database text is a script-injection risk, not a memory or server fault: not in this phase; user to decide.

- [x] Write failing tests first (run the bomb test once under `ulimit -v 1500000`; ~0.6 GB, 0.6 s): a counted-repeat bomb is rejected before compile, an over-long pattern is rejected, an invalid pattern gives a message (bold: no server error; translations: not "No results found"), a real database error is still raised, a fifth concurrent regex search is told the server is busy.
  → verify: run the new tests; paste the failure output here before any fix.
    Failure output before the fix (run under `ulimit -v 4000000`; 23 failed, 32 passed; `tests/tools/test_tipitaka_db_deadline.py` could not even import `SearchStopped`):
    ```
    test_bomb_pattern_allocates_little            AssertionError: child grew by more than 100 MB compiling (?:a{1500}){1500}
    test_search_guard.py (10 more)                AttributeError: module 'tools.search_deadline' has no attribute 'SearchStopped' (new names)
    test_very_long_number_query... [25/4000/5000] assert 500 == 200
    test_very_long_page_address_is_not_found      500, not 404
    test_audio_range_with_a_huge_number...        500
    test_bad_pattern_ends_with_a_message...(bold) OperationalError: user-defined function raised exception (server error)
    test_bad_pattern_returns_an_error...(trans.)  KeyError: 'error' (answered "no results")
    test_tar_member_outside_the_folder_is_refused Failed: did not refuse ../evil.txt
    test_unzip_extracts_only_the_database_file    ['download_and_unzip_db.py', 'tipitaka-translation-data.db'] != ['tipitaka-translation-data.db']
    test_unzip_refuses_a_zip_without_the_database DID NOT RAISE ValueError
    ```
    The 19-digit query passed: it fits SQLite's integer. The cap is 18 digits, one short of the edge.
- [x] `tools/search_deadline.py`: one `SearchStopped` base (timeout, rejected pattern, busy) with a user message; reject patterns over 2000 chars or with `len(pattern) x product of every {n}/{n,m} count` over 100,000; map `regex.error`, `MemoryError`, `RecursionError`, `OverflowError` to a rejected pattern; compile inside the guard in `regexp_search` and `sub`; shrink the compiled-pattern cache to 4; at most 4 regex searches at once.
  → verify: unit tests pass; `(?:a{3000}){3000}` is rejected in under 0.1 s with peak memory growth under 100 MB; a 34-letter word through `fuzzy_replace` is accepted.
    Result: `tests/tools/test_search_guard.py` 36 passed. Also found and closed during this phase: (1) recursion patterns such as `(?R)?` crashed a 1.2 GB-capped child with MemoryError while matching, so recursion and fuzzy matching are refused; (2) the translation query pasted the pattern into SQL and `text()` read `:a` in `(?:abc)` as a missing parameter, so such searches took the slow fallback: the pattern is now a bound value (test `test_pattern_with_a_colon_or_quote_uses_the_combined_query`).
- [x] `exporter/webapp/main.py` and `tools/tipitaka_db.py`: handle any `SearchStopped` in `/bd_search` and `/tt_search`; re-raise a stopped search through the union fallback.
  → verify: route tests pass for bomb, invalid and busy cases; the bold route no longer returns 500 for `(`.
- [x] `tools/tarballer.py`: extract with `filter="data"`. `download_and_unzip_db.py`: extract only the expected database file and refuse any other name.
  → verify: new tests: a tar with `../evil` is refused; a zip with an extra member extracts only the database; existing audio and zip tests pass.
- [x] Huge numbers: dictionary query digits, page-address digits and the audio Range header all answer without a server error. Page address: a custom route converter limited to 18 digits (longer falls through to 404). Query: more than 18 digits is "no match". Range: at most 15 digits per number, otherwise the full file.
  → verify: new tests: 25-digit and 5000-digit dictionary query answer 200 "No results found"; a 5000-digit page address answers 404; a 5000-digit Range answers 200; an ordinary page id and a normal Range still work.
- [x] Fallback cap: `search_tipitaka` takes a `limit` and the union fallback passes the remaining rows to it.
  → verify: new test: `search_tipitaka` on a real table with a match-everything pattern and `limit=5` returns 5 rows.
- [x] Adversarial battery: 20 or more hostile patterns (nested repeats, alternation, lookarounds, back-references, recursion, Unicode classes, deep nesting, big counts) each run in a child process capped at 1 GB, against a 20 KB text; each must finish in under 6 s and either return or be stopped.
  → verify: the battery passes; the result table (pattern, outcome, seconds, memory growth) is pasted here.
- [x] Docs and notes: API page error texts; spec "not included" list corrected; plan results.
  → verify: read the diff of the docs.
- [x] Phase check: ruff check, ruff format, pyright on every touched file, `just typecheck`, full `uv run pytest tests/`; revert each new fix once and count failures (bomb tests under the 1.5 GB cap).
  → verify: results recorded here.

Phase 5 results (final check: ruff check, ruff format, pyright on 15 files clean; `just typecheck` 0 errors; `uv run pytest tests/` 2330 passed, 12 deselected):
- Adversarial battery (`tests/tools/test_search_battery.py`, 45 hostile patterns, each in a child process capped at 1.2 GB, 3 at a time): 0 crashed; slowest 2.0 s (the time budget, `(\w+\s?)*$`); largest memory growth 3 MB. Before the recursion rule: 3 crashed with MemoryError (`(?R)`, `(?R)?`, `(?0)*`).
- Each new fix reverted alone (12 reverts, whole new test set, 4 GB cap, files restored): cost cap 6 failed; recursion/fuzzy rule 17; length cap 1; busy limit 1; dictionary digit cap 3; permalink digit cap 1; audio Range cap 1; bold route stop guard 1; tar filter 1; zip database-only 1; bound pattern 3; single-table limit 1.
- One test claimed too much and was corrected: 900-level nesting compiles or is refused depending on the Python recursion limit at that moment (another test changes it). Both are safe, because the 2000-character cap bounds the depth.
- The submodule `resources/tipitaka_translation_db` holds one changed file (`download_and_unzip_db.py`). It needs its own commit in that repository.
- `just deps`: 6 findings now (7 before this thread). `regex` and `starlette` are declared as direct dependencies; the new `starlette` import in the webapp main file would otherwise have added a finding.

Round 3 (finding from the pi test agent, 2026-10-22):
- Agent finding: with `concurrent=True` the regex package times a single match by process CPU time, so four runaway matches in four threads all stopped at 1.05 s, not 4 s. CONFIRMED by measurement (1 thread: 4.00 s; 4 threads: 1.05 s). Agent proposal: multiply the budget by 4. DECLINED: the timeout applies to one row at a time (microseconds), so ordinary scans are not affected by it, and a x4 wall budget would let one runaway search run 16 s.
- What the follow-up measurement found instead: four ordinary full translation scans at once ALL stopped at "took too long" at exactly 4.00 s. Real cause: concurrent searches fight over Python's global lock. One scan: 1.4 s wall, 1.3 s CPU. Two at once: 3.8 s wall, 2.7 s CPU each. Three: 9.0 s, 4.9 s. Four: 17.8 s, 7.7 s. So four at once is slower than four in a row (5.6 s).
- Fix: the budget is the search's own CPU time (`time.thread_time`) with a 5x wall backstop; one search runs at a time, up to three wait up to 10 s, the rest are told "busy" at once.
- Real-data result after the fix: 4 full scans at once finish at 1.3, 2.6, 3.9 and 5.2 s, none stopped; 6 at once: 4 served, 2 told "busy" in 0.0 s.
- Tests written first: two fake-clock tests (CPU not wall; wall backstop), three queue tests, one test with four real scans in threads. Before the fix 2 of them failed (waiting used the budget; four scans at once timed out). Reverting each new piece alone: queue allows many 4 failed; budget on wall time 1 failed; no wall backstop 1 failed; no waiting 2 failed.

Round 4 (opinion from the pi agent, 2026-10-22, evidence-checked, one item changed):
- "Recursion/fuzzy rule is over-engineered, the budget already bounds it": half right. Measured under a 1.2 GB cap with only the time budget: `(?R)`, `(?R)?`, `(?0)*`, `(?P<x>(?&x)a?)`, `((?1))` all hit MemoryError in 0.4-0.6 s at 550-780 MB, far faster than the 4 s budget, so the recursion rule STAYS. Fuzzy patterns (including 7 non-matching worst cases) never exceeded 32 MB; the slow ones ended at the 4.00 s budget, so the fuzzy rule and its `\p{L}` exception are REMOVED. Test added: a slow fuzzy pattern is ended by the budget alone.
- "Collapse the exception classes": DECLINED. Behaviour is identical, tests tell causes apart by type, and the saving is about 15 lines of churn.
- "Wrong: 4 slots with the budget accounting": already fixed in round 3 (one search runs, three wait, CPU-time budget); a legitimate 1.3 s scan survives a full house (measured 1.3, 2.6, 3.9, 5.2 s).
- "Delete the semaphore once nginx exists": DECLINED. `limit_req` limits requests per client; it cannot make searches take turns. The slowdown with 4 at once (17.8 s each against 1.4 s) happens regardless of how many clients send them.

Round 5 (second pi review, 2026-10-22; findings F1-F4 checked):
- F1 (two clocks disagree): confirmed and harmless (stops early, never late). Comment added in `tools/search_deadline.py::regexp_search`.
- F2 (nothing bounds the non-regex routes): CONFIRMED by a new measurement, and worse than the memory figure: lookups also lose throughput to the global lock. 8 lookups: 6.7 s one at a time, 7.6 s two at a time, 12.3 s four, 16.7 s eight. 40 at once on the live server: 115 s per wave. Fix: dictionary lookups take turns (2 running, 40 waiting up to 20 s, then HTTP 503 busy) in a middleware using `anyio.CapacityLimiter`; waiting costs no thread. Result on a test server, same 40 lookups: 22 s total, 22 served, 18 busy after 20 s, `/status` 0.10 s throughout, memory +15 MB (before: +130 MB).
- F3 (memory ratchet): NOT a ratchet. Two waves of 40 lookups on the live server: 664 -> 665 -> 668 MB. Settled allocator memory, bounded by the thread pool (40 x ~2 MB). `--limit-max-requests` still rejected: the start script runs one plain process, which would exit and stay down. A memory ceiling on the borrowed server belongs in its service settings, outside this repository.
- F4 (new Engine per translation session): DECLINED, with a reason. Caching it is not a safe drive-by: a shared pooled connection would be used from several threads (the sqlite default forbids it), and the cached helper in `db/db_helpers.py` turns on write-ahead mode, which would change the 807 MB translation database on disk. File handles stay at 21-29 (measured by the review). Pre-existing, not part of this issue.
- Test note: the lookup tests share one `TestClient` used as a context manager. Separate clients each run their own event loop, and a waiting request is not woken from another loop (the real server has one loop). That cost one wrong 5 s trace before it was understood.
- Lookup turn-taking reverted one part at a time (8 tests in `tests/exporter/webapp/test_lookup_turns.py`): full-queue check removed 3 failed; turn not given back 2 failed; wait never times out 1 failed; `/gd` not limited 1 failed. Files restored; `anyio` declared as a direct dependency (`just deps` 6 findings, 7 before this thread).

Round 6 (third pi review, of the lookup turn-taking, 2026-10-22):
- Passed live: 40-at-once flood (22 served, 18 busy, 21.3 s; `/status`, `/audio` and `/bd_search` answered in under 0.11 s throughout); the busy body has the exact JSON the page reads; a slow client reading a large page does not hold a turn; 30 aborted waiting requests leaked nothing; 99 tests passed.
- F1 (defect): the busy 503 skipped the CORS middleware, so a page on another site got a CORS error and could not read the message. FIXED: the busy answer carries `Access-Control-Allow-Origin`, `Access-Control-Expose-Headers: Link` and the licence `Link` header itself. F2 (licence header missing on the 503): same fix.
- F3 (defect): a browser preflight (OPTIONS) waited 19.9 s in the line. FIXED: only GET requests take turns.
- F4 (tuning): confirmed. Two heavy lookups finish together in about 1.9 s, so a 20 s wait drains about 20. `LOOKUP_MAX_WAITING` 40 -> 20 (longer waiting lines only made visitors wait 20 s and then be told busy); `Retry-After` 5 -> 10.
- F5 (memory 538 -> 585 MB after flood and probing, not returned): allocator retention, the limiter recovers and file handles plateau. No change. F6 (new Engine per translation session): pre-existing, declined earlier with a reason.
- Tests written first (2 failed before the fix: no cross-origin header; the preflight got 503). Each fix removed alone fails one test: no cross-origin header 1, no licence link 1, preflight throttled 1. I did not repeat the live flood after the fix, on the user's instruction; the measured numbers above stand.

