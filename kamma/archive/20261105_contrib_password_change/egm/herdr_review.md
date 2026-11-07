# herdr pane review — spec + plan (2026-11-07)

Reviewer: the herdr pane `wB:p73` ("reviewer", pi on DeepSeek V4 Pro,
same repo), owner-requested in addition to the EGM gates. Read-only.
The full review text as delivered is preserved verbatim at the bottom
of this file.

13 findings: 2 Blockers, 1 Major, 10 Nits. All 13 accepted and folded
into `spec.md` + `plan.md` before this record was written.

| # | Finding | Sev | Decision | Where fixed |
|---|---|---|---|---|
| B1 | Unix-socket `proxy_pass` missing the mandatory second colon — socket path swallows the URI, 502s both the page and the gate, `nginx -t` passes | Blocker | Accept | Spec both templates (`.sock:/`, `.sock:/check`); plan Phase 3 verify greps rendered files for the colon |
| B2 | "Unconditional" site-file patch double-adds `/_dpd_pw_check` on a fresh build (template already renders it at 6d) → duplicate location → `nginx -t` fails | Blocker | Accept | Spec: step always runs but is IDEMPOTENT (insert-if-absent + marker-count assert, the Step 7d pattern); plan Phase 4 |
| M1 | Restore-from-`.bak` drops the nginx group (`copy2` never preserves ownership) → bare restore re-creates the 500 trap | Major | Accept | Spec write-path step 6 (re-apply captured mode+gid on restore); plan Phase 1 test |
| N1 | `/check` relies on implicit Authorization pass-through | Nit | Accept | Spec: explicit `proxy_set_header Authorization` in the internal location |
| N2 | Marker 644 rationale backwards; 600 suffices (only reader is the root service); 644 leaks forced-change state | Nit | Accept | Spec: marker 600, rationale corrected; plan test updated |
| N3 | Smoke-run POST rejected by CSRF guard (curl sends no Origin) | Nit | Accept | Plan Phase 2: `-H "Origin: https://localhost"`, rejected-then-accepted pair |
| N4 | uvicorn re-applies socket mode but never the group on restart | Nit | Accept | Spec + plan: kill→revive CHECK asserts socket still `660 root:www-data` |
| N5 | set_password.sh duplicates flags — drift guard needed | Nit | Accept | Spec + plan: parity test (both scripts emit `$2y$05$`) |
| N6 | `.bak` retains the previous hash indefinitely | Nit | Accept | Spec + runbook: documented as a deliberate recovery artifact |
| N7 | Crash window between replace and marker delete → forced re-change | Nit | Accept | Spec: crash-window note; runbook triage mention |
| N8 | 7b-migrated users never armed — unstated | Nit | Accept | Spec + plan: one line in Step 7b/7e |
| N9 | Route type unspecified; `async def` + subprocess would block the loop | Nit | Accept | Plan Phase 2: routes are plain `def` (threadpool + threading.Lock) |
| N10 | `After=network-online.target` unnecessary for a unix-socket service | Nit | Accept | Spec unit block: dropped |

## Verified correct by the reviewer (no change)

Write path reproduced live with real `htpasswd` (`-B -C 5 -i` →
`$2y$05$`, `-vi` 0/3); cost-5 baseline matches; CSRF guard model sound;
`identify_user` safe behind per-user `auth_basic`; the
`error_page 403 = @pw_@USER@` + `return 302` idiom is correct
(`absolute_redirect` absolutizes the target); stale-socket removal by
`create_unix_server` means `Restart=always` won't crash-loop; the
auth_basic-vs-auth_request ordering assumption is low-stakes either
way; all plan file paths match the repo layout and `.venv/bin/python`
exists for the unit.

## Net effect

Two pre-implementation fixes in the nginx layer (B1, B2) that no local
gate could have caught — `nginx -t` passes with B1 and no nginx runs in
this clone — plus one restore-path clause (M1) and ten tightenings.
Everything else in the design was independently reproduced or confirmed.

---

## Original review text (verbatim, as delivered)

> Review of spec.md + plan.md for kamma/threads/20261105_contrib_password_change (read-only; no edits made). Findings with severity and file:line evidence.
>
> VERDICT: design is largely sound (CSRF model, socket ACL, verify-before-replace, auth_request + named-location redirect are correctly reasoned; Gate 3 already caught most readiness gaps). One Blocker breaks the whole feature, one deterministic fresh-build breakage, plus a few real gaps the gates missed.
>
> === BLOCKERS ===
>
> B1 — nginx unix-socket proxy_pass syntax missing the mandatory colon (spec.md:126, spec.md:147)
>   proxy_pass http://unix:/run/dpd-password.sock/;      (line 126)
>   proxy_pass http://unix:/run/dpd-password.sock/check; (line 147)
> Both wrong. nginx needs a colon between socket path and URI:
>   proxy_pass http://unix:/run/dpd-password.sock:/;       (trailing slash -> strips prefix)
>   proxy_pass http://unix:/run/dpd-password.sock:/check;  (URI -> rewrites to /check)
> nginx finds the first ':' (the "unix:" marker) then looks for a SECOND ':' to split socket path from URI. With none, the whole remainder becomes the socket path:
>   - line 126 -> socket path "/run/dpd-password.sock/" (trailing slash) -> connect fails -> 502, and the /@USER@/password/ prefix is NOT stripped (no URI) -> FastAPI 404 even if it connected.
>   - line 147 -> socket path "/run/dpd-password.sock/check" -> 502.
> This breaks both the change page AND the gate. nginx -t PASSES (valid URL string), so only the live deploy CHECK catches it. The plan's only local check (Phase 3 "eyeball against the spec") reproduces the error instead of catching it. Fix in both spec and plan templates before implementing.
>
> B2 — "Unconditional" site-file patch double-adds /_dpd_pw_check on a fresh build (spec.md:164-166, spec.md:234-235, plan Phase 3)
> The internal location is added TWICE: Phase 3 adds it to nginx_contrib.conf.template, and runbook Step 7e patches it into the live site file "unconditionally". On a fresh build, Step 6d renders the new template (already containing location = /_dpd_pw_check), then 7e inserts it again -> duplicate location -> nginx -t fails "duplicate location". The runbook's audience IS a new server, so this is the primary path.
> Step 7d's /status patch already shows the right pattern (assert text.count(marker)==1 and "location = /status" not in text). Step 7e needs the same idempotency guard. "Unconditional" should mean "always run this step", NOT "always insert regardless of presence".
>
> === MAJOR ===
>
> M1 — restore-from-.bak path does not restore the nginx group (spec.md:110-112, steps 5-6)
> Step 1 makes .bak via shutil.copy2, which preserves mode (640) but NOT ownership -> the copy is root:root (service runs as root). Step 6 says "restore from .bak", but a bare restore leaves the live htpasswd 640 root:root -> nginx locked out -> 500, the exact failure the restore exists to fix (the spec itself names this trap at line 88-89). The restore must re-apply chmod 640 + chgrp to nginx's group. Neither spec nor plan states this. Also .bak is never chgrp'd, so on the server it stays root:root — harmless as a backup but it's the file you'd restore FROM, so it must be fixed up on the way back in.
>
> === NITS === (N1–N10 as dispositioned in the table above)
>
> === VERIFIED CORRECT (no change) ===
> - Write path works with real htpasswd: reproduced -B -C 5 -i <temp> <user> updating an entry -> $2y$05$ hash; -vi returns 0 (correct) / 3 (wrong). Temp-copy-before-update flow is sound.
> - -C 5 matches the existing baseline (add_contributor.sh uses -B, default cost 5).
> - CSRF guard is sound (Origin exact / Referer prefix https://<Host>/ blocks the cross-site cached-credential POST; trailing slash prevents host vs host.evil confusion).
> - identify_user is safe: nginx per-user auth_basic validates the Authorization header against the correct per-user htpasswd before the service sees it, so decoded username always matches the URL user — no cross-user change.
> - error_page 403 = @pw_@USER@; + return 302 in the named location is the correct idiom (empty = takes the named location's 302; absolute_redirect on absolutizes the relative /@USER@/password/ target).
> - Stale-socket concern already handled: asyncio create_unix_server(path=...) removes a stale socket file before binding, so Restart=always won't crash-loop on restart (only the group needs the subclass re-apply, per Nit 4).
> - auth_basic-vs-auth_request ordering assumption is low-stakes: in both orders an unauthenticated request ends in 401 (not a redirect), and the "fresh browser → 401" CHECK holds either way.
> - File paths in the plan all match the existing layout, and .venv/bin/python exists for the unit's ExecStart.
>
> NET: fix B1 (the colon) and B2 (idempotent patch) before implementing — both are nginx-layer, which the gates couldn't exercise locally. M1 is a one-clause addition to the write-path spec. Rest is tightening.
