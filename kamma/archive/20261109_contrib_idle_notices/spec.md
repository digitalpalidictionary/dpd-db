# Spec: contributor server — idle sleep and nightly-update warnings

**GitHub issue:** #215 (contributor web server). Do not comment on or close the issue.
**Thread:** `20261109_contrib_idle_notices` · planned 2026-11-09 with `/kamma:1-plan-egm`.

## Overview

The contributor server runs one gui2 web process per contributor (systemd unit `dpd-gui@<user>`, `scripts/server_contrib/dpd-gui@.service`) behind nginx at `https://<server>/<user>/`. The server has 2 vCPU, 8 GB memory and 4 GB swap. Contributors live in many time zones.

Two problems:

1. **Idle processes hold memory.** A process with no page open holds about 87 MB. The first page that connects loads the database and builds the tabs: about 943 MB when ready, 1,046 MB after one Pass1 book (`kamma/archive/20261102_contrib_mem_savings/artifacts/results.md`, rows 22–23). That memory stays until the nightly stop, even if the person left hours ago. CPython rarely gives freed memory back to the OS, so the dependable way to free it is to end the process.
2. **The nightly stop has no warning.** Root's cron starts `scripts/server_contrib/maintenance_window.py` at 01:00 server time (Asia/Colombo). Its first action stops every instance (`run_maintenance`, the `_systemctl("stop", …)` call). Anyone typing loses their unsaved form with no notice. Instances stop every night, even when nothing is rebuilt; a rebuild night takes 30–55 minutes.

This thread adds, on the contributor server only:

- **Idle sleep:** after 30 minutes with no user action, a 2-minute "Still there?" countdown; then the browser is sent to a static "asleep" page and the process exits. systemd restarts an empty process (about 87 MB) that loads the database only when the person comes back.
- **Nightly warnings:** the maintenance window announces its stop time 30 minutes ahead in a small notice file. Each editor shows a top banner at 30, 15, 10, 5 and 1 minutes, then sends the browser to a static "offline" page at the stop time.
- **A static "offline" page from nginx** whenever an instance is not answering (during the window, or for the seconds while a process restarts), instead of nginx's bare "502 Bad Gateway".

The desktop gui2 does not change.

## What it should do

### A. Idle sleep (gui2, server web sessions only)

1. Everything in A and B runs only when `page.web` is true **and** `is_headless_server()` (`tools/server_mode.py`) is true. The desktop never sleeps and never reads the notice file, even if its `config.ini` has a stray `role = contributor-server`.
2. **Activity.** A user action is anything the browser sends for the page. Flet's web server handles two kinds (`flet_web/fastapi/flet_app.py:383-391`): control events (clicks, keys, tab changes, dropdowns) go to `Session.dispatch_event` (`flet/messaging/session.py:432`); property changes (the text a person types into a field) go to `Session.apply_patch`. gui2 wraps **both** methods on that page's session (`page.session`, `flet/controls/page.py:1304`) with a function that sets one process-wide "last activity" time and then calls the original. gui2 uses no page routes, so route changes are ignored. A page connecting also counts as activity. Phase 1 of the plan must prove that typing into a text field reaches one of the two wrappers; if it does not, stop and tell the owner.
3. **Guard.** If the wrappers cannot be installed (an attribute is missing after a Flet upgrade), gui2 logs one line saying idle sleep is off and keeps running without it. A unit test fails if `Session.dispatch_event` or `Session.apply_patch` disappears, so a Flet upgrade breaks a test, not production.
3a. **Clocks.** Idle time uses `time.monotonic()` (immune to clock changes). The notice stop time (B) is wall-clock UTC, compared with `datetime.now(UTC)`. The two are never mixed.
3b. **Pages held.** The module keeps a process-wide list of every page `main()` has served (appended in `main()`, after `claim_session`). A page counts as **connected** when `page.session.connection is not None`; `page.session` raises `RuntimeError` for a destroyed session (`flet/controls/page.py:1304-1310`), which counts as gone. The watcher removes gone pages from the list on every tick, so the list cannot grow without limit. "Any page connected" in A.5 means at least one page in the list is connected.
3c. **Threads.** The watcher thread never touches a Flet control directly. Every UI action (show or close the countdown, show or change the banner, navigate) is an `async` function handed to `page.run_task`, which schedules it on the page's own event loop with `asyncio.run_coroutine_threadsafe` (`flet/controls/page.py:929-960`). The wrappers run on the event loop and only assign a float; the thread only reads it.
4. **Idle time.** `IDLE_MINUTES = 30` and `COUNTDOWN_SECONDS = 120` are constants in the new gui2 module. The env value `DPD_GUI2_IDLE_MINUTES`, if set, overrides `IDLE_MINUTES`; `0` turns idle sleep off. This is the kill switch: the owner can turn sleep off for a user by editing `/etc/dpd/<user>.env` and restarting that unit, with no code push. The restart drops that person's editor at once, with no warning, so do it when they are not working. An unparseable value logs a line and falls back to 30.
5. **Watcher.** One daemon thread per process wakes every 15 seconds and decides:
   - A page is connected and idle time ≥ `IDLE_MINUTES`, no countdown showing → show the countdown dialog (wording in D).
   - Countdown showing and any event arrives → close it, log "countdown cancelled", keep running.
   - Countdown showing and `COUNTDOWN_SECONDS` pass with no event → **sleep** (step 6).
   - No page connected (tab closed, laptop asleep) and idle time ≥ `IDLE_MINUTES` → sleep at once, with no countdown (there is nobody to show it to).
   - Countdown showing and every page disconnects → the countdown keeps running and the process sleeps when it ends.
   - Countdown showing and a new page connects → that is activity, so the countdown is cancelled (closed on every connected page, best effort).
   - The process has already sent its pages to the offline page (B.5) → do nothing; the window is about to stop the process.
   The decision is a pure function of (now, last activity, countdown start, idle seconds, any page connected, offline sent) that returns one of: nothing, show countdown, cancel countdown, sleep. It can be unit-tested without Flet.
6. **Sleep.** Log one line (step E). Send every page this process has served and still holds — the live one and any page retired by `claim_session` — to the asleep page with `UrlLauncher().launch_url(<url>, web_only_window_name="_self")`. A page that is not connected (3b) is skipped. Wait 3 seconds for the navigation to reach the browser, then `os._exit(0)`. `os._exit` is used because a normal exit from a worker thread does not stop Flet's server loop. Flet only queues outgoing messages, so the 3 seconds are the only flush guarantee; Phase 1 checks that they are enough on the server. The asleep URL is relative to the page, `_dpd/asleep.html`, so it resolves to `/<user>/_dpd/asleep.html` behind the mount prefix (the same pattern as the preview page, `gui2/preview.py:159-164`). Phase 1 must prove that a server-pushed `_self` navigation works in Chrome and Firefox; if it does not, stop and tell the owner.
7. **Restart.** The unit changes `Restart=on-failure` to `Restart=always`, so the clean exit (0) is restarted after `RestartSec=10`. `systemctl stop` (the window) still stops it for good: systemd never restarts a unit it was told to stop. `StartLimitBurst=5` in 300 s still caps a crash loop.
8. **A half-filled form is lost** when the editor sleeps (owner's decision, 2026-11-09). The countdown dialog says so.

### B. Nightly warnings

1. **Notice file.** A shared module, `tools/contrib_notice.py`, owns the format, the path and the read/write functions, so the window and gui2 cannot disagree. Path: the constant `NOTICE_FILE = Path("/var/lib/dpd/notice.json")` (outside the git tree, next to `status.txt` and `contrib_data`, world-readable). Content: `{"stop_at": "<UTC ISO-8601 time>"}`. Written by copy-and-replace (temp file then `os.replace`), mode 644, like `_write_status`. `read_notice()` returns `(stop_at, reason)`: the stop time with reason `"ok"`, or `None` with one of `"absent"`, `"unreadable"` (bad JSON or no permission), `"bad time"`, `"past"`. `"past"` means the stop time is more than 60 seconds ago: a file left behind by a crashed window must not send a person who connects later to the offline page. It never raises. gui2 logs the reason whenever it changes (E), so "absent" and "broken" can be told apart.
2. **The window arms it.** `maintenance_window.py` gets `--warn-minutes N` (default 0 = no notice, so manual and test runs behave as today) and `--notice-file` (default `NOTICE_FILE`). Code position: today `run_maintenance` calls `_systemctl("stop", …)` before its `try:` and checks `stop_failed` inside it. The new code moves that stop call to the start of the `try:`. With N > 0, the first steps inside the `try:` become: write the notice with `stop_at = now (UTC) + N minutes`, log `notice armed: stop at <time>`, wait until `stop_at` plus `OFFLINE_GRACE_SECONDS = 25`, then stop the instances and go on exactly as today. The grace exists because the editors read the notice every 15 s and move to the offline page only after `stop_at`; without it `systemctl stop` kills the process before any editor sees the stop time (found by CodeRabbit, 2026-11-09). The wait is a new injectable `WindowSteps` field (`wait: Callable[[float], None]`, default `time.sleep`), so tests do not sleep. The existing `finally` deletes the notice file after it starts the instances, and logs the deletion. A failure to write or delete the file is logged as a warning and never fails the window. The dirty-tree check now runs 30 minutes later than today; contributor files live outside the git tree, so this changes nothing.
3. **Cron moves to 00:30** with `--warn-minutes 30`, so the stop still happens at 01:00 server time (runbook step 8d and the live crontab).
4. **gui2 reads it.** The same 15-second watcher reads the notice file. Minutes left = `ceil((stop_at − now_utc) / 60 s)`. No banner while minutes left > 30. The **step** is the smallest of 30, 15, 10, 5, 1 that is ≥ minutes left (12 minutes left → step 15; a person who connects at 12 minutes sees the banner at once). The banner opens on every connected page whenever the step differs from the last step shown, so a skipped step simply shows the next one. While the banner is open, its text is refreshed every tick with the current minutes left ("in 12 minutes", then "in 11 minutes"). "Got it" closes it until the step changes. The banner is amber above 5 minutes and red at 5 minutes or less. If minutes left go up (a new notice with a later stop), the same step rule applies. The banner is shown with `page.show_dialog` and so sits on the dialog stack. `is_dialog_open` and `cancel_top_dialog` (`gui2/ui_utils.py:169-200`) must skip `ft.Banner` exactly as they skip `ft.SnackBar`. Otherwise `App.on_keyboard` (`gui2/main.py:381`) treats the open banner as a popup and turns off every keyboard shortcut, Ctrl+S included, for the whole warning period.
5. On the first tick where minutes left ≤ 0, gui2 sends every connected page to `_dpd/offline.html` (same mechanism as A.6), logs it, sets "offline sent", and does not exit; the window's `systemctl stop` ends the process. A page that connects after that is sent to the offline page at once.
6. **Which comes first.** Idle sleep and the warnings run side by side. Idle sleep can still happen before the stop time (the person was away anyway). Once "offline sent" is set, idle sleep is off for the rest of the process's life (A.5), so a page is never sent to two places.

### C. Static pages and nginx

1. Two hand-written HTML files in the repo, `scripts/server_contrib/pages/asleep.html` and `scripts/server_contrib/pages/offline.html`. No external resources, inline CSS, dark background to match gui2, a button and a sentence or two (wording in D). Each button goes to `/<first path segment>/`, read from `location.pathname` in the page's own script. That segment must match `^[a-z][a-z0-9_]{0,31}$` (the `add_contributor.sh` user rule); otherwise the button goes to `/`.
2. They are installed to `/var/www/dpd-pages/` on the server (a runbook step; nginx setup is manual by design, per `scripts/server_contrib/README.md`).
3. The site config (`nginx_contrib.conf.template`) gets one regex location that serves both pages for any user prefix, with no login (they hold nothing private):
   `location ~ "^/[a-z][a-z0-9_]{0,31}/_dpd/(asleep|offline)\.html$" { alias /var/www/dpd-pages/$1.html; }`
   A regex location wins over the plain-prefix per-user location `location /<user>/`, so no per-user copy is needed.
4. The per-user template (`nginx_contrib_user.conf.template`) gets `error_page 502 503 504 /@USER@/_dpd/offline.html;` inside `location /@USER@/`. It must be per-user: that block already sets `error_page 403`, and nginx does not inherit `error_page` into a block that sets its own. Existing users' rendered confs (`/etc/nginx/dpd/<user>.conf`) get the line by hand in the rollout; the live users are `bdhrs` and `deva` (read from the server on 2026-11-09; `alice` does not exist). There is only one regex location, and nginx picks a regex location over a plain prefix whatever the order, so its place in the site file does not matter. The rollout runs `nginx -t` and then checks each page with `curl` on the live host (`nginx -t` alone passes on some broken configs, per CLAUDE.md).

### D. Wording

Plain English. Relative times only: never a server clock time, because contributors are in many time zones. "Press F5" never appears.

- **Countdown dialog** — title "Still there?"; body "You have not used the editor for 30 minutes. To free memory for other contributors, it will go to sleep in 2 minutes. Anything you have not saved will be lost."; one button "I'm here". The body shows the configured minutes. It does not need a live seconds count.
- **Asleep page** — heading "The editor is asleep"; body "It went to sleep after 30 minutes without use, to free memory for other contributors. Anything that was not saved is gone."; button "Wake the editor"; small print "Waking takes about N seconds while the dictionary loads." N is the median of 3 measured wake times (process start → "All tabs and tools ready." snackbar) from the plan's measurement task, rounded up to a whole multiple of 10 (41 → 50). The spec does not guess it, and the page is not installed on the server until N is filled in.
- **Banner** — "The editor restarts for its daily update in 15 minutes. Save your work now. Anything unsaved will be lost." ("in 1 minute" at the last step); button "Got it".
- **Offline page** (changed 2026-11-10 at the owner's request, after the live banner test) — heading "The editor is not running right now"; body "The editor is being updated (the daily update takes up to an hour) or it is starting up. Please wait. A button appears here when the editor is ready." **No button while the editor is down.** The page asks the editor's own address every 15 seconds; any answer other than 502, 503 or 504 means the editor is back, and the button "Open the editor" appears. The asleep page is unchanged: it has its button at once, because waking from sleep works immediately. A sleeping person who clicks while an update runs lands on this page and waits.

### E. Logging

gui2 writes these lines through `tools/printer.py` to stdout, which systemd keeps in the journal (`journalctl -u dpd-gui@<user>`). Each line starts with `lifecycle:`, so `journalctl -u dpd-gui@alice | grep lifecycle:` gives the whole story:
process start (pid, user, idle minutes, or "idle sleep off" with the reason); page connected; notice file state when it changes (`absent`, `unreadable`, `bad time`, `past`, or the stop time); countdown shown; countdown cancelled; asleep (minutes idle, pages sent away, connected or not); notice seen (stop time); banner step shown (minutes left); sent to offline page. The existing "App initialized in …" print and the db-load snackbar spot each get a `lifecycle:` line with elapsed seconds, so a slow wake can be split into process start, db load and warm-up.

The maintenance log gets `notice armed: stop at …` and `notice removed` (B.2).

## Assumptions & uncertainties

Verified this session by reading the source (paths above): the unit's restart policy; the window's stop-first order; the cron line in the runbook; `Session.dispatch_event` (control events) and `Session.apply_patch` (typed values) as the two paths for what the browser sends; `page.session` raising for a destroyed session; `page.run_task` using `run_coroutine_threadsafe`; `UrlLauncher.launch_url(..., web_only_window_name=...)` and `UrlTarget.SELF`; `ft.Banner` is persistent, non-modal, shown with `page.show_dialog`, needs at least one action; the per-user nginx block sets its own `error_page 403`; `server_setup.sh:104-105` re-renders the unit on every run; `add_contributor.sh` refuses to overwrite an existing conf; memory figures from the archived results.

Not verified — Phase 1 of the plan proves or disproves each before any feature code:
- Typing into a gui2 text field produces an event through `Session.dispatch_event` (expected through the page keyboard handler that gui2 sets).
- A server-pushed `launch_url(..., "_self")` navigates the tab in Chrome and Firefox, with no popup block.
- A daemon thread can show and close a dialog and the banner on the page (the warm-up thread already shows snackbars from a worker thread, `gui2/main.py:614-670`, so this is expected to work).
- After the process exits, whether Flet's web client reconnects by itself (`reconnect_interval_ms` / `reconnect_timeout_ms` exist in `flet_web/web/main.dart.js`). The design does not depend on it, because every held page is sent to a static page first. If a page still reconnects after the navigation, that is a bug to report.
- The wake time on the server (process start → editor ready), which the asleep page states.

Accepted Goldfish findings (Gate 1, `egm/gate1.md`):
- (Blocker) Activity must come from event dispatch, not the keyboard hook alone; and the hook must be checked at start (A.2, A.3).
- (Blocker) A clean idle exit is not restarted by `Restart=on-failure` → `Restart=always` (A.7).
- (Blocker) The window itself must arm the warnings before it stops anything; cron moves to 00:30 (B.2, B.3).
- (Blocker) Warnings run on a server-side timer, not on user events (B.4).
- (Blocker) Waking reloads the whole database; the saving exists only for people who stay away; the wake time is measured, not promised (D, plan measurement task).
- (Blocker) The installed unit and nginx files are rendered copies outside git, so the rollout is a manual, ordered step and the window's git rollback cannot undo it (plan rollout phase).
- (Blocker/Major) Every decision is logged (E).
- (Major) The notice file lives outside the git tree (B.1).
- (Major) nginx serves an offline page on 502 from one site-level location; the per-user line is unavoidable (C).
- (Major) Two pages with two wordings; no "F5"; relative times; say that unsaved work is lost (D).
- (Major) Gate on `page.web and is_headless_server()` (A.1).
- (Major) The exit must be certain (`os._exit`, A.6).
- (Major) Sending every held page away removes the storm of tabs reconnecting after the nightly start; a real crowd of people waking at once on 2 vCPU stays a known risk.
- (Nit) A kill switch per user (A.4).

Known risks:
- A window killed hard (not by an exception, which the `finally` handles) while it waits leaves a notice with a future stop time. Editors then show the banner and move to the offline page at that time although nothing was stopped; the offline page's button appears (the editor still answers) and idle sleep stays off in that process until the next restart. A notice more than 60 s past its stop time is ignored. Not guarded further: a heartbeat file was judged more machinery than a rare event deserves (pre-finalize review, 2026-11-10).
- Someone who reads for 30 minutes without clicking or typing gets the countdown. Two minutes to answer it is the guard.
- People who return within the hour after sleeping pay the full database load again. 30 minutes is a trade-off; the env value changes it per user.
- Several people waking at once share 2 vCPU; each wake is CPU-heavy. Not addressed here.
- `page.session.dispatch_event` is a Flet internal. The guard test (A.3) is the alarm on upgrade.

## Constraints

- Desktop gui2 behaviour must not change (A.1).
- `Control.focus()` is a coroutine in Flet 1.0, sync handlers block the event loop, and closing a dialog with `open = False` can leave it on `page._dialogs` so a later `show_dialog` of the same instance raises "Dialog is already opened" (CLAUDE.md, `kamma/tech.md`). Create a fresh dialog/banner object each time it is shown, or guard the reopen.
- `gui2/**`, `tests/**` are excluded from pyright by config: check with `uv run pyright --project /dev/null <file>`. `tools/` and `scripts/` are checked normally. Run `ruff check`, `ruff format`, pyright on every touched file, and `just typecheck` before finishing.
- `__init__.py` files cannot be committed; import from concrete modules.
- No server address or home path in committed text: write `<server-ip>`, `<repo root>`.
- The server is changed by the owner or the server agent (`/herdr-remote`), never by an unasked ssh from the laptop.

## How we'll know it's done

1. Unit tests pass for: the idle decision function (each branch in A.5); the env override and kill switch (A.4); `tools/contrib_notice.py` write/read/stale/garbage cases; the banner step for a given minutes-left; `run_maintenance` with `--warn-minutes` (notice written before stop, wait called with the right time, notice removed in `finally`, write failure does not fail the window, `--warn-minutes 0` unchanged); the guard test that `Session.dispatch_event` and `Session.apply_patch` exist.
2. A local web run of gui2 in server mode with `DPD_GUI2_IDLE_MINUTES=1` shows the countdown after a minute idle; clicking "I'm here" cancels it; leaving it sends the tab to the asleep page and the process exits with code 0.
3. On the server, with a short idle value for `alice`: the countdown, the asleep page, the restart (`systemctl status` shows active with a new pid), the wake, and the journal `lifecycle:` lines all behave as written; the measured wake time is in the asleep page.
4. On the server, a window run with `--warn-minutes` set small (owner-approved test time): the banner steps appear, the tab goes to the offline page at the stop time, nginx shows the offline page while the instance is down, and the maintenance log has `notice armed` and `notice removed`.
5. The live crontab runs at 00:30 with `--warn-minutes 30`; the runbook, README and `kamma/tech.md` say so.
6. Memory: after sleep, `alice`'s process is back near 87 MB (read from `/proc/<pid>/status` VmRSS).

## What's not included

- No on-demand start (socket activation, or nginx starting the unit). A sleeping person costs about 87 MB for the empty process; this can be revisited if the number of contributors grows.
- No draft-saving of a half-filled form, and no "unsaved changes" check (owner chose "sleep anyway").
- No per-instance `MemoryMax` or CPU weighting. The earlier results file mentions a 2 GB `MemoryMax` that the unit does not have; that is a separate decision.
- No change to the database load or warm-up to make waking cheaper.
- No ad-hoc "server restarting" announcements beyond the nightly window (the notice file format allows it later; no command is built for it now).
- No change to the stale "~2.5 GB" comment in `gui2/main.py` or to the Alt+? shortcut table (noticed by reviewers, unrelated).

## Review record

EGM review files are in `egm/`. Gate 1 (`egm/gate1.md`): 6 reviewers, 26 findings, 16 accepted, 8 rejected, 2 escalated and answered by the owner (banner placement, sleep with an unsaved form). The first backend attempt (Azure, plain text) hung and was replaced by DeepSeek's own API in streaming mode. Gate 2 (`egm/gate2.md`): 2 reviewers, 18 findings, 14 accepted, 4 rejected, 0 escalated. Gate 3 (`egm/gate3.md`): 1 reviewer, 21 findings, 19 accepted (all fixed in `plan.md`), 2 rejected, 0 escalated.

Pre-push review (2026-11-09): DeepSeek flash (own API, thinking off, no tools, six pieces of 6–17 KB, streamed) and CodeRabbit (one whole-change run after its free-allowance wait). Accepted and fixed: step memory reset when a notice ends; three test gaps (umask, wait length on a failed write, command-line flags); two README wording fixes; the 25 s grace after the stop time (CodeRabbit, major). Rejected: waiting on navigation futures before exit (3 s flush is the spec's known limit, Phase 5 measures it), lock changes for single assignments, `id(page)` reuse (entries are removed with the page), aborting the window when the notice cannot be written (spec B.2: the stop stays on time), and a data-file grammar note outside this thread.
