## Findings

**BLOCKER 1 — `/check` has no specified home or signature.** Plan Phase 1's core surface is `needs_change(user)`/`clear_marker(user)` only, yet Phase 1's tests demand a "`/check` decision matrix (no header → open, unknown user → open, marker → gated)", and Phase 2 says `/check` uses "the decision function from core" while the user is obtained "from decoded Authorization header" in the service. Nothing defines who parses the header, the function name, or whether it returns `bool` or an HTTP status. Implementer must invent an interface and the tests cannot be written as written. Fix: specify `identify_user(header: str | None) -> str | None` and `check_status(header) -> int` in `password_change.py` with exact return semantics, or move the matrix to the service and delete it from Phase 1.

**BLOCKER 2 — socket chmod ordering unverified against uvicorn.** Phase 2 chmods/chgrps the socket in a "startup hook", but uvicorn binds the `--uds` socket around lifespan startup; if the path is absent at that moment the hook raises and the service never comes up. The plan names no retry, pre-bind, or thread strategy. Fix: pin the mechanism (e.g. poll for the path up to N s, or chmod in `main()` before `uvicorn.run`).

**MAJOR 3 — the new==repeat check has no seam.** Spec requires "new == repeat"; `change_password(user, new_password)` takes one password, while Phase 1 tests length bounds in the core. Invented choice: extra parameter, or service-side check. Fix: state which layer validates repeat and length and what it returns.

**MAJOR 4 — no failure→status map.** For bad length, bad username, unknown user, wrong repeat, CSRF reject, `ChangeError`, only "500" and the CSRF page are pinned. `ChangeError` reason strings and status codes (400 vs 200-with-error-page) are invented. Fix: a reason→status table.

**MAJOR 5 — the failure-injection tests need seams the plan did not name.** "wrong-verify never replaces" and "`.bak` … restore on an induced replace failure" cannot be written without a patchable point; monkeypatching `subprocess.run` also breaks the write step. Fix: name module-level `_run_htpasswd()` / `_replace()` helpers.

**MAJOR 6 — the unit template is not a complete unit.** Spec's block starts at `[Service]` and has no `[Install]`, but Phase 4's step runs `systemctl enable --now`; compare `scripts/server_contrib/dpd-gui@.service:6-8` and `:24-25`. Fix: put a full `[Unit]`/`[Service]`/`[Install]` block in the spec.

**MAJOR 7 — server_setup.sh insertion point and skip marker unspecified.** Plan says only "step-skipping style"; every step in `scripts/server_contrib/server_setup.sh:36-140` has an explicit test. Fix: name the guard (e.g. `/etc/systemd/system/dpd-password.service` exists) and its position relative to "clean tree gate" (`server_setup.sh:122`).

**MAJOR 8 — Phase 5's deploy task is unclosable by its executor.** Executor rules and Phase 5 both assign the deploy to the OWNER, but the verify line is "every 7e CHECK passes on the live server"; `kamma/workflow.md:15-37` closes a task only after local verification. Fix: split into the agent's runbook-checklist task plus an owner-confirmed item.

**MAJOR 9 — workflow duties absent.** No `[ ]`→`[~]` marking, no phase-end run-tests/manual-verify/await-confirmation step (`kamma/workflow.md:65-79`), and no `kamma/tech.md` update though `workflow.md:7` requires tech.md *before* implementation — tech.md already documents contributor-server facts. The plan must also state that `workflow.md:9-10`'s commit steps and the checkpoint commit are report-only (AGENTS.md forbids unasked commits).

**NIT 10** — no htpasswd-dir override; only `DPD_PASSWORD_SOCK` is overridable, so local dev cannot exercise GET/POST without writing `/etc/nginx/dpd`.
**NIT 11** — `location /@USER@/password/` hardcodes `/run/dpd-password.sock` while the socket is overridable; the template check can't be exercised locally.
**NIT 12** — Phase 1's "run twice to prove no `/etc` leakage … read-only-clean `--root`-style tmp dir" is not an actionable check.
**NIT 13** — "404-style page" is ambiguous (real 404 vs 200), and log "outcome" vocabulary plus `/health` body are undefined.
