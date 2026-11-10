# Phase 5 server rollout log (2026-11-09)

Reached over ssh from the laptop with the target from `config.ini`. Live instances: `dpd-gui@bdhrs`, `dpd-gui@deva`.

## 5.1 Pull (done)

Checks first: clone clean (0 changed files), no window running, 2 commits behind, fast-forward yes, 0 `resources/` paths in the diff. `git pull --ff-only origin main` moved the clone from `36b75c79` to `b1b25007`, the same commit as the laptop. Clone clean after. Both instances stayed `active` and were not restarted.

## 5.2 Unit (done)

Backup: `/root/mem/dpd-gui@.service.before_20261109`. Rendered with the installed values (`User=root`, `HOME=/root`, clone `/root/dpd-db`, `uv` `/root/.local/bin/uv`). The only difference from the installed unit was the restart lines. `daemon-reload`. `systemctl show` for both instances: `Restart=always`. Both `active`.

## 5.3 Pages and nginx (partial: the 502 sight check is not done)

Backups in `/root/mem`: `dpd-contrib.before_20261109`, `bdhrs.conf.before_20261109`, `deva.conf.before_20261109`. Installed `offline.html` (mode 644) to `/var/www/dpd-pages/`; `asleep.html` waits for 5.5. Added the regex location to the site file and the `error_page 502 503 504` line to both user confs, from the templates. `nginx -t` passed, `systemctl reload nginx`.

curl on the host (with the server name resolved to loopback), after the reload settled:

| URL | Answer |
|---|---|
| `/bdhrs/_dpd/offline.html`, `/deva/_dpd/offline.html` | 200, text "not running right now" present |
| `/bdhrs/_dpd/asleep.html`, `/deva/_dpd/asleep.html` | 404 (file not installed yet, expected) |
| `/bdhrs/` | 401 (login gate unchanged) |
| `/status` | 401 (unchanged) |

A first check made right after the reload answered 401 for the pages; the same check a few seconds later answered 200. Likely cause: the old nginx workers were still answering for a moment after `reload` (the delay was not timed). Wait a few seconds before the first curl.

Not done at this point: the owner sight check that a stopped instance shows the offline page and not "502 Bad Gateway". It needs a stop of an instance and a login. **Closed later**: see the section "nginx offline page and the button, seen live (2026-11-10 05:05)" at the end of this log.

## 5.8 Cron (done)

Backup: `/root/mem/crontab.before_20261109`. The window line now starts at `30 0 * * *` and has `--warn-minutes 30`; every other argument and the `PATH` line are unchanged. Both instances stay in the line. Tonight (00:30, server time) is the first real run of the new window code; deva is asleep then (Malaysia), so the owner chose not to test the window by hand.

## 5.4 Wake time (partial)

Four attempts on `dpd-gui@bdhrs` (a server restart, then one page opened in the owner's Chrome on the laptop, one page session at a time). Three gave a reading. "tabs ready after" in the journal: 59.6 s (first start after the pull, cold file cache), 18.3 s. The attempt after those did not log a "tabs ready" line within my wait, so it gave no reading; I do not know why. The third reading, 18.1 s, came from a later clean round after the colour fix was pulled. Median of the three readings 59.6, 18.3 and 18.1 is 18.3, rounded up to 20. The 59.6 s start was cold (right after the pull), so 20 s is the typical wake, not a limit.

## 5.5 Asleep page (done)

`asleep.html` now says "Waking takes about 20 seconds". Installed to `/var/www/dpd-pages/` (mode 644) straight from the laptop copy; both users answer 200; no "N seconds" left. The repo copy and its test are changed and need a commit.

## 5.6 Idle sleep live test on bdhrs (done)

The test setting `DPD_GUI2_IDLE_MINUTES` was set in the bdhrs env file only (backup `bdhrs.env.before_idle_test` in `/root/mem`). Checked afterwards: the key is in neither env file nor in the unit. Results:

- Real Chrome tab through nginx, 1-minute setting, tab left alone: `countdown shown after 1.2 min idle`, then `asleep: 3.2 min idle, 1 page(s) sent away, connected=True`, the process exited and the port was free. The tab showed the asleep page (screenshot `asleep_page_live.png`).
- With the real unit: after a sleep with no page open (`connected=False`) systemd restarted the unit after 10 s (`NRestarts=1`). The new process had no page open and held 99.8 MB (`VmRSS` read 18 s after the start); the old one, with a page open, peaked at 766 MB. A loaded editor is the 766 MB figure; the 100 MB is the empty process. A clean restart with no page: 99.9 MB.
- "Wake the editor" brought the editor back: new process, `page connected`, `tabs ready`, idle 30 min (default).
- The test setting is removed and the env file is identical to its backup.

The first attempt (2-minute setting, real Chrome tab, accessibility click) showed no countdown for 9 minutes while the tab was connected. Two later runs, one through an ssh tunnel and one through nginx, both showed the countdown after 1.2 minutes with every event logged: only the connect events arrived. The cause of the first failure is not found. My own screenshot and page reads in that tab came at about 17:31 and reset the idle time; they do not explain the 7 quiet minutes before. If a real contributor reports an editor that never sleeps, add event-name logging first.

## 5.7 Window test: skipped

Owner decision: tonight's 00:30 run is the first real run of the new window (deva is asleep then).

## Cron check after the edit

Cron was checked after the edit: one line, `30 0 * * *`, with `--warn-minutes 30`; the window script accepts both new flags (`--help`). The check of the first real night is section 5.9 below.

## 5.9 First real window (2026-11-10)

Read over ssh at 04:45 server time. Read only; nothing was changed.

Maintenance log `maintenance_20261110.log`:

| Time (server) | Line |
|---|---|
| 00:30:04 | `maintenance window start`, then `notice armed: stop at 19:30:04 UTC` (that is 01:00:04 server time) |
| 01:00:29 to 01:00:30 | stop of `dpd-gui@bdhrs` and `dpd-gui@deva`: 25 s after the announced stop time, as designed (`OFFLINE_GRACE_SECONDS`) |
| 01:01:14 | pull and submodules; reconcile; contributions pushed (4 changed files); translation db present |
| 01:02:11 to 01:28:55 | db rebuilt, components generated, health check passed, WAL re-applied |
| 01:28:56 | both instances started, `notice removed`, `dpd.db.prev` removed, `maintenance window end: rebuilt` |

Other expectations:

- `/var/lib/dpd/status.txt`: `outcome: rebuilt`, `problems: 0`.
- `/var/lib/dpd/notice.json` does not exist.
- Both units `active`, `restarts=0`, since 01:28:56.
- No Traceback, `tick failed` or `could not reach a page` in either journal since 2026-11-09 23:50 (a first query with relative time words returned nothing because `journalctl` could not parse them; it was rerun with absolute times and both journals then had 6 lines each, all systemd stop and start lines).
- Cron: one line, `30 0 * * *`, with `--warn-minutes 30`.

**Banner and offline move: not observed live, and that is not a failure.**

- `dpd-gui@bdhrs` was an empty process with no page open (idle sleep had restarted it earlier in the day: 75.9 MB at the stop).
- `dpd-gui@deva` was still the process started before the new code was pulled (900.8 MB at the stop, up since the previous afternoon), so it did not read the notice file at all. It has run the new code since the 01:28 start.
- So no editor could show the banner or move to the offline page. The banner colours and steps are proven only locally (real Chrome, `banner_amber_15min.png`, `banner_red_4min.png`) and by unit tests. The spec's "how we will know it is done" item 4 (banner seen on the server, tab moved to the offline page at the stop) is still open.

## Live banner test on the server (2026-11-10)

Why: 5.9 could not show the banner (nobody had a page open on new code). Setup: `dpd-gui@bdhrs` stopped; a copy of the editor ran on its port, started with the same env file, idle sleep off, and a private notice file (`/root/mem/test_notice.json`) that ended 8 minutes after it was written. The real notice file was never written, so `deva` (new code since 01:28) was not affected: no banner, offline or notice lines in its journal. The owner opened the editor in his own Chrome through nginx.

Server log of the test copy (all `lifecycle:` lines):

- `notice seen: stop at <time>`
- `banner step 10: 8 minute(s) left`
- `banner step 5: 5 minute(s) left`
- `banner step 1: 1 minute(s) left`
- `sent 1 page(s) to the offline page`
- 0 Traceback, `tick failed` or `could not reach a page` lines.

Seen by the owner on screen: the banner came up, and "Got it" closed it, at step 10 and again on the red banner at step 5. Also confirmed by the owner: his tab landed on the offline page ("The editor is not running right now") at the stop time.

Cleanup: test copy stopped, port free, test notice and pid file removed, `dpd-gui@bdhrs` started from systemd (`active`, 0 restarts), real notice file absent, cron line unchanged.

## Offline page without a button (2026-11-10, owner request)

Why: waking from sleep works at once, so the asleep page keeps its button. During the daily update a click cannot work, so the offline page must not offer one. The page now shows no button, asks the editor's address every 15 seconds, and shows "Open the editor" when the answer is anything but 502, 503 or 504.

Local check (headless Chromium, stub that answered 502 for 20 s and then 200): no button at 4 s; the button visible at 44 s, pointing at the editor. Screenshots `offline_page_waiting.png` and `offline_page_ready.png`. A CSS bug found on the way: the button's own `display` beat the `hidden` attribute; fixed with a `[hidden]` rule and pinned in the test.

Installed on the server (mode 644): both users answer 200 for the offline page, the new text is served, no "Try again" left. Not checked live on the server: the button appearing after a real update; the first real chance is the next night's window.

Known limit: a browser with no cached login gets 401 from the editor address even when the editor is down, and the page reads 401 as "back", so the button can appear early. A click then asks for the login and returns to this page while the editor is still down.

## nginx offline page and the button, seen live (2026-11-10 05:05)

`dpd-gui@bdhrs` stopped with `systemctl stop`; `deva` untouched. The owner opened the editor address in his browser: the offline page showed, with no button ("Checking every 15 seconds."), not a plain 502. After `systemctl start` the button "Open the editor" appeared within the check interval and opened the editor. This closes the one open point of spec item 4.
