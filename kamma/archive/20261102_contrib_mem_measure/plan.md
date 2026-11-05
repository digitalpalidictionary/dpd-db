# Plan: measure where a contributor gui2 instance spends its memory

> **CLOSED 2026-11-02.** Measurement complete; most of its options were
> implemented by the two threads that followed:
>
> - **D (wordfinder, est. 172.1 MB)** — implemented in `267740fc` (the
>   Pass2Add gate); measured −170.0 MB laptop, −169.2 MB server warm.
> - **Slim contributor corpus + compact inflection sets** (L1/L7b/L8, taken
>   up from this measurement instead of option C's lookup-query form) —
>   implemented in `247a8429`; −222.6 MB warm, −439.3 MB after a book.
> - **B (lazy managers, est. 223.1 MB)** — only its wordfinder part is done
>   (that is D): ai_manager, bold_search and the relationship detector
>   still build for every role in the warm-up.
> - **Deferred: E** (one process for all users; 8 users ≈ 12.9 GB → ≈ 3.5 GB)
>   **and F** (concurrency limit) — plus B's manager part and C's original
>   lookup-query form. Revisit when the contributor count demands it.
>
> Task 4.5: the folder was already committed to git (tracked as of closure).
> All figures this thread produced are preserved in this archived folder.

**Thread:** 20261102_contrib_mem_measure · **Spec:** `spec.md` in this folder (read it first)
**GitHub issue:** #215 · never write to the issue · commits reference `#215`
**Scope:** measurement only. No change to `gui2/` or `tools/`. Everything this thread writes lives in this folder.

## Architecture Decisions

- **Three small files in `artifacts/`.** `mem_probe.py` holds the points, the driver, the guards, the server readings and a self-test. `make_tables.py` turns the output into the tables. `mem_stats.py` holds the median and spread helpers both use (same folder, so a plain import works). Numbers in `results.md` come from `make_tables.py`, never from hand-typing.
- **A fresh process per measurement.** The driver starts each child in its own cgroup scope with a memory cap. The child writes one JSON line and exits. A watchdog inside the child covers the case where the cgroup would kill it silently.
- **The staircase and the isolated runs are both kept** (Gate 1): isolated runs give each component's own cost, the staircase gives the real order, and the gap between them is a named row.
- **No import of private gui2 state beyond what the real app imports.** The probe builds components, never `ToolKit` or `App`. It copies the database-patch idea from `kamma/archive/20260710_gui2_perf_and_testing/benchmarks/bench_common.py` instead of importing it.
- **Server numbers are the headline** (the lean build differs from the laptop's db). Laptop numbers give the split.
- **Commands run with `PYTHONPATH=.`** from the repo root, so the probe needs no `sys.path` code. On the server every python command also sets `PYTHONDONTWRITEBYTECODE=1` and uses `uv run --no-sync`, as alice's unit does, so nothing in `~/dpd-db` changes.
- **No `git` command in any task.** The standing rule is never to run git unasked. Checks use `ls`, `find` and the probe's own guard.

## Who does each step

Each task says **WHO**:
- `LOCAL AGENT` — an agent in the maintainer's repo on his laptop (`/home/bodhirasa/MyFiles/3_Active/dpd-db`). Never commits or pushes. Does not run the heavy probe: the user does.
- `MAINTAINER` — the human owner. Runs the laptop probe, uses the browser, copies files to and from the server, commits.
- `SERVER AGENT` — a model on the server (`ssh epitaka`, root). Follows the rules below.

## Where each task runs (summary; reasons in `spec.md`, "Where each measurement runs")

| Phase | Tasks | Machine |
|---|---|---|
| 0 Look-ups | 0.1–0.5 | Laptop |
| 1 Write and test the probe | 1.1–1.4 | Laptop |
| 2 Laptop run | 2.1–2.5: database copy, smoke test, 52-run battery, tables | Laptop |
| 3 Server readings | 3.0 copy the probe over (from the laptop); 3.1–3.8 | Server (3.0 and 3.6 are the maintainer's, 3.4 and 3.5 need his browser) |
| 4 Results | 4.1 copy files back (from the laptop); 4.2–4.5 | Laptop |

Must run on the laptop: Phases 0, 1, 2 and 4. Must run on the server: Phase 3, because
only the server has alice's live instance, the lean database and the nginx path.
Phases 2 and 3 do not depend on each other, so the maintainer may do Phase 3 first or
split them across days. Phase 4 needs both.

## READ THIS FIRST — rules for the SERVER AGENT

You run on the server. Follow these rules exactly. If a rule and a task seem to disagree, STOP and ask.

1. Do the tasks in order, one at a time. Do only `SERVER AGENT` steps. For a `MAINTAINER` step, show him the command, then wait until he says it is done.
2. Copy each command exactly. Do not change, shorten or improve it.
3. After each task run its **CHECK** and compare with **EXPECT**. On a mismatch or an error: STOP, write the command and its full output in `~/mem/results.md`, tell the maintainer, and do not try a fix.
4. Append results ONLY to `~/mem/results.md`. Probe output goes only to `~/mem/`. Never edit `spec.md` or `plan.md`, and never edit any file inside `~/dpd-db`. Every python command in `~/dpd-db` uses `PYTHONDONTWRITEBYTECODE=1` and `uv run --no-sync`.
5. Never print, open, read, grep or edit `config.ini`, any `.env` file, any htpasswd file, any private key, or `/proc/<pid>/environ`.
6. No git command at all in `~/dpd-db`.
7. `systemctl restart`, `stop` or `start` of `dpd-gui@alice`, and the capped probe run, only when the task says so and the maintainer has said yes to that task. If a STOP happens while alice's unit is stopped, tell the maintainer and, with his yes, run `sudo systemctl start dpd-gui@alice` before anything else.
8. The only scripts you may run are the commands in the tasks and `~/mem/mem_probe.py` as the tasks give it.
9. Never touch `~/epitaka-translator`, its files or processes.
10. Never use `pkill`, `killall` or `kill -9`. The only allowed way to end the probe is a plain `kill "$(cat ~/mem/server_run.pid)"`.
11. Long commands run in the background with a pid file. Check it every 5 minutes with the CHECK the task gives (`sleep 300` between checks is allowed). Every wait has a limit. Never loop forever.
12. Ask the maintainer one question at a time.
13. Space unit restarts at least 60 s apart. The unit allows 5 starts in 300 s and then stays failed.

---

## Phase 0 — Look-ups (read-only) — WHO: LOCAL AGENT

- [x] 0.1 **Prior art and import side effects.** Read `kamma/archive/20260710_gui2_perf_and_testing/benchmarks/bench_memory.py` and `bench_common.py` (the `force_throwaway_db_globally` list and `rss_mb`). Read the module-level code of `gui2/main.py` and of the modules it imports at top level, for anything that runs at import (a started thread, a written file, a network call, a server start). Check how a script outside the repo finds `gui2` (`pyproject.toml` packages or editable install). Write `artifacts/notes.md` with: the `get_db_session` import sites (`rg -n "get_db_session" gui2 tools db --type py`), the import-time side effects (or "none"), and whether `PYTHONPATH=.` is needed.
      → verify: `artifacts/notes.md` exists with those three headings; every line cites `file:line`.
- [x] 0.2 **Books.** List the books Pass1Auto can open (`gui2/books.py` `sutta_central_books`, and how `Pass1AutoController` sets `cst_books` for each choice, then `make_cst_text_list` in `tools/cst_sc_text_sets.py`) with their on-disk size: `du -sb` on each book's SuttaCentral folder plus its CST files (`resources/sc-data/sc_bilara_data`, `resources/dpd_submodules/cst/romn_txt`). Pick the four largest. For the server step pick one of the four that is a Pass1Auto choice. Write `artifacts/books.md`: a table of book, SC bytes, CST books used, CST bytes, total; the four chosen; the one for the server; and the exact files the server needs for it.
      → verify: one row per book in `sutta_central_books`; the four chosen have the four largest totals; the CST books column is filled from the code, not guessed.
- [x] 0.3 **AI providers.** Read the constructors of `tools/ai_claude_manager.py`, `tools/ai_gpt_manager.py`, `tools/ai_openai_compat.py`, `tools/ai_gemini_manager.py`. For each, write in `artifacts/notes.md` whether `__init__` makes a network call, starts a subprocess, or reads a key, with `file:line`. Do not open `config.ini`. Any provider that does one of the first two goes into a `IMPORT_ONLY` list in the notes; the probe imports it but does not construct it, in every run including the staircase.
      → verify: `artifacts/notes.md` has one line per provider with `file:line`, and an `IMPORT_ONLY` line (possibly empty).
- [x] 0.4 **Cap tool on the laptop.** Run `systemd-run --user --scope -q -p MemoryMax=100M -p MemorySwapMax=0 true; echo "exit=$?"` and `df -h /tmp | tail -1`. Record both in `artifacts/notes.md`. The database copy needs about 2.2 GB free.
      → verify: `exit=0`; free space on `/tmp` above 5 GB. If not: stop and tell the maintainer.
- [x] 0.5 **Phase check.** Re-read `spec.md` section 1. List, in `artifacts/notes.md`, any point in the spec table that Phase 0 shows cannot be built alone (an import side effect, a constructor that needs a page). If none, write "none".
      → verify: the line exists; if a point is listed, the spec is updated at once (DRIFT rule).

## Phase 1 — Write and test the probe — WHO: LOCAL AGENT

Run every command from `/home/bodhirasa/MyFiles/3_Active/dpd-db`. Other sessions share this tree: touch only files in `kamma/threads/20261102_contrib_mem_measure/`.

- [x] 1.1 **Write `artifacts/mem_probe.py` and `artifacts/mem_stats.py`.** Type hints, `Path` not `os.path`, `ic` not `print` for debugging, no `sys.path` code. Top-level imports of `mem_probe.py` are stdlib and psutil only; every gui2 import happens inside a point function. Interface (do not invent others):
      - `--point <name> [--book <name>] [--books <a,b,c,d>] [--db <path>] --out <jsonl>`: run one point in this process (the child). Names: `bare`, `imports`, `db_manager`, `initialize_db`, `corpus`, `inflections_lists`, `relationship_detector`, `wordfinder`, `ai_manager`, `bold_search`, `spellchecker`, `book` (needs `--book`: that book's `segment_dict`, `word_dict`, and `make_cst_text_list(<its cst books from books.md>, dedupe=True)`), `books_cumulative` (needs `--books`, largest first, one reading after each), `staircase` (the spec's order; no books). Providers listed `IMPORT_ONLY` in `notes.md` are imported, not constructed, in every point.
      - `--all --db <path> --out <jsonl> --books <a,b,c,d>`: the driver. One at a time: a throwaway `bare` run, then 3 runs of each of the 11 isolated points (`bare`, `imports`, `db_manager`, `initialize_db`, `corpus`, `inflections_lists`, `relationship_detector`, `wordfinder`, `ai_manager`, `bold_search`, `spellchecker`), 3 runs of each of the 4 books, 3 of `books_cumulative`, 3 of `staircase`: 52 processes. A point whose spread (max − min) exceeds 10 % of its median is run 3 more times (once per point). A point with one capped run among three is marked `partial`. The driver stops on the first `capped`, `killed` or `error` row, and after 40 minutes in total. Each child is `systemd-run --user --scope -q -p MemoryMax=1500M -p MemorySwapMax=0 -- env MALLOC_ARENA_MAX=2 PYTHONPATH=. uv run <this file> --point ...`.
      - `--unit-readings <unit> --label <text>`: print one JSON object per line, one per python process of the unit, with `label`, `pid`, VmRSS, VmHWM, VmSwap, Threads, `smaps_rollup` Rss, Pss and Private totals, and elapsed seconds. Resolve the cgroup path with `systemctl show -p ControlGroup --value <unit>`, then read `/sys/fs/cgroup<that path>/cgroup.procs`. (On this server it is `/system.slice/system-dpd\x2dgui.slice/dpd-gui@alice.service`, not `/system.slice/<unit>.service`.) Match a process when its `/proc/<pid>/comm` starts with `python`. Read only `status`, `smaps_rollup`, `comm` and `stat`. Never `environ`. An unknown unit prints one `{"error": ...}` line, no traceback.
      - `--selftest`: runs the checks in task 1.2 and prints `SELFTEST_OK` or `SELFTEST_FAIL: <check>`.
      The child first sets the env (`DPD_GUI2_ROLE=contributor-server`, `DPD_GUI2_USERNAME=memprobe`, `DPD_GUI2_DATA_DIR=<tempfile.mkdtemp(prefix="memprobe_")>`), then imports, then replaces `get_db_session` in every module of `sys.modules` where it is the original function (before any engine is built), then asserts `PRAGMA query_only` is 1 on the session the loaders use. Output row, appended to `--out` (append mode): `run_id`, `point`, `outcome` (`ok`, `capped`, `killed` (written by the driver when no row arrives), or `error` with exception type and message, never a secret), `readings` (a list of `{label, rss_mb, pss_mb, uss_mb, hwm_mb, swap_mb, threads}`, labels as in the spec), `rss_after_gc_mb`, `rss_after_trim_mb`, `meta` (commit, Python version, db size, env gates set, providers built, `agy` found, `MALLOC_ARENA_MAX`, load average, deconstructor cache `hit` or `miss`). Watchdog: a thread polls RSS every 0.1 s; at 1400 MB it writes the row with `outcome=capped` and the last reading, then `os._exit(3)`. Guard: record modification times of `gui2/data/`, `gui2/storage/`, the temp dir and `shared_data/` before and after. A change in the first three fails the run; a change in `shared_data/` is recorded as a warning with the file names (other sessions write there). Add `--watchdog-mb` (default 1400) and `--guard-dirs` only so the self-test can use a small cap and a temp dir. Delta formula and prerequisites follow the spec table exactly. Everything the spec forbids stays forbidden.
      DRIFT 2026-11-02 (built differently from the text above; the behaviour in `spec.md` is unchanged):
      - The driver starts each child with `sys.executable` (the venv python that `uv run` already set up), not a second `uv run`. This avoids a venv sync per child.
      - The self-test needs a fake component, so the probe has three test-only flags: `--fake-mb`, `--fake-raise`, `--selftest-cap` (default 150).
      - `--db` is required for the points that read the database; the probe never falls back to the live `dpd.db`. The probe also checks `PRAGMA database_list` names the copy.
      - The throwaway warm-up run is a `bare` run, as written. It does not warm the database file cache. The first run of each database point may be slower, not larger.
      - The warm-up row is not written to the output file. Rows for books carry a `book` field; the child's `book:<name>` label is the reading to use.
      - `mem_probe.py` is about 700 lines after `ruff format`; the limit above is raised to 720.
      → verify: `uv run ruff check --fix` and `uv run ruff format` on both files, then `uv run pyright <file>` (if pyright excludes the path, `uv run pyright --project /dev/null <file>`) print no errors. `mem_probe.py` is under 720 lines (DRIFT 2026-11-02: 600 was a guess; ruff format wraps it to about 700).
- [x] 1.2 **Self-test.** `--selftest` checks, with a fake component and `--watchdog-mb 150`: (a) a 60 MB step has a delta of 60 MB ±15 MB; (b) a 300 MB step prints a `capped` row with a last reading and exits 3; (c) a fake component that raises writes an `error` row; (d) the guard fails when a file in a temp dir is touched and passes when not; (e) median, min, max, the 10 % spread flag and the `partial` rule are right on a hand-made list (these live in `mem_stats.py`); (f) `--unit-readings` on a made-up unit name prints an error line, not a traceback.
      → verify: `PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_measure/artifacts/mem_probe.py --selftest` prints `SELFTEST_OK`. Raise the self-test's cap to 5000, re-run, expect `SELFTEST_FAIL: (b)`; restore, expect `SELFTEST_OK`. The self-test allocates at most 300 MB.
- [x] 1.3 **Write `artifacts/make_tables.py`.** CLI: `make_tables.py --laptop <jsonl> --server <jsonl> --readings <jsonl> --out <md>`. `--readings` is the file the server agent builds with `--unit-readings` (labels `now`, `plus15s`, `db_loaded`, `warmup_done`, `one_book`, `reload1`, `reload2`, `reload3`). It prints the component table (median, min–max, spread flag, staircase delta, PSS delta, class), `interaction gap`, `unbuilt remainder` (server `warmup_done` RSS minus the server staircase total), the projection for 8 and 16 users with one book and with four, and the B–F figures with their sources. The class column comes from a dict at the top of the file (`read-only` or `per-user`), each entry with a one-line reason citing `file:line`. It imports its helpers from `mem_stats.py`.
      → verify: lint clean as in 1.1. Run it on a hand-made fixture (write `artifacts/fixture_laptop.jsonl`, `fixture_server.jsonl`, `fixture_readings.jsonl` and the expected numbers in `artifacts/fixture_expected.md`): the printed numbers equal the expected ones.
- [x] 1.4 **Phase check.** `rg -l "mem_probe|mem_stats" gui2 tools` prints nothing; `ls kamma/threads/20261102_contrib_mem_measure/artifacts` lists exactly `notes.md`, `books.md`, `mem_probe.py`, `mem_stats.py`, `make_tables.py` and the fixtures.
      → verify: both outputs as stated.

## Phase 2 — Laptop run — WHO: LOCAL AGENT prepares, MAINTAINER runs

- [x] 2.1 **WHO: LOCAL AGENT.** Ask the user for the one yes (the standing memory rule). Say: 52 fresh processes, one at a time (more only if a point's spread is above 10 %); each capped at 1.5 GB by the system and at 1.4 GB by the probe; the run stops after 40 minutes or on the first capped, killed or error row; it reads a 2.2 GB copy of the database, never the live one; no network; no write outside this thread's folder and a temp dir. Then make the copy with `sqlite3 dpd.db ".backup <SCRATCH>/dpd_copy.db"` (`<SCRATCH>` is this session's scratchpad directory; print its full path) and check it.
      → verify: `sqlite3 <SCRATCH>/dpd_copy.db "select count(*) from dpd_headwords"` equals the same query on `dpd.db`.
- [x] 2.2 **WHO: MAINTAINER.** Smoke test of two real points, one run each:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_measure/artifacts/mem_probe.py --point bare --out <SCRATCH>/smoke.jsonl && PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_measure/artifacts/mem_probe.py --point db_manager --db <SCRATCH>/dpd_copy.db --out <SCRATCH>/smoke.jsonl`
      → verify (LOCAL AGENT): `<SCRATCH>/smoke.jsonl` has two `ok` rows; the `db_manager` row records `query_only` 1 and a cache `hit` or `miss`; the guard reports no change in `gui2/data` and `gui2/storage`. If not: fix the probe before 2.3.
- [x] 2.3 **WHO: MAINTAINER.** The full run, one command:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_measure/artifacts/mem_probe.py --all --db <SCRATCH>/dpd_copy.db --books <the four from books.md> --out kamma/threads/20261102_contrib_mem_measure/artifacts/laptop.jsonl`
      → verify (LOCAL AGENT): `laptop.jsonl` has the expected number of lines (52, plus 3 per flagged point), none `capped`, `killed` or `error` (if one is, that is the finding and the user decides whether to raise the cap); the guard says no change in the three guarded folders; `ps --sort=-rss -eo pid,rss,cmd | head -5` shows no stray python.
- [x] 2.4 **WHO: LOCAL AGENT.** Run `make_tables.py` on `laptop.jsonl` (with empty server inputs for now) and save `artifacts/laptop_tables.md`. Flag every point with spread above 10 %.
      → verify: every point of the spec table has a row; the staircase total, the sum of isolated deltas and the `interaction gap` are printed.
- [x] 2.5 **Phase check.** Compare today's `corpus` delta with `3.3_memory.json` (63.0 MB bare, 804.3 MB for the corpus step). Write one line in `artifacts/laptop_tables.md` saying how they compare and why they may differ (the corpus became lazy; deferred columns).
      → verify: the line exists and quotes both numbers.

## Phase 3 — Server readings — WHO: SERVER AGENT (with MAINTAINER)

- [x] 3.0 **WHO: MAINTAINER.** `ssh epitaka 'mkdir -p ~/mem && echo "# Results — contrib_mem_measure" > ~/mem/results.md'`, then `rsync --bwlimit=400 /home/bodhirasa/MyFiles/3_Active/dpd-db/kamma/threads/20261102_contrib_mem_measure/artifacts/mem_probe.py /home/bodhirasa/MyFiles/3_Active/dpd-db/kamma/threads/20261102_contrib_mem_measure/artifacts/mem_stats.py /home/bodhirasa/MyFiles/3_Active/dpd-db/kamma/threads/20261102_contrib_mem_measure/spec.md /home/bodhirasa/MyFiles/3_Active/dpd-db/kamma/threads/20261102_contrib_mem_measure/plan.md epitaka:~/mem/`. Start the agent in `~/mem`.
      → verify: `ssh epitaka 'ls ~/mem'` lists the five files.
- [x] 3.1 **WHO: SERVER AGENT.** Readings now:
      `cd ~/dpd-db && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ~/.local/bin/uv run --no-sync ~/mem/mem_probe.py --unit-readings dpd-gui@alice --label now >> ~/mem/readings.jsonl; tail -n 3 ~/mem/readings.jsonl`
      **EXPECT:** one JSON object per python process, with `label` `now` and numbers for VmRSS, VmHWM, VmSwap, Threads and Pss (no range check: the value depends on how long the unit has run). An `error` line: STOP. Append the line, with a heading `## 3.1 Now`, to `~/mem/results.md`.
- [x] 3.2 **WHO: SERVER AGENT.** The server's database, tools and inputs (read-only):
      `ls -l ~/dpd-db/dpd.db ~/dpd-db/shared_data/frequency/cst_file_freq.json`
      `cd ~/dpd-db && PYTHONDONTWRITEBYTECODE=1 ~/.local/bin/uv run --no-sync python -c "import sqlite3; c=sqlite3.connect('file:dpd.db?mode=ro', uri=True); print(c.execute('select count(*) from dpd_headwords').fetchone(), c.execute(\"select count(*) from dpd_headwords where freq_data is not null and freq_data != ''\").fetchone())"`
      `command -v agy || echo NO_AGY; command -v sqlite3 || echo NO_SQLITE3`
      and `ls` of the files `books.md` names for the server book.
      **EXPECT:** sizes, two counts (the laptop has 88,805 non-empty), the tool lines, and every file of the server book present. If a file of the server book is missing, STOP and ask the maintainer to name another of the four. Append under `## 3.2 Database and tools`.
- [x] 3.3 **WHO: SERVER AGENT, maintainer's yes.** Check the cap works as root, then copy the database with low I/O priority:
      `systemd-run --scope -q -p MemoryMax=100M -p MemorySwapMax=0 true; echo "exit=$?"`
      `ionice -c3 nice -n 19 sqlite3 /root/dpd-db/dpd.db ".backup /root/mem/dpd_copy.db"` (if 3.2 printed `NO_SQLITE3`: `cd ~/dpd-db && PYTHONDONTWRITEBYTECODE=1 ionice -c3 nice -n 19 ~/.local/bin/uv run --no-sync python -c "import sqlite3; s=sqlite3.connect('file:dpd.db?mode=ro', uri=True); d=sqlite3.connect('/root/mem/dpd_copy.db'); s.backup(d); d.close()"`)
      `ls -l ~/mem/dpd_copy.db; df -h ~ | tail -1`
      **EXPECT:** `exit=0`; the copy within 5 % of `dpd.db`'s size; at least 3 GB free. Otherwise STOP.
- [x] 3.4 **WHO: SERVER AGENT + MAINTAINER, maintainer's yes and chosen time.** Fresh start in phases. The maintainer confirms alice has no unsaved form input. One step at a time; each reading is the 3.1 command with the label shown, appended to `~/mem/readings.jsonl`:
      1. Agent: `sudo systemctl restart dpd-gui@alice; sleep 15`; reading with `--label plus15s`.
      2. Maintainer: opens `https://<server-ip>.sslip.io/alice/` and tells the agent when "Database loaded." shows. Reading `--label db_loaded`.
      3. Maintainer tells the agent when "All tabs and tools ready." shows. Reading `--label warmup_done`.
      4. Maintainer opens Pass1Auto and the server book from `books.md` (Run, let one pass finish or press Stop) and tells the agent. Reading `--label one_book`.
      **EXPECT:** four readings, RSS rising at each step. If RSS falls or the unit restarts by itself: STOP. Append a summary of the four to `~/mem/results.md` under `## 3.4`.
- [x] 3.5 **WHO: SERVER AGENT + MAINTAINER, maintainer's yes.** Reload test. The maintainer reloads the page once and tells the agent; reading `--label reload1`; repeat for `reload2` and `reload3`. Wait at least 60 s after the restart in 3.4 before the first reload. Then the agent restarts the unit (`sudo systemctl restart dpd-gui@alice`) to drop stale copies. A rise of more than 100 MB per reload is a finding (a leak), not a stop.
      **EXPECT:** three readings with labels `reload1`, `reload2`, `reload3`. Append a summary under `## 3.5`.
- [x] 3.6 **WHO: MAINTAINER.** Say "go" for the capped run when ready.
      → verify: the maintainer says go.
- [x] 3.7 **WHO: SERVER AGENT, maintainer's yes.** The capped run, three times. First stop the unit: `sudo systemctl stop dpd-gui@alice; systemctl is-active dpd-gui@alice` (EXPECT `inactive`). Then, for run 1, 2 and 3 in turn, one command each time (launch and pid file are one line):
      `cd ~/dpd-db && (PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. nohup systemd-run --scope -q -p MemoryMax=1500M -p MemorySwapMax=0 -- env MALLOC_ARENA_MAX=2 ~/.local/bin/uv run --no-sync ~/mem/mem_probe.py --point staircase --db /root/mem/dpd_copy.db --out ~/mem/server.jsonl >> ~/mem/server_run.log 2>&1 & echo $! > ~/mem/server_run.pid)`
      Wait: `kill -0 "$(cat ~/mem/server_run.pid)" 2>/dev/null && echo RUNNING || echo ENDED; tail -n 3 ~/mem/server_run.log` every 5 minutes, at most 15 minutes per run. After 15 minutes still `RUNNING`: `kill "$(cat ~/mem/server_run.pid)"`, then recovery below.
      Then: `sudo systemctl start dpd-gui@alice; systemctl is-active dpd-gui@alice`.
      **EXPECT:** `inactive` before; three rows in `~/mem/server.jsonl` (outcome `ok`, or `capped`, which is a result); `active` after; no stray python in `ps -eo pid,rss,cmd | grep "[m]em_probe"`. **Recovery on any STOP:** tell the maintainer, then with his yes `sudo systemctl start dpd-gui@alice`, then `systemctl is-active dpd-gui@alice` must print `active`.
- [x] 3.8 **WHO: SERVER AGENT. Phase check.** Write `## Phase 3 verdict` in `results.md`: which of 3.1–3.7 met EXPECT, any STOP, the number of server rows by outcome, and whether alice is `active`.
      → verify: the section exists and names every task 3.1–3.7.

## Phase 4 — Results — WHO: LOCAL AGENT

- [x] 4.1 **WHO: MAINTAINER.** Copy the server files back:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && mkdir -p kamma/threads/20261102_contrib_mem_measure/artifacts/server && rsync --bwlimit=400 -r epitaka:mem/results.md epitaka:mem/server.jsonl epitaka:mem/readings.jsonl epitaka:mem/server_run.log kamma/threads/20261102_contrib_mem_measure/artifacts/server/`
      → verify (LOCAL AGENT): `ls artifacts/server/` lists the four files.
- [x] 4.2 **WHO: LOCAL AGENT.** Run `make_tables.py --laptop artifacts/laptop.jsonl --server artifacts/server/server.jsonl --readings artifacts/server/readings.jsonl --out artifacts/tables.md`. Write `artifacts/results.md` from it: the component table, the two reconciliation rows, the projection (one book and four), the B–F ranking table with sources and columns, the reload-test result, and a paragraph on the laptop-versus-server difference. Effort and risk columns are judgement; say so.
      → verify: re-run `make_tables.py`; the table blocks in `results.md` equal `tables.md` (`diff` prints nothing). Every number outside the tables cites a row or a server log line.
- [x] 4.3 **WHO: LOCAL AGENT.** Corrections list in `results.md`: anything in `kamma/archive/20261101_contrib_6_e2e_server_test/` (for example the "Addendum B" figures, the 2.5 GB comment) or in `kamma/threads/20261030_contrib_x_problem_children/` that the numbers contradict, and the edits proposed for `kamma/threads/20261023_contrib_1_web_server/`. Do not edit those files.
      → verify: the list exists; each item quotes the old claim and the new number.
- [x] 4.4 **WHO: LOCAL AGENT. Phase check.** Re-read `spec.md` "How we'll know it's done" items 1–5 and mark each met or not met in `results.md`.
      → verify: five lines, each pointing to the file that proves it.
- [x] 4.5 **WHO: MAINTAINER.** Commit this thread's folder (the local agent suggests the message); decide which of the B–F options to plan next. Commit nothing outside this folder from this thread.
        Closed 2026-11-02: the folder is tracked in git (verified with `git ls-files`). Of B–F: D implemented in `267740fc`; the corpus/set levers implemented in `247a8429` (see the closure note above); the remainder — E, F, B's manager part, C's original form — deferred by the owner.
      → verify: `ls kamma/threads/20261102_contrib_mem_measure/artifacts` lists the probe, the tables, `results.md` and `server/`.
