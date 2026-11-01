# Handoff: temporary server test (rewritten 2026-10-31)

**Thread:** 20261023_contrib_4_temp_server_test · read `spec.md`, then `plan.md`.
**GitHub issue:** #215. Never write to the issue.
**Next task:** Phase 0 (maintainer), then Phase 1, task 1.1. No task is started.

## For the server agent
- You are a smaller model on the server, not Claude. `plan.md` has a rules
  section at the top. Obey it exactly.
- Write results only to `results.md` in this folder. Never edit this file,
  `spec.md` or `plan.md`.
- This folder sits in `~/dpd-contrib/handoff/`, outside the clone. Keep it there. Inside
  `~/dpd-db` it would make tracked files dirty and break `git pull`.
- There is no tmux and no herdr on the server. gui2 runs in the background
  through `~/start_gui2.sh` and stops through `~/stop_gui2.sh` (task 2.7).
- When unsure: STOP, write what you saw in `results.md`, and ask the
  maintainer.

## State of the series
- Done and archived: `contrib_2_edits_json`, `contrib_5_hardening`,
  `contrib_3_preview_before_save`.
- Commit `5497d80c` (contrib_3) was on the maintainer's local `main` only on
  2026-10-30. Task 3.1 checks for it on the server and waits until it is pushed.
- Still open: this thread, `contrib_1_web_server` (Phase 3 onward),
  `contrib_x_problem_children` (needs triage with the maintainer).

## Facts verified locally (2026-10-30 and 2026-10-31)
- `flet run` breaks the data paths. The start script uses
  `uv run python gui2/main.py` with `FLET_FORCE_WEB_SERVER=true`.
- Flet reads `FLET_SERVER_IP`. The start script sets it to `127.0.0.1`.
  Task 2.8 still checks the bind address with `ss -ltn`.
- The preview page is written to `gui2/assets/preview/preview_<user>.html`
  and opened by a relative URL. If the browser blocks the new tab, the
  "Open preview" button in the dialog is the fallback. Untested over a real
  tunnel and behind a path prefix.
- `dpd.db` runs in WAL mode. Task 2.3 folds the WAL into the db before the
  copy, and task 2.4 compares sha256 on both sides.

## What needs the maintainer
- The host and SSH details, Phase 0, and every MAINTAINER step in `plan.md`.
- Typing the API keys (task 2.5) and any password (Phase 4).
- Pushing `main` to GitHub before Phase 3.
- Clicking through the browser checks (tasks 2.9, 3.4, 4.3).
