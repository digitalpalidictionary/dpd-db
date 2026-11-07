# Runbook: set up a new contributor server

**Status:** Not rehearsed end to end on a fresh machine; steps marked UNTESTED were not run.
Every other command was checked on 2026-11-04 against the live server (read-only) or against the script it calls. The live server is called `epitaka` in this file.

## Purpose

This file builds a new DPD contributor web server from an empty Ubuntu machine.
The server runs one copy of the DPD editor (gui2) for each contributor, in a web browser.
The new server replaces the old one. Nothing in this file changes the old server until Step 12.

## Who reads this

Assume you know nothing about this project.
Do exactly what each step says, in order. Do not skip a step. Do not improvise.
If a result differs from `EXPECT`, stop. Tell the owner the exact command and the exact output.

## Rules for the executor

1. Never print a secret. Never `cat`, `grep` or `sed` a file that holds a secret (rule 10 is the one exception): `config.ini`, `*.env`, `*.htpasswd`, private keys. Never run a bare `env`, `printenv` or `export`. To test a login, test the login. To count matches, use `grep -c`.
2. Run any command that can take over 60 seconds detached: `setsid nohup ... < /dev/null > /dev/null 2>&1 &`. Then wait with a bounded loop: `timeout <seconds> bash -c 'until <condition>; do sleep 10; done'`. A tool shell that waits more than 120 seconds is killed, and it kills the job with it.
3. Never use `pkill` or `pkill -f`. Stop a process by its number.
4. Make one change. Then run its `CHECK`. Then go on.
5. Before you edit a system file, copy it: `cp -a <file> /root/mem/<name>.before_<date>`. Run `mkdir -p /root/mem` once.
6. Before any change to ssh or the firewall, open a second ssh connection and keep it open (Step 2 shows how).
7. Say what failed with the exact error text. Do not guess a fix.
8. `grep -c` prints `0` and exits with status 1 when nothing matches. Where an EXPECT is `0`, that exit status is correct.
9. Wait in slices of at most 110 seconds (`timeout 110 bash -c '...'`), then run the CHECK, and repeat. One long wait is killed by the tool shell. A wait loop prints nothing when its time is up, so end it with `|| echo STILL_RUNNING`.
10. The one allowed read of a secret file is the password file in Step 11, and only to pass it to `curl`. Never print it.

## Who does the step (WHO)

| WHO | Meaning |
|---|---|
| `OWNER` | The owner, in the provider's web console, in a browser, or on the owner's own laptop. |
| `AGENT` | An agent, over ssh as `SSH_TARGET`. |

## Values used in this file

Define these once. Use the same names everywhere.

| Name | Value | How to get it |
|---|---|---|
| `NEW_IP` | The new server's public IPv4 address, for example `203.0.113.7`. | The provider's console, after Step 1. |
| `DOMAIN` | `NEW_IP` with dots turned into dashes, then `.sslip.io`. For `203.0.113.7` this is `203-0-113-7.sslip.io`. | Compute it. The name `sslip.io` answers with the address in the name, so no DNS record is needed. With any other domain name, point its A record at `NEW_IP` before Step 6. |
| `SSH_TARGET` | `root@NEW_IP` | Compute it. |
| `OLD_TARGET` | `root@host` of the old server. It must be a root login: the cron and `tar` commands in Steps 7b and 12 act on root's crontab and on system folders. If the old login is not root, stop and tell the owner. | The owner's `[dpd_contributor_server] ssh` setting in the laptop's `config.ini`, read by the OWNER. The agent does not open `config.ini`. |
| `CLONE` | `/root/dpd-db` | Fixed. The scripts default to `$HOME/dpd-db`, and `$HOME` is `/root`. |
| `DATA` | `/var/lib/dpd/contrib_data` | Fixed. `add_contributor.sh` sets it. |
| Contributors | A list of `user port` pairs. `alice 8551` is first. Next ports: 8552, 8553, ... | The OWNER names each user: lower-case letters, digits and `_`, starting with a letter, no `added` inside. The port is unique, from 1024 to 65535. |
| `MAINTAINER_USER` | The contributor account the owner uses to read `/status`. Today it is `alice`. | The OWNER names it. It must be in the contributor list. |

In every command, replace `NEW_IP`, `DOMAIN`, `SSH_TARGET`, `OLD_TARGET`, `MAINTAINER_USER` and each `<angle>` item with its value before you run it.

Every command in Steps 2 to 9 runs on the new server: `ssh SSH_TARGET '<command>'`, or inside a login. Steps 1, 10 and 11 run on the laptop or in a console. Steps 7 and 12 name both machines.

## The 12 steps

**Order of execution:** Steps 1 to 9, then 11a and 11b, then 12a to 12c2, then Step 10, then 11c, then 12d to 12f. Step 10 and the test word in 11c need the final data on the new server, so they come after 12c. Each step heading keeps its number so that cross references stay fixed.

1. Order the server and get root ssh with a key.
2. Time zone, keys-only ssh, firewall, automatic updates.
3. Packages, uv, swap, clone, submodules.
4. `config.ini` with the API keys.
5. First database build.
6. Service unit, nginx and the certificate.
7. Contributors, and the `/status` page.
8. Deploy key and the nightly cron job.
9. Restricted read-only key for the laptop pull.
10. Laptop side: point the pull at the new server.
11. Full check from outside.
12. Cutover and retirement of the old server.

## Step 1. Order the server and get root ssh with a key

**WHO:** OWNER.

Order an Ubuntu 24.04 machine with at least 2 vCPU and 8 GB memory and 65 GB disk.
Add the owner's ssh public key to root at creation. Write down `NEW_IP`.
The live server is Ubuntu 24.04.5 LTS with 2 vCPU and 8 GB.

First contact (laptop): `ssh -o StrictHostKeyChecking=accept-new root@NEW_IP 'echo OK'`. This trusts the new host once. `BatchMode` would refuse to ask, so the first contact does not use it.

CHECK (laptop): `ssh -o BatchMode=yes root@NEW_IP 'echo OK'`

EXPECT: `OK`

## Step 2. Time zone, keys-only ssh, firewall, automatic updates

**WHO:** AGENT.

**2a. Safety line.** Open a second connection. Leave it open until Step 2d is done.

```
ssh -o ControlMaster=yes -o ControlPath=/tmp/cm-new -o ControlPersist=60m -o BatchMode=yes -fN root@NEW_IP
```

CHECK: `ssh -o ControlPath=/tmp/cm-new -O check root@NEW_IP`

EXPECT: `Master running (pid=...)`

**2b. Time zone.** A fresh image is on UTC. The nightly job runs at 01:00 in the server's zone. The owner's zone is Asia/Colombo.

```
ssh SSH_TARGET 'timedatectl set-timezone Asia/Colombo'
```

CHECK: `ssh SSH_TARGET 'timedatectl | grep "Time zone"'`

EXPECT: `Time zone: Asia/Colombo (+0530, +0530)` (checked on `epitaka`)

**2c. Keys-only ssh.** The cloud image has a file `50-cloud-init.conf` that says `PasswordAuthentication yes`. sshd keeps the FIRST value it reads, and it reads the files in name order. So the new file must sort first: its name starts with `01-`.

```
ssh SSH_TARGET 'mkdir -p /root/mem && cp -a /etc/ssh/sshd_config.d /root/mem/sshd_config.d.before_20261104'
ssh SSH_TARGET 'cat > /etc/ssh/sshd_config.d/01-dpd-keys-only.conf' <<'EOF'
# DPD: keys only. Sorts first, and sshd keeps the first value it reads,
# so this wins over 50-cloud-init.conf (PasswordAuthentication yes).
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
ssh SSH_TARGET 'sshd -t && systemctl reload ssh'
```

CHECK: `ssh -o ControlPath=none -o BatchMode=yes SSH_TARGET 'sshd -T | grep -E "^(passwordauthentication|kbdinteractiveauthentication|permitrootlogin) "'`

EXPECT (the three lines in any order):

```
permitrootlogin without-password
passwordauthentication no
kbdinteractiveauthentication no
```

(checked on `epitaka`; `without-password` is how sshd prints `prohibit-password`). The fresh login in the CHECK uses no shared connection, so it proves a new login still works.

**2d. Firewall, with a self-disarming timer.** The timer turns the firewall off after 5 minutes. It protects you if a rule locks you out. Cancel it only after a fresh login works.

```
ssh SSH_TARGET 'systemd-run --on-active=5min --unit=dpd-ufw-deadman /usr/sbin/ufw disable'
ssh SSH_TARGET 'ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable'
```

Port 80 must stay open: the certificate renewal needs it.

CHECK (fresh login, no shared connection): `ssh -o ControlPath=none -o BatchMode=yes SSH_TARGET 'ufw status | head -8'`

EXPECT:

```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
22/tcp (v6)                ALLOW       Anywhere (v6)
```

(checked on `epitaka`). Only when the CHECK passes, cancel the timer and close the safety line:

```
ssh SSH_TARGET 'systemctl stop dpd-ufw-deadman.timer'
ssh -o ControlPath=/tmp/cm-new -O exit root@NEW_IP
```

CHECK: `ssh SSH_TARGET 'systemctl list-timers --no-pager | grep -c dpd-ufw-deadman'`

EXPECT: `0`

**2e. Automatic security updates.** UNTESTED on a fresh machine. On `epitaka` the package is installed and `20auto-upgrades` holds both lines.

```
ssh SSH_TARGET 'DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y unattended-upgrades && dpkg-reconfigure -f noninteractive unattended-upgrades'
```

CHECK: `ssh SSH_TARGET 'cat /etc/apt/apt.conf.d/20auto-upgrades'`

EXPECT:

```
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
```

## Step 3. Packages, uv, swap, clone, submodules

**WHO:** AGENT.

The server clones `main` from GitHub. The files this runbook names (`server_setup.sh`, `add_contributor.sh`, the nginx templates, `config_server.template`) must be on `main` first. The OWNER confirms: `git ls-tree origin/main scripts/server_contrib/server_setup.sh scripts/server_contrib/add_contributor.sh scripts/server_contrib/nginx_status.conf.template` prints three rows.

**3a. Swap.** Run this once. If `/swapfile` exists, the command stops without a change: report it. UNTESTED on a fresh machine (the commands are the normal ones; the size is from the README: 4 GB). The first build uses almost all memory. Do not build without swap.

```
ssh SSH_TARGET 'test ! -e /swapfile && cp -a /etc/fstab /root/mem/fstab.before_20261104 && fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile && echo "/swapfile none swap sw 0 0" >> /etc/fstab'
```

CHECK: `ssh SSH_TARGET 'swapon --show'`

EXPECT: a row `/swapfile file 4G ...` (checked on `epitaka`: `/swapfile file 4G`).

**3b. Packages for the web side.** UNTESTED on a fresh machine. `epitaka` has these installed.

```
ssh SSH_TARGET 'DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 update && DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=600 install -y nginx certbot python3-certbot-nginx apache2-utils rsync git curl'
```

CHECK: `ssh SSH_TARGET 'which nginx certbot htpasswd rsync git'`

If you see `Could not get lock`, wait 5 minutes and run the command again. If the tool shell stops an `apt-get` command at 120 seconds, run `ssh SSH_TARGET 'dpkg --configure -a'`, then run the same `apt-get` command again: it resumes.

EXPECT: five paths, such as `/usr/sbin/nginx`, `/usr/bin/certbot`, `/usr/bin/htpasswd`, `/usr/bin/rsync`, `/usr/bin/git`.

**3c. First run of the setup script.** The script installs its own packages (`pkg-config`, `libicu-dev`, `golang-go`), installs `uv`, clones the repository, loads four submodules and runs `uv sync`. It then stops because `config.ini` is not there yet. This takes more than 60 seconds, so run it detached.

The script is `scripts/server_contrib/server_setup.sh` in the repository. It is not on the machine yet, so fetch it from GitHub:

```
ssh SSH_TARGET 'curl -fsSL https://raw.githubusercontent.com/digitalpalidictionary/dpd-db/main/scripts/server_contrib/server_setup.sh -o /root/mem/server_setup.sh && chmod 700 /root/mem/server_setup.sh'
ssh SSH_TARGET 'rm -f /root/mem/setup.pid'
ssh SSH_TARGET "setsid nohup bash -c 'echo \$\$ > /root/mem/setup.pid; exec /root/mem/server_setup.sh /root/dpd-db' < /dev/null >> /root/mem/setup.log 2>&1 &"
```

Wait for it, in slices (up to 30 minutes in all: repeat this command until it prints `JOB_ENDED`, at most 17 times):

```
timeout 110 bash -c 'until ssh SSH_TARGET "test -s /root/mem/setup.pid && ! kill -0 \$(cat /root/mem/setup.pid) 2>/dev/null"; do sleep 10; done' && echo JOB_ENDED || echo STILL_RUNNING
```

CHECK: `ssh SSH_TARGET 'tail -3 /root/mem/setup.log'`

EXPECT: the last line of the log is `copy config.ini into /root/dpd-db, then run this script again`. If a line that starts with `refused:` is the last, stop and report it.

## Step 4. `config.ini` with the API keys

**WHO:** OWNER. The agent never opens, prints or edits `config.ini`.

The template is `scripts/server_contrib/config_server.template`. It has the sections `[version]`, `[regenerate]`, `[generate]`, `[user]`, `[dictionary]`, `[exporter]`, `[anki]`, `[apis]` and `[gui2]`. The owner fills in two values under `[apis]`: `deepseek` and `openrouter`. Everything else stays as it is. `config_server.md` explains each setting.

On the laptop, in the repository:

```
umask 077
cp scripts/server_contrib/config_server.template /tmp/config_new.ini
# edit /tmp/config_new.ini: in the two lines that say <FILL IN ...>, replace everything from < to > with the key (no brackets, no spaces). Change nothing else.
scp /tmp/config_new.ini root@NEW_IP:/root/dpd-db/config.ini
ssh root@NEW_IP 'chmod 600 /root/dpd-db/config.ini'
shred -u /tmp/config_new.ini
```

CHECK: `ssh SSH_TARGET 'stat -c "%a %U %n" /root/dpd-db/config.ini; grep -c "FILL IN —" /root/dpd-db/config.ini'`

EXPECT:

```
600 root /root/dpd-db/config.ini
0
```

The second line must be `0`: no placeholder is left. (A comment on line 3 of the template also says "FILL IN", but without the dash, so it is not counted.) (On `epitaka` the file is `600 root`.)

## Step 5. First database build

**WHO:** AGENT.

Run the setup script again. It now does the initial setup, downloads the audio index, installs the `dpd-gui@.service` unit and runs the first build through the maintenance window (`--no-systemd --no-push`). It takes 35 to 55 minutes on 2 vCPU with 8 GB. Run it detached.

```
ssh SSH_TARGET 'rm -f /root/mem/setup.pid'
ssh SSH_TARGET "setsid nohup bash -c 'echo \$\$ > /root/mem/setup.pid; exec /root/dpd-db/scripts/server_contrib/server_setup.sh /root/dpd-db' < /dev/null >> /root/mem/setup.log 2>&1 &"
# repeat until it prints JOB_ENDED, at most 45 times (about 80 minutes in all)
timeout 110 bash -c 'until ssh SSH_TARGET "test -s /root/mem/setup.pid && ! kill -0 \$(cat /root/mem/setup.pid) 2>/dev/null"; do sleep 10; done' && echo JOB_ENDED || echo STILL_RUNNING
```

CHECK: `ssh SSH_TARGET 'tail -2 /root/mem/setup.log; cat /root/dpd-db/logs/last_built_commit | wc -c; ls -l /root/dpd-db/dpd.db | awk "{print \$5}"'`

EXPECT: the last log line is `SETUP_DONE`. `last_built_commit` holds 41 characters (a commit hash and a newline). The size of `dpd.db` is about 883,000,000 bytes (at least 800,000,000). If the log ends with an error, or `dpd.db` is smaller than 800 MB, stop and report. Do not start the contributors' instances.

If the job died halfway, run the same command again. Each step skips what is done.

## Step 6. Service unit, nginx and the certificate

**WHO:** AGENT.

**6a. The service unit.** `server_setup.sh` already installed `/etc/systemd/system/dpd-gui@.service`. One instance runs per contributor. The unit holds `FLET_WEB_APP_PATH=%i`, which mounts each instance under its own path (`/alice/`). Without it, a second contributor gets a blank page.

CHECK: `ssh SSH_TARGET 'systemctl cat dpd-gui@alice | grep -E "FLET_WEB_APP_PATH|EnvironmentFile|ExecStart"'`

EXPECT (checked on `epitaka`; `systemctl cat` prints the unit file as written, so `%i` stays unexpanded):

```
Environment=FLET_WEB_APP_PATH=%i
EnvironmentFile=/etc/dpd/%i.env
ExecStart=/root/.local/bin/uv run --no-sync python gui2/main.py
```

To see the expanded value for one instance: `ssh SSH_TARGET 'systemctl show -p Environment dpd-gui@alice'`. EXPECT `Environment=HOME=/root FLET_WEB_APP_PATH=alice` (checked on `epitaka`). The instance must exist (Step 7).

**6b. Stop the default web page.** The nginx package ships a default site on port 80. The certificate step needs port 80 free.

```
ssh SSH_TARGET 'rm -f /etc/nginx/sites-enabled/default && systemctl stop nginx'
```

CHECK: `ssh SSH_TARGET 'ss -tln | grep -c ":80 "'`

EXPECT: `0`

**6c. The certificate.** UNTESTED on a fresh machine. `epitaka` uses `authenticator = nginx`, but its first issue was not recorded, so this step uses the standalone method, which does not need an nginx site first. The two hooks stop nginx for a few seconds at each renewal, so the renewal can use port 80. The hooks are saved in the renewal file.

```
ssh SSH_TARGET 'certbot certonly --standalone -d DOMAIN --non-interactive --agree-tos --register-unsafely-without-email --pre-hook "systemctl stop nginx" --post-hook "systemctl start nginx"'
```

If the owner wants expiry mail, replace `--register-unsafely-without-email` with `-m <owner email>`.

CHECK: `ssh SSH_TARGET 'certbot certificates | grep -E "Certificate Name|Expiry"'`

EXPECT: `Certificate Name: DOMAIN` and an `Expiry Date:` about 89 days away. On `epitaka`: `Expiry Date: 2027-01-29 ... (VALID: 86 days)`.

Then test the renewal:

```
ssh SSH_TARGET 'certbot renew --dry-run 2>&1 | tail -3'
ssh SSH_TARGET 'systemctl is-enabled certbot.timer'
```

EXPECT: `Congratulations, all simulated renewals succeeded` and `enabled`. If the dry run fails, stop and report.

**6d. The site file.** The template is `scripts/server_contrib/nginx_contrib.conf.template`. Replace `@SERVER_NAME@` with `DOMAIN` (it appears four times, once in a comment).

```
ssh SSH_TARGET 'mkdir -p /etc/nginx/dpd'
ssh SSH_TARGET 'sed "s/@SERVER_NAME@/DOMAIN/g" /root/dpd-db/scripts/server_contrib/nginx_contrib.conf.template > /etc/nginx/sites-available/dpd-contrib && ln -sf /etc/nginx/sites-available/dpd-contrib /etc/nginx/sites-enabled/dpd-contrib'
ssh SSH_TARGET 'nginx -t'
```

EXPECT from `nginx -t`:

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

Do not start nginx yet. The certificate hook may already have started it, with no site loaded. Step 7d restarts it, after the contributors' files exist.

## Step 7. Contributors, and the `/status` page

**WHO:** AGENT, except where it says OWNER.

Each contributor has four things: a password file, an env file, an nginx location file and a running instance. `add_contributor.sh` makes the first three. It also sets the right group on the password file, so nginx can read it. Without that group, a new address answers 500.

**7a. A new contributor.** The OWNER types the password: it is asked on the terminal, so the OWNER runs this one in their own ssh login, not through the agent. Type the same password again into the password file of Step 11 (`~/dpd_pw_<user>`).

```
ssh -t SSH_TARGET '/root/dpd-db/scripts/server_contrib/add_contributor.sh <user> <port>'
```

Do 7a OR 7b for each user, never both: `add_contributor.sh` refuses a user that already exists. Run 7a once for each new contributor in the list. `alice 8551` goes first, because it is the `/status` login in the live setup. The script also writes `/etc/nginx/dpd/<user>.initial` (mode 600): the forced-first-change marker. At their first login the contributor is sent to the change-password page (Step 7e) until they change the password; then the marker is gone and it never appears again. The password in `~/dpd_pw_<user>` is valid only until the contributor changes it — after a self-service change the file is stale and Step 11a's curl for that user answers `401`.

CHECK: `ssh SSH_TARGET 'stat -c "%a %U:%G %n" /etc/nginx/dpd/<user>.htpasswd /etc/nginx/dpd/<user>.conf /etc/dpd/<user>.env'`

EXPECT (checked on `epitaka`; on a new server nginx's group is also `www-data`):

```
640 root:www-data /etc/nginx/dpd/<user>.htpasswd
600 root:root /etc/nginx/dpd/<user>.conf
600 root:root /etc/dpd/<user>.env
```

If the script printed `WARNING: could not give ... to nginx's group`, run `chgrp www-data /etc/nginx/dpd/<user>.htpasswd` and check again.

**7b. A contributor who already exists on the old server.** They keep their password, port and words. Copy their files through the laptop, so no password is shown. Do this while the old server runs. Contributors keep working on the old server until Step 12, so Step 12 copies the data folder again.

```
ssh OLD_TARGET 'tar -C / -cf - etc/dpd etc/nginx/dpd var/lib/dpd/contrib_data' | ssh SSH_TARGET 'tar -C / -xf -'
ssh SSH_TARGET 'chgrp www-data /etc/nginx/dpd/*.htpasswd && chmod 640 /etc/nginx/dpd/*.htpasswd && chmod 600 /etc/dpd/*.env /etc/nginx/dpd/*.conf'
```

7b replaces 7a for the users it copies. Run the 7a CHECK for each of them, then do 7c. If `OLD_TARGET` is not `root@...`, the old login needs `sudo` for the `tar`. If the old server has a user who should NOT move, delete that user's files on the new server: `/etc/dpd/<user>.env`, `/etc/nginx/dpd/<user>.htpasswd`, `/etc/nginx/dpd/<user>.conf` and every file `/var/lib/dpd/contrib_data/*_<user>.*`. The old server has no `<user>.initial` markers, so copied users arrive unarmed: they keep their password and are never sent to the change page. To force it, reset them with `scripts/server_contrib/set_password.sh`.

**7c. Start the instances.** The database from Step 5 must exist.

```
ssh SSH_TARGET 'systemctl enable --now dpd-gui@<user>'
```

Run it for each contributor. Wait 60 seconds. The instance loads the database before it answers.

CHECK: `ssh SSH_TARGET 'systemctl is-active dpd-gui@<user>; systemctl is-enabled dpd-gui@<user>'`

EXPECT:

```
active
enabled
```

Judge an instance by what its page returns (Step 11), not by its log. The log lags by minutes.

**7d. The `/status` block.** The block makes the result of each night's run visible in a browser, behind the maintainer's own login. The template is `scripts/server_contrib/nginx_status.conf.template`. In it `@MAINTAINER@` is `MAINTAINER_USER`. The block goes inside the `server { ... }` of `/etc/nginx/sites-available/dpd-contrib`, after the `include` line.

```
ssh SSH_TARGET 'cp -a /etc/nginx/sites-available/dpd-contrib /root/mem/dpd-contrib.before_status'
ssh SSH_TARGET 'python3 - <<EOF
import io
site = "/etc/nginx/sites-available/dpd-contrib"
block = io.open("/root/dpd-db/scripts/server_contrib/nginx_status.conf.template", encoding="utf-8").read().replace("@MAINTAINER@", "MAINTAINER_USER")
text = io.open(site, encoding="utf-8").read()
marker = "    include /etc/nginx/dpd/*.conf;\n"
assert text.count(marker) == 1 and "location = /status" not in text
indented = "".join("    " + line if line.strip() else line for line in block.splitlines(True))
io.open(site, "w", encoding="utf-8").write(text.replace(marker, marker + "\n" + indented, 1))
EOF'
ssh SSH_TARGET 'nginx -t && systemctl restart nginx && systemctl is-active nginx'
```

CHECK: `ssh SSH_TARGET 'grep -c "location = /status" /etc/nginx/sites-available/dpd-contrib; nginx -T 2>/dev/null | grep -c "alias /var/lib/dpd/status.txt"'`

EXPECT: `1` and `1`. The `nginx -t` lines are the two from Step 6d, and `is-active` prints `active`.

**7e. The password gate.** Contributors change their own password at `https://DOMAIN/<user>/password/`. A new login with a marker armed (Step 7a, or a `set_password.sh` reset) is redirected there until they change it. The page is served by `dpd-password.service` (a root-run FastAPI app on the unix socket `/run/dpd-password.sock`), which rewrites the htpasswd file preserving its mode and group and deletes the marker on success. `server_setup.sh` installs and enables the unit (Step 5), and users added by 7a already get the gate in their conf. What remains here: the unit check, the site file, the confs of users copied in 7b, and the reload. **WHO:** AGENT.

Unit check (on a fresh build `server_setup.sh` did this; the check is the same either way):

```
ssh SSH_TARGET 'systemctl is-active dpd-password; systemctl is-enabled dpd-password'
curl --unix-socket /run/dpd-password.sock http://localhost/health
```

EXPECT: `active`, `enabled`, then `ok`. If the unit is missing (a server set up before this feature), install it the way `server_setup.sh` does:

```
ssh SSH_TARGET "sed -e 's|@CLONE@|/root/dpd-db|g' /root/dpd-db/scripts/server_contrib/dpd-password.service | tee /etc/systemd/system/dpd-password.service >/dev/null && systemctl daemon-reload && systemctl enable --now dpd-password"
```

The site file needs the internal location `location = /_dpd_pw_check` (every user conf's `auth_request` points at it). A fresh build already renders it from `nginx_contrib.conf.template` at 6d. The patch below always runs but inserts only when absent — on a fresh build it prints `skipped`:

```
ssh SSH_TARGET 'cp -a /etc/nginx/sites-available/dpd-contrib /root/mem/dpd-contrib.before_password'
ssh SSH_TARGET 'python3 - <<EOF
import io
site = "/etc/nginx/sites-available/dpd-contrib"
text = io.open(site, encoding="utf-8").read()
if "_dpd_pw_check" in text:
    print("skipped: already present")
else:
    block = """    # The forced-first-change subrequest for every user\'s auth_request
    # gate (one definition per server; per-user confs only reference it).
    location = /_dpd_pw_check {
        internal;
        proxy_pass http://unix:/run/dpd-password.sock:/check;
        proxy_pass_request_body off;
        proxy_set_header Content-Length \"\";
        proxy_set_header Authorization $http_authorization;
        proxy_set_header Upgrade \"\";
        proxy_set_header Connection \"\";
        proxy_connect_timeout 2s;
        proxy_read_timeout 5s;
    }
"""
    marker = "    include /etc/nginx/dpd/*.conf;\\n"
    assert text.count(marker) == 1
    io.open(site, "w", encoding="utf-8").write(text.replace(marker, marker + "\\n" + block, 1))
    print("inserted")
EOF'
```

Users copied in 7b carry confs rendered from the old template, without the gate. Regenerate each from the new template (the port comes from the env file; the backup goes to `/root/mem/`):

```
ssh SSH_TARGET 'mkdir -p /root/mem; for env in /etc/dpd/*.env; do
    user=$(basename "$env" .env)
    port=$(sed -n "s/^FLET_SERVER_PORT=//p" "$env")
    cp -a "/etc/nginx/dpd/$user.conf" "/root/mem/$user.conf.before_password"
    sed -e "s|@USER@|$user|g" -e "s|@PORT@|$port|g" /root/dpd-db/scripts/server_contrib/nginx_contrib_user.conf.template > "/etc/nginx/dpd/$user.conf"
    chmod 600 "/etc/nginx/dpd/$user.conf"
done'
ssh SSH_TARGET 'nginx -t && systemctl reload nginx && systemctl is-active nginx'
```

CHECK: `ssh SSH_TARGET 'grep -c "location = /_dpd_pw_check" /etc/nginx/sites-available/dpd-contrib; ls /etc/nginx/dpd/*.initial 2>/dev/null | wc -l; stat -c "%a" /run/dpd-password.sock'`

EXPECT: `1`, the number of users added through 7a or reset with `set_password.sh` (users copied in 7b have none), then `660`.

## Step 8. Deploy key and the nightly cron job

**WHO:** AGENT, except 8b (OWNER).

**8a. Make the deploy key on the server.** UNTESTED on a fresh machine. It lets the server push the `contributions` branch.

```
ssh SSH_TARGET 'ssh-keygen -t ed25519 -N "" -C "dpd contributor server" -f /root/.ssh/dpd_deploy && cat /root/.ssh/dpd_deploy.pub'
```

The output is the PUBLIC key, one line. It is safe to print. Never print `dpd_deploy` without `.pub`.

**8b. Add it to GitHub.** **WHO:** OWNER. Open the repository on GitHub: Settings, Deploy keys, Add deploy key. Paste the public line. Tick "Allow write access". Save. Do not delete the OLD server's deploy key yet: the old cron job still needs it until Step 12f.

Known risk, accepted by the owner on 2026-11-03: a deploy key can write to `main` even when `main` is protected. Treat the key as a full write key.

**8c. Tell git to use it.** Both settings are needed: the push address and the ssh command. The fetch address stays `https`.

```
ssh SSH_TARGET 'cd /root/dpd-db && git remote set-url --push origin git@github.com:digitalpalidictionary/dpd-db.git && git config core.sshCommand "ssh -i ~/.ssh/dpd_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"'
```

CHECK: `ssh SSH_TARGET 'cd /root/dpd-db && git remote -v; git config --get core.sshCommand; git ls-remote --heads git@github.com:digitalpalidictionary/dpd-db.git main | wc -l'`

EXPECT (checked on `epitaka`):

```
origin	https://github.com/digitalpalidictionary/dpd-db (fetch)
origin	git@github.com:digitalpalidictionary/dpd-db.git (push)
ssh -i ~/.ssh/dpd_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new
1
```

The `ls-remote` proves the key can read. It cannot prove the key can write. The first night's run proves that: `/status` then shows no push error (Step 11).

**8d. The cron job.** The `PATH` line is required. Cron's short default path has no `uv`, and the window runs `uv` by name. Without the line, the first night fails at the rebuild with `No such file or directory: 'uv'`. Add one `--instance dpd-gui@<user>` for each contributor. The line is one line.

```
ssh SSH_TARGET 'crontab -l 2>/dev/null > /root/mem/crontab.before_20261104; true'
ssh SSH_TARGET 'cat > /root/mem/new_crontab' <<'EOF'
PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
0 1 * * * cd /root/dpd-db && /root/.local/bin/uv run --no-sync scripts/server_contrib/maintenance_window.py --data-dir /var/lib/dpd/contrib_data --instance dpd-gui@alice --status-file /var/lib/dpd/status.txt >> /root/mem/window_cron.log 2>&1
EOF
ssh SSH_TARGET 'crontab /root/mem/new_crontab && systemctl restart cron'
```

In the `EOF` text, write one `--instance dpd-gui@<user>` for each contributor, after the one for `alice`.

CHECK: `ssh SSH_TARGET 'crontab -l; systemctl is-active cron'`

EXPECT: the same two lines (checked on `epitaka`; it has one `--instance`), then `active` (checked on `epitaka`). The restart makes cron use the zone set in Step 2b.

Skip 8d here. It is done in Step 12c2, after the old server's cron job has stopped. Two servers must never push the `contributions` branch. (If the old server is already gone, do 8d now and skip 12c2.)

## Step 9. Restricted read-only key for the laptop pull

**WHO:** AGENT, on the laptop with ssh to the new server.

The laptop pull uses its own key, `~/.ssh/dpd_contrib_pull`. The server accepts it only to read one folder. It cannot run a command or write.

**9a. Safety line and backup.**

```
ssh -o ControlMaster=yes -o ControlPath=/tmp/cm-new -o ControlPersist=30m -o BatchMode=yes -fN root@NEW_IP
ssh -o ControlPath=/tmp/cm-new root@NEW_IP 'cp -a /root/.ssh/authorized_keys /root/mem/authorized_keys.before_pull && wc -l < /root/.ssh/authorized_keys && ls -l /usr/bin/rrsync'
```

Note the number of lines. `rrsync` must exist. Check that the file ends with a newline: `ssh -o ControlPath=/tmp/cm-new root@NEW_IP 'tail -c1 /root/.ssh/authorized_keys | xxd -p'` must print `0a` (checked on `epitaka`). If it does not, stop and report: the new line would join the last key.

**9b. Append one line. Never rewrite the file.** The public key comes from the laptop file `~/.ssh/dpd_contrib_pull.pub`. If that file is missing, make it first: `ssh-keygen -t ed25519 -N "" -C "dpd-contrib-pull" -f ~/.ssh/dpd_contrib_pull`.

```
{ printf 'restrict,command="/usr/bin/rrsync -ro /var/lib/dpd/contrib_data" '; cat ~/.ssh/dpd_contrib_pull.pub; } | ssh -o ControlPath=/tmp/cm-new root@NEW_IP 'cat >> /root/.ssh/authorized_keys'
```

CHECK: `ssh -o ControlPath=none -o BatchMode=yes root@NEW_IP 'echo OK; wc -l < /root/.ssh/authorized_keys'`

EXPECT: `OK`, then the line count from 9a plus one. Close the safety line: `ssh -o ControlPath=/tmp/cm-new -O exit root@NEW_IP`.

**9c. Prove the key reads and nothing else.**

```
K="ssh -i $HOME/.ssh/dpd_contrib_pull -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ForwardAgent=no"
rsync -r --list-only -e "$K" root@NEW_IP: | head -3
$K root@NEW_IP 'id'
rsync -e "$K" /etc/hostname root@NEW_IP:/
```

EXPECT (checked on `epitaka` with the same key):

1. The listing shows `additions_<user>.json` rows. If the folder is empty, it shows only the `.` row.
2. The `id` command prints `/usr/bin/rrsync error: SSH_ORIGINAL_COMMAND does not run rsync` and no `uid=`.
3. The push prints `/usr/bin/rrsync error: sending to read-only server is not allowed` and then `rsync error: error in rsync protocol data stream (code 12)`.

If the `id` command prints `uid=`, the line is wrong. Stop. Open a safety line as in 9a, then restore the backup: `ssh -o ControlPath=/tmp/cm-new root@NEW_IP 'cp -a /root/mem/authorized_keys.before_pull /root/.ssh/authorized_keys'`. Tell the owner. Do not edit the file by hand.

## Step 10. Laptop side: point the pull at the new server

**WHO:** OWNER, then AGENT.

**Order.** Do Step 10 after 12c2, when the data on the new server is final. Before then, a pull from the new server would bring the older copy from Step 7b over newer files on the laptop. Do not do 10a, 10b or 11c before 12c2.

**10a.** **OWNER.** In the laptop's `config.ini`, under `[dpd_contributor_server]`, change the `ssh` value to `root@NEW_IP`. Change nothing else. The agent does not edit `config.ini`. The first connection trusts the new host by itself.

**10b.** **AGENT.** The daily pull skips a day that is already done. To run one now, move the status file aside, then run the pull once:

```
cd ~/MyFiles/3_Active/dpd-db && mv logs/contrib_pull_status.txt logs/contrib_pull_status.txt.old; just contrib-pull
```

CHECK: `cd ~/MyFiles/3_Active/dpd-db && head -4 logs/contrib_pull_status.txt`

EXPECT: `outcome: pulled`, a `finished:` time, `last_success:` with today's date, and one line for each contributor that has files. If the editor (gui2) is open, the outcome is `skipped: editor open`. Close the editor and run again.

## Step 11. Full check from outside

**WHO:** AGENT. The passwords are in files that only the OWNER made, one file for each user, mode 600, for example `~/dpd_pw_<user>`. The agent never prints a password. Do not put a password in a command text: read it from the file.

To make one file, the OWNER runs this in their own terminal, once for each user:

```
read -rs -p 'password: ' p && printf '%s' "$p" > ~/dpd_pw_<user> && chmod 600 ~/dpd_pw_<user>; unset p
```

**11a. Each contributor's page loads.** Without a password, the address must refuse. With the right password, it must answer.

```
curl -s -o /dev/null -w '%{http_code}\n' https://DOMAIN/<user>/
printf 'user = "<user>:%s"\n' "$(cat ~/dpd_pw_<user>)" | curl -s -K - -o /dev/null -w '%{http_code}\n' https://DOMAIN/<user>/
```

EXPECT: `401`, then `200` (on `epitaka` the public address answers `401`). The password goes to `curl` through its standard input, so it does not show in the process list. For a user copied in Step 7b the owner may not know the password and has no file: check only the `401`, and ask the owner or the contributor to log in once in a browser.

**11b. The status page.** It needs the maintainer's login.

```
printf 'user = "MAINTAINER_USER:%s"\n' "$(cat ~/dpd_pw_MAINTAINER_USER)" | curl -s -K - https://DOMAIN/status | head -4
```

EXPECT: after the first night's run (the cron job is installed in Step 12c2, so before the night after cutover the page answers `404`: that is expected) the first line is `outcome: rebuilt` (or `outcome: skipped`), then `finished:`, `commit:` and `problems: 0` (checked on `epitaka`). Before the first night the file does not exist and the page answers `404`. Check again the next morning. A push error shows in the `problems` lines.

**11c. The first pull brings a test word.**

0. **AGENT.** Copy the `<user>:` line from `logs/contrib_pull_status.txt` into your notes: it holds the entry count before the test.
1. **OWNER.** Log in to one contributor page in a browser. Add one test word. Save it.
2. **AGENT.** Check that the server file changed: `ssh SSH_TARGET 'ls -l --time-style=full-iso /var/lib/dpd/contrib_data/additions_<user>.json'`. The time must be a few minutes old.
3. **AGENT.** Do this only after 12c2 and Step 10. Move the status file aside and pull, as in Step 10b.
4. **OWNER.** Process or reject the test word in the editor. Step 12c replaces the new server's data folder with the old one, so a test word saved here is lost on the server at cutover. Do not use a contributor's real work for this test.

EXPECT: `outcome: pulled`, and `<user>: pulled N files, M entries` where `M` is one more than before.

**11d. The password page and the forced-first-change gate.** Uses one contributor's login file from Step 11. Run these from the laptop, in this order.

Without a password, the password page refuses, like the editor:

```
curl -s -o /dev/null -w '%{http_code}\n' https://DOMAIN/<user>/password/
```

EXPECT: `401`.

With a marker armed (a user added through 7a, or reset through `set_password.sh`), a logged-in visit to the editor is redirected to the password page:

```
printf 'user = "<user>:%s"\n' "$(cat ~/dpd_pw_<user>)" | curl -s -K - -o /dev/null -w '%{http_code} %{redirect_url}\n' https://DOMAIN/<user>/
```

EXPECT: `302 https://DOMAIN/<user>/password/`. A browser whose credentials are NOT cached yet gets the `401` prompt instead (auth_basic answers first) — that is expected.

The change itself: log in to `https://DOMAIN/<user>/password/` in a browser (OWNER, or the contributor), type the new password twice, submit. EXPECT: the page says the password was changed. Then:

```
printf 'user = "<user>:%s"\n' "$(cat ~/dpd_pw_<user>)" | curl -s -K - -o /dev/null -w 'old: %{http_code}\n' https://DOMAIN/<user>/
ssh SSH_TARGET 'ls /etc/nginx/dpd/<user>.initial 2>/dev/null || echo marker gone; stat -c "%a %U:%G" /etc/nginx/dpd/<user>.htpasswd; ls /etc/nginx/dpd/<user>.htpasswd.bak'
```

EXPECT: `old: 401` (the old password stops working at the next prompt), `marker gone`, still `640 root:www-data`, and the `.bak` is present — it keeps the previous hash until the next change; that is the recovery copy, not a leak to fix. Re-arm and check the editor is reachable again with the new password (put the new password in a fresh `~/dpd_pw_<user>` first):

```
ssh SSH_TARGET 'rm /etc/nginx/dpd/<user>.initial && touch /etc/nginx/dpd/<user>.initial && chmod 600 /etc/nginx/dpd/<user>.initial'
printf 'user = "<user>:%s"\n' "$(cat ~/dpd_pw_<user>)" | curl -s -K - -o /dev/null -w 'new: %{http_code}\n' https://DOMAIN/<user>/
ssh SSH_TARGET 'rm /etc/nginx/dpd/<user>.initial'
```

EXPECT: `new: 200`, and the marker removed again (unless this user should stay forced, then leave it).

Fail-closed check: kill the service and watch it come back.

```
ssh SSH_TARGET 'systemctl kill dpd-password; sleep 2; systemctl is-active dpd-password; curl -s -o /dev/null -w "editor: %{http_code}\n" --unix-socket /run/dpd-password.sock http://localhost/health; stat -c "socket: %a %U:%G" /run/dpd-password.sock'
```

EXPECT: `active`, `editor: 200`, and the socket STILL `660 root:www-data` — uvicorn re-applies the mode on restart but never the group, so this line is the one that catches a lost group. While the service is down the editor answers `500`; triage for any 500 on a user URL: `systemctl status dpd-password` first, nginx second.

## Step 12. Cutover and retirement of the old server

**WHO:** OWNER decides. AGENT does 12a to 12d.

**12a. Stop the old server's cron job FIRST.** Two servers must never push the `contributions` branch.

```
ssh OLD_TARGET 'mkdir -p /root/mem && crontab -l > /root/mem/crontab.saved_for_retire && crontab -r'
```

CHECK: `ssh OLD_TARGET 'crontab -l 2>&1'`

EXPECT: `no crontab for root`.

**12b. Stop the old instances, so their files stop changing.**

```
ssh OLD_TARGET 'systemctl stop dpd-gui@<user>'
```

Run it for each contributor. This ends their sessions. Warn them before.

CHECK: `ssh OLD_TARGET 'systemctl is-active dpd-gui@<user>'`

EXPECT: `inactive`

**12c. Copy the data folder once more, through the laptop.** The first copy in Step 7b is old by now. First stop the new server's instances, so none holds old state in memory. Move the new server's test data aside (nothing is deleted), copy, then start them again.

```
ssh SSH_TARGET 'systemctl stop dpd-gui@<user>'
ssh SSH_TARGET 'mv /var/lib/dpd/contrib_data /root/mem/contrib_data.new_server_test_20261104'
ssh OLD_TARGET 'tar -C / -cf - var/lib/dpd/contrib_data' | ssh SSH_TARGET 'tar -C / -xf -'
```

CHECK: run `ssh <machine> 'cd /var/lib/dpd/contrib_data && ls | sort | xargs sha1sum | sha1sum'` on both machines.

EXPECT: the two hashes are equal. Then start each instance again: `ssh SSH_TARGET 'systemctl start dpd-gui@<user>'`.

**12c2. Install the cron job on the new server.** Do Step 8d now, with its CHECK. The old cron job stopped in 12a, so only one server pushes. If you did 8d earlier because the old server was already gone, skip this.

**12d. Keep a backup of the old data folder on the laptop.** The limit keeps the download under 400 KB per second.

```
mkdir -p ~/backups && rsync -a --bwlimit=400 -e ssh OLD_TARGET:/var/lib/dpd/contrib_data/ ~/backups/old_contrib_data_20261104/
```

CHECK: `ls ~/backups/old_contrib_data_20261104 | wc -l`

EXPECT: the same number as `ssh OLD_TARGET 'ls /var/lib/dpd/contrib_data | wc -l'`.

**12e. Tell the contributors the new address.** **WHO:** OWNER. It is `https://DOMAIN/<user>/`. Their user names and passwords do not change when Step 7b was used. Users added through 7a start on the change page: their first login asks them to replace the initial password (between 10 and 72 characters) before the editor opens, and after that their password is their own — `set_password.sh` on the server is the reset path if one is ever lost.

**12f. Retire the old server.** **WHO:** OWNER.

1. On GitHub, delete the old server's deploy key (Settings, Deploy keys).
2. Check the next morning that `/status` on the new server says `outcome: rebuilt` or `skipped`, and that the pull ran (`logs/contrib_pull_status.txt`).
3. Only then close the old server at the provider.

The first night after the cutover: the new server's window sees `main` moved, so it rebuilds. This takes 35 to 55 minutes, and the instances are down for that time.
