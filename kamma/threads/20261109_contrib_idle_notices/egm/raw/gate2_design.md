Findings (design critique). Word budget spent on problems only.

## Blockers

**1. Clock source unstated / unbounded — the pure decision function's inputs are underspecified.**
A.5 says "now"; B.4 says "whole minutes left". Evidence: `scripts/server_contrib/maintenance_window.py:517` (`datetime.now()`) and the spec's `stop_at` as "UTC ISO-8601". Implementation invents: monotonic vs wall clock. If the watcher uses `time.monotonic()` for idle (correct — NTP says nothing) but parses `stop_at` as wall clock, then a step change (or the 30-minute window crossing an NTP correction) makes minutes-left jump backwards, re-firing "Got it"-dismissed steps and a red banner reappearing. Fix: name the two clock domains explicitly; compute minutes-left from `datetime.now(UTC)`, idle from `time.monotonic()`, and define the rule when the computed minutes-left *increases* (reset dismissal state? re-show?).

**2. Notice file left behind — B.1's 2-hour staleness rule collides with the process lifetime.**
`read_notice()` returns `None` when the stop time is >2h past. A crash during the window leaves `notice.json` with a stop time already past; next evening a fresh run overwrites it, fine. But the *server agent* rolling back git (`rollback.pre_commit`) can revert `maintenance_window.py` to a pre-feature version that never writes or deletes the notice, while the new gui2 keeps reading the stale file for up to 2 hours each night — banners at 30/15/10/5/1 pointing at a stop that already happened. Fix: state whether the notice is versioned with the window, and have B.4 treat "stop_at is in the past by <0" as an active countdown only when the file's mtime is within N minutes (or write a `pid`/`run_id` into the JSON — the format is described as extensible at "What's not included" but nothing consumes it).

**3. Two windows / one process — page-connection bookkeeping is undefined.**
A.5's branch "No page connected … sleep at once" needs a per-process *set* of held pages. The spec never says who adds/removes entries, and Flet re-creates a `Session` on reconnect only when `candidate.connection is None` (`flet_web/fastapi/flet_app.py:284-289`), else a fresh `Session` is made (`:296`). So a page that reloads yields a new `Session` while the old one lingers until expiry — a retired-page set that "grows" as the spec warns, but with no removal predicate given. Fix: define connection state as `page.session.connection is not None` sampled by the watcher, define retirement (session expiry / `disconnect` dispatch), and cap the set.

**4. Thread safety is asserted, not designed.**
A.5: one daemon thread; A.6 calls `UrlLauncher().launch_url(...)` from it. `flet/messaging/session.py:559-569` shows `after_event` mutating `page._services` and context vars; `__send_message` (`:613-624`) appends to `__send_buffer` when `__conn` is `None`. Calling into a Session off the loop races the event-loop task that set `connection = None` in `disconnect` (`:206-221`). Fix: specify that all Flet calls go through `asyncio.run_coroutine_threadsafe(..., page.loop)` (`page.py:1336-1343`) and that the watcher only mutates plain attributes.

**5. nginx regex vs prefix — C.3 is wrong as written for the 502 path.**
`scripts/server_contrib/nginx_contrib_user.conf.template:9` `error_page 502 503 504 /@USER@/_dpd/offline.html` points at a URI that the *regex* location is claimed to win. But `alias /var/www/dpd-pages/$1.html` in a regex location captures `$1` from `location.pathname`-shaped URIs only if the request is not internally redirected into the prefix block's auth chain. `auth_request /_dpd_pw_check` is only in the prefix block, so the regex page is unauthenticated (intended) — but C.4's per-user `error_page` fires *after* auth, and internal redirects re-run location matching, so an unauthenticated 502 retry against `.../_dpd/offline.html` will hit the regex (no auth) — fine — while a request for the *same* path typed directly also skips auth. Nothing states the regex must be declared **before** `include /etc/nginx/dpd/*.conf`; `nginx_contrib.conf.template:12` puts `include` first, and the spec says only "one regex location" with no placement rule. Regex vs prefix precedence is not order-dependent, but **two** regexes and the `^~` modifier are; state the placement and add a test with `nginx -T`.

## Majors

**6. "Two windows" — `run_maintenance` writes the notice *inside* the `try` after `_systemctl("stop")` is already called at `maintenance_window.py:519` (spec B.2 says "before it stops anything", but the current code stops first, outside the try). An implementer must move the stop; the spec's B.2 wording reads as satisfied by the existing order. Fix: name the exact reordering and that `stop_failed` early-return (`:523-528`) now happens after the warning wait.**

**7. Page connecting during the countdown — unhandled.** A.5 has no branch for "countdown showing, page count went to zero" (tab closed) or "countdown showing, new page connects". B.4 says a late page "gets the current step at once", but A.5 says nothing for the countdown. Fix: one more row in the decision table.

**8. `os._exit(0)` at A.6 races the send queue.** `send_message` (`flet_app.py:410-426`) only enqueues; the 3 s sleep is the only flush guarantee, and a 943 MB process under swap may not flush in 3 s. Unstated fallback.

**9. `--warn-minutes` wait is unbounded and untested against `STEP_TIMEOUT`.** A 30-minute `time.sleep` inside `run_maintenance` before `_capture_rollback` means the dirty-tree check (`:531`) runs 30 minutes later than today; the spec doesn't say whether the check moves too, so a contributor edit made during the warning window changes behaviour.

## Nits

- A.4 kill switch via `/etc/dpd/<user>.env` requires a unit restart — that restart itself drops the editor with no warning; not stated.
- D: asleep-page "N seconds" is a placeholder the plan must fill; if the measurement task slips, the page ships with a guessed number, contradicting "The spec does not guess it."
- E: no `lifecycle:` line for the notice file being *unreadable* vs *absent*, though B.1's four `None` cases are indistinguishable to the operator.