# Spec: contributor dashboard

Status: rewritten 2026-11-13 from the owner's brief. Replaces the first draft (a usage table).

## Overview

The owner wants one page that shows, at a glance, the state of the contributor web server right now: who is in the editor, when each contributor was online in the last 24 hours, how many words they added, and how full the server is. The page uses the DPD look (`identity/`).

While in this area, two small editor-side changes: the DPD logo replaces the Flet logo on the editor's loading screen, and the DPD logo appears on the "asleep" page.

## What it should do

### The dashboard page

- **Header:** the DPD logo (dark version), the title "Contributor dashboard", and the time the page was written.
- **Two big numbers:**
  - words added today, by all real contributors together;
  - words added in total, by all real contributors together.
- **Server row:** one horizontal row of meters. Each meter is a bar that fills left to right: empty = little use, full = lots. Meters: disk, memory, swap, CPU load (5-minute average divided by the core count). Each meter shows its percent and the amounts (`19 of 96 GB`). The bar colour turns amber above 70 % and red above 90 %.
- **One lane per contributor:**
  - a status dot with a word: **online** (green, pulsing): the editor holds an open page; **going to sleep** (amber): the idle countdown is showing; **asleep** (grey): the editor runs empty; **down** (red): the unit is not running.
  - a timeline of the last 24 hours, with "now" at the right edge, one block per visit, a tick every 3 clock hours, and a stronger line at midnight labelled with the new day. Hovering a block shows its start, end and minutes. (Changed 2026-11-13 at the owner's request: the first version showed 00:00 to 24:00 of today.)
  - the minutes online in the last 24 hours, words today and words in total for that contributor. Words stay per calendar day, because the editor counts them per date;
  - a line under the name: "online since 13:02", "added today, not seen yet" (account date from its env file, within 14 days), "asleep, last seen 10:31" (or "yesterday", or a date, up to 14 days back), with the editor's memory.
- Test users (`bdhrs`, `deva`) get a lane with a "test" tag, below the real contributors. Their words do not count in the two big numbers.
- The page reloads itself every 60 seconds.
- Dark and light themes follow the browser setting, with the DPD colours from `identity/css/dpd-variables.css` and the Inter font from `identity/fonts/`.
- The page works at phone width: the lane's numbers wrap under its timeline.

### Editor loading screen

- The editor's web loading screen shows `identity/logo/dpd-logo-dark.png` instead of the Flet logo.

### Asleep page

- `scripts/server_contrib/pages/asleep.html` shows the DPD dark logo above its heading. The logo is inline SVG, because nginx serves only the two HTML files under `/_dpd/`.

## Current behaviour (verified 2026-11-13 on the live server, read-only)

- Each contributor runs as a systemd unit `dpd-gui@<user>`; users and ports live in `/etc/dpd/<user>.env`. Eight units today: test users `bdhrs`, `deva`; real contributors `antonio`, `cjyeh`, `danz`, `meg`, `panya`, `suddhassaddho` (all added 2026-11-13).
- The editor prints `lifecycle: ...` lines to the unit's journal (`gui2/server_lifecycle.py`). In `journalctl -o json` these lines carry `_SYSTEMD_UNIT=dpd-gui@<user>.service`. The systemd lines (`Started ...`, `Stopped ...`) carry `UNIT=dpd-gui@<user>.service`. The short text output does not name the unit on editor lines, so the JSON output is needed.
- Lines that matter, all seen in the real journal:
  - `lifecycle: page connected` and `lifecycle: page reconnected`: a page is open. One process can log several `page connected` lines (a second tab or a reload).
  - `lifecycle: countdown shown after <N> min idle` and `lifecycle: countdown cancelled`.
  - `lifecycle: asleep: <N> min idle, ...`: the editor exits. The last action was `<N>` minutes before this line.
  - `Stopped dpd-gui@<user>.service ...`: the nightly window (01:00) or a manual restart stopped the editor.
  - `dpd-gui@<user>.service: Main process exited ...`, `Failed with result ...`, `Deactivated successfully`: the process ended. These also end a visit, because a unit that hits its start limit (5 starts in 300 s) stays failed and never logs `Started`.
  - `Started dpd-gui@<user>.service ...`: systemd started an empty editor (after sleep, a stop, or a kill: `Main process exited, code=killed, status=9/KILL` was seen on 2026-11-09).
  - There is no line when a person closes the browser tab. An open visit with nobody there lasts until the `asleep` line, 30 to 32 minutes later.
- Words: the editor counts each new word it saves in `daily_log_<user>.json` in `/var/lib/dpd/contrib_data/` (`gui2/daily_log.py`), as `{"YYYY-MM-DD": {"pass1": N, ...}}`, dated in server time. Today only `bdhrs` and `deva` have one; the real contributors have not saved a word yet, so the file is missing for them.
- Memory: an empty editor holds about 77 MB (`MemoryCurrent`, read today on all eight units); one with a page holds about 775 to 900 MB.
- Server: 2 cores, 8 GB memory, 4 GB swap, 96 GB disk (21 % used). Time zone Asia/Colombo (+05:30). `psutil` is already a project dependency.
- `/status` is served by nginx from `/var/lib/dpd/status.txt`, behind the maintainer's htpasswd file (`scripts/server_contrib/nginx_status.conf.template`).
- Flet's web server looks for each file in the app's assets folder (`gui2/assets/`) before its own web folder (`flet_web/fastapi/flet_static_files.py`). The loading screen in Flet's `index.html` shows `icons/loading-animation.png` (512 × 512). So a file at `gui2/assets/icons/loading-animation.png` replaces it, with no change to Flet's files. Git ignores only `gui2/assets/preview/`, so the new image must be added to git by name; it reaches the server with the nightly pull.

## Design

- One script, `scripts/server_contrib/contrib_dashboard.py`, run by cron every minute on the server.
- Each run reads everything again, plus one saved file of minutes per day (below):
  1. `journalctl -u 'dpd-gui@*' --since <14 days ago> -o json`. Fourteen days give each lane a "last seen" time, and a visit open at midnight keeps its start.
  2. `systemctl show -p Id -p ActiveState -p MemoryCurrent` for every unit named by `/etc/dpd/*.env`.
  3. Every `daily_log_<user>.json` in the data folder.
  4. `psutil` for disk, memory, swap and load.
- Visits come from the journal: a visit starts at the first `page connected`/`reconnected` with no visit open, and ends at `asleep` time minus its idle minutes, or at `Stopped`/`Started`. A visit with no end is open; on the timeline it runs to now. Visits are cut to the last 24 hours.
- Periods (added 2026-11-13 at the owner's request): a toggle Day · Week · Month · Year · All. Day = last 24 hours and Week = last 7 days, as visit timelines. Month = last 30 days (bar per day), Year = last 52 weeks (bar per Monday-start week), All = every month since the first day with words or minutes (bar per month). Bar heights share one scale across lanes. The big words number and each lane's minutes and words follow the period; "total" stays all-time. The browser keeps the choice in local storage across the 60-second reload; without it the page shows Day.
- Time online per day is saved, in seconds, in `/var/lib/dpd/dashboard_seconds.json`, because the journal is deleted from its oldest end at its size limit. Each run recounts the last 7 days from the journal (it surely still holds them, and an open visit can shrink when it closes) and keeps older days as saved. A day is only recounted when the journal read covers all of it (the read's first line is at or before that midnight), so a cleared journal or a failed read never erases saved days. A visit across midnight counts on both days. A damaged file (bad JSON, bad text, wrong shape) is set aside as `.corrupt.<time>`; a failed save is logged and the page is still written.
- The page goes to `<out-dir>/index.html`, written to a temp file and then renamed, so nginx never serves half a page. The script copies the logo and the Inter font into `<out-dir>` when they are missing.
- nginx serves `<out-dir>` at `/dashboard/`, behind the maintainer's htpasswd file, like `/status`.

## Decisions taken (the owner can overrule)

- Address `/dashboard/`; output folder `/var/lib/dpd/dashboard/`.
- Cron every minute, page reload every 60 seconds.
- Day, Week, Month, Year and All through a toggle (replaces the earlier "last 24 hours only").
- Test users are shown, tagged, last, and left out of the two big numbers.
- "Words" = new words saved, the same count as the editor's own counter in its top bar.
- Time shown is server time, which is the owner's time (both +05:30).

## Assumptions & uncertainties

- A visit with nobody there counts until the editor sleeps (up to 32 minutes too long). The journal has no "page closed" line, and the brief says no editor change for the dashboard.
- A visit open at the nightly stop ends at the stop, even when the person left earlier.
- The `asleep` line is printed 3 seconds before the process exits. If it were lost, the process-exit line that follows would still end the visit.
- A hard power loss writes no stop line, so a visit open at that moment runs until the next `Started` after boot. A clean reboot logs `Stopped` and is fine. Not handled: it needs a power cut, and the boot id in the journal could fix it later.
- systemd reports "activating" during the 10-second auto-restart after a sleep. The lane counts that as asleep, not down.
- Browsers can cache Flet's loading image. A person may see the old logo once until the cache refreshes.

## Constraints

- No change to the editor's behaviour. The only editor-side file added is the loading image.
- Server config (nginx, cron) is verified on the live host with `curl`, not in the dev clone.
- Six real contributors use the server: never restart their units to test.
- The page is private: behind the maintainer login, never committed with real data. Committed text holds no server address (`<server-ip>`).
- Back up any server file before changing it (`/root/mem/<file>.before_<date>`).

## How we'll know it's done

- Unit tests turn real journal lines (copied from the test users' journal) into the expected visits and lane states.
- The page, written from the fixture into the scratchpad, shows the lanes, meters and numbers, in dark and light, and at phone width.
- On the server: `/dashboard/` answers 401 without a login and 200 with the maintainer login, and the page time moves every minute.
- The editor's loading screen shows the DPD logo (local web run of gui2).
- The asleep page shows the DPD logo.

## What's not included

- Alerts, emails or notifications.
- Changes to how the editor logs actions.
- The offline page (not in the brief).
- Any page that contributors can see.
