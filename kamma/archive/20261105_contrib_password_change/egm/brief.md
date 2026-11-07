# EGM brief — 20261105_contrib_password_change

## Request

From the 20261030 triage (item 15, owner wants it), tied to GitHub issue
digitalpalidictionary/dpd-db#215 ("Contributor Onboarding: Easy GUI Setup &
Data Submission"). A contributor on the DPD contributor server logs in via
nginx basic auth. Today only the maintainer sets passwords, through
`scripts/server_contrib/add_contributor.sh`; a contributor who wants a new
password must ask the maintainer. The owner wants contributors to change
their own password.

## Anchored hypothesis

Keep nginx basic auth exactly as it is. Add a minimal self-service
change-password page: a tiny FastAPI app (`fastapi`/`uvicorn` are already
project dependencies) bound to 127.0.0.1, proxied by nginx at one shared
path, that verifies the user's current password against the per-user
htpasswd file (via the already-installed `htpasswd -vb` CLI), then
atomically rewrites the bcrypt hash (temp file + `os.replace`). nginx reads
the htpasswd file on every request, so no reload is needed. gui2 is not
touched; the maintainer keeps the root override.

## Verified facts (claims to re-check, not facts)

Checked against the repo on 2026-11-07:

- `scripts/server_contrib/add_contributor.sh` creates, per user:
  `/etc/dpd/<user>.env`, `/etc/nginx/dpd/<user>.htpasswd` (bcrypt via
  `htpasswd -B`, default cost, mode 640 root:<nginx-group>), and
  `/etc/nginx/dpd/<user>.conf` (a `location /<user>/` with per-user
  `auth_basic` realm, proxying to `127.0.0.1:<port>`, ports from 8551).
- Username rule enforced there: `^[a-z][a-z0-9_]{0,31}$`, and never contains
  `added`.
- The nginx site config includes `/etc/nginx/dpd/*.conf` inside one
  `server {}` block; the shared `location = /status` block (maintainer's
  own login) was added by hand into the site file — precedent for one more
  shared location.
- The whole server stack runs as root: the runbook drives `root@<ip>`, the
  clone lives at `/root/dpd-db`, `dpd-gui@.service` gets `User=$(id -un)`
  = root, and the nightly maintenance window runs from root's crontab.
- Host: Ubuntu 24.04, 2 vCPU, 8 GB RAM (memory was already cut twice in
  20261102 threads), ports 22/80/443 open, TLS via sslip.io domain.
- `fastapi>=0.110.2` and `uvicorn>=0.30.1` are already dependencies
  (pyproject.toml). `htpasswd -v` (verify) is supported by the installed
  apache2-utils.
- gui2 contains no password code; authentication is entirely nginx. The
  env var `DPD_GUI2_USERNAME` holds the username but no secret.
- Runbook: `scripts/server_contrib/NEW_SERVER_RUNBOOK.md` documents every
  server step; `nginx_contrib_user.conf.template` and
  `nginx_status.conf.template` are the nginx templates.

## Web research (prior art, 2026-11-07)

This problem is old and repeatedly solved; every found tool uses the same
pattern — keep basic auth, serve a small change-password page, verify the
current password, rewrite the htpasswd entry atomically:

- nginx reads `auth_basic_user_file` on every request; rotation guidance is
  atomic temp-file + rename; no reload needed (nginx docs; NovelCrypt
  "Rotate .htpasswd Passwords Without Downtime", 2026-08-11).
- `gcavalcante8808/htpwd` — Flask web UI for users to change their own
  htpasswd password, over SSL. Closest match, tiny, unmaintained (★1).
- `soster/htadmin` (★18) — PHP editor with a self-service area where every
  user changes his own password; admin creates users; docker-compose.
- `mcserep/htaccessManager` (★2) — PHP, relies on `PHP_AUTH_USER` (the page
  itself sits behind the same basic auth).
- `frogsong/htpasswd-portal` (★1) — PHP portal for HTTP-authenticated users
  with a password change tool.
- Bigger family that REPLACES basic auth with form login + `auth_request`:
  `qvest-digital/loginsrv` (★1926), `travisghansen/external-auth-server`
  (★336), oauth2-proxy, Authelia. Heavier: new session layer, cookie
  management, more moving parts than this thread needs.

No tool is standard/maintained enough to adopt as-is for this stack (most
are PHP or stale); all confirm the minimal pattern above.

## Architecture forks still open (owner decides after gates)

1. Shared page (`/password/`, app itself asks username + current password)
   vs per-user authed path (`/<user>/password/` reusing the existing
   per-user basic auth, app reads the Authorization header).
2. Service privilege: run as root (consistent with the rest of the box) vs
   dedicated user + loosened htpasswd dir permissions.
3. Password policy (minimum length) and brute-force throttling strength.
4. Standalone page only, vs also an in-gui2 button later (defer?).
