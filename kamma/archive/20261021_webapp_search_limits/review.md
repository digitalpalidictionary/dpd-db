## Thread
- **ID:** 20261021_webapp_search_limits
- **Objective:** Add server-side memory, row and time limits to the webapp searches and lookups (GitHub issue #268), and close every server or memory hole found along the way.

## Files Changed
- `exporter/webapp/main.py` — `/bd_search` and `/tt_search` limits, stop messages, digit-safe page address and Range header, lookup turn-taking middleware.
- `exporter/webapp/toolkit.py` — escaped `%`/`_` in the lookup, `.get` on the ascii map, 18-digit id guard.
- `exporter/webapp/static/tipitaka_translations.js` — "100+" count and server error text.
- `tools/search_deadline.py` (new) — CPU-time budget, pattern guard, recursion rule, one-at-a-time regex queue, `install_regexp`.
- `tools/tipitaka_db.py` — `limit` everywhere, bound pattern, stops re-raised, fallback capped.
- `tools/bold_definitions_search.py`, `tools/tarballer.py` — deadline REGEXP; tar `data` filter.
- `resources/tipitaka_translation_db/download_and_unzip_db.py` (submodule) — extract only the database file.
- `docs/technical/api_endpoints.md`, `pyproject.toml`, `uv.lock` — contract text; `regex`, `starlette`, `anyio` declared.
- 9 new test files under `tests/exporter/webapp/` and `tests/tools/`.

## Findings
Reviews, in order: (1) independent zero-context subagent; (2) a second independent reviewer (user-supplied); (3) three live test rounds by the pi agent "server test review"; (4) the implementer's own probes. No blocking or major finding is open. Notable findings and outcomes:
| # | Severity | Where | What | Outcome |
|---|----------|-------|------|---------|
| 1 | blocking | `search_deadline.py` | The `regex` package, added for the time limit, compiled `(?:a{3000}){3000}` into 2.4 GB (6.5 GB on the real route) | Fixed: pattern length and repeat-cost guard before compile |
| 2 | major | `search_deadline.py` | Recursion patterns (`(?R)`, `((?1))`) ran out of memory in 0.5 s, faster than the budget | Fixed: recursion rule (fuzzy rule tried, then removed on evidence) |
| 3 | major | `search_deadline.py` | Wall-clock budget failed 4 ordinary scans at once; concurrent searches fight over the global lock (1.4 s alone, 17.8 s each at 4) | Fixed: CPU-time budget, one running + 3 waiting |
| 4 | major | `main.py` | Same collapse for dictionary lookups (40 at once held the server 115 s) | Fixed: 2 running + 40 waiting, then HTTP 503 |
| 5 | major | routes | Huge digit strings gave 500s (query, page address, Range) | Fixed |
| 6 | minor | `tipitaka_db.py` | `:a` in `(?:abc)` sent translation searches down the slow fallback | Fixed: bound parameter |
| 7 | minor | `tarballer.py`, downloader | Unfiltered extraction | Fixed |
| 8 | minor | various | Test gaps and one over-claiming test | Fixed |
| 9 | major | `main.py` | The busy 503 skipped the CORS middleware, so a page on another site could not read it | Fixed: headers added to the busy answer |
| 10 | major | `main.py` | A browser preflight (OPTIONS) waited in the lookup line for up to 20 s | Fixed: only GET takes turns |
| 11 | minor | `main.py` | Waiting line of 40 could not drain in the 20 s window | Fixed: 20, `Retry-After` 10 |
Declined with evidence (in plan): merging exception classes; `--limit-max-requests`; caching the per-session engine (hazard: shared threads, write-ahead mode on the translation db); `x4` budget.

## Fixes Applied
- All of the above, each written test-first with the failing output recorded in `plan.md`.

## Test Evidence
- `uv run pytest tests/` (scope: whole suite) → 2348 passed before the round 6 fixes, 2350 passed, 12 deselected after them (the two new tests); `just typecheck` 0 errors, ruff clean.
- `just typecheck` (scope: whole repo) → 0 errors. ruff check, ruff format, pyright on 16 touched files (tests via `--project /dev/null`) → clean.
- Hostile-pattern battery, 45 patterns, each in a 1.2 GB-capped child process → 0 crashed, slowest 2.0 s, most memory growth 3 MB.
- Each fix reverted alone (about 28 reverts across rounds, files restored) → each fails at least one test.
- Real data: 4 full scans at once 1.3/2.6/3.9/5.2 s, 6 at once serves 4 and refuses 2 instantly; 40 heavy lookups at once 22 s (was 115 s), `/status` 0.10 s, memory +15 MB.
- pi agent live rounds 1-3 (server restarted each time): all requested checks passed; 190 tests passed in its last run.
- User ran the browser checks by hand (round 1) and reported all passed.

## Not Verified
- The pi agent reviewed the lookup turn-taking (round 6) and found the two defects above. The fixes were checked by the implementer's tests and revert checks only; the pi agent did not re-test after them, and the live flood was not repeated after them.
- CodeRabbit was not run (repo rule needs the user's permission; none given).
- gui2 checked by reading its callers and the full suite only; the GUI was not run.
- HTML shown from database text (script injection) is not changed: not a memory or server fault; user to decide.
- Rate limiting per visitor needs the web server in front (nginx); no code here can do it.
- The submodule change is uncommitted in its own repository.

## Verdict
PASSED
- Review date: 2026-10-22
- Reviewer: independent subagent, a second independent reviewer, the pi agent (4 rounds); verdict written by the implementer at the user's instruction after extensive re-review
