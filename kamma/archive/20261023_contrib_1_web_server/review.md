## Thread
- **ID:** 20261023_contrib_1_web_server
- **Objective:** Contributor web server (one gui2 instance per contributor), plus the daily pull of their files to the maintainer's laptop and a runbook for a new server. Issue #215.

## Files Changed (this review covers Phases 4 to 7 and the loop proof; Phases 1 to 3 were reviewed earlier)
- `scripts/server_contrib/contrib_pull.py` (new) — the daily pull: list, check, copy, reconcile, merge, status.
- `scripts/server_contrib/merge_contrib_files.py` — log written atomically; shared files written atomically; a save check for the tests file.
- `scripts/server_contrib/dpd-contrib-pull.service`, `.timer` (new), `justfile` — systemd user timer and the two recipes.
- `scripts/server_contrib/NEW_SERVER_RUNBOOK.md` (new), `scripts/server_contrib/README.md`, `kamma/tech.md` — docs.
- `tests/scripts/server_contrib/test_contrib_pull.py` (new), `test_merge_contrib_files.py` — tests.
- Spec, plan, handoff, `pull_spec.md`, `egm_pull/`, the problem children spec and plan — thread records.
- Data written by the real pull: `shared_data/deconstructor/checked.csv`, `manual_corrections.tsv`.

## Findings
Four reviewers, run in parallel, no edits while they ran: an independent agent with no memory of the work, CodeRabbit (scripts pass: 4 findings; tests pass: a 503 from CodeRabbit, then 0 findings on the one retry), pi DeepSeek `deepseek-v4-pro` at max reasoning (7 findings). An earlier round (CodeRabbit 6, DeepSeek 11) is recorded in `plan.md` under 8.6. Every finding was checked against the code or the live server first.

| # | Severity | Location | What | Decision |
|---|----------|----------|------|----------|
| 1 | major | `contrib_pull.py` `_check_lines` | `manual_corrections` had no column check; a 3-column line stops the Go build (verified in `tsv.go`) | FIXED, 3 reviewers agreed |
| 2 | major | `contrib_pull.py` `_check_json` | a huge or odd `id` string made reconcile raise and stopped the run for everyone (verified: `int("9"*5000)`, `int("²")`) | FIXED, test: one bad contributor, others arrive |
| 3 | major | `merge_contrib_files.py` | failed save of the tests file looked like success and the line was logged as handled | FIXED: read back after save, raise if missing |
| 4 | minor | `merge_contrib_files.py` | shared files rewritten in place; a kill truncates them | FIXED: temp file and rename, mode kept |
| 5 | minor | `contrib_pull.py` `run` | failure text with extra lines could fake `last_success` and suppress a day | FIXED: one line, 300 characters |
| 6 | minor | `contrib_pull.py` | `ControlPath` in the owner's ssh config could bypass the restricted key; listing walked the whole tree | FIXED: `ControlPath=none`, `ClearAllForwardings=yes`, no `-r` |
| 7 | minor | `contrib_pull.py` | empty server folder reported plain `pulled`; one-column files accepted a tab | FIXED |
| 8 | minor | tests | tests that stayed green on revert (secret redaction in a remote run, ssh options picked, `main`, dry run vs today's gate, first `last_success` wins) | FIXED, tests added |
| 9 | minor | unit, justfile, docs | no start timeout on the unit; no `uv` guard; spec and tech notes disagreed with the code | FIXED |
| 10 | major | runbook | Steps 10 and 11c contradicted Step 12c; old server must be a root login; wrong `grep -c` count; host-key prompt under BatchMode; "four files" unnamed; wait arithmetic; long `apt` commands | FIXED, execution order stated |
| 11 | rejected | DeepSeek m3 (earlier round) | non-UTF-8 names crash the run | wrong: rsync escapes them; test added |
| 12 | nit, skipped | imports of two private helpers; `user_of` double call; unsorted test imports | noted as problem 26 |

## Fixes Applied
All of the above. Revert checks (fix removed, count of failing tests): manual_corrections columns 4, entry id 8, listing without `-r` 1, `ControlPath` 1, one-line outcome 1, empty folder 1, tab check 2, tests-file save check 1, atomic user dictionary 1, file mode 1. Files restored after each (compared with `cmp`).

## Test Evidence
- `uv run pytest tests/scripts/server_contrib -q` (scope: the whole contributor-server test folder, 209 tests) → 209 passed.
- `uv run pytest tests/ -q` (scope: whole suite, run before these fixes) → 2840 passed, 1 failed: `test_maintenance_window.py::...failure_and_its_reason`; not reproduced in 5 reruns; not touched by this thread; recorded as problem 27.
- `uv run ruff check`, `ruff format`, `pyright` on the four Python files, `pyright --project /dev/null` on both test files → clean.
- `just typecheck` (whole repo) → 0 errors.
- Live: first real pull, a second real pull with a new word, the full loop through a manual nightly window (rebuilt, problems 0, new word in the server db, alice's files empty), the timer ran 15 times today (08:00 to 15:00), each `skipped: already done today`, exit clean.

## Not Verified
- The timer doing a real pull unattended: today every run skipped. The first one is 2026-11-05 08:00 (task 8.5).
- The runbook on a fresh machine. Steps marked UNTESTED were not run: swap, web packages, unattended-upgrades, the first certificate, the deploy key and its GitHub write access.
- The tests-file save check was proved with a stub; a real disk failure was not made.
- `just typecheck` after the very last doc edits was not rerun (no Python changed after the last run).
- One full-suite failure (problem 27) is unexplained.
- Onboarding of a real contributor (8.4, now the owner's video) and the notice popup at 22:30 on a real failure.
- The two rejected-by-scope items: gui2 Delete versus Reject (problem 12), shared preview folder (19).

## Verdict
PASSED
- Scope: the code, tests and docs of Phases 4 to 7. Finalize should wait for task 8.5 (the first unattended pull, 2026-11-05) and 8.4, because the plan still has them open.
- Review date: 2026-11-04
- Reviewer: Claude Sonnet 5.5 (implementer), independent Claude subagent, CodeRabbit CLI 0.9.2, pi DeepSeek `deepseek-v4-pro`
