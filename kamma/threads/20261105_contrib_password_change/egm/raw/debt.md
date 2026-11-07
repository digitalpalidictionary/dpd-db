Findings, worst first.

**Major — the 640 root:<nginx-group> invariant will be silently re-broken by the page.**
`scripts/server_contrib/add_contributor.sh:71-94` exists precisely because `640 root:root` locks the nginx worker out and "every request to the new URL answers 500". A temp-file + `os.replace` in a Python app creates `600 root:root` by default and *drops the group*; `os.replace` also swaps the inode, taking ACLs/xattrs with it. Failure: the contributor changes their password, their own URL 500s forever, and nothing in the design knows it. Fix: extract the chmod/chgrp logic into one place both the shell script and the app call (or have the app chmod 640 + chgrp the detected group after replace), and assert it in a test.

**Major — untestable as hypothesised; the precedent exists and is being bypassed.**
`tests/scripts/server_contrib/test_add_contributor.py:13-27` runs the real script under `--root tmp_path`, skipping when `htpasswd` is absent. A page that hardcodes `/etc/nginx/dpd/<user>.htpasswd` and needs root has no equivalent affordance, so the only code path that touches credentials ships untested. Fix: `--root`/`--htpasswd-dir` injection, verify+rewrite in a plain module (no FastAPI import needed), tests at `tests/scripts/server_contrib/`.

**Major — the shared path collides with the username grammar.**
`add_contributor.sh:25-33` allows `^[a-z][a-z0-9_]{0,31}$` and only forbids `added`. `password` is legal, so is `status` today (already a latent bug). A contributor named `password` yields two identical prefix locations, `nginx -t` fails, and the reload that would publish every other change fails with it. Fix: a reserved-name list in `add_contributor.sh`, with a test.

**Major — a rebuilt server silently loses the feature.**
The site template only has `include /etc/nginx/dpd/*.conf;` (`scripts/server_contrib/nginx_contrib.conf.template:12`); the `/status` precedent was inserted *by hand* into the live sites file (runbook Step 7d). Add the password location the same way and the next rebuild (runbook is the only build record) produces contributors with no way to change a password, and no CHECK to notice. Fix: put the block in `nginx_contrib.conf.template` with a placeholder, so the template is the single source, not a hand-edit step.

**Major — the runbook's stored passwords become false.**
Step 7a tells the OWNER to copy each password into `~/dpd_pw_<user>`; Step 11a uses those files for its CHECK. After any self-service change those checks answer 401 and a future operator reads it as a broken server. Fix: runbook must scope the file ("valid until the contributor changes it") or drop it in favour of an owner-run reset.

**Major — two auth paths, one of them undocumented and unthrottled.**
nginx basic auth has no rate limit anywhere; the page's own count will be app memory — lost on restart, no audit trail, nothing to read at 3am. Worse, changing a password does not end existing Flet sessions: nginx auths the websocket handshake once (`nginx_contrib_user.conf.template:12-17`, `proxy_read_timeout 3600s`), so the user believes they are locked out when they are not. Fix: put throttling at the proxy (`limit_req`/fail2ban) so one mechanism covers both paths, and state the session caveat in the page text.

**Major — `htpasswd -vb file user password` puts the plaintext on argv.**
Directly contradicts runbook rule 1 ("do not put a password in a command text"): visible in `ps`/`/proc` and in any command logging. Fix: `-i` on stdin, as `add_contributor.sh:72-76` already does.

**Nit — format coupling.** The page must pass `-B` explicitly and match the script's cost, or entries drift to `$apr1$`. Python 3.13 dropped stdlib `crypt`, so replacing the CLI later needs a new dependency plus `$2y$` prefix handling.

**Nit — unowned page.** Inline HTML/CSS in a repo whose UI is Flet: nothing lints it, nothing themes it, and it belongs to nobody. Use a `jinja2` template file (already a dependency).

**Nit — a third root-run service** on a box whose memory was cut twice, with no health check and no runbook line describing what to do when it dies.
