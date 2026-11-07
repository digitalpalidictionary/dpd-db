# EGM Gate 3 — implementation-readiness audit (2026-11-07)

Backend: same as Gates 1–2 — `pi`/deepseek-flash, one fresh Goldfish,
read the plan, the spec, and the referenced repo files. Returned within
the cap; no fallback. Raw output: `raw/gate3.md`; prompt:
`prompts/gate3.txt`.

13 findings: 2 Blockers, 7 Majors, 4 Nits. All dispositions below; every
Accept was fixed in `plan.md` (and two in `spec.md`) before this file
was written.

| # | Finding | Sev | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| 1 | `/check` decision has no home/signature; Phase 1 tests unwritable as planned | Blocker | Accept | plan tasks contradicted each other | Spec + plan: `identify_user()` + `check_gated()` in core, service maps to 200/403; matrix moved to those functions |
| 2 | Startup-hook chmod races uvicorn's bind; service may never come up | Blocker | Accept | uvicorn binds around lifespan startup — timing is real | Spec + plan: `uvicorn.Server` subclass chmods AFTER `startup()` bind; ExecStart runs the module |
| 3 | new==repeat and length validation layer unpinned | Major | Accept | no seam named | Plan Architecture Decisions: service validates repeat + length (form re-render), core enforces length too |
| 4 | No failure→status map (400 vs 200-page vs 500) | Major | Accept | statuses were implicit | Plan: full map in Architecture Decisions |
| 5 | Failure-injection tests need named seams | Major | Accept | monkeypatching subprocess.run breaks the write step | Plan: `_run_htpasswd()` and `_replace()` module seams |
| 6 | Unit template incomplete (no `[Unit]`/`[Install]`) though `enable --now` is run | Major | Accept | dpd-gui@.service precedent | Spec: complete unit block; plan task references it |
| 7 | server_setup.sh insertion point + skip guard unspecified | Major | Accept | every step there has an explicit test | Plan: position (after systemd-unit step, before clean-tree gate) + guard named |
| 8 | Phase 5 deploy task unclosable by its executor (workflow closes on local verification) | Major | Accept | executor split was blurred | Plan: three tasks — local gates, agent handoff note, owner-run item that stays open but blocks nothing |
| 9 | Workflow duties absent: `[~]` marking, phase-end steps, tech.md-before-implementation, report-only commits | Major | Accept | kamma/workflow.md + AGENTS.md | Plan: executor-rules paragraph + tech.md task first in Phase 1 |
| 10 | No htpasswd-dir override for local dev | Nit | Accept | only the socket was overridable | Spec + plan: `DPD_HTPASSWD_DIR` |
| 11 | Template hardcodes the socket path | Nit | Reject (keep) | production nginx config must pin the real path; local smoke bypasses nginx | Noted in plan: template exercised only via `nginx -t` on the server |
| 12 | "Run twice to prove no /etc leakage" not actionable | Nit | Accept | vague check | Plan: `rg -n "/etc" <test file>` → zero hits instead |
| 13 | "404-style page" ambiguous; outcome vocabulary and /health body undefined | Nit | Accept | underspecified | Plan: unknown user → 200 error page; outcome ∈ {ok, rejected:<reason>}; /health body `ok` |

## Escalations

None — every gap had one defensible answer, recorded above.

## Verdict

After the fixes: no Blockers or Majors remain open against the plan;
Nits 11 (rejected, reasoned) and the rest folded. The plan is
self-contained for a zero-context implementer.
