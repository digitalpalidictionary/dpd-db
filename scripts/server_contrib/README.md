# Contributor web server tooling

Server-side scripts for the hosted gui2 **contributor web server** (issue #215,
round 2 — the zero-install web version of gui2 for non-technical contributors).
Each contributor gets one gui2 web instance. Their work goes to per-user files
in `DPD_GUI2_DATA_DIR` (outside the repo). A nightly window pulls `main`,
drops what the maintainer has handled, pushes the rest to the `contributions`
branch, and rebuilds the scratch db when `main` has moved.

Setting up a new server: see `NEW_SERVER_RUNBOOK.md`.

See also: `config_server.md` (the lean rebuild — kept/dropped step rationale),
`spec.md`/`plan.md` in `kamma/threads/20261030_contrib_5_hardening/`.

## New server

`server_setup.sh [clone dir]` (default `~/dpd-db`) builds a server from a fresh
clone. It is safe to re-run; each step is skipped when its result exists.

- Packages, uv and the clone: apt (`pkg-config`, `libicu-dev`, `golang-go`), uv, `git clone`.
- Four submodules: `sc-data`, `dpd_submodules`, `tipitaka.rte` and `tipitaka_translation_db`. The frequency
  setup reads the SYA corpus from `tipitaka.rte`. `tipitaka_translation_db` holds the script that downloads
  the translation database (807 MB) the Transl tab searches; the nightly window downloads it when it is missing.
- Setup runs: `uv sync --all-groups`, `initial_setup_run_once.py`, the audio index download.
- It stops until `config.ini` is in the clone. Copy it, then run the script again.
- The first build is the maintenance window itself (`--no-systemd --no-push`).
- The systemd unit `dpd-gui@.service` is installed. Enable one instance with
  `sudo systemctl enable --now dpd-gui@<user>`. Logs: `journalctl -u dpd-gui@<user>`.
  `dpd-password.service` (the change-password page behind `/<user>/password/`,
  forced first change) is installed and enabled by the same script; logs:
  `journalctl -u dpd-password`.

Measured (2026-11-01, 2 vCPU, 8 GB, 4 GB swap): first build 2051 s (~34 min), lowest
free memory ~170 MB, swap peak ~130 MB. Do not build without swap.

Left out on purpose (one-time, per-host, or secret): swap, nginx and the
certificate, `add_contributor.sh` (asks for a password), the deploy key,
`systemctl enable`. The steps are in
`kamma/threads/20261101_contrib_6_e2e_server_test/plan.md`.

- The window no longer runs `git submodule update --init`. If `main` ever needs a
  new submodule, init it once by hand on the server. An existing server loads `resources/tipitaka_translation_db` this way once.
- The deploy key is for pushes only: `git remote set-url --push` plus
  `core.sshCommand`. It needs write access. Delete it when the server goes away.

## The nightly maintenance window

`maintenance_window.py` is the orchestrator:

```
stop instances
  → capture rollback     (db copy, HEAD, every delivered contributor file)
  → dirty-tree check     (tracked files only; a dirty tree refuses the window)
  → git pull --ff-only + submodule update
  → contrib_reconcile    (drop what main has processed or merged)
  → contrib_push         (contributions branch; a failure is logged, not fatal)
  → translation db       (downloaded when missing; a failure is logged, not fatal)
  → rebuild only if HEAD differs from logs/last_built_commit
       db_rebuild_from_tsv.py → generate_components_server.py → health check
       → re-apply WAL → restore the tracked files the build rewrote
  on ANY failure after the pull: restore db, HEAD and contributor files
start instances (always)
```

A failed instance stop, a failed dirty-tree check or a failed pull skips
reconcile, push and rebuild. Every run logs to `logs/maintenance_YYYYMMDD.log`.

- Every user shares one data folder, `/var/lib/dpd/contrib_data`
  (`add_contributor.sh` sets it; file names carry the user). Pass the same folder
  to the window with `--data-dir`, or set `DPD_GUI2_DATA_DIR` for it.
- A corrupt contributor JSON stops the window (it rolls back) every night until
  someone fixes the file. This is deliberate: it never guesses.
- The push overwrites whatever is on the remote `contributions` branch. Do not
  commit to it by hand.
- `htpasswd` files are written mode 640 and given to nginx's group (found with
  `nginx -T`, or set `HTPASSWD_GROUP`). If the script warns that it could not,
  run the `chgrp` by hand, or the URL answers 500.
- Each instance is mounted under `/<user>/` (`FLET_WEB_APP_PATH=%i` in the unit),
  and nginx passes the prefix on (no trailing slash on `proxy_pass`). Mounted at
  the root, every user's page asks the domain root for its engine files, and only
  one instance can answer there.

### Run it

Production (cron on the server, 01:00 IST on a host in IST):

The `PATH` line is required. Cron's short default path has no `uv`, and the
window runs `uv` by name for the rebuild. Without it the first night fails at
the rebuild (2026-11-04: `No such file or directory: 'uv'`; the rollback worked).

```bash
PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 1 * * * cd /root/dpd-db && /root/.local/bin/uv run --no-sync scripts/server_contrib/maintenance_window.py --data-dir /var/lib/dpd/contrib_data --instance dpd-gui@alice --status-file /var/lib/dpd/status.txt >> /root/mem/window_cron.log 2>&1
```

Add one `--instance` per contributor unit.

Local dry-run (no systemd, no push — safe against a scratch copy):

```bash
cd <scratch repo> && uv run scripts/server_contrib/maintenance_window.py --no-systemd --no-push
```

Flags: `--no-systemd`, `--no-push`, `--instance <unit>` (repeatable),
`--db-path`, `--data-dir` (default: `DPD_GUI2_DATA_DIR`, else `gui2/data`),
`--worktree` (default: `<project-root>_contrib_worktree`), `--log-dir`,
`--status-file`, `--remote`, `--branch`.

### The failure surface (`/status`)

Every run rewrites `--status-file` (default `<log-dir>/status.txt`) with the
outcome, the time, the commit and every ERROR/WARNING line of that day's log.
On the server, point it at a path nginx can read and serve it behind the
maintainer's own login, so a failed night is visible without a mail stack:

```nginx
location = /status {
    auth_basic "DPD maintenance status";
    auth_basic_user_file /etc/nginx/dpd/<maintainer>.htpasswd;
    alias /var/lib/dpd/status.txt;
    default_type text/plain;
    add_header Cache-Control "no-store";
}
```

The block is kept in `nginx_status.conf.template` in this folder. A run that
cannot write the status file logs `could not write the status file` and still
finishes normally: the status file never decides the window's outcome.

## Update the server now (manual, no rebuild)

Use this to put a code or draft-file change on the server today, without
waiting for the 01:00 window. Done and verified on 2026-11-08 (`7cf7aa5c`,
the Pass1 `family_compound` removal). The window rebuilds the db (30 to 55
minutes) whenever `main` moved, so do not run it by hand for this. It sees the
moved commit and rebuilds that night anyway.

Do not use this when the change needs a db rebuild to take effect (a new
column, new data in `dpd.db`). Wait for the window.

1. Commit and push to `main`. The server pulls from GitHub, so unpushed work
   never arrives. A new file must be added by name first.
2. Take the target from `[dpd_contributor_server] ssh` in `config.ini`. Never
   write the address in a doc. Every command below runs over `ssh <target>`.
3. Look first, change nothing:
   - `cd /root/dpd-db && git status --porcelain | wc -l` must print `0`. A dirty
     checkout makes the pull fail, and the window refuses to run on one too.
   - `ps -eo pid,args | grep "[m]aintenance_window"` must print nothing. Do not
     use `pgrep -f maintenance_window`: the ssh command line itself matches it.
   - `git fetch origin main`, then `git rev-list --count HEAD..origin/main` is
     how far behind it is, and `git merge-base --is-ancestor HEAD origin/main`
     must succeed (a fast-forward).
   - `git diff --name-only HEAD origin/main` must not list `resources/` submodule
     paths. If it does, use the window, which also runs the submodule update.
   - `systemctl list-units "dpd-gui@*" --all` lists the instances to restart.
4. Stop, pull, start. The `trap` starts the instances again even if the pull
   fails:

   ```bash
   cd /root/dpd-db; trap "systemctl start dpd-gui@<user>" EXIT
   systemctl stop dpd-gui@<user>
   git pull --ff-only origin main
   ```

   Give `stop` and `start` every instance from step 3. Never use `git reset`
   or `git checkout` on the server to force it.
5. Check, do not trust the "started" line:
   - `systemctl is-active dpd-gui@<user>` prints `active`, and `NRestarts` is `0`.
   - `journalctl -u dpd-gui@<user> -n 6 -o cat` shows `Stopped` then `Started`.
     The `status=143` and `Failed with result 'exit-code'` lines before it are
     the normal result of a stop request.
   - The editor URL answers `401` without a login (the nginx password gate).
   - `grep` the server's copy of the changed file for the change.
6. Contributors lose their open editor session for about a minute, and
   unsaved fields in it. Their finished-word lists and data folder are outside
   the checkout and are untouched.

The next 01:00 window pulls nothing new, sees `main` moved since
`logs/last_built_commit`, and rebuilds as normal.


## The pieces

| Script | Does |
|---|---|
| `contrib_reconcile.py` | Drops a JSON entry when main's `additions_added.json` / `corrections_added.json` holds its `(key, hash)`. Drops a flag line when `contrib_lines_merged.json` holds it for that file. Never drops the header of a variant or spelling file. Writes an emptied file, never deletes it. |
| `contrib_push.py` | Resets `contributions` to the clone's `HEAD` in a separate worktree, copies in the delivered files, commits if anything differs, and always `git push --force-with-lease` after `git fetch --prune`. |
| `merge_contrib_files.py` | Maintainer side. Folds each contributor's flag files into the shared files and logs every handled line in `gui2/data/contrib_lines_merged.json`. |
| `maintenance_window.py` | The orchestrator above. |
| `generate_components_server.py` | LEAN rebuild — only the steps gui2 reads. No pytest. See `config_server.md`. |
| `server_setup.sh` | Builds a server from a fresh clone. See "New server". |
| `dpd-gui@.service` | systemd unit template, one gui2 instance per contributor. Filled and installed by `server_setup.sh`. |
| `config_server.template` | Server `config.ini` template. Copy to `config.ini`; NEVER commit the result. |
| `contrib_pull.py` | Laptop side. Copies the contributors' files from the server once a day, checks them, drops what you already handled, and merges the flag files. See "The daily pull". |
| `dpd-contrib-pull.service`, `dpd-contrib-pull.timer` | systemd user unit templates for the daily pull. `just contrib-pull-install` fills and installs them. |
| `NEW_SERVER_RUNBOOK.md` | Step by step set-up of a new server, written for an agent with no context. |

The delivered file kinds (additions, corrections, user dictionary, checked,
manual corrections, variants, spelling, test exceptions) come from one list in
`tools/contrib_entry.py`. History, daily log, presets and stash files are
never delivered.

## The daily pull

Runs on the maintainer's laptop, by itself. A systemd user timer starts it every
30 minutes from 08:00 to 22:30. The run that finds today already done stops at once.

1. It lists the server folder with `rsync` over ssh (read-only key `~/.ssh/dpd_contrib_pull`).
2. It checks every name and size, copies the accepted files to a scratch folder, and checks their content.
3. One bad file drops all the files of that contributor for today. The others go on.
4. It drops what you already processed (`contrib_reconcile.py`) and any test exception whose id is not a reserved id.
5. It copies the rest into `gui2/data`, then runs `merge_contrib_files.py` for the flag files.
6. It does nothing while the editor (gui2) is open.

- **Status:** `logs/contrib_pull_status.txt`. **Log:** `logs/contrib_pull.log`. A skipped run writes neither, so the status keeps the last real result.
- **By hand:** `cd ~/MyFiles/3_Active/dpd-db && just contrib-pull` (to see what it would do without changing anything, run `uv run scripts/server_contrib/contrib_pull.py --dry-run`).
- **Reading `outcome:`:** `pulled` is good. `pulled with problems` means a contributor was skipped; the line below names the file and the reason. `partial` means the editor opened mid-run; the next run repeats it. `failed: ...` gives the error. `pulled with problems` sends a desktop notice at once. A `failed` or `partial` run sends one only on the last run of the day (22:30), because a later run may repair it.
- **Undo a bad run:** restore a named shared file with `git restore <file>` (you, not an agent). The contributor files in `gui2/data` are copies; the next pull brings them back.
- **Do not run `just contrib-merge` as well.** The pull replaces it.
- A new server: see `NEW_SERVER_RUNBOOK.md`.

## Maintainer: taking in contributions

> **Replaced by the daily pull** (see "The daily pull" above). This route is the fallback if the pull is not set up. Do not run both.

There are no pull requests. From the repo root:

```bash
cd ~/MyFiles/3_Active/dpd-db && just contrib-merge
```

This fetches `origin/contributions`, merges it into local `main`, and runs
`merge_contrib_files.py`.

- **Merge before you process.** Processing removes entries from main's copy of
  a contributor file. A branch built before that can conflict.
- **A conflicted merge:** abort it (`git merge --abort`). The next night's
  branch is built on current main and is clean.
- **Backup & Quit** commits `additions_added.json`, `corrections_added.json`
  and `contrib_lines_merged.json` with the TSV backup, so the logs reach main
  together with the words they describe. The server never runs it.

## Adding a contributor

Done and verified on 2026-11-08 for the user `deva` (port 8552). Run it as
root on the server, in `/root/dpd-db`. The target comes from
`[dpd_contributor_server] ssh` in `config.ini`; never write the address here.

1. Pick a free port. `grep -h "^FLET_SERVER_PORT" /etc/dpd/*.env` lists the
   used ones; take the next number up from 8551. The script refuses a port
   that is already taken.
2. Pick the user name: lower-case letters, digits or `_`, starting with a
   letter, and without `added` in it. `/etc/dpd/<user>.env` must not exist.
3. Create the login, the env file, the nginx file and the data folder. The
   password is read from stdin when stdin is a pipe, so it never sits in a
   file:

   ```bash
   cd /root/dpd-db
   printf '<password>\n' | bash scripts/server_contrib/add_contributor.sh <user> <port> ["Extra,Tabs"]
   ```

   A contributor gets the tabs Pass1Add and Transl. Extra tabs are optional
   and come only from `Bold Search`, `DB`, `√`, `Infl`; the last three are
   read-only (see `gui2/contributor_tabs.py`).
4. Start the editor and let nginx see the new file:

   ```bash
   systemctl enable --now dpd-gui@<user>
   nginx -t && systemctl reload nginx
   ```

5. Add the unit to the nightly job, or the window will not stop it before the
   pull and the rebuild. Back up the crontab first, then add one more
   `--instance dpd-gui@<user>` to the `maintenance_window.py` line:

   ```bash
   mkdir -p /root/mem && crontab -l > /root/mem/crontab.before_<user>
   crontab -l | sed 's|--instance dpd-gui@<last user>|& --instance dpd-gui@<user>|' | crontab -
   crontab -l | grep -o -- '--instance [^ ]*'
   ```

6. Check it from outside, not just on the server (host = the server's
   `https://<ip with dashes>.sslip.io`):
   - `systemctl is-active dpd-gui@<user>` prints `active`, and `NRestarts` is `0`.
   - `curl -s -o /dev/null -w '%{http_code}' https://<host>/<user>/` prints `401`.
   - The same with `-u <user>:wrong` prints `401`.
   - The same with `-u <user>:<password>` prints `302`, redirected to
     `/<user>/password/`. That is the forced first password change; the marker
     `/etc/nginx/dpd/<user>.initial` makes it happen, and the service deletes
     the marker once they choose a new password.
   - The other users' services are still `active`.
7. Send the user their URL, user name and temporary password. Send the
   password in a separate message from the URL.

The data folder is shared and flat (`additions_<user>.json` and so on), so
nothing is created per user there. Give each contributor a different Pass1
book, as the note in `gui2/pass1_file_manager.py` asks.

## Removing a contributor

Resetting a password (contributor forgot theirs, or it must change):
`sudo scripts/server_contrib/set_password.sh <user>` — new hash, same
mode/group as `add_contributor.sh`, marker armed so the next login lands on
the change page.

1. Run a maintenance window.
2. Process or reject all their entries.
3. Archive their files in `/var/lib/dpd/contrib_data` (`*_<user>.*`; do not
   delete them).
4. Remove their env file, htpasswd entry and nginx files.

Deleting their files first loses any work not yet pushed.
