# Plan: contributor dashboard

Read `spec.md` first.

## Architecture Decisions

- One script, `scripts/server_contrib/contrib_dashboard.py`, run by cron every minute (`uv run --no-sync` from `/root/dpd-db`, like `maintenance_window.py`).
- It reads everything again each run: no state file. It reads the last 14 days of the journal, so a lane can say when that person was last seen (1,903 lines on 2026-11-13, parsed in 8 ms).
- Pure functions for the parts that can be tested without a server: journal lines → events → visits → lane states, and data → HTML. The systemctl, journalctl and psutil calls stay in thin readers.
- One static HTML page with inline CSS; the DPD variables are read from `identity/css/dpd-variables.css` at run time, so a palette change reaches the page. No JavaScript libraries.

## Phase 1 — Visits and lanes — *Pro*

- [x] Copy real `dpd-gui@bdhrs`/`deva` journal lines (JSON, only the fields the parser reads) into `tests/scripts/server_contrib/data/dashboard_journal.jsonl`.
  → verify: the fixture holds `page connected`, `page reconnected`, `countdown shown`, `asleep`, `Started`, `Stopped`, and no server address.
  → done: 239 lines from 2026-11-09 to 2026-11-13. The real journal has no `countdown cancelled` line yet; a synthetic test covers it.
- [x] Write the parser, visit builder and lane states, with tests in `tests/scripts/server_contrib/test_contrib_dashboard.py`.
  → verify: tests pass; a visit ended by `asleep: 32.1 min idle` at 16:20:27 ends at 15:48:21.
  → done: 17 pass. Reverting the idle subtraction fails 1 test; letting every connect open a new visit fails 2.
- [x] Print every visit the parser builds from the full fixture and read them all.
  → verify: none is negative, none spans a stop.
  → done: 13 visits, all closed, none negative, each ends at a stop or at the last action before sleep. Today's live journal and unit state (fetched read-only, parsed on the laptop) give 8 asleep lanes at about 73 MB, which matched the server.

## Phase 2 — Page — *Fast*

- [x] Write the server readers (systemctl, daily logs, psutil) and the HTML writer.
  → verify: write the page from the fixture into the scratchpad; look at it in dark, light and phone width.
  → done: screenshots at 1300 px dark and light and at 400 px; the phone layout was fixed after the first look.
- [x] Add `gui2/assets/icons/loading-animation.png` (copy of `identity/logo/dpd-logo-dark.png`).
  → verify: a local web run of gui2 serves the DPD logo at `/icons/loading-animation.png`.
  → done without starting gui2: Flet's own file server (`FletStaticFiles` with `assets_dir=gui2/assets`) resolves `icons/loading-animation.png` to the new file, byte-identical to the DPD logo.
- [x] Add the inline DPD dark logo to `scripts/server_contrib/pages/asleep.html`.
  → verify: open the page; the logo shows above the heading.
  → done: screenshot checked.
- [x] Phase check: ruff check, ruff format, pyright on the new files; the tests.
  → verify: all clean.
  → done: ruff, ruff format, pyright (and pyright on the test file with `--project /dev/null`), 17 tests, `just typecheck` all clean.

## Review — 2026-11-13

- CodeRabbit (script folder, test folder) and one independent reviewer, run in parallel.
- Fixed: two overlapping cron runs shared one temp file (each run now uses its own name); a process that died without a `Started` line left its visit open all day (process-exit lines now end a visit); the 10-second auto-restart after a sleep showed the lane as down (`activating` now counts as up); journalctl exits 1 when no unit matches, which stopped the page from being written (now logged and the page still written).
- Not fixed, written in the spec: a hard power loss counts as time online until the next boot.
- Spec corrected: `gui2/assets/` is not tracked as a folder; the loading image must be added to git by name.
- 5 tests added (22 in all). Undoing each fix fails its test.
- Lane labels shortened to "min", "today", "total" at the owner's request.

## Owner changes after the live look — 2026-11-13

- The timeline shows the last 24 hours, now at the right edge; ticks on clock hours, midnight labelled with the day. Minutes count the same 24 hours.
- A never-seen account says "added today, not seen yet" (env file time) instead of "not seen in 14 days".
- The memory figure keeps its number and unit on one line.
- 5 tests added (27 in all). Reverting the window fails 1; dropping the added wording fails 1.

## Phase 3 — Server install — *Fast* (needs the owner's go-ahead)

- [x] Add `scripts/server_contrib/nginx_dashboard.conf.template`; install it on the server with a backup; `nginx -t`; reload.
  → verify: `curl` on the host answers 401 without a login and 200 with the maintainer login.
  → done 2026-11-13: `nginx -t` ok, reloaded; 401 without a login, `/dashboard` → 301 to `/dashboard/`. The 200 with a login is the owner's browser check (no password on the agent side).
- [x] Add the cron line with a backup of the crontab.
  → verify: after 2 minutes the page time has moved.
  → done: page rewritten at 14:33:02, cron log empty.
- [x] Copy the new `asleep.html` to `/var/www/dpd-pages/` with a backup (runbook step 6e).
  → verify: `curl` of `/<user>/_dpd/asleep.html` holds the logo.
  → done: 200, logo present, wake time still 20 seconds.
- [ ] The loading image reaches the server with the next nightly pull after the commit.
  → pulled by hand on 2026-11-13 (`c800ded2`, no editor restart: the pull held no code the editors run). Owner to confirm the logo on the next editor load.
  → verify: the next day, `/<user>/icons/loading-animation.png` is the DPD logo.
- [ ] Phase check: `just typecheck`; `scripts/server_contrib/README.md` names the page and the cron line.
  → verify: typecheck clean; the README names both.
  → README section, install record and runbook Step 7f written 2026-11-13; typecheck clean. Tick after the owner's browser check.
