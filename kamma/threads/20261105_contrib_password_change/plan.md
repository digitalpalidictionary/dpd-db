# Plan: a contributor changes their own password

**Thread:** 20261105_contrib_password_change
**Spec:** `kamma/threads/20261105_contrib_password_change/spec.md`
**GitHub issue:** digitalpalidictionary/dpd-db#215

## Architecture Decisions

- **Two modules, not one.** `scripts/server_contrib/password_change.py`
  holds the plain core (username rule, `identify_user`, write path,
  verify, marker ops, `check_gated`, Origin/Referer decision) with the
  htpasswd directory injected via a constructor argument — no fastapi
  import, so tests stay light. `scripts/server_contrib/password_service.py`
  is the thin FastAPI layer (routes, HTML, socket permissions) over that
  core.
- **unix socket, no TCP port** (`/run/dpd-password.sock`, 0660
  root:nginx-group; `DPD_PASSWORD_SOCK` and `DPD_HTPASSWD_DIR` env
  overrides for dev/tests). Kernel ACL replaces a shared secret. Socket
  permissions are fixed by a `uvicorn.Server` subclass overriding
  `startup()` — chmod AFTER the bind; a startup-hook chmod races the
  bind (Gate 3).
- **Named-location redirect** (`error_page 403 = @pw_@USER@;` +
  `location @pw_@USER@ { return 302 /@USER@/password/; }`) — always
  emits a real `Location` header; per-user names avoid collisions in the
  shared `server {}`.
- **Internal subrequest location** `/_dpd_pw_check` lives once in the
  site template (`nginx_contrib.conf.template`); the live site file gets
  it via an unconditional runbook patch BEFORE any auth_request-bearing
  user conf is deployed, and `add_contributor.sh` warns when the
  installed site file lacks it.
- **set_password.sh is self-contained bash**, duplicating the ~15-line
  chgrp/nginx-group logic from add_contributor.sh rather than sourcing
  it — both scripts stay runnable standalone, matching repo style.
- **Verify-before-replace** (`htpasswd -vi` on the temp file, empirically
  proven) under a per-user `threading.Lock`; the marker is deleted only
  after a real verification passed. No fallback path exists.
- **Validation layers pinned** (Gate 3): `POST /` in the service checks
  repeat-match, then length 10–72, and re-renders the form with an
  inline message on failure (plain-form UX — no 400s); the core also
  enforces length bounds and raises `ChangeError` as defense in depth.
  The POST route reads the urlencoded body with stdlib `parse_qs`
  (`fastapi.Form` would pull in python-multipart, a new dependency —
  forbidden) and runs the blocking write via
  `starlette.concurrency.run_in_threadpool`; GET routes stay plain
  `def`. Same off-loop guarantee, same per-user lock.
  Failure→status map: Origin/Referer reject → 200 error page; unknown
  user → 200 error page; validation → 200 form page + inline message;
  `ChangeError` → 500 error page + journald ERROR; success → 200 success
  page; `/check` → 200/403 only; `/health` → 200, body `ok`.
- **Test seams named** (Gate 3): core exposes module-level
  `_run_htpasswd(args: list[str], input: str) -> CompletedProcess` and
  `_replace(src: Path, dst: Path) -> None` (thin `os.replace` wrapper);
  tests monkeypatch these for failure injection.
- Not abstracted: no CSRF token machinery (Origin/Referer check only),
  no template engine (plain HTML string), no attempt to share the
  username regex with the shell script (re-implemented + tested).

## Executor rules

- Repo tasks run as the **AGENT** in this clone (cwd = repo root;
  `uv run` prefix; never `pip`).
- The server deploy is **OWNER**-run over ssh, following runbook Step 7e
  which this thread writes — the runbook is the single deploy source;
  the plan does not duplicate its commands. The Phase 5 owner item stays
  open until the owner reports the CHECK outputs; it blocks nothing
  else.
- Every touched Python file passes `uv run ruff check --fix <file>`,
  `uv run ruff format <file>`, `uv run pyright <file>` (for
  `tests/**` use `uv run pyright --project /dev/null <file>`).
  Finish with `just typecheck`.
- Lint gates for this thread's files: scripts under
  `scripts/server_contrib/` use plain ruff/pyright (not excluded).
- Workflow duties (per `kamma/workflow.md`, adjusted by AGENTS.md):
  mark tasks `[ ]` → `[~]` → `[x]` as you go; at each phase end run the
  affected tests, announce, and propose manual checks — report-only, no
  blocking approval gates, and no commits unless the owner asks
  (propose the message instead).

## Model Strategy

| Phase | Tier | Suggested model | Reason |
|---|---|---|---|
| 1 | Pro | strongest available | security-critical write path; mode/gid invariants; locks |
| 2 | Fast | workhorse | thin mechanical layer over a pinned core |
| 3 | Fast | workhorse | config templates + shell scripts, fully specified by the spec |
| 4 | Fast | workhorse | unit, setup script, docs; prose and sed |
| 5 | Fast | workhorse | verification sweeps and handoff |

## Phase 1 — core write module + tests — *Pro*

- [x] Update `kamma/tech.md` FIRST (workflow.md rule): one dated bullet
  under contributor-server facts — the change page, the forced-first-
  change gate, the marker file, the unix socket, cost-5 pin.
  → verify: `rg -n "password" kamma/tech.md` shows the new dated line.
- [x] Write `scripts/server_contrib/password_change.py`:
  `USERNAME_RE` (+ `added` substring rule), `valid_username()`,
  `identify_user(auth_header: str | None) -> str | None` (base64 decode,
  validate, `<dir>/<user>.htpasswd` exists), `PasswordStore(htpasswd_dir:
  Path)` with `change_password(user, new_password)` (bak → temp →
  `htpasswd -B -C 5 -i` → verify temp with `htpasswd -vi` → fchmod/
  fchown from original's stat, EPERM-tolerant → `_replace` → stat assert
  → fsync dir; per-user `threading.Lock`), `needs_change(user)` /
  `check_gated(user)`, `clear_marker(user)`, `origin_allowed(origin,
  referer, host)`; module seams `_run_htpasswd(args, input)` and
  `_replace(src, dst)`; passwords only ever touch stdin of subprocesses;
  temp files dot-prefixed in the same directory, removed on failure;
  `ChangeError` carrying a short reason for every branch.
  → verify: `uv run pyright scripts/server_contrib/password_change.py`
  0 errors; `uv run ruff check scripts/server_contrib/password_change.py` clean.
- [x] Write `tests/scripts/server_contrib/test_password_change.py`
  (skipif no `htpasswd`; `tmp_path` store only): hash updated; old
  rejected / new accepted; mode preserved; gid preserved same-user;
  `.bak` written and used for restore via a monkeypatched `_replace`
  raising OSError; wrong-verify (monkeypatched `_run_htpasswd` failing
  the verify step) never replaces and never clears the marker; marker
  cleared only on success; `valid_username` rejects bad names and
  `added`; `identify_user` matrix (None/garbled header → None, unknown
  user → None, known → user); `check_gated` matrix; `origin_allowed`
  matrix; length bounds (9, 10, 72, 73 bytes).
  → verify: `uv run pytest tests/scripts/server_contrib/test_password_change.py -v`
  all pass; `rg -n "/etc" tests/scripts/server_contrib/test_password_change.py`
  → zero hits (nothing outside tmp_path).

## Phase 2 — FastAPI service layer — *Fast*

- [x] Write `scripts/server_contrib/password_service.py`: FastAPI app
  with `GET /` (form HTML string, user via `identify_user`, unknown →
  200 "no such user" error page), `POST /` (Origin/Referer guard →
  repeat-match → length → `PasswordStore.change_password` → success page
  with the caveats text; failure map per Architecture Decisions),
  `GET /check` (silent; `identify_user` + `check_gated` → 200/403),
  `GET /health` (body `ok`); GET routes are plain `def` (FastAPI's
  threadpool); the POST route is async for the body read only and runs
  the blocking write via `run_in_threadpool` (stdlib parse_qs —
  `Form` needs python-multipart, a forbidden new dep; herdr review N9
  intent preserved: the event loop never blocks and the per-user
  `threading.Lock` applies in the worker thread); journald line per
  GET/POST (user, X-Real-IP, outcome ∈ {`ok`, `rejected:<reason>`});
  never logs passwords or the Authorization header. `main()` builds a
  `uvicorn.Server` subclass whose `startup()` fixes socket mode/group
  AFTER the bind (0660, nginx-group detection with `HTPASSWD_GROUP`
  override); `DPD_PASSWORD_SOCK`/`DPD_HTPASSWD_DIR` env overrides.
  → verify: `uv run pyright scripts/server_contrib/password_service.py`
  0 errors; ruff clean.
- [x] Local smoke run: `DPD_PASSWORD_SOCK=/tmp/pw.sock
  DPD_HTPASSWD_DIR=/tmp/pwht uv run python -m
  scripts.server_contrib.password_service` in the background (after
  creating a test user's htpasswd in /tmp/pwht); `curl --unix-socket
  /tmp/pw.sock http://localhost/health` → `ok`; `curl … /check` with no
  header → 200; `stat -c %a /tmp/pw.sock` → 660; POST the form WITH an
  Origin header the guard accepts — `curl -H "Origin: https://localhost"
  … -d "new_password=…&repeat=…"` — → hash changed in /tmp/pwht (a bare
  POST is correctly rejected by the CSRF guard; herdr review N3); kill
  the server.
  → verify: outputs recorded 2026-11-07: health body `ok`; `/check`
  with no header → 200; `stat -c %a /tmp/pw.sock` → 660 (group = the
  caller's here — no nginx on the laptop; on the server the startup
  hook chgrps to the nginx group); bare POST with auth but no Origin →
  rejection page, hash unchanged; POST with `Origin: https://localhost`
  → success page, `htpasswd -vi` verifies the new hash; armed marker +
  identified user → `/check` 403, no header → 200; GET / renders the
  form for alice; log lines `POST alice - rejected:csrf` / `POST alice
  - ok` / `GET alice - ok` (no passwords, no headers). One deviation,
  recorded per the drift gate: `fastapi.Form` needs python-multipart
  (a forbidden new dep), so POST reads the urlencoded body with stdlib
  `parse_qs` and runs the write via `run_in_threadpool` — same
  off-loop guarantee.

## Phase 3 — nginx templates, issuance scripts — *Fast*

- [x] Update `scripts/server_contrib/nginx_contrib_user.conf.template`:
  add `location /@USER@/password/` (same realm/file, unix-socket
  proxy_pass with trailing slash, Host/X-Real-IP/X-Forwarded-For/
  Authorization headers, 30 s timeouts) and the gate in
  `location /@USER@/` (`auth_request /_dpd_pw_check;` +
  `error_page 403 = @pw_@USER@;` + `location @pw_@USER@ { return 302
  /@USER@/password/; }`), exactly as written in the spec.
  → verify: render both templates for `USER=alice PORT=8551` via the
  `sed` line from `add_contributor.sh` and eyeball against the spec;
  no `_` before `/password/` anywhere; every unix-socket `proxy_pass`
  carries the SECOND colon (`rg -n "unix:/run/dpd-password.sock"
  <rendered files>` — each hit must read `.sock:/`, herdr review B1).
- [x] Update `scripts/server_contrib/nginx_contrib.conf.template`: add
  the internal `location = /_dpd_pw_check` block from the spec
  (proxy_pass to the socket's `/check`, body off, Upgrade/Connection
  stripped, 2 s/5 s timeouts).
  → verify: `rg -n "_dpd_pw_check" scripts/server_contrib/` shows it in
  exactly the site template and (rendered name) the user template.
- [x] Update `scripts/server_contrib/add_contributor.sh`: write the
  marker LAST (`$nginx_dir/$user.initial`, `chmod 600`, `--root`-safe)
  and warn (chgrp-warning precedent) when the rendered conf contains
  `auth_request` but the installed site file lacks `_dpd_pw_check`.
  → verify: `uv run pytest tests/scripts/server_contrib/test_add_contributor.py -v`
  still green; add one test asserting the marker exists with mode 600
  under `--root` and that a failed rerun leaves no marker.
- [x] Write `scripts/server_contrib/set_password.sh <user>`: refuses a
  missing user (file must exist), prompts or reads stdin, `htpasswd
  -B -C 5 -i`, same chmod 640/chgrp/nginx-group logic as the add
  script, writes the marker; `--root DIR` support like the add script.
  → verify: new `tests/scripts/server_contrib/test_set_password.py`
  (mirror the add script's test shape) passes; resetting a user created
  by the add script changes the hash and arms the marker; the parity
  test (both scripts emit `$2y$05$` hashes) passes.

## Phase 4 — unit, setup, docs — *Fast*

- [x] Add `scripts/server_contrib/dpd-password.service` — the COMPLETE
  unit from the spec (`[Unit]` Description, `[Service]` block with
  `ExecStart=@CLONE@/.venv/bin/python -m scripts.server_contrib.password_service`,
  `[Install]` WantedBy=multi-user.target). Mind the module form: a direct
  script path puts `scripts/server_contrib` on sys.path and breaks the
  repo-standard `from scripts.server_contrib...` import (pyrefly caught
  this; `-m` with cwd on sys.path is the working shape).
  → verify: `systemd-analyze verify` on a rendered copy if available,
  else lint by eye against `dpd-gui@.service` structure; every `@…@`
  placeholder appears in server_setup.sh's sed.
- [x] Update `scripts/server_contrib/server_setup.sh`: new step
  "password service unit", placed right after the existing "systemd
  unit" step and BEFORE "clean tree gate"; guard = skip when
  `/etc/systemd/system/dpd-password.service` already exists (else
  render with the same sed placeholders + `daemon-reload` +
  `systemctl enable --now dpd-password`).
  → verify: `bash -n scripts/server_contrib/server_setup.sh` clean;
  the new step's skip-check is present (grep).
- [x] Update `scripts/server_contrib/NEW_SERVER_RUNBOOK.md`: new
  **Step 7e "the password gate"** (install unit → enable → ensure the
  internal location is present in the live site file — IDEMPOTENT,
  insert only when absent, assert marker count, the Step 7d `/status`
  pattern; a fresh build already renders it from the template at 6d,
  herdr review B2 — → regenerate existing user confs →
  `nginx -t` → reload → CHECK list from the spec (live checks live in runbook **11d**, a new lettered substep, per the drift gate), including the
  `Location:` header check, the fresh-browser 401 check, the
  `stat 640 root:www-data` check, and the socket still being
  `660 root:www-data` after kill→revive); touch Step 7a (marker
  mention), Step 7b (users copied from the old server are NOT armed),
  Step 11a (new CHECKs + one sentence that the `.bak` keeps the
  previous hash), Step 12e (handover text with
  `/<user>/password/`).
  → verify: a zero-context reader can follow 7e start-to-finish with
  only the runbook in hand (self-check by re-reading; the herdr review
  re-audits).
- [x] Update `scripts/server_contrib/README.md`: one line for
  `set_password.sh` and one for `dpd-password.service`/the change page,
  in the existing telegraphic style.
  → verify: `rg -n "set_password|dpd-password" scripts/server_contrib/README.md` hits.

## Phase 5 — verification + deploy handoff — *Fast*

- [x] Full local gates: `uv run pytest tests/scripts/server_contrib/`
  green; ruff + format + pyright on every touched file;
  `uv run pytest tests/` (fast suite) green; `just typecheck` clean.
  → verify: recorded 2026-11-07 — `tests/scripts/server_contrib/` 256
  passed; full fast suite 2997 passed, 12 deselected; ruff + format
  clean on all four touched Python files; pyright 0 errors;
  `just typecheck` 0 errors (after fixing pyrefly's sibling-import
  finding: the service now imports
  `scripts.server_contrib.password_change` and the unit runs
  `python -m scripts.server_contrib.password_service` — a direct script
  path breaks that import because sys.path[0] becomes the script dir).
- [x] Hand off the deploy: present runbook Step 7e + its CHECK list to
  the owner as the deploy instruction (the runbook is the single
  source; nothing is deployed from the plan).
  → verify: handoff note in the final report names runbook Steps 7e
  and 11d (the live checks landed in 11d, a new lettered substep —
  recorded per the drift gate). THE DEPLOY IS NOT RUN: it needs the
  live server and the OWNER.
- [ ] OWNER deploy confirmation (owner-run, ssh, per runbook 7e): every
  7e CHECK passes on the live server — fresh browser → 401; armed
  marker → 302 with `Location:`; change → old password 401 / new 200;
  `stat 640 root:www-data`; marker gone; socket health; kill → revive
  AND the socket is still `660 root:www-data`.
  → verify: owner reports each CHECK output back into this task's note;
  the task stays open until then (blocks nothing).

## Post-review

After `/kamma:3-review` and the herdr pane review pass: fold findings,
then `/kamma:4-finalize` (commit message suggestion only — no GitHub
writes; per AGENTS.md the finalize GitHub step is skipped).
