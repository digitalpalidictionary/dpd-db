# Task 3.5 local live check (2026-11-09)

Setup: gui2 web, `DPD_GUI2_ROLE=contributor-server`, scratch data folder, `DPD_GUI2_IDLE_MINUTES=1`, port 8651, headless Chromium. Screenshot of the countdown: `live_countdown.png`.

| Step | Result |
|---|---|
| Process start line | PASS: `lifecycle: process start: pid …, user probeuser, idle 1 min (env)` then `page connected` |
| Countdown after about 1 min idle | PASS: `countdown shown after 1.1 min idle`; dialog "Still there?" on screen |
| "I'm here" cancels | PASS: log `countdown cancelled`, dialog gone |
| Countdown left alone | PASS (second run, after the fix below): `asleep: 3.1 min idle, 1 page(s) sent away, connected=True`; the tab URL became `http://127.0.0.1:8651/_dpd/asleep.html` (404 locally, no nginx); process exit code 0; no process left |
| Log order | PASS: process start, page connected, app built, tabs ready, notice file: absent, countdown shown, (countdown cancelled), asleep |

## Bug found by this check

First run: the log said `could not reach a page: handler must be a coroutine function`. The navigation used a lambda, and `page.run_task` refuses anything but a coroutine function. The process exited, but the tab did not move. The unit-test fake page had accepted any callable, so tests passed. Fixed in `gui2/server_lifecycle.py` (`_navigate`); the fake page in `tests/gui2/test_server_lifecycle.py` now raises the same `TypeError`. With the old code restored, 2 tests fail.

## Seen, harmless

Right after the `asleep` line the tab tried to reconnect and built a page in the dying process ("page connected", "App initialized in 0.93s"), with Flet websocket errors in the log. The tab still ended on the asleep page. On the server the process restarts 10 s later, so the tab is already on a static page.

## Not checked locally

- A hidden browser tab: whether tab hide or focus events count as activity (the probe saw `app_lifecycle_state_change` events on navigation). Check on the server in 5.6.
- The banner (no `/var/lib/dpd` on the laptop): covered by unit tests, checked live in 5.7.
