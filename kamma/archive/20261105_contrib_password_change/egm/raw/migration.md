## Migration & backward-compatibility review

**1. Blocker — atomic rewrite silently destroys the htpasswd file's group.**
`add_contributor.sh:96-105` goes to real trouble to make each hash `640 root:<nginx-group>` (runbook Step 7a CHECK asserts `640 root:www-data`). A temp file + `os.replace` in a root-run process produces `root:root` (`umask 022` → 644, or 600 under `umask 077`). nginx reads the file per request as `www-data`, so the *first* self-service change turns that contributor's whole instance into 500s, permanently, until the maintainer chgrps by hand. Fix: `os.open(temp, O_CREAT|O_WRONLY, 0o640)`, `fchown` to the existing target's `st_gid` (stat it before replace), `os.chmod` after; assert mode/gid in a test.

**2. Blocker — there is no deployment path for the new service.**
`server_setup.sh:112-116` installs exactly one unit, from `dpd-gui@.service`. The nightly window's `_default_pull` (`maintenance_window.py`) only does `git pull` + submodule update: new Python code lands, but no unit is installed and no running service is restarted (the window stops/starts only the `--instance` gui2 units). A hand-installed unit on the live box is untracked state; a fresh build from the runbook would have no password service at all. Fix: add a `dpd-passwd.service` template + install step in `server_setup.sh`, and have the window restart it (or an explicit runbook step) so the running process isn't stale code.

**3. Major — the shared nginx location would live in a hand-edited, git-untracked file.**
`/etc/nginx/sites-available/dpd-contrib` is generated from `nginx_contrib.conf.template` by runbook Step 6d; that template contains only `include /etc/nginx/dpd/*.conf` (line 13). A location appended by hand is lost on any regeneration of the site file — the same trap `/status` already fell into (patched inline in Step 7d). Fix: put the shared location in a file installable into `/etc/nginx/dpd/` (the include picks it up, no site-file edit) or in the template itself, and add the runbook step.

**4. Major — after this change there is no reset path.**
`add_contributor.sh:56-62` refuses any user whose files exist, and the README's "Removing a contributor" only deletes. Once a contributor forgets the new password, recovery is undocumented hand-editing of `/etc/nginx/dpd/<user>.htpasswd`. Fix: add `--reset` to the script (or a documented `htpasswd -B` runbook step) and have the app's failure text name it.

**5. Major — the username rule must be re-implemented, and it isn't shared.**
The page takes a username from an unauthenticated request and builds a filesystem path from it. The only existing validator is shell (`add_contributor.sh:36-40`: `^[a-z][a-z0-9_]{0,31}$`, no `added`). Anything weaker is path traversal writing a bcrypt line as root. Fix: one Python validator, same regex, and require the target file to already exist — never create.

**6. Major — service privilege breaks existing hashes.**
Fork 2 (dedicated user) is a migration trap: existing files are `640 root:www-data`, unreadable to a new user, so every current contributor's first attempt fails. If that fork wins, the plan needs a one-time `chgrp dpd-passwd /etc/nginx/dpd/*.htpasswd` runbook step plus a change to `add_contributor.sh`.

**7. Major — no rollback for htpasswd state.**
`_capture_rollback` restores db, HEAD and `delivered_files(data_dir)` only. A bug that truncates a hash file locks a user out with no backup. Fix: write `<user>.htpasswd.bak` before replace; document restore.

**8. Nit — port reservation.** `add_contributor.sh:65-72` guards only `FLET_SERVER_PORT`; a fixed password-app port must be excluded from the 8551+ sequence and documented.

**9. Nit — runbook/script text.** The runbook insists step numbers stay fixed ("Each step heading keeps its number"), so use a lettered substep; also extend Step 11a's curl checks, Step 12e's message to contributors, and `add_contributor.sh`'s closing "Next, on the server" echoes to mention the change-password URL.
