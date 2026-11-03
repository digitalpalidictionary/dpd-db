# Spec: measure where a contributor gui2 instance spends its memory

**Thread:** 20261102_contrib_mem_measure
**Date:** 2026-11-02
**GitHub issue:** [#215 — Contributor Onboarding](https://github.com/digitalpalidictionary/dpd-db/issues/215). Never write to the issue.
**Builds on:** `kamma/archive/20261101_contrib_6_e2e_server_test/` (read `artifacts/server/results.md`, "Addendum B": the only server memory reading). Feeds `kamma/threads/20261023_contrib_1_web_server/` (production server design) and the memory options in `kamma/threads/20261030_contrib_x_problem_children/`.
**Plan:** `plan.md` in this folder. Its Phase 0 does the look-ups this spec leaves open (which books, which AI providers, tools on the server).

## Overview

One contributor gui2 web instance used 1.25 GB (RSS and peak both) on the borrowed
server. That is one reading, taken warm, after book runs and additions. Each new
contributor adds one more instance, so memory sets how many contributors a server
holds and what it costs.

Nobody knows where the 1.25 GB goes. Six ways to cut it were listed on 2026-11-02:

- A: measure first (this thread).
- B: no warm-up preload for contributors.
- C: answer "is this word known" from the lookup table, not an in-memory set.
- D: frequency data in the database, not a JSON dictionary.
- E: one process for all users, with shared read-only data.
- F: start an instance only while its person is online.

This thread measures. It changes no gui2 or tools code. It ends with a table of
numbers and a ranking of B to F that the owner can act on.

## Where each measurement runs

Two machines, two jobs. The laptop gives the split by component. The server gives
the real total. Neither can do the other's job well.

| Item | Where | Why |
|---|---|---|
| Look-ups: book sizes, AI provider constructors, cap tool (Phase 0) | Laptop | Reads source and local files only. |
| Write and test the probe (Phase 1) | Laptop | Needs the repo and a small self-test. |
| Copy of the live database (`.backup`, 2.2 GB) | Laptop | The laptop db is the full build; the copy protects the live file. |
| The 52-run battery: 11 isolated points, 4 books, cumulative books, staircase | Laptop | 22 cores and 31 GB, owned by the user, who watches it. On the server it would be slow on 2 CPUs, would need about 50 commands from a small model, and would put the other project's 8 GB box at risk. |
| Tables, the `interaction gap` row, results, corrections (Phase 4) | Laptop | Pure analysis of files. |
| Readings of alice's live instance now (3.1) | Server | Only the server has the instance behind the 1.25 GB figure. |
| Database size, `freq_data` count, tools, chosen-book files (3.2) | Server | The lean build differs from the laptop db. |
| Database copy on the server (3.3) | Server | The capped run must read the server's own database. |
| Fresh start in phases (3.4) | Server | Needs the real instance and the maintainer's browser. |
| Reload test (3.5) | Server | Only a real browser session behind nginx shows the leak. |
| Capped run of the staircase, 3 times (3.7) | Server | Same code on the server's database gives the `unbuilt remainder` row and the laptop-versus-server comparison. |

What needs both: the comparison. The server's warm RSS minus the server's staircase
total is the `unbuilt remainder`; the laptop's staircase total and isolated deltas give
the `interaction gap`. The headline numbers are the server's; the laptop's explain them.

Not planned: running everything on the server. It is possible, but slower, riskier for
the shared box, and a heavier task for a small model. If the owner chooses it, Phase 2
moves to Phase 3 and the 52 runs need a server-side driver and the book files there.

## Prior art (found by Gate 1; verified)

`kamma/archive/20260710_gui2_perf_and_testing/benchmarks/` measured part of this on
2026-07-10: bare process 63.0 MB, after `DatabaseManager()` 69.1 MB, after
`initialize_db()` 873.4 MB, so 804.3 MB for the corpus step (`results/3.3_memory.json`,
script `bench_memory.py`, helpers `bench_common.py`). That was before the corpus
became lazy: today `initialize_db()` no longer loads the corpus (see
`is_db_loaded`'s docstring in `gui2/database_manager.py`), and the corpus loads in
`load_corpus()`. So the old number must be re-measured against today's code. The same
archive's `findings.md` (C3) guessed 300–700 MB for the wordfinder JSON; that was
never measured.

## What it should do

### 1. A probe script, kept in this thread's `artifacts/`, not shipped

`artifacts/mem_probe.py` runs one measurement per process. Each run is a fresh
interpreter, so no earlier run leaves heap behind. It builds only the pieces it
measures. It never builds `ToolKit` or `App`.

**Points measured** (each prints one JSON line):

| Point | What it builds | Needs first |
|---|---|---|
| `bare` | Fresh interpreter plus psutil. | — |
| `imports` | `import gui2.main` (every module `python gui2/main.py` imports at start). Lazy imports inside functions show up in the point that triggers them. | — |
| `db_manager` | `DatabaseManager(<temp checked.csv path>)`. | — |
| `initialize_db` | `initialize_db()` (lemma, pos, family and decon sets; no corpus). | `db_manager` |
| `corpus` | `load_corpus()` (all headwords as ORM objects). | `db_manager` |
| `inflections_lists` | `make_inflections_lists()` (`all_inflections` and the missing-meaning set). | `corpus` |
| `relationship_detector` | `get_relationship_detector()`. | `corpus` |
| `wordfinder` | `WordFinderManager()` (loads `cst_file_freq.json`). | — |
| `ai_manager` | `AIManager()` with `agy` removed from PATH. | — |
| `bold_search` | `BoldDefinitionsSearchManager()`. | — |
| `spellchecker` | `CustomSpellChecker(<explicit temp file>)`. | — |
| `book:<name>` | That book's `segment_dict` and `word_dict`, plus its CST word list. | — |
| `books_cumulative` | The four chosen books in one process, largest first, one reading after each. | — |
| `staircase` | One process, in this order, one reading after each step: `bare`, `imports`, `db_manager`, `initialize_db`, `corpus`, `inflections_lists`, `wordfinder`, `ai_manager`, `bold_search`, `relationship_detector`, `spellchecker`. The tab views and `WordFinderPopup` are UI and are not built. | — |

**Delta formula.** Every isolated run records: `bare`, then `imports`, then it builds
the prerequisites in the "Needs first" column and records a reading, then builds the
point and records a reading. The point's delta is that last reading minus the reading
before it. `imports` has its own row: its delta is `imports` minus `bare`. This way
each component's delta excludes the shared imports and its prerequisites.

**Readings at every point:** RSS, PSS and USS (psutil `memory_full_info`, which reads
`smaps_rollup`), VmHWM, VmSwap, thread count. At the end of each isolated run, two
more RSS readings: after `gc.collect()` and after `malloc_trim(0)`. This separates
transient peak from what the process keeps.

**Metadata on every row:** git commit, Python version, `dpd.db` size, the env gates
set, which AI providers were built, whether `agy` was found, `MALLOC_ARENA_MAX`, load
average, whether the deconstructor cache was a hit or a miss, and the outcome.

**Outcomes.** `ok`, `capped`, `killed`, or `error` (an exception: its type and message, never a secret). A `capped` row records the last reading the watchdog
printed and the point reached. If the cgroup kills the process first and no line is
printed, the driver records `killed (no output)`. A capped or killed run is left out
of the median, and its point is reported as "more than X MB". If one of the three runs
for a point is capped, the other two are still reported and the row is marked
"partial".

**Repeats.** One throwaway warm-up run at the start (warms the file cache), then the
median of 3 fresh processes per point, with min and max. A point whose spread
(max − min) is more than 10 % of its median is flagged and run three more times.
The staircase runs 3 times too.

### 2. Safety rules for the probe (all from Gate 1 and Gate 2)

- **No write to the live db.** Run against a copy made with `sqlite3 dpd.db ".backup <scratchpad>/dpd_copy.db"` (a plain `cp` of a WAL-mode file can miss recent writes). The path has no override (`tools/paths.py:15`: `base_dir / "dpd.db"`), so the probe patches `get_db_session` the way `bench_common.force_throwaway_db_globally()` does, but finds the targets itself: after the imports and before any call, it walks `sys.modules` and replaces `get_db_session` in every module where it is the original function (`database_manager.py:14` imports it by name; the detector worker at `database_manager.py:~827` calls it too). The patch must happen before the first engine is built, because `db/db_helpers.py` caches engines by resolved path. Copy the idea, not an import from the archive.
- **Env set first.** The first lines of the script, before any import, set `DPD_GUI2_ROLE=contributor-server` (turns on `PRAGMA query_only`, `db/db_helpers.py:74-82`), `DPD_GUI2_USERNAME=memprobe`, and `DPD_GUI2_DATA_DIR=<temp dir>` (so any per-user path from `gui2/paths.py:70-95` lands in the temp dir). The probe asserts that `PRAGMA query_only` returns 1 on the session the loaders really use.
- **Cache hit or miss.** `get_all_decon_no_headwords` writes to `db_info` only on a cache miss (`database_manager.py:321-343`); a contributor-role write fails and is swallowed. A `.backup` copy of the laptop db probably has a warm cache, so that path is not exercised. Record hit or miss on every row.
- **Divergence from a real contributor, stated.** A bare `DatabaseManager` has no overlay (`_own_edits` is unset), so the per-user additions (`database_manager.py:218-222`) and the per-user sandhi list are not loaded. Those are small JSON files. The probe does not feed them, because it must not touch user files.
- **No other writes.** Never call `add_to_dictionary`, `SpeechMarkManager.save`, `regenerate_from_db`, or anything that saves a manager. The spell checker gets an explicit temp dictionary path. Record modification times of `gui2/data/`, `gui2/storage/`, the temp dir and `shared_data/` (which holds the shared user dictionary) before and after. A change in the first three fails the run. A change in `shared_data/` is a warning with the file names, because other sessions write there.
- **No secrets, no network.** The probe never prints config values, provider objects or environment variables. `AIManager` runs with `agy` removed from PATH. Phase 0 first reads each AI provider constructor for network or subprocess calls. A provider that has one is measured by import only.
- **Memory cap.** Each process runs under `systemd-run --user --scope -p MemoryMax=1500M -p MemorySwapMax=0`, plus an in-process watchdog that prints its last reading and calls `os._exit` at 1.4 GB RSS. `ulimit -v` is not used: it caps address space, which Python threads and glibc arenas inflate, so it fails early and gives no number. `MALLOC_ARENA_MAX=2` is set and recorded. Raising the cap needs the user's yes first.
- **One driver, one yes.** The probe has an `--all` mode that runs the whole sequence one process at a time. The count is 52 processes: 1 throwaway, 11 isolated points × 3, 4 books × 3, the cumulative book run × 3, and the staircase × 3. A point with a spread above 10 % adds 3 more. The user is told once, up front, with the full list and the caps, and says yes once. The driver has a hard total timeout of 40 minutes (a guess: the sequence has never been timed) and stops on the first `capped` or `killed` row. Memory probes still follow the standing rules: check `ps --sort=-rss` for strays afterwards.

### 3. Book growth

`SuttaCentralSource.segment_dict` and `word_dict` are `cached_property` on the
module-level `sutta_central_books`, so each book opened keeps its index for the life
of the process (`gui2/books.py`). Phase 0 lists the books by on-disk size and picks
the four largest (SuttaCentral JSON and CST text together, as Pass1Auto loads them).
Each book runs in its own fresh process for its own cost. One more run opens the same
four in one process, largest first, with a reading after each. Then stop: no other
books.

### 4. Server readings (through the server agent)

**Who and where.** Host alias `epitaka` (root login), the clone `~/dpd-db`, the unit
`dpd-gui@alice`. The "server agent" is a model on that server, run by the
maintainer, bound by the rules at the top of `plan.md`. The maintainer copies
`mem_probe.py` to `~/mem/` on the server with `rsync --bwlimit=400`. Outputs go to
`~/mem/`, and the maintainer copies them back into `artifacts/server/`.

Server work is read-only except for the steps marked "(maintainer's yes)".

1. **Now.** For alice's running python process: VmRSS, VmHWM, VmSwap, thread count, `smaps_rollup`, and how long it has run. Never `environ`. The PID comes from the unit's cgroup (`systemctl show -p ControlGroup`; on this server `/system.slice/system-dpd\x2dgui.slice/dpd-gui@alice.service`, because a template instance sits in its own slice), not from `pgrep -f`: the unit runs `uv run --no-sync python gui2/main.py`, so MainPID is the `uv` wrapper and the python process is its child.
2. **Fresh start, in phases (maintainer's yes).** Restart alice's unit. Read at +15 s (process, imports, FastAPI, no page). The maintainer opens the page. The agent reads again when he reports "Database loaded.", again when he reports "All tabs and tools ready.", and again after he opens one Pass1Auto book (chosen in Phase 0). The differences give the db load, the tab views plus managers, and one book.
3. **Reload test (maintainer's yes, at a time he chooses).** The maintainer reloads the page 3 times; read after each. Flet keeps a replaced session for up to an hour (`kamma/tech.md`) and `claim_session` leaves the old `App` alive (`gui2/main.py`, comment above `claim_session`). This shows whether reloads leak, which would mean 1.25 GB already includes old copies. Afterwards restart the unit to clean up. The code comment's "about 2.5 GB" for a second app is a comment, not a measurement. alice is the maintainer's own test account, so no real contributor loses work; the maintainer confirms she has no unsaved form input.
4. **The server's database and tools.** `dpd.db` size, headword count, and how many headwords have a non-empty `freq_data` (read-only query, `mode=ro`). The lean build drops the frequency steps (`scripts/server_contrib/generate_components_server.py`), so the server corpus may be lighter than the laptop's. On the laptop, 88,805 headwords have a non-empty `freq_data`. Also `command -v agy` and `command -v sqlite3`.
5. **One capped probe run on the server (maintainer's yes).** The staircase (it has no books), run as root on a `.backup` copy of the server db, with alice's unit stopped for the run and started after. The same guards as section 2 apply: role, `query_only`, modification-time guard, temp data dir. First check that the cap works there: `systemd-run --scope -p MemoryMax=100M true` as root must exit 0. The box had 5526 MB available at rest (Addendum B). The cap is 1.5 GB as on the laptop. If the run is `capped`, that is a result, and raising the cap needs the maintainer's yes.

### 5. Output: `artifacts/results.md`

**Component table.** One row per point: isolated delta (median, min–max, flagged if
spread is above 10 %), staircase delta, PSS delta, and a class. The class is
`read-only` (built only from inputs identical for every user, so a shared process
could keep one copy) or `per-user` (depends on the user or the session). The class is
a judgement from reading the code, not a measurement: PSS and USS of a single process
cannot show what two processes could share. Rows: `bare` and `imports` (paid once per
process), each component, each book.

**Two reconciliation rows**, named so they cannot be confused:

- `interaction gap` = laptop staircase total − (`bare` + `imports` + sum of the isolated component deltas). It is the effect of shared pages and allocator reuse.
- `unbuilt remainder` = server warm RSS (after "All tabs and tools ready", before any book) − server staircase total (section 4.5). It is what the probe does not build: tab views, Flet session state, FastAPI, anything else. How it splits between per-process base and per-session UI is not measured; for option E it is treated as per-user, which is an upper bound. If `unbuilt remainder` is more than 20 % of server warm RSS, say so and propose one `tracemalloc` run on the largest piece as a follow-up. It is not built here.

**Which database.** The server numbers (section 4) are the headline, because the lean
server db differs from the laptop's. The laptop numbers give the split between
components. The output states the difference between the two.

**Projection for 8 and 16 contributors.** The fixed baseline is memory used with no
gui2 running: 1066 MB (`results.md` "3.1 Pre-state"; it includes the other project on
that box). Two book assumptions: each user opens one book, and each user opens four.
Today: baseline + N × per-instance. With option E: baseline + shared (the `read-only`
rows, paid once) + N × (the `per-user` rows + the `unbuilt remainder`).

**Ranking of B to F.** Each option gets its figure from one measured point, and each
figure is an upper bound:

| Option | Figure from |
|---|---|
| B no warm-up preload | `wordfinder` + `ai_manager` + `bold_search` + `relationship_detector` deltas. The real saving depends on what contributors open; that is not measured. |
| C lookup table, not a set | `inflections_lists` delta. The cost of a lookup query is not measured. |
| D frequency data in the db | `wordfinder` delta. |
| E one shared process | sum of the `read-only` rows × (N − 1), minus nothing for the `unbuilt remainder`. |
| F start only while online | no per-instance saving; memory = K online × per-instance. K comes from the owner, not from this thread. |

Columns: MB saved per instance, effect at 8 and 16 users, effort, risk. Effort and
risk are judgement. The choice between E and F stays with the owner. Option A is the
thread itself and is not ranked.

**Corrections.** Anything in `kamma/archive/20261101_contrib_6_e2e_server_test/` or the
problem-children thread that the numbers contradict is listed, not edited.

## Decisions made while planning (none was away-mode)

The owner was present, and Gates 1 and 2 escalated nothing. Two choices went one way
because the repo or a standing rule settled them:

1. **Cap method.** cgroup `MemoryMax` plus a watchdog, not `ulimit -v`. The user's standing rule names `ulimit -v 1500000`, written for runaway regex probes. Gate 1 found it fails early for a loader. The 1.5 GB number is kept.
2. **Three runs, not one; one yes for the batch.** The standing rule says run once and tell the user before. It was written for unbounded probes. This probe is capped, and one reading of a noisy quantity is not a measurement. The user says yes once to the whole capped batch.

## Assumptions & uncertainties

Gate 1 findings accepted (record in `egm/gate1.md`; 25 raw findings):

- **[Major]** Part of the answer exists in the July benchmark; re-measure rather than re-derive.
- **[Blocker]** `ulimit -v` caps virtual memory, not RSS; use a cgroup cap and a watchdog.
- **[Blocker]** A capped run gives no number; `capped` is its own outcome.
- **[Major]** Isolated and in-process measurements disagree by design; report both, with a named gap.
- **[Major]** RSS hides sharing; record PSS and USS.
- **[Major]** Peak and steady state differ; read before, after `gc.collect()`, after `malloc_trim(0)`.
- **[Major]** Laptop and server differ (db size, lean build, providers); run the probe on both.
- **[Major]** Constructing app managers can write files; build components only, guard modification times.
- **[Major]** The deconstructor cache save commits to `db_info` outside the contributor role; use a db copy and set the role in the probe.
- **[Major]** Book indexes live for the process; limit to the largest books.
- **[Major]** The old `App` may stay in memory after a reload; the reload test checks it.

Gate 2 findings accepted (record in `egm/gate2.md`; 25 raw findings):

- **[Blocker]** Phase 0 and the server commands were missing; this spec now names the host, unit, user, copy method and outputs, and `plan.md` carries the commands.
- **[Major]** Delta formula, step order, `capped` rule and the two "unattributed" definitions were unclear; now defined in sections 1 and 5.
- **[Major]** The staircase leaves out tab views and Flet state; the server phase readings and the `unbuilt remainder` row cover them.
- **[Major]** PSS cannot show what is shareable; the class is a code judgement and says so.
- **[Major]** The probe has no overlay and a laptop db copy has a warm decon cache; both are stated and recorded.
- **[Major]** The server capped run was under-protected; it is reduced, uses a copy, repeats the guards and checks the cap first.
- **[Major]** About 70 processes against a per-run confirmation rule; one driver and one yes.

Gate 3 findings accepted (record in `egm/gate3.md`; 20 raw findings):

- **[Blocker]** The cgroup path of a template instance is not `system.slice/<unit>.service`; checked on the server.
- **[Blocker]** Plain `uv run` on the server can sync the venv alice's unit uses; use `--no-sync` and `PYTHONDONTWRITEBYTECODE=1`.
- **[Blocker]** A failed server run could leave alice stopped; the plan has a recovery step and one allowed way to end the probe.
- **[Blocker]** `~` inside a quoted `.backup` command is not expanded; use absolute paths.
- **[Major]** No `error` outcome, no smoke test before the full run, no CLI for the table script, no check that the chosen book exists on the lean server, and a `git status` check against the standing rule; all fixed in `plan.md`.

Verified this way (source read or command run on 2026-11-02): the 63 → 873 MB benchmark
result; `claim_session` and its comment; `load_corpus`, its deferred columns, and that
`initialize_db` no longer loads it; the warm-up list; `WordFinderManager` loading
`cst_file_freq.json` (70.9 MB on disk); `AIManager.__init__`; `cached_property` on book
indexes; `CustomSpellChecker` as a singleton; `PRAGMA query_only` for the contributor
role; `save_decon_no_headwords_cache` committing to the db; `Gui2Paths.for_user`;
`psutil>=7.0.0`; `systemd-run` 255, the cgroup memory controller and the user manager
on this machine; 88,805 non-empty `freq_data` rows on the laptop.

Not verified:

- The peak of the corpus load (the July benchmark recorded only the value after it).
- Whether the server's `freq_data` is empty; only the lean-build list was read.
- Whether any AI provider constructor makes a network call or starts a process; Phase 0 reads them.
- Whether a reload really leaks an old `App`; section 4.3 tests it.
- Whether `systemd-run` with a memory cap works as root on the server; section 4.5 checks first.
- Whether `sqlite3` exists on the server; section 4.4 checks, and Python's backup API is the fallback.
- How long the whole `--all` sequence takes; the 40-minute timeout is a guess.

## Constraints

- No change to gui2 or tools code, and no commit of probe code outside this thread's folder.
- The user runs every laptop command. The server agent runs only the commands in `plan.md`, with the maintainer's yes at each restart, stop or capped run.
- Never read, print or edit `config.ini` or any `.env`. Never touch `~/epitaka-translator` or its processes on the server.
- The probe never writes to `dpd.db`, `gui2/data/`, `shared_data/` or the spell-checker dictionaries.
- Memory caps as in section 2. Check for stray processes after each probe.

## How we'll know it's done

1. `artifacts/mem_probe.py --all` completes on the laptop: every point, three runs each, and the modification-time guard reports no change.
2. The server readings from section 4 are in `artifacts/server/`, including the phase readings, the reload test and the capped server run.
3. `artifacts/results.md` has the component table, both reconciliation rows, the projection for 8 and 16 contributors, and the B–F ranking.
4. Every number in `artifacts/results.md` is quoted from a probe output line or a server log in `artifacts/`.
5. Anything the numbers contradict in earlier threads is listed, not edited.

## What's not included

- Any fix: no change for options B to F. This thread only ranks them.
- A direct measure of Flet's per-session UI cost, or two live sessions in one process. gui2 cannot host two (the session guard retires the first), and a second server instance would cost about 2.5 GB more on a shared 8 GB box.
- CPU, start-up time, or price per server.
- `tracemalloc`, unless the `unbuilt remainder` is above 20 %.
- Editing `kamma/threads/20261023_contrib_1_web_server/` or the problem-children thread; edits are listed for the maintainer.

## Review record

Gate 1 (idea): 3 Goldfish on native subagents (six lenses paired), 25 raw findings
(2 Blocker, 16 Major, 7 Nit): 19 accepted, 4 accepted in part, 2 merged as
duplicates, 0 rejected, 0 escalated. See `egm/gate1.md`.
Gate 2 (spec): 2 Goldfish on native subagents, 25 raw findings (2 Blocker, 14 Major,
2 Minor, 7 Nit): 21 accepted, 3 accepted in part, 1 merged, 0 rejected, 0 escalated.
See `egm/gate2.md`.
Gate 3 (plan readiness): 1 Goldfish on native subagents, 20 raw findings (4 Blocker, 10 Major, 6 Nit): 20 accepted, 0 rejected, 0 escalated. See `egm/gate3.md`.
