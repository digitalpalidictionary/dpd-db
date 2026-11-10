# Gate 1 — idea stress-test

Backend: pi, DeepSeek API (`--provider deepseek --model deepseek-flash --thinking off --mode json`), six reviewers in parallel, one lens each.

Backend switch: the first attempt ran on Azure's `deepseek-v4.1-flash` in plain text mode, one reviewer at a time. The first reviewer ran 8 min 46 s with no output and ~0.1 % CPU; it was stopped by pid and the run restarted on DeepSeek's own API in streaming mode at the owner's request. All six then returned (625–902 words).

## Raw findings

### contrarian

I have enough context. Key facts gathered: Flet 1.0.1, Flet already tracks page sessions and has `on_disconnect`/`on_close` (main.py:836-841), and the "already open" session-lock pattern already exists. The deployment files (systemd/nginx/cron) are not in the repo — I only had indirect evidence. Let me report.

## Findings

**Blocker — the whole idle-reclaim ladder is new code for something systemd + kernel already do.**
Evidence: `gui2/main.py:836-841` shows the app already gets `on_disconnect`/`on_close` callbacks and the code relies on them (`claim_session`/`release_session`). The hypothesis proposes a hand-rolled "last action" tracker, a per-minute poller, a countdown UI, and an exit. The Linux kernel + systemd already detect and reclaim. Failure scenario: you rebuild session-lifetime logic (idle clock, countdown, exit path, wake page) that duplicates process supervision, and you must now maintain it against Flet's reconnect quirks. Fix: drop the tracker. Let systemd manage the process and use a `RuntimeMaxSec`/`IdleTimeout`-style unit knob or a tiny `systemd-run`/socket-activation setup; Flet's `on_disconnect` already fires when the browser leaves.

**Blocker — "exit the process, systemd restarts an empty one" is reinventing socket activation.**
Evidence: `gui2/main.py:741-796` — `_initialize_db_in_background` runs on every startup, and `build_ui` starts it unconditionally. The plan wants a "lazy load db only when a page connects" empty process. Failure scenario: you add a new "empty vs loaded" startup state and a wake trigger, duplicating what systemd socket activation does for free (kernel holds the listening socket; the service starts on first connect; no page-connection hook needed). Fix: use socket activation (`.socket` unit) or `systemd` `Restart=always` with an `ExecStartPre` gate; do not add a bespoke empty-state to `main.py`.

**Major — Flet already owns page lifecycle; a second idle clock can deadlock the single-session lock.**
Evidence: `gui2/main.py:823-861` — one live session per process, newest wins; `release_session` guards on page identity. Failure scenario: the idle "exit" races `claim_session`'s retire path — the idle timer fires while `_session_page` is mid-swap, exits, and systemd restarts a process still holding a stale page reference; or the countdown keeps `_session_page` non-None so `on_disconnect` never frees it. Fix: if any idle logic survives, gate exit on `release_session` having run; better, delete it and rely on `on_disconnect`.

**Major — the nightly notice-file + per-minute poller duplicates systemd timers and nginx.**
Evidence: the hypothesis itself lists nginx templates and a cron line as the maintenance window; `gui2/main.py` has no clock/file-watch today. Failure scenario: gui2 writes a poller thread that reads a file every 60s for each of N contributor processes — N pollers contending on one file, plus clock-skew between the cron writer and the reader. Fix: `systemd` timer writes the deadline; gui2 reads it via one `systemd`-provided mechanism, or skip the file entirely and let nginx return a 503 message page during the maintenance window (nginx `return 503` + `error_page`). nginx already serves the "being updated" page with zero Python.

**Major — two static pages are unnecessary; nginx can serve one.**
Evidence: request item 3 (rebuild warning) and the static "being updated"/"asleep" pages. Failure scenario: two hand-written HTML pages to keep in sync with the real state, drifting (page says "updating" while idle, or vice versa). Fix: one nginx `error_page 503 /maintenance.html`; the same page covers idle-exit, rebuild, and crash — the visitor doesn't care which.

**Nit — the "still there?" countdown is UI for a problem the process can solve silently.**
Evidence: `gui2/main.py:1` — the app is a Flet web app; the browser reconnect is handled by Flet's client. Failure scenario: a contributor watching a countdown they can't act on. Fix: let the browser sit on the nginx wake page; only if Flet loses the socket does the client show its own reconnect.

**Nit — wording/placement debate (request item 4) is resolved by the nginx page.**
Evidence: n/a — no snackbar/header code needed. Fix: one static page, minimal wording, no new Flet control.

**Nit — scope creep: two static pages + notice file + poller + countdown is four new mechanisms for one requirement.** None is backed by a library; systemd socket activation, `Restart=`, an `IdleTimeout` knob, and nginx `error_page` cover the whole brief without new application code.

**Caveat:** the systemd unit, nginx templates, and cron line are **not in this repo** (I searched `deploy/`, `scripts/maintenance.py`, `scripts/daily_rebuild.sh` — all absent). So the hypothesis's "systemd restarts…" and "nginx shows the same page" are unanchored here; if you keep any of the custom code, it must land in files that don't exist yet, which raises, not lowers, the YAGNI cost.

Bottom line: the requirement is real but almost entirely solvable by systemd (socket activation + restart/idle policy) and nginx (`error_page`). The proposed gui2 idle tracker, countdown, notice-file poller, and second static page should be cut.

### cost

# Goldfish review — cost, quota, resource economics

Measured baseline: warm 943.3 MB, 1,045.7 MB after one book (peak 1,113.4). The hypothesis's 1.2–1.5 GB is stale but the plan's economics don't depend on it. The plan is mostly sound; the failures are in the wake storm, the cold-start cost, and the fact that nothing caps a process.

## Blockers

**1. The idle exit does not reclaim what the plan assumes, and the wake rebuild costs the same as it saved.**
`gui2/main.py:711-760`. Exiting the process does free everything (unlike dropping objects in-process — the hypothesis is right about that). But the "empty ~87 MB" state is only reachable while nobody connects. Every reconnect runs `App(page)` (`gui2/main.py:841`), then `build_ui` → `_initialize_db_in_background` → `_warmup_in_background` (`gui2/main.py:657-704`), which rebuilds corpus + inflection hashes + detector unconditionally, no matter which tab the wake page lands on. Cost per wake: ~11 s of pure CPU on 2 vCPU (the code's own figure, `gui2/main.py:609`) plus 943 MB, before the user does anything. A contributor who opens the editor, reads, closes it, and opens it once more an hour later pays the full 1 MB→943 MB ramp twice. The plan saves memory only for people who stay away; it saves *nothing* for the common read-a-word-and-leave pattern, and it adds a 60-second wall to each of them. Fix: make the contributor warm-up demand-driven (build the corpus only when a save/lookup actually needs it, not on `build_ui`), and measure a real wake→ready latency before promising "about a minute" in the wording.

**2. Simultaneous wakes on 2 vCPU.**
`gui2/main.py:657-704`, `scripts/server_contrib/dpd-gui@.service`. If several contributors return at the same hour (the plan's own premise: a global user base, so overlapping wakes are the normal case, not the edge case), N processes each run an 11 s CPU-bound warm-up. Two vCPUs meant 2 wake-ups serialize; 5 wake-ups is ~30 s of queueing stacked on top, and every instance in the middle of it looks hung. There is no admission control, no niceness, and no shared cache. Fix: the plan needs a wake queue or a per-instance `CPUWeight`/`Nice` so a waking instance cannot starve a working one; otherwise "it takes about a minute" becomes "it takes as long as the neighbours".

## Major

**3. The nightly window's `start` is the same storm, with no warning possible.**
`scripts/server_contrib/maintenance_window.py:453-455` — `_systemctl("start", ...)` starts every instance in a loop inside `finally`, after up to 55 minutes of rebuild. All N processes then run the 943 MB ramp and an 11 s warm-up at once, on the same 2 vCPU that just spent an hour building. Peak RSS is N×~1.1 GB *simultaneously*, not staggered — exactly the shape that reaches swap. Peak here is the plan's worst untested number. Recovery wakes (item 1) can also pile onto this window. Fix: stagger the `start` calls (a few seconds apart is not enough — the ramp is ~20 s, so spacing must exceed that, or the units need `CPUWeight=`).

**4. Nothing in the unit bounds a process.**
`scripts/server_contrib/dpd-gui@.service:10-21`. No `MemoryMax`, despite the archived results (`20261102_contrib_mem_measure/artifacts/results.md`, correction 2) explicitly noting "the cap of 2 GB per instance (`MemoryMax`)" — a cap that does not exist in this unit or in runbook Step 6a. The archived savings thread also records 2,059.4 MB observed with two extra browser sessions in one process (`20261102_contrib_mem_savings/artifacts/results.md`, caveats) — 2× the budgeted figure, and `StartLimitBurst=5`/`Restart=on-failure` means an OOM kill can take the unit down for the night. The plan removes the one thing currently limiting per-process growth (the nightly restart) and replaces it with a timer that may never fire if the idle detection is broken. Add `MemoryMax=2G` before shipping, and check `MemoryMax` behaviour against the on-failure restart policy.

**5. Peak during the rebuild window is unchanged and was never measured here.**
`maintenance_window.py:207-215` — `_capture_rollback` `shutil.copy2`s the whole 883 MB db to `dpd.db.prev` on disk (page cache), so the window adds ~883 MB of dirty pages plus the rebuild's own peak on a machine whose instances "start every night after the window". The plan says instances start after the window; it does not say the box has any headroom then. Fix: no fix required, but the plan's claim that it "reclaims resources for active people" should not be validated at the same time the box is doing its heaviest work.

**6. `page.session`-based idle tracking has no measurement behind it.**
`gui2/main.py:152` sets `page.on_keyboard_event`, and item 3 of the hypothesis proposes counting "last user action" from events. Any activity the plan does not hook (a tab click, a field edit) will read as idle, and the plan's own "still there?" countdown fires under someone who is mid-form. `gui2/main.py:764-770` already documents that a half-filled form is lost on exit. Fix: track activity at the Flet event-dispatch layer, and require the countdown to be visibly acknowledged before exit.

## Nit

**7.** `gui2/ui_utils.py:137` snackbars are the existing status channel — fine for the "asleep" message, but a 30-minute warning delivered via a 2–5 s `duration` snackbar is unreliable (one missed paint and it's gone). A `ft.Banner` in `_web_header` (`gui2/main.py:182-195`) survives and answers the owner's question 4.

### ux

I've read the inputs and the key files (the runbook `NEW_SERVER_RUNBOOK.md` is not in the repo, so step 8d and the cron line are unverified). Findings:

**1. Blocker — the nightly stop is silent because it kills before anything can talk to the browser.** `maintenance_window.py:447` calls `_systemctl("stop", ...)` as the first action, before `_capture_rollback` and the pull. The hypothesis's "notice file 30 minutes ahead" has no writer: nothing in this file writes a notice, and the cron line only starts at 01:00 (`0 1 * * *`). Scenario: a contributor in, say, Jakarta or Hawaii is mid-form at 01:00 Colombo; the process dies with no notice at all — worse than the current state for anyone hoping for the 30-minute warning. Fix: the cron line must run a *separate* pre-window pass at 00:30 that only writes the notice file (30/15/10/5/1 schedule computed from a stop-at timestamp in the file), and the 01:00 run must read/reuse it; announcing inside the window itself is too late.

**2. Blocker — the warning cannot reach a browser that has not sent a recent event.** The hypothesis hangs the 1-minute file check on Flet's event dispatch (`Session.dispatch_event`). A contributor who typed nothing for 20 minutes sends no events, so no check runs, and the 30/15/10/5 warnings never appear. Fix: drive the warning from a server-side `page.run_task` timer thread that calls `page.update()`, not from event dispatch, and verify the hypothesis's untested `dispatch_event` hook is not the only trigger.

**3. Major — the filesystem notice file cannot be per-user, and paths race.** `WindowConfig.status_file` (`maintenance_window.py:71`) is a single path; per-user notice files would need `--status-file` repeated per instance, but `_config_from_args:487` accepts one value only, and the arg parser has a single `--status-file`. With multiple contributors each gui2 needs its own file. Fix: one shared read-only file (no per-user state needed) in a www-readable dir, path from `/etc/dpd/<user>.env`, and template-ify the value in `dpd-gui@.service`.

**4. Major — an empty process serves 502s, not the "being updated" page.** nginx has no fallback: `nginx_contrib_user.conf.template:29` proxies unconditionally and the only `error_page` is `403 = @pw_`. Scenario: after the 01:00 stop, a returning contributor at 01:05 gets nginx's 502 page, not the friendly static page the hypothesis promises. Fix: add `proxy_intercept_errors on; error_page 502 503 504 = @asleep_@USER@;` with a static page under `/@USER@/asleep/`, served behind the same `auth_basic` (otherwise a stranger learns /alice/ exists).

**5. Major — "It takes a moment to get back to full power" is wrong on the wake path.** `_initialize_db_in_background` runs after paint (`main.py:768-772`), and per the memory table the process reaches ~1.5 GB only after the db load *and* warm-up. Wording "about a minute" invites the contributor to click Pass1Add immediately, and any stale tab still redirected to the asleep page. Fix: on the wake page say "Click to open the editor. It takes about a minute to load the dictionary — the page shows progress." And keep the existing "Database loaded." snackbar (`ui_utils.py:137`) as the completion signal, since it already exists.

**6. Major — what they lose is not disclosed anywhere.** No whole-form autosave exists; `example_stash_manager.py:39` only persists source/sutta/example for the "last" slot and saves on *stash*, not on typing. A 30-minute warning that says "the editor will restart" reads like a refresh. Fix wording: "The server restarts for its nightly update in 30 minutes. Anything you have typed but not saved will be lost — save your book with ✔ before then." Repeat the same sentence at 15/10/5/1.

**7. Major — the two "get back to work" moments are not distinguished.** Asleep (idle reclaim) is routine and self-correcting; the nightly window may *fail* and leave the instance down for an unknown time (`finally` at :504 always restarts, but a hung pull can hold it 3600 s, `STEP_TIMEOUT`). One shared page for both makes the nightly outage look like the contributor's fault and the idle sleep look alarming. Fix: two pages, two wordings — idle: "The editor went to sleep because it was idle. Click to wake it — about a minute." Nightly: "A nightly update is running. The editor returns by ~02:00 Sri Lanka time (see your local time: **<computed>**)." Never reuse "press F5".

**8. Major — time zones.** The owner's audience is global; "01:00" is meaningless to them, and `_write_status:196` stamps `finished:` in server-local `datetime.now()`. Fix: the alert must state the *local* stop time (browser-side JS, or a viewer-supplied offset passed to the notice endpoint), or at minimum "the daily update starts at 01:00 Colombo (UTC+5:30)". Do not print a bare server timestamp to contributors.

**9. Nit — "press F5 to restart" is the wrong instruction.** F5 reloads the *browser*, not the server and not an exited process. The asleep page should carry a single button ("Open the editor") that navigates to `/@USER@/`. Reserve "reload" wording for the already-open-in-another-tab case, whose existing message `ALREADY_OPEN_MESSAGE` (`main.py:780`) already covers it.

**10. Nit — placement (the owner's question).** Header bar, not snackbar: `show_global_snackbar` `duration=4000` and `_web_header` (`main.py:192`) scrolls away, so a snackbar during typing or scrolled-down work is invisible, and a snackbar shares the dialog stack (`ui_utils.py:170`). Fix: a non-dismissable `ft.Banner` or a fixed strip above the tab row, pinned outside the scrolling canvas, colour-coded (yellow 30–15, orange 10–5, red 1), with a "Save now" affordance. Also: the idle "still there?" countdown must never fire while a field holds unsaved text without saying so.

**Unverified:** runbook step 8d and the actual cron line (file absent); Flet's default reconnect behaviour.

### migration

Findings, migration lens. Ordered by severity.

**Blocker — idle-exit rewrite is unprotected by `Restart=on-failure` (evidence: `scripts/server_contrib/dpd-gui@.service:19-20`, `kamma/archive/20261102_contrib_mem_measure/artifacts/results.md` Deviations §1).**
gui2 already exits non-zero on SIGTERM ("`systemctl stop` left the unit in state `failed`"). A deliberate idle exit is a *clean* exit: `Restart=on-failure` will leave the unit `inactive`, so the URL 502s until someone logs in. Worst case: the idle watchdog fires during the rebuild branch *instead of* the maintenance stop, the window then runs with a live process on the old db. Fix: worker exit code 0 must be restarted — either `Restart=always` with `ExecStop`/`SuccessExitStatus` semantics checked, or (safer) a separate `dpd-gui-idle@.service`/`.socket` activation path, plus an explicit `systemctl start` at the end of the idle path. Decide and *measure* which exit codes systemd sees before shipping.

**Blocker — nightly cron line and the switch land in one commit with no staging (evidence: `scripts/server_contrib/maintenance_window.py:427-470`, `NEW_SERVER_RUNBOOK.md` step 8d, file absent from the tree).**
The hypothesis changes the unit, the maintenance window, nginx templates and adds pages. `maintenance_window.py` `pull --ff-only` + `git reset --hard` rollback means: the first night after the push, the *new* code pulls *itself*, and if the rebuild step fails, `git reset --hard <pre-commit>` restores the **old** unit/window — but the installed `/etc/systemd/system/dpd-gui@.service` and `/etc/nginx/dpd/*.conf` are **not under git** (they are `sed`-rendered by `server_setup.sh:99-103` and `add_contributor.sh:133-135`). Rollback of `maintenance_window.py` therefore runs new-guif2 + old-unit + old-nginx, an untested combination. Fix: version the rendered unit/nginx stamp (e.g. write the template hash into `/etc/dpd/`), and add an idempotent `render_configs.sh` the window calls after pull — or declare the switch requires a manual runbook step and keep it out of the auto-pulled commit.

**Major — the notice file must survive `git reset --hard` and `_restore_build_changes` (evidence: `maintenance_window.py:330-355`, `:376-395`).**
`_restore_build_changes` runs `git checkout -- <every changed tracked file>` unconditionally after a rebuild. If the notice file, the two static pages, or the nginx "being updated" page are tracked and written *during* the window (the 30-min-ahead writer will be), the next window's dirty-tree check (`:376`) refuses the whole night and the window returns FAILED with instances stopped-then-started and nothing updated. Fix: put the notice file under `logs/` (gitignored) like `LAST_BUILT_FILE`, add it to the read-only status file's directory, and confirm the two static pages are read from `config.data_dir`/`log_dir`, not the worktree.

**Major — desktop gui2 regression risk is unguarded (evidence: `gui2/main.py:116-190`, `tools/server_mode.py:24`).**
The idle timer, the notice poller and `UrlLauncher` navigation must be behind `is_headless_server()`. `is_headless_server()` falls back to `config_read("gui2","role")`, and *server* `config.ini` is copied by hand (`server_setup.sh:76-79`). If the role is set there but the env file is re-rendered without `DPD_GUI2_ROLE`, or vice versa, a desktop user with `role = contributor-server` in their local config.ini gets their editor exited mid-edit. Fix: gate on `FLET_FORCE_WEB_SERVER`/`page.web and is_headless_server()`, never role alone; assert at startup and log.

**Major — no rollback for half-filled forms, and the "still there?" page claims safety it does not have (evidence: `gui2/main.py:665-700` comment, `gui2/example_stash_manager.py:37-44`).**
Only the `last` example/commentary stash is persisted. Exiting loses Pass2Add/Sp/' forms. The idle flow must be cancelled by *any* keystroke and must not exit while a dialog is open (`is_dialog_open`, `gui2/ui_utils.py:170`) or while a tab's work is unsaved. Otherwise contributors lose work nightly-adjacent, which is worse than the nightly stop today.

**Nit — the static wake page is outside the mount (evidence: `scripts/server_contrib/nginx_contrib_user.conf.template:8-31`).**
Only `/@USER@/` is proxied; a `/.dpd/asleep.html` page needs its own `location` in every rendered per-user conf. Existing confs are rendered once by `add_contributor.sh` and never re-rendered, so every current contributor needs a manual nginx edit + reload — a runbook step the EGM omits.

**Rollback summary missing:** there is no plan for a *bad idle implementation* (guessing at reconnect/`_self` behaviour). Ship it behind `DPD_GUI2_IDLE_MINUTES=0` (disabled) for one night, with the notice file writer already live and only the message shown.

### observability

I have enough for the observability lens. Findings below.

## Findings (observability & debuggability)

**1. Blocker — the proposed idle mechanism is invisible by construction.** `gui2/main.py:152` sets `page.on_keyboard_event` only; there is no `on_interaction`, click, or scroll hook. The hypothesis says "gui2 tracks the last user action" — but almost every event in this app is a button click, dropdown change, or tab switch, none of which reach a keyboard-only hook. Built as written, the idle timer would show "you are inactive" to a contributor who has been clicking for ten minutes. There is no log line at all, so the maintainer's first triage question ("did it sleep on its own, or did the user idle out?") would be answered only by reproducing the bug. Fix: derive activity from `Session.dispatch_event`, and log every idle→asleep transition with the idle duration and the last event name.

**2. Blocker — "my work vanished" has no forensic trail.** The process exit path planned (`os._exit`/systemd restart) writes nothing. `claim_session` (`gui2/main.py:794-805`) logs only when it *fails* to retire a page (`pr.red`). `release_session` logs nothing. `main()` (`gui2/main.py:827-845`) logs nothing on start or exit. `pr.red` goes to stdout only (`tools/printer.py:107-110`), which systemd sends to the journal — and `TimeoutStopSec=30` (`scripts/server_contrib/dpd-gui@.service:27`) means a stop during a half-filled form leaves no record of what the contributor had typed. Fix: log start (pid, role, user), the claimed session, every idle/notice/stop decision with the reason, and on exit the active tab and whether the form was dirty. Without a dirty-form flag the answer to "did they lose work?" is unknowable.

**3. Major — the nightly warning depends on a file nobody monitors.** `maintenance_window.py:90-91, 300-302` writes `status.txt` only in `_write_status`, i.e. **after** the window ends. The notice file the hypothesis proposes (written 30 min ahead) does not exist in any anchor, and nothing in `_make_logger` (`maintenance_window.py:196-210`) records *when* the warning was written or whether gui2 noticed it. If a contributor says "I got no warning", the maintainer cannot tell whether the file was never written, was written too late, or was written and gui2 failed to poll. Fix: log the notice-file write with a timestamp in the maintenance log, and have gui2 log each poll hit at the moment it shows the 30/15/10/5 banner.

**4. Major — sleep/wake is indistinguishable from a crash in the logs.** `Restart=on-failure` with `RestartSec=10` (`dpd-gui@.service:23-24`). The memory report already records a related ambiguity: `systemctl stop` leaves the unit `failed` because "gui2 exits non-zero on SIGTERM" (`kamma/archive/20261102_contrib_mem_measure/artifacts/results.md`, Deviations). A planned idle exit that also exits non-zero is, in journalctl and `systemctl status`, identical to an OOM or an exception. Fix: exit 0 on intentional sleep, and `systemctl kill --signal=SIGCONT`/`systemd-notify` a distinct state, or at minimum log one line `pr.green("idle sleep: N minutes, reason=...")` so `journalctl -u dpd-gui@alice | grep 'idle sleep'` answers it.

**5. Major — no wake-side signal.** The claimed wake path ("systemd restarts an empty process ~87 MB that loads the db when a page connects") has no log around `App(page)` vs `_initialize_db_in_background` (`gui2/main.py:766-771`). A contributor reporting "it takes minutes, not a minute" leaves the maintainer unable to separate process start from db load from warm-up. `App initialized in Xs` is a bare `print` (`gui2/main.py:843`), not routed through `pr` and not timed against db load. Fix: log a `wake` line at process start, at db-ready, and at warm-up-done with elapsed times.

**6. Nit — the notice surface hides.** `show_global_snackbar` uses `page.show_dialog` (`gui2/ui_utils.py:143,166`), behind `is_dialog_open` (`ui_utils.py:156-167`) which excludes snackbars from the "a popup is open" test. A 30-minute warning delivered as a 4-second snackbar while the contributor is in a modal will scroll, not appear. No metric distinguishes "shown" from "seen". Fix: use a persistent `ft.Banner` for the countdown, log `notice shown` each time, and never replace an open dialog.

**7. Nit — `status.txt` records outcome, not windows.** `maintenance_window.py:229-262` copies lines matching ` ERROR `/` WARNING ` from the run. The 30-minute-before notice is not in it, so `/status` cannot corroborate a "no warning" complaint. Add a `notice-warned:` line each time the notice file is written.

### techdebt

**Long-term tech debt review — gui2 / Flet / cron / nginx coupling**

**Blocker — the "restart empty process" premise conflicts with `claim_session`'s own design note.** `gui2/main.py:781-786` states Flet does not always fire `on_disconnect` on reload, so the old page is retired in-process rather than being relied on to release. The plan instead depends on `on_disconnect`-driven idle tracking and on the browser reconnecting to a *new* pid. Two failure modes follow: (a) if the idle timer keys off `on_disconnect`, a naturally closed tab never reclaims memory — the exact 1.5 GB the whole EGM exists to reclaim; (b) if the timer exits the process while the websocket is live, `release_session` never runs and the client's own reconnect (untested, per your own claim list) may re-hit a half-dead socket. Fix: track activity from a real event hook, not `on_disconnect`; verify Flet's `reconnect_*` behaviour before designing the exit; give the exit a hard path (`os._exit` after a best-effort page update) so a hung socket can't leave a zombie holding 1.5 GB.

**Major — memory reclaim is not actually delivered by the design.** Your own note says CPython rarely returns freed memory, and `results.md` shows the app's mass is built in `App.__init__`/warm-up, not at `main()` (`gui2/main.py:614-700`, `_WARMUP_TAB_ORDER`). The proposal's "restart an empty process" only works if the *exit* is guaranteed and systemd actually restarts. `Restart=on-failure` with `StartLimitBurst=5`/300 s (`scripts/server_contrib/dpd-gui@.service:6-7`) means an idle-exit that returns 0 is **not** restarted — a deliberate `sys.exit(0)` yields a dead unit with nginx 502s, and a crash-looping instance hits the burst limit and stays down until the next cron run. Fix: exit non-zero by contract (document it in the unit) or add `Restart=always` + `RestartSec` with a `SuccessExitStatus=0` review; and assert the limit can't be tripped by an idle-exit loop.

**Major — nginx coupling is per-user templated and will duplicate the maintenance page N times.** `scripts/server_contrib/nginx_contrib_user.conf.template` is stamped per contributor by `add_contributor.sh`. Adding a "being updated" static page means either (a) N copies of the same `location = /@USER@/maintenance` block, drifting independently, or (b) a `root`/`try_files` path nginx must be able to read — while the file is *written by root cron* into `logs/`, which the template's own comment notes "only root can read" (`maintenance_window.py:45-49`). Fix: serve the maintenance page from a single site-level `error_page 502 503 = /maintenance.html` plus `proxy_intercept_errors`, not a per-user location; write the notice file world-readable to a fixed `/var/lib/dpd/` path, not under `logs/`.

**Major — two independent idle/warning clocks with no rendezvous.** gui2 polls a notice file every minute; cron writes it 30 min ahead. `maintenance_window.py` stops instances *before* any of the 30–55 min work, and `_systemctl("stop", ...)` is the first action (`run_maintenance`, line ~"stop_failed"). If the pre-stop notice is written by a wrapper script that is not the same code path as the window, a manual run (`server_setup.sh:157` calls it with `--no-systemd --no-push`) or an operator's ad-hoc `maintenance_window.py` invocation bypasses every warning. Fix: make the notice a *step inside* `run_maintenance` (it already has an injectable `WindowSteps` seam), so no invocation can stop instances without arming warnings.

**Major — Flet-internals dependency.** `Session.dispatch_event` / `page.session` are private-ish; the plan's "last user action" tracker will pin gui2 to Flet 1.0.1 internals exactly as `page._dialogs.controls` already does (`gui2/ui_utils.py:175`). On the next Flet upgrade, paths break silently — the app keeps working, the timer never fires, memory is never reclaimed, and no one notices. Fix: add a startup self-test (or a one-line assertion) that the hook is installed, and prefer a public hook (`on_keyboard_event` already set at `main.py:152` catches keys but not mouse).

**Nit — comments already rot.** `main.py:777-778` cites "~2.5 GB" which `results.md` correction #5 explicitly retracts. Any doc added for this feature will rot the same way. Fix: cite `results.md` by anchor rather than inlining numbers.

**Nit — Alt+? doesn't advertise PgUp/PgDn**

The shortcut table claims "Page Up / Page Down — Scroll Pass2Add" but no `("Page Up", …)` row is generated; only `_SCROLL_KEYS` exists (`main.py:344-348`, `shortcut_groups`). Same class of drift the new warning UI will accumulate.

## Disposition

Facts were checked against the source before each decision. "Escalate" items go to the owner as single questions.

| # | Finding (deduplicated) | Severity | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| 1 | Contrarian: use systemd socket activation / an idle knob instead of an in-app idle clock | Blocker | Reject | A Flet tab keeps one websocket open while the person is away, so any connection-level idle measure (socket activation, `systemd-socket-proxyd --exit-idle-time`) never fires. Flet's `ft.run` binds its own port. Only the app sees clicks and keys. | spec: Assumptions |
| 2 | Contrarian: the unit, nginx and cron files are not in the repo | — | Reject | False: `scripts/server_contrib/dpd-gui@.service`, `nginx_contrib*.conf.template`, runbook step 8d hold them | — |
| 3 | nginx should answer a 502 with a friendly static page, from one site-level location, not N per-user copies | Major | Accept | `nginx_contrib_user.conf.template` has no `error_page` for 502; per-user confs are rendered once by `add_contributor.sh` and never re-rendered | spec: What it should do §C |
| 4 | Contrarian: one static page instead of two; drop the "still there?" countdown | Major/Nit | Reject | Asleep and nightly-update need different wording (UX #7). Without the countdown, a person reading without typing loses their form with no chance to stop it | — |
| 5 | Waking reloads the whole db (~943 MB); the saving only exists for people who stay away; measure the wake time before the message promises "about a minute" | Blocker | Accept | `App(page)` builds per session; `kamma/archive/20261102_contrib_mem_savings/artifacts/results.md` rows 22–23 | spec: Assumptions; plan: measurement task |
| 6 | Many people waking at once, and every open tab reconnecting after the nightly start, overload 2 vCPU | Major | Accept (partly) | Sending each browser to a static page before the process stops removes the reconnect storm; a real simultaneous wake stays a recorded risk; no CPU weighting added | spec: Assumptions, Not included |
| 7 | No `MemoryMax` on the unit, although an earlier results file talks of a 2 GB cap | Major | Reject (out of scope) | Confirmed: unit has none (`rg MemoryMax scripts/server_contrib/` → only the password service). A cap kills an active person's editor; a separate decision | spec: Not included |
| 8 | Rebuild-window peak memory | Major | Reject | Reviewer itself says no fix needed; unchanged by this thread | — |
| 9 | Activity must come from Flet's event dispatch (clicks, keys, tab changes), not the keyboard hook; check at start that the hook is in place, since it ties gui2 to Flet internals | Blocker | Accept | `flet/messaging/session.py:432` `dispatch_event`; called from `flet_web/fastapi/flet_app.py:385` | spec §A; plan: guard test |
| 10 | Snackbars vanish in 2–5 s and share the dialog stack; the header scrolls away | Nit | Escalate | `gui2/ui_utils.py:137-163`; `gui2/main.py:182-195` | owner question: placement |
| 11 | The window itself must arm the warnings 30 min ahead (a step in `run_maintenance`), cron moves to 00:30 | Blocker | Accept | `maintenance_window.py` stops instances first (`run_maintenance`); runbook cron `0 1 * * *` | spec §B |
| 12 | Warnings must run on a server-side timer, not on user events | Blocker | Accept (clarify) | The hypothesis said "checks every minute"; made explicit | spec §B |
| 13 | One shared notice file outside the git tree, readable by every instance | Major | Accept | `_restore_build_changes` / dirty-tree check act on tracked files; `/var/lib/dpd/` already holds `status.txt` and `contrib_data` | spec §B |
| 14 | Wording: say unsaved typing is lost, tell them to save; no "press F5"; a button that opens the editor; relative times ("in 15 minutes"), not server clock times | Major | Accept | Server zone Asia/Colombo (tech.md); no form autosave | spec §D wording |
| 15 | Two wordings: asleep (routine) vs nightly update (may last up to an hour) | Major | Accept | `STEP_TIMEOUT = 3600` | spec §C |
| 16 | A clean idle exit (0) is not restarted by `Restart=on-failure` → URL 502s until morning | Blocker | Accept | `dpd-gui@.service:22`; SIGTERM already exits non-zero (mem_measure results, Deviations) | spec §A: `Restart=always` |
| 17 | Installed unit and nginx files are rendered copies outside git; the window's git rollback cannot roll them back; existing servers need a manual step | Blocker | Accept | `server_setup.sh:104-105` re-renders the unit on every run; `add_contributor.sh` refuses to overwrite | plan: rollout phase |
| 18 | Gate everything on `page.web and is_headless_server()`, so a desktop with a stray role setting is never put to sleep | Major | Accept | `tools/server_mode.py` falls back to `config.ini` | spec §A |
| 19 | Don't sleep while the form holds unsaved work | Major | Escalate | No whole-form autosave (`gui2/example_stash_manager.py` covers only examples/commentary) | owner question: unsaved work |
| 20 | Don't sleep while a dialog is open | Major | Reject | A forgotten open dialog would then block the reclaim forever; the countdown dialog is the guard | — |
| 21 | A kill switch so a bad idle build can be turned off without a code push | Nit | Accept | One env value in `/etc/dpd/<user>.env`, `0` = off | spec §A |
| 22 | Log every decision: start, session claim, idle → asleep with idle time, notice armed, warning shown, wake timings; one maintenance-log line when the notice is written | Blocker/Major | Accept | gui2 logs nothing on start/exit today (`gui2/main.py:811-845`) | spec §E |
| 23 | The exit must be certain even if the socket hangs | Major | Accept | Flet's server loop runs in the main thread; plan uses a hard exit after a short grace | spec §A |
| 24 | Idle detection must not rely on `on_disconnect` | Blocker | Reject (already so) | The clock is process-wide and counts from the last event, so a closed tab simply stops sending events | — |
| 25 | Stale "~2.5 GB" comment in `gui2/main.py:776`; Alt+? table lacks PgUp/PgDn | Nit | Reject | Unrelated to this thread; reported to the owner | — |
| 26 | Brief's 1.2–1.5 GB per instance is stale | Major | Accept | mem_savings results: 943.3 MB ready, 1,045.7 MB after one book | spec: Overview |

Counts: 26 findings — 16 accepted (incl. 2 partly/clarify), 8 rejected, 2 escalated.

## Owner answers to the escalations (2026-11-09)

- #10 Placement of the nightly warnings → **Top banner** (persistent, non-blocking, "Got it" hides it until the next step, amber then red at 5 minutes).
- #19 Half-filled form when the editor sleeps → **Sleep anyway** (same as the nightly stop today; the 2-minute "Still there?" countdown is the only guard).
