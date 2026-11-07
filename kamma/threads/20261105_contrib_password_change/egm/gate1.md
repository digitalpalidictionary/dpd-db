# EGM Gate 1 — idea stress-test (2026-11-07)

Backend: owner-named external CLI `pi -p --provider deepseek --model
deepseek-flash --no-session --tools read` (native DeepSeek API, verified
baseURL https://api.deepseek.com). Smoke probe passed (read tool used,
first line returned). Six reviewers, one per lens, all returned within
time cap. The native `reviewer` subagent was smoke-probed first but then
superseded by the owner's named backend; no Goldfish ran on it. Raw
output: `raw/{contrarian,cost,ux,migration,observability,debt}.md`.
Prompts: `prompts/`. No fallbacks, no caps hit.

## Deduplicated findings and dispositions

48 raw findings deduplicated to 21. Facts were re-checked against source
before Accept (files read: `add_contributor.sh`, `dpd-gui@.service`,
`server_setup.sh`, nginx templates, `maintenance_window.py`,
`tests/scripts/server_contrib/test_add_contributor.py`, `pyproject.toml`,
runbook).

| # | Finding (lenses) | Sev | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| 1 | Temp+`os.replace` yields 600/644 root:root; nginx group lost → user's URL 500s forever while page said success (contrarian, cost, ux, migration, observability, debt) | Blocker | Accept | add_contributor.sh umask 077 + chmod 640 + nginx-group chgrp read; runbook Step 7a CHECK asserts 640 root:www-data | Spec constraint: copy st_mode/st_gid from existing file, fchmod/fchown before replace, stat+verify after, restore .bak on failure; tested |
| 2 | Root service + username from form = unauthenticated oracle + any-user rewrite; path traversal into replace target (contrarian, cost, ux, migration) | Blocker | Accept + Escalate Q1 | add_contributor.sh regex is shell-only; no other validator exists | Fork decision Q1; either way: username derived from nginx-authenticated header or validated by same regex + file-must-exist |
| 3 | Re-verifying the current password in-app is redundant behind auth_basic, and is the oracle without it (contrarian) | Major | Accept | nginx auth_basic validates every proxied request | Folded into Q1 options |
| 4 | bcrypt cost drift: script writes cost 5 (no -C), python default 12 = 128× per-request bcrypt for nginx (cost, debt) | Major | Accept | add_contributor.sh:84 `htpasswd -B -c` no -C; nginx verifies per request | Spec constraint: pin `-C 5` to match today's baseline |
| 5 | No deployment path: unit not installed by anything tracked; nightly pull only git-pulls; rebuilt server loses the feature; hand-edited site file is the /status trap (migration, debt, observability) | Blocker | Accept | server_setup.sh installs exactly one unit; maintenance_window.py rollback covers db/HEAD/data only | Plan: unit + nginx template in repo, server_setup.sh step, runbook step with CHECKs, deploy = nginx -t + reload |
| 6 | No supervision/health/memory cap for the new resident process (observability, cost, debt) | Blocker | Accept | dpd-gui@.service precedent has Restart/RestartSec; box memory already cut twice | Unit: Restart=always, MemoryMax≈128M, /health route, runbook CHECK |
| 7 | `htpasswd -vb file user password` puts plaintext in argv — runbook forbids it twice (ux, observability, debt) | Major | Accept | runbook rule 1 + Step 11; add_contributor.sh already uses -i when piped | Spec constraint: passwords only via stdin (-i); confirm -v -i combo at implementation; fork 1 needs no current-password verify at all |
| 8 | Live Flet websocket survives the change (auth at handshake, 3600s timeout) — old credential keeps editing (ux, debt) | Major | Accept + Escalate Q2 | nginx_contrib_user.conf.template proxy_read_timeout 3600s, auth on upgrade only | Documented caveat + owner decision on auto-restart |
| 9 | Browser replays cached basic-auth; next request 401s and pre-filled prompt loops; user reads it as broken (contrarian, ux) | Major | Accept | basic-auth semantics; no repo dependency | Success-page copy: close DPD tabs, expect one fresh login prompt |
| 10 | Contributor has no way to learn the page exists; nothing in gui2 or the §12e handout mentions passwords (ux, migration) | Blocker | Accept | contributor_tabs.py read-only surface; runbook §12e text | Folded into Q1 (path choice) + runbook §12e update |
| 11 | Forgotten password has no path at all: add_contributor.sh refuses existing users; maintainer improvises htpasswd by hand (and drops the chgrp fix); owner's stored ~/dpd_pw_<user> files go stale (contrarian, migration, ux, debt) | Major | Accept | add_contributor.sh existence refusal; runbook Step 7a/11a password files | New maintainer-run set_password.sh (reuses chgrp logic) + runbook reset step + stale-file scoping note |
| 12 | Username 'password' collides with a shared /password/ location; 'status' already collides with /status (latent) (ux, debt) | Major | Accept | add_contributor.sh forbids only 'added' | Reserved-name list in add_contributor.sh + test, regardless of fork |
| 13 | Untestable as hypothesised; the only credential-touching code would ship with zero tests (debt) | Major | Accept | tests/scripts/server_contrib/ exists, --root + skipif precedent | Architecture: plain module with injectable dir, thin FastAPI layer, mirror tests asserting mode/gid preservation |
| 14 | No audit trail: brute-force and disputed changes untraceable; source IP not forwarded so all logs read 127.0.0.1 (observability) | Major | Accept (reduced) | contrib_pull/maintenance logging precedents read | journald per-attempt line (user, ip, outcome — never the password); X-Real-IP/X-Forwarded-For in the location; runbook triage matrix |
| 15 | Separate /var/log/dpd/password.log file + own status file (observability) | Nit | Reject | journald already is the box's per-unit log surface; /var/log journal persists on Ubuntu 24.04 | — |
| 16 | Startup shape: `uv run` adds ~40 MB; any db/gui2/tools import drags SQLAlchemy/Flet into a 2 KB job; sync subprocess in async handler serializes (cost) | Major | Accept | ExecStart precedent in dpd-gui@.service | ExecStart .venv python -m uvicorn directly; imports stdlib+fastapi only; subprocess via asyncio.to_thread |
| 17 | Fixed port unreserved; add_contributor.sh guards only FLET_SERVER_PORT (migration) | Nit | Accept | port check code read | Fixed port 8500 (below 8551+ range), documented in runbook + script comment |
| 18 | Nothing reusable exists to adopt as-is (passlib htpasswd stale since 2020, fastapi-users own DB, SSO family replaces basic auth wholesale) (contrarian) | Nit | Accept | web research in brief.md confirms | Research note in spec; minimal-code route confirmed |
| 19 | Build nothing — maintainer script is the whole requirement (contrarian) | Blocker | Reject | owner already decided in the 20261030 triage (item 15) that contributors change their own password; the sub-points survive as #11 | Offered back to owner as Q1 option 3 (overrule path) |
| 20 | Use jinja2 for the page (debt) | Nit | Accept-modified | jinja2 is a dep (pyproject.toml:11) | Mechanical: plain HTML string constant; a two-field form needs no template engine |
| 21 | Memory premise unverifiable; record headroom before sizing (cost) | Nit | Accept | no source states current headroom | Deploy CHECK records free -m and MemoryCurrent once |

## Escalations for the owner (decision gates, one question each)

- **Q1 — architecture fork** (from #2, #3, #10, #19): per-user authed path vs
  shared unauthenticated page vs no page at all.
  **RESOLVED (owner, 2026-11-07):** fork A — `/<user>/password/` behind each
  user's own basic-auth realm. Maintainer issues an easy initial password;
  contributor changes it after first login. Implication: findings #2, #3, #10
  resolve to "username from the nginx-authenticated header; no current-password
  form field; discovery via the first-login dialog"; #12 is moot (no shared
  /password path; `location = /status` exact match already wins over a
  hypothetical /status/ prefix). #19's reset script is still taken (see #11).
- **Q2 — session invalidation** (from #8): restart the contributor's gui2
  instance after a successful change, or only document the 3600s caveat.
  **RESOLVED (owner, 2026-11-07):** no restart — document only ("they're just
  going to have the one page open; don't over-engineer").
- **Owner-directed addition (2026-11-07):** on first login while the initial
  password is still in force, gui2 opens a modal ("second screen") asking the
  contributor to change their password, linking to the change page. Driven by
  a marker file the issuance/reset scripts write and the change service
  deletes. This is the enforcement level chosen between banner, text-only and
  hard auth_request enforcement.

## Rejected findings (owner may overrule)

- #15 separate log/status files — journald already covers it.
- #19 build-nothing — contradicts the owner's recorded triage decision;
  surfaced again honestly as Q1 option 3.
