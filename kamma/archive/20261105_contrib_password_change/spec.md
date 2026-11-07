# Spec: a contributor changes their own password

**Thread:** 20261105_contrib_password_change
**Date:** 2026-11-07 (placeholder spec of 2026-11-05 replaced)
**GitHub issue:** digitalpalidictionary/dpd-db#215 (contribution website part)
**Status:** planned via kamma-1-plan-egm; Gates 1–3 and the herdr review done

## Overview

Contributors log into the contributor server (`https://<host>/<user>/`) via
nginx basic auth against per-user htpasswd files. Today only the maintainer
sets passwords, through `scripts/server_contrib/add_contributor.sh`; a
contributor who wants a new password must ask. This thread gives
contributors self-service password change with a forced change on first
login, without touching gui2 and without replacing basic auth.

Chosen design (owner decisions, 2026-11-07):

1. **Change page behind the user's own realm** — the page lives at
   `/<user>/password/`, protected by the same per-user `auth_basic` that
   protects the editor. The form asks only for the new password (twice);
   nginx has already authenticated the request, so there is no username
   field and no current-password field, and no unauthenticated verify
   oracle.
2. **Forced first change by redirect gate** — when the maintainer issues or
   resets a password, a marker file `/etc/nginx/dpd/<user>.initial` is
   written. While it exists, an nginx `auth_request` subrequest to the
   service's `/check` endpoint returns 403 for the editor location and a
   redirect sends the browser to `/<user>/password/`. The editor is
   unreachable until the password is changed; the service deletes the
   marker on success. No banner, no nag, no gui2 change.
3. **Maintainer keeps the override** — a new `set_password.sh` resets any
   user's password over ssh (and re-arms the marker).

## What it should do

### The change service (`scripts/server_contrib/password_service.py`)

- One FastAPI app served by uvicorn on a **unix socket**
  `/run/dpd-password.sock` (NOT a TCP port — see security note below).
  Stdlib + fastapi/uvicorn imports only; never imports from `db/`,
  `gui2/`, `tools/`.
- On startup the app chmods the socket to `0660` and chgrps it to the
  nginx group (same detection as `add_contributor.sh`: `nginx -T` user
  line, `HTPASSWD_GROUP` override) so only nginx (www-data) and root can
  connect. A local process that is neither cannot reach the service at
  all, so it cannot forge an `Authorization` header and change someone's
  password (Gate 2 design finding: "the service trusts any local caller").
- `GET /` — HTML form (new password + repeat, no JavaScript, plain HTML
  string in the module — no template engine). Identifies the user by
  decoding the `Authorization` header nginx forwarded (base64 basic
  auth), validates the username against the full `add_contributor.sh`
  rule (`^[a-z][a-z0-9_]{0,31}$` AND not containing `added`), and
  requires `/etc/nginx/dpd/<user>.htpasswd` to already exist (never
  creates). Shows "Changing the password for <user>".
- `POST /` — same identification, then:
  - **CSRF guard** (Gate 2: cached basic-auth credentials ride cross-site
    form POSTs): accept only when `Origin == https://<Host>` or
    `Referer` starts with `https://<Host>/`; otherwise reject with a
    clear error page ("open the password page directly"). No cookies or
    tokens needed.
  - Validate: new == repeat; 10 ≤ length ≤ 72 bytes (bcrypt truncates
    beyond 72 — verified empirically); no composition rules.
  - The write path (below). On success: delete the marker if present;
    return a success page linking to `/<user>/` that explains: close
    other DPD tabs; the next login prompt expects the NEW password; an
    editor tab already open may keep working up to 1 hour on the old
    login (nginx `proxy_read_timeout 3600s` keeps the websocket open;
    the owner chose documenting this over restarting the instance).
- `GET /check` — for the nginx `auth_request` subrequest: **403 only
  when** it can positively identify an existing user whose marker file
  exists; **200 in every other case** (header absent or unparsable, user
  unknown). nginx's basic auth is the real gate for unauthenticated
  visitors — `auth_basic` answers 401 before `auth_request` runs — so
  `/check` never needs to fail closed on identity it cannot parse.
  `/check` logs nothing (it fires on every editor request). The core
  module owns the two pieces: `identify_user(auth_header) -> str | None`
  (decode, validate, file-exists) and `PasswordStore.check_gated(user)
  -> bool`; the service maps `None`/`False` → 200 and `True` → 403.
- `GET /health` — 200, for the runbook CHECK
  (`curl --unix-socket /run/dpd-password.sock http://localhost/health`).
- Logging: one journald line per `GET /` and `POST /` (via stderr →
  systemd): timestamp, user, client IP (from `X-Real-IP` set by nginx),
  outcome. `/check` is silent. Passwords and raw Authorization headers
  are never logged.

### The write path (the part that must not break anything)

Gate 1 #1: a naive temp-file + `os.replace` produces `600 root:root`,
drops the nginx group, and the user's whole URL answers 500 forever.
Gate 2 added: verify-before-replace under a per-user lock (two racing
POSTs otherwise let the loser pass verification against the winner's
hash). Therefore, all under a per-user lock (single worker process):

1. `shutil.copy2` the htpasswd file to `<user>.htpasswd.bak` (single
   rolling backup, same directory).
2. Copy to a dot-prefixed temp file in the same directory.
3. `htpasswd -B -C 5 -i <temp> <user>` with the new password on stdin
   (passwords never in argv — Gate 1 #7; the runbook forbids argv
   passwords). `-C 5` matches the existing baseline from
   `add_contributor.sh`; a higher cost would multiply nginx's per-request
   bcrypt up to 128× (Gate 1 #4).
4. **Verify the temp**: `htpasswd -vi <temp> <user>` with the new
   password on stdin — empirically proven to work (exit 0 correct /
   exit 3 wrong, 2026-11-07). No fallback path exists or is needed;
   the marker is never deleted unless this real verification passed.
   Failure → delete temp, 500, original untouched.
5. `os.fchmod`/`os.fchown` the temp to the ORIGINAL file's mode and gid
   (stat before replace; today `640 root:www-data`; tolerate EPERM when
   not run as root, e.g. in tests), `os.replace`, fsync the directory.
6. Stat-assert mode and gid on the real file; failure (or any earlier
   failure after step 1) → restore from `.bak` AND re-apply the
   captured mode + gid to the restored file (`shutil.copy2` preserves
   mode but never ownership, so the `.bak` is root:root and a bare
   restore would re-create the very 500 trap this path guards against
   — herdr review M1), log, 500.
7. Delete `/etc/nginx/dpd/<user>.initial`.

   Known crash window: a crash between steps 5 and 7 leaves the new
   password live with the marker still armed — the user is simply
   asked to change again (herdr review N7); the success page and the
   runbook triage say so. The `.bak` keeps the previous hash until the
   next change — a deliberate recovery artifact, documented in the
   runbook (herdr review N6).

No nginx reload is needed for any of this: nginx re-reads
`auth_basic_user_file` on every request (web-verified; the deploy CHECK
re-verifies with a live change).

### Forced-first-change gate (nginx)

`nginx_contrib_user.conf.template` gains, per user (all inside the
per-user conf file; every name embeds `@USER@` so per-user confs never
collide in the shared `server {}`):

- `location /@USER@/password/` — same `auth_basic` realm and file,
  `proxy_pass http://unix:/run/dpd-password.sock:/;` (note the colon
  before the trailing slash — nginx splits socket path from URI at the
  SECOND colon; without it the whole remainder becomes the socket path
  and every request 502s while `nginx -t` still passes; herdr review
  B1), `proxy_set_header Host $host`, `X-Real-IP` /
  `X-Forwarded-For`, `Authorization` passed explicitly
  (`proxy_set_header Authorization $http_authorization;` — pass-through
  is the default, stated for the implementer), plain HTTP timeouts
  (~30 s; no websocket here).
- The existing `location /@USER@/` gains `auth_request /_dpd_pw_check;`,
  `error_page 403 = @pw_@USER@;`, and the same file adds
  `location @pw_@USER@ { return 302 /@USER@/password/; }` — the
  named-location + `return` form always emits a real `Location` header
  (the `error_page 403 =302 /path;` shorthand's redirect behaviour was
  contested in Gate 2 and cannot be verified without a live nginx; the
  chosen form needs no verification beyond the deploy CHECK). The
  redirect target was typo-checked: `/@USER@/password/`, no stray `_`.

`nginx_contrib.conf.template` (the site template, tracked in the repo)
gains the shared internal subrequest location, defined once:

```nginx
location = /_dpd_pw_check {
    internal;
    proxy_pass http://unix:/run/dpd-password.sock:/check;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    # The gate depends on this header; state it, never rely on the
    # pass-through default (herdr review N1).
    proxy_set_header Authorization $http_authorization;
    # The subrequest inherits the websocket handshake's upgrade headers.
    proxy_set_header Upgrade "";
    proxy_set_header Connection "";
    proxy_connect_timeout 2s;
    proxy_read_timeout 5s;
}
```

Deployment ordering and guards (Gate 2: a user conf carrying
`auth_request` with no matching internal location makes that user's URL
answer 500):

- The live site file must be patched with the internal location BEFORE
  any user conf with `auth_request` is deployed. The runbook step
  ALWAYS RUNS but is IDEMPOTENT: it inserts the block only when absent
  and asserts the marker count, exactly like Step 7d's `/status` patch
  — a fresh build already renders the block from the site template at
  Step 6d, and an unconditional insert there would duplicate the
  location and fail `nginx -t` (herdr review B2). CHECK
  `nginx -T | grep -c _dpd_pw_check` → exactly the expected count.
- `add_contributor.sh` warns loudly (the chgrp-warning precedent) when
  the rendered conf contains `auth_request` but the installed site file
  (respecting `--root`) does not contain `_dpd_pw_check`.
- Known residual: after the marker is gone, a 403 returned by the gui2
  app itself inside `/<user>/` would also be redirected to the password
  page. Flet does not emit 403s; accepted and documented.
- Fail-closed coupling (accepted): if `dpd-password.service` is down,
  the editor location answers 500 until systemd restarts it
  (`Restart=always`, `MemoryMax=128M`; triage matrix documents
  500 = check `dpd-password`).
- `auth_request` is a standard module in Ubuntu's nginx; the deploy
  CHECK confirms it (`nginx -T 2>/dev/null | grep auth_request`).

### Issuance and reset

- `add_contributor.sh`: password flow unchanged, plus writes the marker
  LAST (after all other steps succeed, so a mid-script failure cannot
  leave an armed-but-broken user), at `$nginx_dir/$user.initial`
  (`--root`-prefixed like every other path — the existing tests run
  under `--root`). Mode 600 (what the script's `umask 077` already
  yields) is correct and deliberate: the only reader is the root-run
  service, and a world-readable marker would leak forced-change state
  (herdr review N2; set it explicitly anyway, for clarity).
- New `scripts/server_contrib/set_password.sh <user>`: maintainer-run
  reset for an EXISTING user (the add script refuses existing users —
  Gate 1 #11). Terminal prompt or piped stdin, `htpasswd -B -C 5 -i`,
  same chmod/chgrp/nginx-group logic as the add script, re-arms the
  marker. Refuses unknown users (file must exist).
- Runbook: the owner's `~/dpd_pw_<user>` initial-password files go stale
  after the first self-service change; the runbook text scopes them
  ("valid until the contributor changes it") — Gate 1 #11.

### Unit and deployment surfaces (all tracked in the repo — Gate 1 #5)

- `dpd-password.service` template beside `dpd-gui@.service`, filled by
  the same sed pattern as `server_setup.sh` uses for the gui2 unit
  (complete unit, comparable to `dpd-gui@.service`):

```ini
[Unit]
Description=DPD contributor password change service (unix socket)

[Service]
Type=simple
User=root
WorkingDirectory=@CLONE@
ExecStart=@CLONE@/.venv/bin/python -m scripts.server_contrib.password_service
Restart=always
RestartSec=5
MemoryMax=128M

[Install]
WantedBy=multi-user.target
```

  The module's `main()` runs uvicorn programmatically on the socket and
  fixes permissions only AFTER the bind (a `uvicorn.Server` subclass
  overriding `startup()` — a startup-hook chmod races the bind and can
  crash the service). `--app-dir` import trick not needed (the module
  is run as a file). No `uv run` wrapper, no repo imports — Gate 1 #16.
  No TCP port is used, so no port needs reserving — Gate 1 #17 became
  moot. Env overrides for dev/tests: `DPD_PASSWORD_SOCK` (default
  `/run/dpd-password.sock`) and `DPD_HTPASSWD_DIR` (default
  `/etc/nginx/dpd`).
- `server_setup.sh` gains the install step (fresh builds must get the
  feature — a rebuilt server must not silently lose it).
- `NEW_SERVER_RUNBOOK.md`: new lettered substep **7e** ("the password
  gate") for the live server: create the unit, `systemctl enable --now
  dpd-password`, patch the site file with the internal location
  (unconditional, before any user conf), regenerate each existing
  user's `/etc/nginx/dpd/<user>.conf` from the new template,
  `nginx -t` + reload, then CHECKs. Edits to existing text: Step 7a
  (mention the marker), Step 7b (one line: users copied from the old
  server are NOT armed — the gate applies to newly issued or reset
  passwords only, herdr review N8), Step 11a CHECKs (password page
  401→200; armed marker → 302 with `Location:` header; changed
  password → old 401 / new 200; `stat -c "%a %U:%G"
  /etc/nginx/dpd/<user>.htpasswd` still `640 root:www-data`; marker
  gone; `curl --unix-socket … /health`; fresh browser → 401 prompt,
  not 302; after the kill→revive CHECK the socket is STILL
  `660 root:www-data` — uvicorn re-applies the mode but never the
  group, herdr review N4; one sentence noting the `.bak` keeps the
  previous hash), Step 12e handover text (the URL `/<user>/password/`
  and the forced first change).
- The nightly maintenance window is NOT modified: it pulls the repo but
  never touches units or nginx, and the service's code is stable; if
  the module ever changes, the runbook step includes
  `systemctl restart dpd-password`.

### Tests (Gate 1 #13)

`tests/scripts/server_contrib/test_password_change.py`, mirroring the
`test_add_contributor.py` precedent (skipif no `htpasswd`; `--root`-style
injection via a constructor/config argument on the plain core module —
the FastAPI layer stays thin and untested-by-default). The core write
logic is a plain module function with an injectable htpasswd directory.
Tests, with the real `htpasswd` binary:

- hash updated; old password rejected (`htpasswd -vi` exit 3), new
  accepted (exit 0);
- mode preserved across the replace; gid preserved in the same-user
  case (fchown EPERM tolerated when not root; the root:www-data case is
  the runbook's server CHECK);
- `.bak` exists and restores on an induced failure, with mode and gid
  re-applied to the restored file;
- a parity test: `add_contributor.sh` and `set_password.sh` emit the
  same `$2y$05$` hash format (drift guard for the duplicated flags —
  herdr review N5);
- verification failure (wrong new password passed to verify) never
  replaces the file and never deletes the marker;
- marker deleted only on success; `/check` decision function 200/403
  matrix; username rule (bad names rejected, `added` rejected);
  Origin/Referer decision matrix; length bounds 10 and 73 bytes.

## Assumptions & uncertainties

- Verified against source (2026-11-07): everything in `egm/brief.md`'s
  facts list (per-user htpasswd/conf/env layout, 640 root:<nginx-group>
  invariant, root-run stack, fastapi/uvicorn already deps, test
  precedent, rollback scope of the nightly window).
- Verified empirically on this laptop (2026-11-07): `htpasswd -vi`
  stdin verify works (0 correct / 3 wrong); `htpasswd -B -C 5 -i`
  writes `$2y$05$` hashes; 80-byte password fails verification
  (bcrypt 72-byte truncation is real).
- Web-verified: nginx re-reads the htpasswd file per request; no reload
  for content changes. Re-verified live in the deploy CHECK.
- Assumed: `auth_basic` runs before `auth_request` in nginx's access
  phase (standard Ubuntu build order), so unauthenticated visitors get
  the 401 prompt, never the redirect. The deploy CHECK (fresh browser →
  401) verifies this on the live nginx.
- Assumed: uvicorn's `--uds` + in-app chmod/chgrp covers socket
  permissions; verified in the plan's local run.
- Assumed: ~5 contributors, changes are rare; no load concerns. bcrypt
  cost 5 is today's proven baseline (nginx already computes it on every
  authenticated request).
- Gate 1 accepted findings folded in: #1 mode/gid trap (Blocker), #2/#3
  oracle avoided by the authed path (Blocker/Major), #4 cost pin
  (Major), #5 deployment path (Blocker), #6 supervision (Blocker), #7
  argv leak (Major), #8/#9 session + cached-credential caveats (Major,
  documented only — owner), #10 discovery solved by the gate itself,
  #11 reset path + stale owner files (Major), #13 test surface (Major),
  #14 audit lines + real IP (Major), #16 startup shape (Major), #18
  nothing reusable (research note).
- Gate 2 accepted findings folded in: redirect form made unambiguous
  and typo-proof (Blocker), error_page scoped inside the location and
  per-user named locations to avoid server-level collisions (Blocker),
  unconditional site-file patch + add_contributor guard for the
  internal location (Blocker), `/check` semantics fully specified
  (Blocker), Authorization forwarding stated (Major), full unit spec
  (Major), logging scoped to GET/POST (Major), marker `--root` +
  chmod 600 + write-last (Major), injectable-dir mechanism named
  (Major), CSRF guard (Major), verify-temp-under-lock (Major),
  real-verify-only marker deletion (Major), local-caller hardening via
  unix socket (Major), subrequest header hygiene + timeouts (Major),
  403-swallowing residual documented (Major→accepted), 72-byte cap,
  .bak single rolling backup, temp cleanup (Nits).
- Gate 1 rejected/moot: reserved usernames (moot — no shared location;
  `location = /status` exact match wins over a `/status/` prefix
  anyway), separate log files (journald covers it), build-nothing
  (owner decided the feature exists), jinja2 (plain HTML string).
  Gate 2 rejected: none — all findings accepted or folded as above.

## Constraints

- No gui2 changes at all (owner).
- No session restart after a change (owner: don't over-engineer).
- No new Python dependencies; no SSO/auth-model replacement.
- Passwords never in argv, logs, or journald; the service never creates
  htpasswd files, only rewrites existing ones.
- The service listens only on the unix socket; nginx is the only client.
- Runbook step numbers are fixed — new material goes in lettered
  substeps (7e here).
- Writes are rare; the per-user lock plus atomic full-file replace is
  the entire concurrency story.

## How we'll know it's done

- `uv run pytest tests/scripts/server_contrib/test_password_change.py`
  green (plus the whole `tests/scripts/server_contrib/` folder), ruff +
  pyright clean on every touched file, `just typecheck` clean.
- On the server (runbook CHECKs): with a marker armed, browsing to
  `/<user>/` after login redirects (302 with `Location:`) to
  `/<user>/password/`; a fresh browser gets a 401 prompt, not a
  redirect; changing the password succeeds; the OLD password then gets
  401 and the NEW one 200; `stat` still shows `640 root:www-data`; the
  marker is gone; the editor loads without redirect.
  `set_password.sh` re-arms everything.
- journald shows the GET/POST attempt lines; killing the service →
  systemd revives it and the editor returns within RestartSec.

## What's not included

- Any gui2 change (banner, dialog, menu, or logic).
- Session invalidation / auto-logout / instance restart after a change.
- Self-service forgotten-password reset (email etc.) — the maintainer's
  `set_password.sh` is the reset path.
- Rate limiting or fail2ban — there is no unauthenticated endpoint;
  basic-auth brute force on the editor is pre-existing surface,
  unchanged by this thread.
- Any change to the maintainer's own credentials, ssh access, or the
  `/status` page.
- Hard password composition rules (length 10–72 only).

## Review record

Gate 1 (idea): 6 Goldfish on `pi`/deepseek-flash (native DeepSeek API),
probe passed, no fallbacks — 48 raw findings → 21 deduplicated: 17
accepted (4 Blockers, 9 Majors, 4 Nits), 3 rejected/moot, 1
accepted-modified; 2 escalations resolved by the owner (fork A: per-user
path; no session restart) + 1 owner-directed refinement (redirect gate
replacing the gui2 modal; zero gui2 changes). Full record: `egm/gate1.md`,
raw output in `egm/raw/`.

Gate 2 (spec): 2 Goldfish (comprehension + design critic), same backend
— 22 raw findings: 4 Blockers, 12 Majors, 6 Nits; all accepted and
folded in or documented as accepted residuals; none escalated; none
rejected. Empirical checks added (htpasswd flag behaviour). Full
record: `egm/gate2.md`.

Gate 3 (plan readiness): 2 Goldfish-inherited findings fixed pre-plan;
13 raw findings from one Goldfish — 12 fixed, 1 rejected-with-reason
(`egm/gate3.md`).

herdr pane review (spec + plan, 2026-11-07): the `reviewer` pane
(pi/DeepSeek V4 Pro, same repo) — 2 Blockers (unix-socket `proxy_pass`
missing the second colon; fresh-build duplicate location), 1 Major
(restore-from-`.bak` drops the nginx group), 10 Nits. All 13 accepted
and folded into spec + plan; its "verified correct" list (write path,
CSRF model, identify_user safety, error_page idiom, stale-socket
handling, auth ordering) recorded in `egm/herdr_review.md`.
