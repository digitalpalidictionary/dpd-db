# Phase 5 server rollout log (2026-11-09)

Reached over ssh from the laptop with the target from `config.ini`. Live instances: `dpd-gui@bdhrs`, `dpd-gui@deva`.

## 5.1 Pull (done)

Checks first: clone clean (0 changed files), no window running, 2 commits behind, fast-forward yes, 0 `resources/` paths in the diff. `git pull --ff-only origin main` moved the clone from `36b75c79` to `b1b25007`, the same commit as the laptop. Clone clean after. Both instances stayed `active` and were not restarted.

## 5.2 Unit (done)

Backup: `/root/mem/dpd-gui@.service.before_20261109`. Rendered with the installed values (`User=root`, `HOME=/root`, clone `/root/dpd-db`, `uv` `/root/.local/bin/uv`). The only difference from the installed unit was the restart lines. `daemon-reload`. `systemctl show` for both instances: `Restart=always`. Both `active`.

## 5.3 Pages and nginx (done, except the 502 sight check)

Backups in `/root/mem`: `dpd-contrib.before_20261109`, `bdhrs.conf.before_20261109`, `deva.conf.before_20261109`. Installed `offline.html` (mode 644) to `/var/www/dpd-pages/`; `asleep.html` waits for 5.5. Added the regex location to the site file and the `error_page 502 503 504` line to both user confs, from the templates. `nginx -t` passed, `systemctl reload nginx`.

curl on the host (with the server name resolved to loopback), after the reload settled:

| URL | Answer |
|---|---|
| `/bdhrs/_dpd/offline.html`, `/deva/_dpd/offline.html` | 200, text "not running right now" present |
| `/bdhrs/_dpd/asleep.html`, `/deva/_dpd/asleep.html` | 404 (file not installed yet, expected) |
| `/bdhrs/` | 401 (login gate unchanged) |
| `/status` | 401 (unchanged) |

A first check made right after the reload answered 401 for the pages; the same check a few seconds later answered 200. nginx new workers need a moment after `reload`; wait before the first curl.

Not done: the owner sight check that a stopped instance shows the offline page and not "502 Bad Gateway". It needs a stop of an instance.

## 5.8 Cron (done)

Backup: `/root/mem/crontab.before_20261109`. The window line now starts at `30 0 * * *` and has `--warn-minutes 30`; every other argument and the `PATH` line are unchanged. Both instances stay in the line. Tonight (00:30, server time) is the first real run of the new window code; deva is asleep then (Malaysia), so the owner chose not to test the window by hand.

## 5.4 Wake time (partial)

Three rounds on `dpd-gui@bdhrs` (restart, then one page opened in the owner's Chrome, one page session at a time). "tabs ready after" in the journal: 59.6 s (first start after the pull, cold file cache), 18.3 s. Round 3 did not log a "tabs ready" line within my wait and is not counted. One clean round is still needed before the number goes on the asleep page.
