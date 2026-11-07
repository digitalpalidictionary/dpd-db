## Findings

**1. Blocker — the feature solves no case that can occur.** The only documented password flow is owner-sets-once (runbook §7a, `add_contributor.sh:76-77`), and the owner keeps every plaintext password at `~/dpd_pw_<user>` (runbook §11). Nothing in the repo or thread records a contributor asking to change one. Worse, the page cannot serve the case that motivates self-service — a contributor who *forgot* their password: behind `auth_basic` they cannot reach the page, and outside `auth_basic` it degenerates into an unauthenticated password-verify oracle (see 4). It only serves a logged-in user who wants a *different* password.
Fix: don't build it. A `set_password.sh` that reuses `add_contributor.sh:82-94` (the `nginx -T` group detection that everyone gets wrong) plus a `chgrp` is ~15 lines, maintainer-run over ssh, triggerable by any existing channel. Add one runbook step. That is the whole requirement.

**2. Blocker — a root-privileged HTTP service rewriting all auth files.** `/etc/nginx/dpd/*.htpasswd` is `640 root:www-data` (`add_contributor.sh:77,89`), so the app must run as root or be given dir write. gui2 cannot do it: each instance runs `User=@USER@` (`dpd-gui@.service:13`). If the username comes from a form field rather than nginx's `$remote_user`, any contributor authenticates once and rewrites *every other contributor's* hash, and any unvalidated username is a path segment into an `os.replace` target.
Fix (only if built): username from `$remote_user` header alone, `^[a-z][a-z0-9_]{0,31}$` as at `add_contributor.sh:24`, target path built from a fixed prefix, temp file in that directory only, no other capability in the process.

**3. Major — `os.replace` silently locks the user out.** The temp file inherits `umask 077` root:root (`add_contributor.sh:71`), so after replace nginx cannot read the hash and `/user/` answers 500 — the contributor's only work channel dies, and recovery needs the maintainer with ssh. This is the exact failure the existing script warns about twice (`add_contributor.sh:79-94`; README "or the URL answers 500").
Fix: `os.fchmod(tmp, 0o640)` + `os.fchown` to nginx's group *before* `os.replace`, fsync file and dir, then re-verify with `htpasswd -vb` and roll back on failure.

**4. Major — the "verify current password" step is either redundant or a liability.** Behind `auth_basic`, nginx already proved the credential; re-running `htpasswd -vb` only adds a bcrypt subprocess per attempt. Exposed without auth_basic, it is a rate-limit-free brute-force oracle on a 2 vCPU / 8 GB host measured at ~170 MB free RAM (README), where four concurrent gui2 instances already fight for memory.
Fix: take `$remote_user` from the auth_basic layer; never verify a password submitted in a form; no rate-limit design needed because no verify endpoint exists.

**5. Nit — browser caching.** After a successful change the tab keeps replaying the old basic-auth credential, so the next request 401s and the user reads it as "my new password is wrong". Needs explicit "close all browser windows" copy, and a re-prompt-tolerant response.

**6. Nit — there is nothing to reuse, which supports not building.** `fastapi`/`uvicorn` are genuine deps (`pyproject.toml:6-7`), but `passlib.apache.HtpasswdFile` (the only htpasswd read/verify/write library) is maintenance-only since 1.7.4 (2020) and not installed; `fastapi-users` keeps users in its own DB, not in htpasswd files; `authelia`/`lldap`/`oauth2-proxy` replace basic auth wholesale — far more surface than the problem. Contributors have unix accounts (`dpd-gui@.service:13`) but ssh is keys-only (runbook §2c), so there is no contributor shell path either.

Net: the reused-dependency route does not exist, and the no-code route is one maintainer script.
