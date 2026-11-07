# EGM Gate 2 — spec review (2026-11-07)

Backend: same as Gate 1 — `pi -p --provider deepseek --model
deepseek-flash --no-session --tools read`. Two fresh reviewers
(comprehension, design critic), each read `spec.md` and the files it
references. Both returned within the cap; no fallbacks. Raw output:
`raw/gate2_comprehension.md`, `raw/gate2_design.md`. Prompts:
`prompts/gate2_*.txt`.

22 raw findings. Facts re-checked before Accept; two claims were settled
empirically on this laptop rather than argued: `htpasswd -vi` stdin
verify works (0/3 exit codes), and >72-byte passwords fail verification.
One claim could not be settled without a live nginx (`error_page 403
=302 /path` external-vs-internal redirect) — resolved by choosing the
unambiguous named-location + `return 302` form instead.

| # | Finding (reviewer) | Sev | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| 1 | Stray `_` in `error_page … /@USER@_/password/` renders a 404 loop (comprehension) | Blocker | Accept | typo in spec line, visible | Spec: typo-fixed target + deploy CHECK |
| 2 | `error_page` in per-user conf applies at server level, last include wins (comprehension) | Blocker | Accept | includes are inside `server {}`; directives outside `location` are server-scoped | Spec: error_page explicitly inside the location + per-user named location |
| 3 | Site-file patch made conditional ("if regenerating") — live file won't regenerate; auth_request names a missing location → 500 (both) | Blocker | Accept | runbook 6d/7d history read | Spec: unconditional patch, ordering (site file BEFORE user confs), add_contributor.sh grep-warn, `nginx -T` CHECK |
| 4 | `/check` behaviour with absent/garbled Authorization undefined (both) | Blocker | Accept | semantics were unstated | Spec: 403 only for positively identified user with marker; 200 otherwise; fresh-browser CHECK |
| 5 | Authorization forwarding unstated in snippets (comprehension) | Major | Accept | nginx default is pass-through, but implicit | Spec: explicit `proxy_set_header` line |
| 6 | Unit under-specified: relative ExecStart, no User/WorkingDirectory/module (comprehension) | Major | Accept | dpd-gui@.service precedent | Spec: full unit block with @CLONE@ fill, --app-dir form |
| 7 | "Every attempt logs one line" vs /check per editor request (comprehension) | Major | Accept | Flet pages issue many requests | Spec: GET/POST only; /check silent |
| 8 | Marker write must respect --root and survive umask 077 → chmod 644, write last (comprehension + design nit) | Major | Accept | add_contributor.sh --root tests + umask read | Spec: issuance section |
| 9 | "Injectable dir" names no mechanism; gid test needs chgrp-able group (comprehension + design nit) | Major | Accept | test_add_contributor.py precedent read | Spec: constructor arg on plain core module; EPERM-tolerant gid assertion |
| 10 | CSRF: cached basic-auth credentials ride cross-site form POSTs (design) | Major | Accept | classic basic-auth CSRF; field was dropped for oracle reasons | Spec: Origin/Referer guard + tests |
| 11 | Concurrent POSTs: verify-after-replace lets loser pass on winner's hash (design) | Major | Accept | race reasoning valid | Spec: verify the TEMP before replace, per-user lock |
| 12 | Fallback ("hash line looks right") verifies nothing; marker must never be deleted without a real verify (design) | Major | Accept — and mooted the fallback | `htpasswd -vi` empirically works | Spec: fallback removed, real verify mandatory |
| 13 | Service trusts any local caller with a forged header (design) | Major | Accept | loopback TCP reachable by any local uid | Spec: unix socket 0660 root:nginx-group; no TCP port at all |
| 14 | Subrequest inherits websocket Upgrade/Connection headers; no timeouts on /check (design) | Major | Accept | auth_request subrequest copies original headers | Spec: internal location strips them, 2s/5s timeouts |
| 15 | error_page 403 swallows app-emitted 403s inside the location (design) | Major | Accept as documented residual | Flet emits no 403s | Spec: residual documented |
| 16 | `error_page 403 =302 /path` may internal-redirect without Location (design) | Blocker* | Accept by substitution | could not verify without live nginx | Spec: named location + `return 302` (always emits Location); CHECK asserts `Location:` |
| 17 | New-user 500 when site file predates the thread (design) | Blocker* | Accept | same root as #3 | Covered by #3's guard + ordering |
| 18 | Max length / .bak rotation / temp cleanup / marker race nits (design) | Nit | Accept | bcrypt 72-byte truncation proven empirically | Spec: 10–72 bounds, rolling .bak, cleanup |
| 19 | Tests: gid needs root; missing cases listed (design) | Nit | Accept | EPERM reality | Spec: test list includes the matrix |
| 20 | "jinja2-level imports" vs "no template engine" contradiction (comprehension) | Nit | Accept | wording | Spec: plain HTML string, jinja2 not mentioned |
| 21 | Username rule omits the `added` substring rule; /health CHECK path; caveat mechanism unnamed; runbook substep parentless (comprehension) | Nit | Accept | add_contributor.sh:39-42 | Spec: full rule, socket curl, 3600s named, Step 7e |
| 22 | Marker ordering under `set -e` leaves armed-but-broken users (design) | Nit | Accept | shell semantics | Spec: marker written last |

(*) Severity as treated: #16/#17 arrived as parts of Blocker findings and
were fixed as such.

## Escalations

None — every Gate 2 resolution is a one-defensible-answer engineering
choice (constraint 9), made and recorded above. The CSRF guard
(current-password field vs Origin check vs token) was the only genuine
fork; Origin/Referer check chosen because it keeps the form at two
fields, needs no token state, and is trivially testable — noted here so
the owner can overrule at review time.

## Rejected findings

None rejected outright; #12's fallback clause was removed rather than
argued.
