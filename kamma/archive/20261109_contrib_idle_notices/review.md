## Thread
- **ID:** 20261109_contrib_idle_notices
- **Objective:** contributor server: idle sleep, nightly-update banner and offline pages (#215)

## Files Changed
- `gui2/server_lifecycle.py` — new: idle sleep, countdown, banner, move to the static pages
- `gui2/main.py`, `gui2/ui_utils.py` — attach on web sessions on the server; banners do not block shortcuts
- `tools/contrib_notice.py` — new: notice file format and path
- `scripts/server_contrib/maintenance_window.py` — `--warn-minutes`, `--notice-file`, 25 s grace, notice removal
- `scripts/server_contrib/pages/asleep.html`, `offline.html` — new static pages (offline: no button until the editor answers)
- `scripts/server_contrib/dpd-gui@.service`, `nginx_contrib.conf.template`, `nginx_contrib_user.conf.template` — restart always, page location, 502 error page
- `scripts/server_contrib/README.md`, `NEW_SERVER_RUNBOOK.md`, `kamma/tech.md` — cron 00:30, pages step, new tech entry
- tests under `tests/gui2/`, `tests/tools/`, `tests/scripts/server_contrib/` — new and extended
- thread folder: spec, plan, artifacts (probe, local check, server rollout log, done list, screenshots), egm notes

## Findings
Reviewers: DeepSeek flash through its own API (no tools, thinking off, eight pieces of 7–16 KB, streamed; piece 1 was rerun because the first answer was a refusal) and CodeRabbit (one whole-thread run against the base commit: **0 findings**). An earlier Claude subagent was cancelled by the owner and gave no findings.

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `NEW_SERVER_RUNBOOK.md`, `done_list.md` | done-list item 4 read "Met" although it rested on a hand-started copy and a manual stop, not a window run | overstated evidence | rewritten as "met by substitution" with the three pieces named; item 3 and 6 wording tightened; "nothing open" replaced by four specific gaps |
| 2 | major | `kamma/tech.md` | an older bullet still said the cron runs at 01:00 | an operator could reinstate the race | now 00:30 with the 01:00 stop |
| 3 | minor | `maintenance_window.py` vs `server_lifecycle.py` | the 25 s grace is tied to the editors' 15 s check in another module with nothing linking them | a longer tick would silently break the offline move | test `test_the_window_waits_longer_than_one_editor_check_plus_the_flush` (fails when the grace is 10) |
| 4 | minor | tests | guards missing: `apply_patch` becoming async; banner staying open after a shortcut and after Escape; amber to red boundary; negative minutes; defaults without the flags; wait ran before a failed pull | tests could stay green on wrong behaviour | all added; the red boundary and grace tests were reverted to confirm they fail |
| 5 | minor | `offline.html` | first check only after 15 s | a person landing just after the editor returns waits | early check after 3 s (test pins it; reverted to confirm) |
| 6 | minor | docs | `--notice-file` help did not say editors read the default path; docstring omitted the no-page fast sleep and the env switch; runbook check only proved the placeholder was gone; duplicate 5.9 heading; 5.3 partial never closed | misleading text | all corrected |
| 7 | minor | spec | a window killed hard while waiting leaves a future notice | wrong offline move in that rare case | recorded under Known risks, not guarded |

Rejected after reading the code (reasons in the spec "Review record" and here): "countdown then stop time sends the asleep page" (the notice is handled before idle in every tick and `offline_sent` stops idle); lock races on dict writes (no iteration, scalar writes under the GIL); `id(page)` reuse (entries are removed with the page); `attach` twice per session; "I'm here" not touching (the click is an event, and a live run cancelled it); error page re-entering the auth location (a regex location wins, seen live); poll reads the error page as 200 (nginx keeps the status; the owner saw no button while the editor was down); a failed notice write stopping blind (spec B.2: the stop stays on time).

## Fixes Applied
- All rows 1–7 above. No change to the editor's behaviour; one change to a static page (early check), installed on the server.

## Test Evidence
- `uv run pytest tests/gui2/ tests/tools/ tests/scripts/server_contrib/ -q` (scope: whole related folders, 7 slow tests deselected) → 1902 passed
- `uv run pytest tests/ -q` (scope: whole repo, after all fixes, 12 slow tests deselected) → 3164 passed
- `just typecheck` (scope: whole repo) → 0 errors
- `uv run ruff check`, `ruff format`, `pyright` on every touched Python file (gui2 and tests with `--project /dev/null`) → clean
- Revert checks (code or fix removed, new test must fail): grace 25 to 10, red threshold 5 to 6, early page check removed, notice removal, offline override, chmod, step-memory reset, strict `run_task` fake → each failed the named test, then restored
- Live: local real-Chrome and headless runs, a server run through nginx, a real night window, a live banner test, a live stop and start (`artifacts/`)

## Not Verified
- A banner on a real unit during a real window (nobody had a page open on new code the first night); the offline move at the stop inside a real window.
- One unexplained first idle test on 2026-11-09 where a connected tab never got the countdown; two later runs worked.
- The button appearing after a full 30 to 55 minute update; seen only after a short stop and start.
- CodeRabbit's reviewed scope (base commit versus working tree) is as its tool reports; I did not confirm it covered the uncommitted files.

## Verdict
PASSED
- Review date: 2026-11-10
- Reviewer: DeepSeek flash (API) and CodeRabbit; findings triaged and fixed by the implementing Claude session, model: claude-sonnet-5-5
- Independence: full for finding generation (separate models, no shared context); reduced for triage and fixes (same session as the implementer)
