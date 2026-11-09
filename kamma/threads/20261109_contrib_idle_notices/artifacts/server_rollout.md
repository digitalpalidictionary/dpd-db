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

Not done: the owner sight check that a stopped instance shows the offline page and not "502 Bad Gateway". It needs a stop of an instance and a login, so the owner does it in a browser; it can be folded into the next planned stop.

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

## 5.9

The check of tonight's logs, tomorrow morning. Cron was checked after the edit: one line, `30 0 * * *`, with `--warn-minutes 30`; the window script accepts both new flags (`--help`).
