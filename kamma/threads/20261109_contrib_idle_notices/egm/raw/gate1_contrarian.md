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