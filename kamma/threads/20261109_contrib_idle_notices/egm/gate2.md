# Gate 2 — spec review

Backend: pi, DeepSeek API (`--provider deepseek --model deepseek-flash --thinking off --mode json`), 2 reviewers in parallel. Both returned on the first attempt (636 and 902 words).

## Raw findings

### comprehension

I have enough to report. Findings below.

## Restatement

On the contributor web server only, gui2 should watch one global "last user action" clock fed by every client event Flet dispatches. After 30 idle minutes it shows a "Still there?" dialog with a 2-minute cancel window; when that expires (or immediately if no page is connected) it navigates every page the process holds to a static asleep page and `os._exit(0)`, and systemd restarts an empty process. Separately, the nightly maintenance job writes a stop time into a shared JSON notice file, gui2's watcher reads it, shows an amber/red top banner at 30/15/10/5/1 minutes, and navigates pages to a static offline page at the stop time. nginx serves both static pages, including as the 502/503/504 error page. All decisions log `lifecycle:` lines.

## Problems

**Blocker — "every held page" is undefined.** `spec.md:60` says send "every page this process has served and still holds — the live one and any page retired by `claim_session`". `gui2/main.py:823-843` only keeps one `_session_page`; retired pages are replaced, not retained, and `release_session` drops them. A fresh implementer has no list to iterate and would have to invent a registry. Fix: name the data structure (e.g. a set of live `Page` objects kept by the wrapper) and who adds/removes.

**Blocker — the same page can be sent to two destinations at once.** `spec.md:53` (idle sleep) and `spec.md:87` (stop time) both fire from the same 15 s watcher on the same pages. The spec says "independent" (`spec.md:88`) but never states precedence when a countdown expires during the warning window, or when the banner is open at sleep. `spec.md:110` also claims the offline page covers the asleep case, contradicting two distinct pages. Fix: state a priority rule and which URL wins.

**Major — `Session.dispatch_event` is not the only client path.** `spec.md:36` calls it "the single path", but `flet_web/fastapi/flet_app.py:366-375` dispatches `route_change` via `page._trigger_event` directly, and `flet_app.py` handles `UPDATE_CONTROL_PROPS` without dispatch at all. Navigation/tab-route changes therefore may not count as activity, contradicting "tab changes" in `spec.md:36`. Fix: name exactly which Flet paths are wrapped, or wrap `page._trigger_event` too.

**Major — `page.session` raises rather than returning.** `flet/controls/page.py:1305-1315`: `session` raises `RuntimeError("An attempt to fetch destroyed session.")` when the session is gone. Spec A.2/A.6 assume a callable attribute and "a page whose connection is dead is skipped silently" — there is no stated mechanism for detecting deadness. Fix: state how liveness is tested (try/except vs `on_disconnect` bookkeeping).

**Major — `Restart=always` and `os._exit` contradict `systemctl stop` semantics only for signals.** `spec.md:63` asserts systemd never restarts a stopped unit — true, but the window's `_systemctl("stop", …)` runs in `maintenance_window.py:~470` *before* `finally` starts instances; a process that `os._exit`s during a stop transition is a race the spec never addresses. Also `TimeoutStopSec=30` (`dpd-gui@.service:20`) vs a 3 s navigation wait is unmentioned. Fix: state the expected interleaving.

**Major — the notice wait is unbounded in `WindowSteps`.** `spec.md:75-78` makes the wait "an injectable step", but `maintenance_window.py` `run_maintenance` has no `WindowSteps.wait` field today and the stop happens *before* `try:` — adding the notice write "first in `run_maintenance`" means before `_systemctl("stop")`, outside the `finally` that deletes the notice. If `_make_logger` or the write throws, the delete never runs. Fix: specify the exact code position and that the notice deletion is inside the same `finally`.

**Nit — undefined units/terms.** `spec.md:44` "working out the whole minutes left" — floor or round? `spec.md:46` "next step" after "Got it" is undefined when a step is skipped (e.g. reader arrives between 10 and 5). `spec.md:96` "N is the measured wake time … rounded up to the next 10 seconds" — 10 s rounding of 11 s gives 20 s, odd but unspecified as such.

**Nit — stale path references.** `spec.md:36` cites `flet/messaging/session.py:432`; the method body begins at that line but `flet_app.py:385` → actual call site is `flet_app.py:389`. Minor, but a naive reader will mis-grep.

### design

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

## Disposition

| # | Finding (deduplicated) | Severity | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| 1 | "Every held page" has no data structure; who adds and removes pages (comprehension B1, design B3) | Blocker | Accept | `gui2/main.py:777-806` keeps only `_session_page` | spec A.3b |
| 2 | Idle sleep and the stop time can send a page to two places; no precedence | Blocker | Accept | spec read | spec A.5 last row, B.5, B.6 |
| 3 | `dispatch_event` is not the only path: typed values arrive as `UPDATE_CONTROL_PROPS` → `apply_patch`; route changes bypass it | Major | Accept | `flet_web/fastapi/flet_app.py:383-391`; gui2 has no `on_route_change` (`rg`) | spec A.2, A.3 |
| 4 | `page.session` raises for a destroyed session; liveness test unstated | Major | Accept | `flet/controls/page.py:1304-1310`; `session.connection` is set to `None` in `disconnect` (`flet/messaging/session.py:214-216`) | spec A.3b |
| 5 | `os._exit` during a window stop races `Restart=always`; `TimeoutStopSec` | Major | Reject | systemd does not restart a unit whose stop was requested; an exit during the stop only ends it sooner. `TimeoutStopSec=30` bounds the stop, unrelated to the 3 s wait | — |
| 6 | Notice write position: today the stop runs before the `try`, outside the `finally` | Major | Accept | `maintenance_window.py` `run_maintenance` | spec B.2 |
| 7 | Minutes-left rounding, skipped steps, rounding of N undefined | Nit | Accept | spec read | spec B.4, D |
| 8 | Line reference `flet_app.py:385` should be 389 | Nit | Reject | the `dispatch_event` call sits at 383-386 in the installed file | — |
| 9 | Clock domains: monotonic idle vs wall-clock stop time | Blocker | Accept | spec read | spec A.3a, B.4 |
| 10 | A notice file left by a crash makes later pages go offline for up to 2 h | Blocker | Accept (partly) | stale window narrowed to 60 s past; no run id or versioning added | spec B.1 |
| 11 | Thread safety: calls into Flet from the watcher thread | Blocker | Accept | `page.run_task` → `asyncio.run_coroutine_threadsafe` (`flet/controls/page.py:929-960`) | spec A.3c |
| 12 | nginx regex placement / order | Blocker | Reject (+ rollout check) | nginx picks a matching regex over a plain prefix regardless of order; only one regex exists. Rollout adds `nginx -t` plus `curl` | spec C.4 |
| 13 | Countdown while pages connect or disconnect | Major | Accept | spec read | spec A.5 rows |
| 14 | `os._exit` may cut queued messages; 3 s is the only flush | Major | Accept | `flet_app.py` `send_message` only queues | spec A.6; plan Phase 1 probe |
| 15 | Dirty-tree check runs 30 min later | Major | Reject | contributor files live in `/var/lib/dpd/contrib_data`, outside git | spec B.2 note |
| 16 | Kill-switch restart drops the editor without warning | Nit | Accept | — | spec A.4 |
| 17 | N placeholder could ship as a guess | Nit | Accept | — | spec D (page not installed until N is filled) |
| 18 | Notice file "absent" vs "broken" indistinguishable to the operator | Nit | Accept | — | spec B.1 reason, E |

Counts: 18 findings — 14 accepted (1 partly), 4 rejected, 0 escalated.
