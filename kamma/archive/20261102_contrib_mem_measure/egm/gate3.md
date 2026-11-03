# Gate 3 — plan readiness audit (2026-11-02)

Backend: native subagents (`Agent`, general-purpose). One Goldfish. No failed run.

## Raw findings

**Findings, worst first. Task 3.7 and the 3.1 cgroup path are the blockers.**

**Blocker**
1. **The cgroup path in `--unit-readings` is probably wrong (plan.md:62).** It reads `/sys/fs/cgroup/system.slice/<unit>.service/cgroup.procs`. The unit file `scripts/server_contrib/dpd-gui@.service` has no `Slice=`. A template instance therefore lands in `system.slice/system-dpd\x2dgui.slice/dpd-gui@alice.service`. 3.1 would print an error and STOP, and 3.4, 3.5 and 4.2 would have no readings. Fix: resolve the path from `systemctl show -p ControlGroup dpd-gui@alice`, or read `/proc/<pid>/cgroup`. State the path format in 1.1.
2. **`uv run` on the server can modify `~/dpd-db` (plan.md:93, 97, 102, 117).** Plain `uv run` syncs `.venv` first, and alice's unit uses `--no-sync` (service file `ExecStart`). The run could change the environment alice's service uses. It also breaks rule 4 (never edit anything in `~/dpd-db`). Importing gui2 writes `__pycache__` there as well. Fix: use `uv run --no-sync` everywhere and add `PYTHONDONTWRITEBYTECODE=1`.
3. **The `.backup` command uses `~` inside a quoted sqlite dot-command (plan.md:102).** The shell does not expand the `~` in `".backup ~/mem/dpd_copy.db"`. sqlite3 fails with "unable to open", or writes to a literal path. Fix: use `/root/mem/dpd_copy.db`, as the fallback already does. The 2.1 laptop copy is fine because it uses an absolute `<SCRATCH>` path.
4. **Task 3.7 can leave alice stopped, with no recovery (plan.md:115-119).**
   - Any STOP under rule 3 (capped run errors, the 30-minute limit, a probe exception) leaves alice down. Rule 7 allows `start` only when the task says so, and no step covers that case.
   - Hitting the 30-minute limit leaves the probe running. Rule 10 bans `pkill` and `kill -9`, and no stop command is given.
   - Fix: add an explicit "on STOP: ask the maintainer, then `sudo systemctl start dpd-gui@alice`". Name the allowed way to end the probe, which is the PID from the pid file with a plain `kill`. Say whether the 30 minutes applies per run or in total.

**Major**
5. **`$!` does not survive across separate commands (plan.md:117-118).** `echo $! > server_run.pid` is a separate line, and each tool call is a new shell, so the PID file would be empty. `cd … && nohup … &` also backgrounds a subshell. Fix: put the launch and `echo $! > …` in one command line, joined with `;`.
6. **The reruns lose data (plan.md:119).** The log is redirected with `>`, so each rerun overwrites the earlier log. The plan does not say whether `--out` appends, and the pid-and-wait procedure for runs 2 and 3 is only implied. Fix: use `>>`, require the probe to append, and spell out the launch and wait steps for each run.
7. **There is no `error` outcome (plan.md:64, spec.md:81).** The spec allows only `ok`, `capped` and `killed`. The server's lean build may lack `cst_file_freq.json`, or an AI provider may fail. The result is an exception with no row, and 3.7's EXPECT cannot be checked. Fix: add an `error` outcome carrying the exception type and message, with no secrets.
8. **The point semantics are ambiguous in 1.1.**
   - `server_staircase` is "the staircase without books", but the spec's staircase has no books (spec.md:64).
   - A cumulative four-book run needs a point name. `--book` takes one name, and the spec table calls it `book:<name>`.
   - The "CST word list" call is not named.
   - Whether the staircase stops at `ai_manager` when Phase 0.3 finds a network call is not stated.
9. **The 1.1 driver drops spec rules.** The "rerun three more times when spread is over 10 %" rule is missing, and so is the "partial" marking. The run count is also inconsistent. The driver as specified makes about 52 processes (1 + 33 + 12 + 3 + 3), but 2.1 tells the user "about 70" (spec.md:102). The maintainer's yes would rest on a wrong figure. Fix: align the numbers.
10. **`make_tables.py` has no CLI (plan.md:69, 129).** 1.3 says it reads JSONL, but 4.2 also feeds it "server readings of 3.1 and 3.4", which are lines appended to `results.md`. The flags and the markdown-parsing format are unspecified. The `unbuilt remainder` needs the "warm-up done" reading from that file. Fix: write the CLI and the `results.md` line format, for example one JSON line under each heading.
11. **There is no smoke test of the real points before the 52-process run.** The self-test (1.2) uses only a fake component. The `get_db_session` patch and the `query_only` assertion are never exercised before the maintainer starts `--all`. Add a task that runs `--point db_manager` and `--point bare` once under the cap, with the user's yes.
12. **The server run has two untested inputs.** No task checks that the chosen book (3.4 step 4) exists on the lean server, which may lack sc-data. 3.2 and 3.3 do not check that the server has `cst_file_freq.json` and the other probe inputs.
13. **The `git status` calls conflict with the global "never run git" rule (plan.md:71, 80).** Tasks 1.4 and 2.2 tell the local agent to run `git status`. This is a standing-rule conflict, so ask the user. Also, `gui2/data` is probably gitignored, so that check proves nothing.
14. **`--unit-readings` is underspecified (plan.md:62, 94).** The `comm` match (`python` or `python3`) is not given. The EXPECT says "one line per python process", but the interface says "print one JSON line". The 3.1 EXPECT of 1000–1500 MB is also meaningless right after the 3.4 restart.

**Nit**
- The 3.3 free-space EXPECT is a flat 3 GB. The `.backup` of about 2 GB on the shared box has no `ionice` and no rate limit.
- The temp-dir location for `DPD_GUI2_DATA_DIR` is not named. Neither is where the selftest function lives, which is needed for the median and spread logic that both `mem_probe.py` and `make_tables.py` need.
- The laptop guard (`shared_data/`) can fail falsely when other sessions or the "data update" habit write there.
- The 3.4 "wait 15 s" and the 5-minute waits assume the server agent can sleep.
- Restarts in 3.4, 3.5 and 3.7 count toward `StartLimitBurst=5` within 300 s. That is fine if they are spaced out, but nothing says to space them.
- The child command `uv run python <file>` conflicts with the global rule that scripts run as `uv run script.py`.


## Disposition

| ID | Finding | Severity | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| G3-01 | `--unit-readings` cgroup path is wrong for a template instance | Blocker | Accept | checked on the server: `systemctl show -p ControlGroup` returns `/system.slice/system-dpd\x2dgui.slice/dpd-gui@alice.service`; the plan's path does not exist | plan 1.1 |
| G3-02 | Plain `uv run` on the server can sync `.venv` and write `__pycache__` in `~/dpd-db` | Blocker | Accept | unit file line 17 uses `--no-sync` | plan rules 4, tasks 3.x |
| G3-03 | `~` inside a quoted sqlite `.backup` command is not expanded | Blocker | Accept | reasoning (shell does not expand `~` inside quotes) | plan 3.3 |
| G3-04 | Task 3.7 can leave alice stopped and the probe running; no recovery or stop command | Blocker | Accept | rules 7 and 10 read | plan rules 7, 10, 3.7 |
| G3-05 | `$!` does not survive across separate commands | Major | Accept | reasoning (each call is a new shell) | plan 3.7 |
| G3-06 | Reruns overwrite the log and the output file | Major | Accept | reasoning | plan 1.1, 3.7 |
| G3-07 | No `error` outcome: an exception leaves no row | Major | Accept | spec outcomes list read | spec 1; plan 1.1 |
| G3-08 | Point semantics ambiguous: `server_staircase`, cumulative books, the CST word-list call, import-only providers | Major | Accept | spec table read (the staircase has no books) | plan 0.2, 1.1 |
| G3-09 | Driver drops the 10 % rerun and `partial` rules; run count wrong (52, not about 70) | Major | Accept | counted: 1 + 11x3 + 4x3 + 3 + 3 = 52 | spec 2; plan 1.1, 2.1 |
| G3-10 | `make_tables.py` has no CLI and no input format for server readings | Major | Accept | reasoning | plan 1.3, 3.x, 4.2 |
| G3-11 | No smoke test of the real points before the full run | Major | Accept | reasoning | plan 2.2 |
| G3-12 | Server inputs untested (cst_file_freq.json, the chosen book on the lean server) | Major | Accept | reasoning | plan 3.2 |
| G3-13 | `git status` steps conflict with the standing 'never run git' rule; `gui2/data` is probably ignored | Major | Accept | global rule read | plan 1.4, 2.3 |
| G3-14 | `--unit-readings` underspecified (comm match, output shape); the 3.1 range check is meaningless | Major | Accept | reasoning | plan 1.1, 3.1 |
| G3-15 | Backup copy has no I/O limit; free-space check is thin | Nit | Accept | reasoning | plan 3.3 |
| G3-16 | Temp dir location and the shared stats helpers are unnamed | Nit | Accept | reasoning | plan 1.1 (`mem_stats.py`) |
| G3-17 | Laptop guard can fail falsely on `shared_data/` writes by other sessions | Nit | Accept | reasoning | plan 1.1 |
| G3-18 | Waits assume the server agent can sleep | Nit | Accept | reasoning; `sleep` is allowed, loops are bounded | plan rule 11 |
| G3-19 | Restarts count toward StartLimitBurst=5 in 300 s | Nit | Accept | unit file lines 8-9 read | plan rule 13 |
| G3-20 | Child command uses `uv run python <file>`; the standing form is `uv run <file>` | Nit | Accept | global rule read | plan 1.1 |

Counts (from the table): 20 raw findings: Blocker 4, Major 10, Nit 6. Accepted 20, rejected 0, escalated 0.
