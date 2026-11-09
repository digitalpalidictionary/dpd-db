You are a Goldfish reviewer. You have no earlier context. You are strictly read-only: report findings, change nothing.

Safety:
- Never open a file that may hold secrets: `.env`, `*.ini` with keys, htpasswd files, private keys.
- Never run or import project code. Some modules load API keys when imported.
- Use no network and no ssh.
- Never create files or run git.

The repo is the current directory (the Digital Pali Dictionary project). Use the read tool with repo-relative paths.

Task: Lens: UX for non-technical contributors around the world. Is it clear what happened and what to do? Where should the warnings show, and what wording? What do they lose? Time zones?

Inputs: The request and anchored hypothesis below.

# EGM brief — 20261109_contrib_idle_notices

**Issue:** #215 (contributor web server)

## Request (owner's words, condensed)

1. When a contributor is inactive, reclaim the server resources so active people get them. The user base is global, so people use the server at different hours.
2. When they have gone inactive, show a message in the GUI saying so, and that it takes a moment to get back to full power. The owner asked us to choose the wording (maybe "press F5 to restart").
3. Before the daily rebuild, warn the user that the editor shuts down in 30, 15, 10, 5 minutes, and so on.
4. The owner asks where the warning should go: a snackbar? a message bar in the header?


## Anchored hypothesis

Every contributor's gui2 process stays loaded at ~1.2–1.5 GB from first use until the nightly stop, even while the person is away, and the nightly stop at 01:00 cuts people off with no warning. Approach: (1) on the server only, gui2 tracks the last user action; after N idle minutes it shows a "still there?" countdown, then sends the browser to a static "the editor is asleep — click to wake, it takes about a minute" page and exits; systemd restarts an empty process (~87 MB) that loads the database only when a page connects. (2) The nightly job writes the planned stop time into a small notice file 30 minutes ahead; gui2 checks the file every minute and shows warnings at 30/15/10/5/1 minutes, then sends the browser to a static "being updated" page; nginx shows the same page while the instance is down. Scope: gui2 server mode only (desktop unchanged), the systemd unit, the maintenance window and its cron line, the nginx templates, two static pages.


Claims to re-check, not facts:


- One gui2 process per contributor: systemd unit `scripts/server_contrib/dpd-gui@.service`, `Restart=on-failure`, `RestartSec=10`, `StartLimitBurst=5` in 300 s. Port per user from `/etc/dpd/<user>.env`, bound to 127.0.0.1, nginx in front (`scripts/server_contrib/nginx_contrib_user.conf.template`, basic auth per user, `proxy_read_timeout 3600s`).
- Memory per process on the server (`kamma/archive/20261102_contrib_mem_measure/artifacts/results.md`): 86.5 MB 15 s after start with no page open; 718.6 MB after the db load; 1,165.9 MB after the warm-up; 1,485.0 MB after one Pass1 book; alice's long-running instance 1,542.8 MB. Since then a word-finder change saves ~170 MB for contributors without the Pass2Add tab. The database and warm-up load happen per page session (`App(page)` in `gui2/main.py`), not at process start.
- Server: 2 vCPU, 8 GB memory, 4 GB swap (`kamma/tech.md`).
- CPython rarely gives freed memory back to the OS, so dropping objects inside a running process is not a reliable way to reclaim it (general knowledge, not measured here).
- Nightly window: root cron `0 1 * * *` runs `scripts/server_contrib/maintenance_window.py --instance dpd-gui@<user> ...` (server zone Asia/Colombo, `NEW_SERVER_RUNBOOK.md` step 8d). It stops every instance, pulls, reconciles, pushes, rebuilds only if `main` moved (30–55 min), then starts every instance in a `finally`. Instances stop every night, even when nothing is rebuilt.
- gui2 has one live session per process (`claim_session` / `release_session`, `gui2/main.py:774-825`); a newer page retires the older one.
- Every client event in Flet 1.0.1 passes through `Session.dispatch_event` (`.venv/.../flet/messaging/session.py:432`; called from `flet_web/fastapi/flet_app.py:385`). `page.session` gives the Session (`flet/controls/page.py:1304`). gui2 sets `page.on_keyboard_event` (`gui2/main.py:152`).
- Flet's web client has `reconnect_interval_ms` / `reconnect_timeout_ms` settings (`flet_web/web/main.dart.js`); its default reconnect behaviour was NOT checked. A reconnect to a new process with an unknown session id creates a new session and runs `main` again (`flet_web/fastapi/flet_app.py:275-341`).
- `UrlLauncher.launch_url(..., web_only_window_name=...)` exists (`flet/controls/services/url_launcher.py:72`), and `UrlTarget.SELF = "_self"` exists. Whether a server-pushed `_self` navigation works in the browser was NOT checked.
- Snackbars go through `show_global_snackbar` (`gui2/ui_utils.py:137`) → `page.show_dialog`, and the app already uses them for short status messages ("Database loaded.", "All tabs and tools ready."). `ft.Banner` exists in Flet 1.0.1. The web header (`_web_header`, `gui2/main.py:182-195`) scrolls away with the page on purpose.
- No whole-form autosave exists in gui2; only the example/commentary "last" stash (`gui2/example_stash_manager.py`). A process exit loses a half-filled form.
- `tools/server_mode.py::is_headless_server()` tells server mode apart from the desktop.



Read the inputs and every file they reference. Open at most 15 files.

Report each finding as: severity (Blocker / Major / Nit), evidence as `file:line`, the failure scenario, and the fix.
Lead with problems. No praise. Use at most 600 words.
