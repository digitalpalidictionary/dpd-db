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