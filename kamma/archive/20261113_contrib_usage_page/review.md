# Review: contributor dashboard

Verdict: **PASSED**

The reviews ran during the thread; this file collects them. Details per round are in `plan.md`.

## Files changed

- `gui2/assets/icons/loading-animation.png` (new)
- `scripts/server_contrib/NEW_SERVER_RUNBOOK.md`
- `scripts/server_contrib/README.md`
- `scripts/server_contrib/contrib_dashboard.py` (new)
- `scripts/server_contrib/nginx_dashboard.conf.template` (new)
- `scripts/server_contrib/pages/asleep.html`
- `tests/scripts/server_contrib/data/dashboard_journal.jsonl` (new)
- `tests/scripts/server_contrib/test_contrib_dashboard.py` (new)

## Round 1 — first version (CodeRabbit + an independent Claude reviewer)

- Fixed: overlapping cron runs shared one temp file; a process that died without a `Started` line left its visit open; the 10-second auto-restart after sleep showed the lane as down; journalctl's exit 1 on no matching unit stopped the page.
- Not fixed, recorded in the spec: a hard power loss counts as time online until the next boot.

## Round 2 — period toggle and saved history (CodeRabbit + pi DeepSeek, deepseek-flash, thinking off)

- Fixed: a recent day the journal read did not cover (or a failed read) was erased from the saved history; bad text in the saved file was not caught; a failed save stopped the page; the set-aside rename could crash or overwrite an older damaged copy; no test ran `main()`; the All note showed the 1st of the month.
- Not fixed: Day/Week minutes and the bars can differ by under a second a day; the 4 % minimum bar height is on purpose; style nits.

## CPU meter (after round 2)

- No external reviewer. The meter now shows busy share since the previous run instead of the load average. Guarded by 2 tests; putting the load figure back fails 1.

## Test evidence

- `uv run pytest tests/scripts/server_contrib/test_contrib_dashboard.py`: 39 passed.
- Every fix was proven by undoing it once: each undo failed its test.
- ruff, ruff format, pyright (and `pyright --project /dev/null` on the test file) and `just typecheck`: clean.
- Live: `/dashboard/` answers 401 without a login; cron rewrites the page every minute with an empty cron log; the owner viewed the page.
