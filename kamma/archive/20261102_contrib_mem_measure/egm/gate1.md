# Gate 1 — idea review (2026-11-02)

Backend: native subagents (`Agent`, general-purpose). Smoke probe passed first (read one file, returned its first line). Six lenses paired onto three Goldfish (small thread: one probe script plus a runbook). No backend switch, no failed run.

## Raw findings

### Goldfish 1 — Contrarian/YAGNI + long-term debt

**Findings (problems only)**

1. **Major (Lens 1): Half the answer already exists.**
   - `kamma/archive/20260710_gui2_perf_and_testing/benchmarks/results/3.3_memory.json` is a measured baseline. A bare process is 63 MB, `DatabaseManager()` construction is 69 MB, and `initialize_db()` (the corpus load) takes it to 873 MB. That is about 804 MB, roughly 64% of the 1.25 GB reading.
   - The same archive has `bench_memory.py`, `bench_common.py` (`rss_mb()` via psutil) and `bench_corpus.py`. `findings.md` (Theme B, C3, C4) already names the suspects.
   - The brief lists neither the 804 MB corpus figure nor `bench_memory.py` as prior art. It cites only the startup probe `probe_warmup.py`.
   - The 804 MB figure may be stale, since the thread says later work changed the corpus (deferred columns, per the brief). Its only open question is whether it still holds.
   - Fix: re-run the existing `bench_memory.py`-style probe. Then ask only what the remaining ~380 MB is (wordfinder JSON, AI imports, detector, per-book indexes). That is two or three deltas, not a seven-component split.

2. **Major (Lens 1): Options B, C and D can be ranked from known facts.**
   - The biggest consumer is the headword corpus (`database_manager.py:181`). Options C and D target small pieces. D is the 70.9 MB JSON, which expands several times in Python, but that is still a single delta.
   - E, one process with shared read-only data, would save the most. It is also the only option that needs real design (fork-shared, or a per-user session).
   - F cuts idle memory, and a per-user memory number cannot rank it. It depends on how many contributors are online at once.
   - A ranking by "MB saved" ignores cost and risk. A table of numbers will not choose between E and F.
   - Fix: decide E versus F on concurrency and effort. Use one measurement only for the wordfinder and AI deltas.

3. **Major (Lens 2): "Each component in its own fresh process" does not reproduce the real split.**
   - Isolated loads miss shared pages, interpreter and import overlap, and allocator fragmentation. Examples are SQLAlchemy and the `DpdHeadword` classes imported by both the corpus and the detector, and `pass1_auto_controller.py:271`'s `all_inflections` built from the same rows.
   - The sum of isolated components will not equal 1.25 GB, and the gap cannot be assigned to anything.
   - The brief's own `claim_session` note says that when a new page retires the old one, the old `App` stays in memory (about 2.5 GB with two). So 1.25 GB may already include a leaked second session.
   - Fix: measure incrementally inside one process (RSS delta after each step, in real startup order, plus `tracemalloc` or `pympler` for Python objects). That is the pattern `bench_memory.py` already uses.

4. **Major (Lens 2): The probe design is brittle.**
   - Instantiating `ToolKit`, `WordFinderManager` or the detector means importing private gui2 internals. The brief itself notes that importing tools can run `config_read`, which reads `config.ini`.
   - `bench_common.force_throwaway_db_globally()` shows what that costs: it has to monkeypatch every `get_db_session` binding. A hard-coded component list goes stale as soon as the warm-up in `gui2/main.py:558` changes.
   - Fix: keep the script in the thread's `artifacts/` and do not ship it. Drive the real warm-up and sample RSS on a timer. Use `/proc/<pid>/smaps_rollup` on the server, or psutil locally.

5. **Major (Lens 1): "Measure growth as books are opened" is open-ended.**
   - Growth depends on which books and in what order. `segment_dict` and `word_dict` are `cached_property`, so the cost is per book and permanent. Without a stated book set and a cap, it will not stop.
   - Fix: open the 3 or 4 largest books once, report MB per book, and stop.

6. **Nit: Single-reading baseline.** The 1.25 GB is one reading, after book runs and additions, with VmHWM equal to RSS. It is not a fresh-start figure, and a session leak could be inflating it. Take a fresh-start RSS on the server before and after the first book.

7. **Nit: The server agent can only run read-only commands.** Reading `/proc` is fine, but you cannot start a clean instance there. So the comparison between fresh and warm has to be local.

**Bottom line:** Narrow the thread to a re-run of `bench_memory.py` with a few more checkpoints, and a short per-book growth table. Do not build a per-component fresh-process probe, and do not treat the ranking as a memory-only question.

### Goldfish 2 — Cost/load + observability

**Findings: contrib_mem_measure brief, two lenses (Cost/quota/load, then Observability)**

**1. Blocker — `ulimit -v 1500000` caps virtual address space, not memory.** (brief.md:41)
- Python 3.13 with glibc per-thread malloc arenas reserves 64 MB of address space per thread. Flet and the warm-up run thread pools, and SQLite can use mmap. Virtual size typically runs well above RSS.
- Scenario: the probe dies with MemoryError or a failed thread start at an RSS far below 1.5 GB. Or the cap is raised until it protects nothing.
- Fix: use a cgroup limit instead (`systemd-run --user -p MemoryMax=1500M -p MemorySwapMax=0`). If that is not possible, add an in-process RSS watchdog that aborts at 1.4 GB. Set `MALLOC_ARENA_MAX=2` for every run and record it.

**2. Blocker — 1.5 GB is not a realistic cap for the full app, and the brief never says what happens at the cap.** (brief.md:24)
- The live total is 1.25 GB. The probe also adds its own overhead: imports, a measuring process, a fresh interpreter for each component.
- The corpus load is transient. `load_corpus` (database_manager.py:181) loads all 89,763 ORM rows through `.all()`. SQLAlchemy builds the identity map and the result list at the same time, so peak is well above steady state.
- A component that trips the cap gives no number, and the harness may report it as "0" or "n/a".
- Fix: set per-component caps, and log "capped at X" as its own outcome. Record peak (VmHWM) and steady state (after `gc.collect()` plus `malloc_trim`) separately.

**3. Major — the dev machine and the server are different workloads.**
- Dev `dpd.db` is 2.2 GB (`ls -la dpd.db`). The server's db is 511 MB (results.md:1243, which also lists `resources` at 2.2 GB).
- Page-cache and mmap behaviour differ. Whether `frequency/*.json`, `sc_bilara_data` and CST text are the same size is unknown.
- Role and config differ too. `DPD_GUI2_ROLE=contributor-server` sets `query_only` and suppresses shell-outs (`tools/server_mode.py:20`). The AI managers are gated on keys in `config.ini` (`ai_manager.py:77,83`) and on `agy` being on PATH (`ai_manager.py:89`).
- Scenario: the dev split is projected onto the server, and the AI and provider share is wrong.
- Fix: record db size, which env vars were set, which providers were built, and whether `agy` was found. Have the server agent take the one read-only `/proc/<pid>/smaps_rollup` sample that counts.

**4. Major — RSS is the wrong ranking metric for option E.**
- Option E (one process, shared read-only data) is about sharing. RSS counts shared pages in full for every process, and fresh-process-per-component runs share the interpreter and library pages.
- Fix: record PSS and USS from `smaps_rollup` (psutil `memory_full_info`), plus the Python heap (`tracemalloc` or `sys.getallocatedblocks`) separately from the RSS minus heap remainder. The remainder is native: SQLite, the Flet client libraries, glibc fragmentation.
- Components cost less alone than in sum, because shared imports (sqlalchemy, flet) are counted once. State that the split sums to more than the whole, or measure incrementally in one process (deltas) as well as in isolation.

**5. Major — the warm-up peak and steady state are conflated.**
- glibc rarely returns freed heap to the OS. The 1.25 GB figure is after book runs and additions and is a peak (VmHWM equals RSS). It includes transient garbage, such as the corpus-load result and JSON parse temporaries.
- `json.load` of the 70.9 MB `cst_file_freq.json` (`tools/wordfinder_manager.py:52`) peaks at several times its file size. A 70.9 MB file costs well over 70.9 MB in Python objects.
- Scenario: option D (frequency data in the db) is credited with the peak when the steady-state saving is smaller, or the reverse.
- Fix: read RSS before load, after load, after `gc.collect()`, and after `malloc_trim(0)` via ctypes.

**6. Major — one run is not trustworthy.**
- Sources of noise: warm versus cold page cache, other tenants on the dev box, and swap use.
- On the server, a measurement with swap active makes RSS lie low. Record `VmSwap` and `/proc/meminfo`.
- Fix: take a throwaway warmup run, then a median of at least 3 fresh processes per component, and report min and max. Check load first (`uptime`). The brief's "run once" rule (brief.md:41) conflicts with this. Say so to the user. Use 3 runs if the cap allows.

**7. Major — the probe could harm the 8 GB shared server.**
- The brief says server work is read-only through the agent. Running the loader there is not read-only: it would take about 1.25 GB, and the first build already got within about 170 MB of the wall (results.md:1237).
- `get_db_session` runs `PRAGMA journal_mode=WAL`, which is a write (`db/db_helpers.py:~73`). `query_only` is set after it. Importing `db_helpers` and opening `dpd.db` on dev can touch the WAL and SHM files. Use a copy, or `file:...?mode=ro`.
- Fix: on the server, `/proc` reads only. Run all loaders on dev, against a copy of the db at `/tmp`.

**8. Major — the book-growth curve depends on which books are opened, in what order, and on shared state.**
- `segment_dict` and `word_dict` are cached and kept for the life of the process. `tools/spelling.py` is a process singleton where the first caller's `user_dict` wins.
- Fix: log the book order and the index sizes. Open each book in its own fresh process for the per-book cost, and run a second cumulative sequence. Tag each row of output with the process's first-caller state.

**9. Nit — the 2.5 GB claim in the `claim_session` comment (main.py:~665) is unmeasured.** It is the old-App-leak figure, and it counts for option F. Measure it, or label it a guess.

**10. Nit — the output must record the measured state.**
- Per row: which method, git commit, Python version, and which env and config gates were on.
- Also per row: whether `load_corpus` had finished, whether the warm-up had finished (`_warmup_in_background` runs in a thread, so poll for completion rather than sleeping), and RSS, PSS, USS, VmHWM, VmSwap and thread count.
- Also: any threads still running, such as the `agy` probe and the Flet pool. Without this, a reader cannot tell steady state from mid-warm-up.

**11. Nit — the existing probe cannot be reused unchanged.** `probe_warmup.py` runs `ft.run(main)` with a real Flet server and `start_dpd_server()`. That opens a port and needs a browser client. A component probe needs no network, per the safety rules. Build a separate harness.

### Goldfish 3 — UX/ergonomics + migration/writes

I read the brief and 8 source files. I ran nothing, and I did not open `config.ini`. Findings are ordered by severity.

**Major: constructing `ToolKit` is not zero-write, and `ToolKit` is the wrong unit to probe.**
- `gui2/toolkit.py:38-100` builds `HistoryManager`, `DailyLog`, `SandhiFileManager`, the `Pass2*` managers and `FilterPresetsManager` in one constructor, and it calls `pre_initialize_gui_data`. `gui2/history.py:54` and `gui2/daily_log.py:48` call `_save()`, which does `mkdir` and writes under `gui2/data`. I did not read the constructors of `DailyLog`, `SandhiFileManager` or the `Pass2*` managers, so I can't say whether they write at construction. `HistoryManager.__init__` only loads the file.
- Fix: the probe builds only the components it measures (`DatabaseManager`, `WordFinderManager`, `AIManager`, `BoldDefinitionsSearchManager`, `SpeechMarkManager`). It never builds `ToolKit` or `App`.
- Add a before/after guard that lists mtimes of `gui2/data`, `gui2/storage` and `shared_data`.
- Run the probe against a copy: `cp` the db into the scratchpad, or run with `DPD_GUI2_ROLE=contributor-server`. A copy also avoids any `-wal`/`-shm` side effects on the live file. I did not check how `ProjectPaths` resolves `dpd_db_path`, so confirm it can be pointed at the copy.

**Major: the db write guard exists only in the contributor role.**
- `db/db_helpers.py:76-82` sets `PRAGMA query_only = ON` only when `is_headless_server()` is true. `PRAGMA journal_mode=WAL` runs first, on every connect.
- `gui2/database_manager.py:314-345`: `get_all_decon_no_headwords` writes the decon cache into `db_info` on a cache miss (`save_decon_no_headwords_cache`). Without the role, `initialize_db` can write to the 2.2 GB db. With the role, the write fails and is swallowed. It prints "decon cache refresh failed", which reads like a normal message.
- `tools/server_mode.py:19-20` falls back to `config_read("gui2", "role")`, which reads `config.ini`. Setting `DPD_GUI2_ROLE=contributor-server` makes `or` short-circuit, so `config.ini` is not read on this path.
- Fix: the probe script must set `DPD_GUI2_ROLE=contributor-server` itself, before any import. It should also assert `PRAGMA query_only` returns 1 on its session. Do not rely on the maintainer exporting the variable.
- Also, a role-guarded run measures an `initialize_db` that skips the cache write. State this in the output.

**Major: `AIManager` reads `config.ini` and starts a thread.**
- `tools/ai_manager.py:77,83` call `config_read("apis", ...)`. The manager builds the claude/codex/gpt providers unconditionally, and `agy` on PATH starts a probe thread.
- Fix: measure it as the import delta plus construction with `PATH` stripped of `agy`. Never print provider dicts or anything config-derived. Block the network, for example with `unshare -n` or a socket-patching wrapper. The brief does not say which. I did not check whether provider constructors make network calls.

**Major: `ulimit -v 1500000` will give false failures and hides the measurement.**
- `ulimit -v` caps virtual address space, not RSS. Python 3.13 plus the flet/SQLAlchemy imports can reach that cap with little resident memory. A component that exceeds it dies with `MemoryError` and no number. The corpus load is the likely one, since it is the biggest.
- The cap means peak and steady memory cannot be separated for exactly the components being ranked.
- Fix: make the brief's single 1.5 GB cap a per-process abort guard. Have the probe poll `psutil` RSS in a thread and call `os._exit` when it crosses 1.5 GB. Print the number before exiting.
- Report three values per component: the RSS delta after import only, the delta after `gc.collect()`, and `VmHWM`.
- Run each component in its own fresh process. The warm-up preload shares allocator state, so the sum of the isolated runs will not equal the 1.25 GB, and the brief's table needs a reconciliation row ("unattributed"). Without one, a tired reader can't turn the table into a choice between A and F.

**Major: the "contributor owns the spell checker" claim and the singleton.**
- `CustomSpellChecker` is a first-caller-wins singleton (`tools/spelling.py:24-33`) and `add_to_dictionary` rewrites a file (`:97`). The probe must never call `add_to_dictionary`. The spell checker needs its own measurement process.

**Minor (Nit): claims in the brief that need re-checking.**
- "~2.5 GB for a second tab" and "old App stays in memory" are comments, not measurements. Treat them as hypotheses.
- `WordFinderManager.__init__` (`tools/wordfinder_manager.py:35`) only loads `cst_file_freq.json`. The brief's "frequency data total ~200 MB" is on-disk size. Memory after `json.load` is typically several times larger, so measure it instead of scaling from disk size.
- `SuttaCentralSource.segment_dict` and `word_dict` (`gui2/books.py:42-69`) are `cached_property`, and `word_dict` is a defaultdict of lists. The growth-per-book measure needs a fixed book order, and must say whether it also builds CST books.
- `SpeechMarkManager.__init__` is read-only. `save()` and `regenerate_from_db`, which `gui2/pass2_add_view.py:697` calls, write `speech_marks.json`. Never call either.

**Minor (Nit): server agent steps.**
- Reading `/proc/<pid>/status` is safe, but "pid of `python gui2/main.py`" is ambiguous when instances for several users run.
- Give the smaller model one literal command: `pgrep -f` matches the wrapper shell. Tell it to take the PID from the unit or from the `--port`-keyed process, and to print `VmRSS` and `VmHWM` only, with no `environ`, which holds secrets.
- Make the probe emit one machine-readable line per component, `component=... rss_mb=... hwm_mb=...`. A final script then ranks A through F, so no model has to do the arithmetic.

## Disposition

| ID | Finding | Severity | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| G1-01 | Earlier work already measured part of it (63 MB bare, +804 MB corpus load, 2026-07-10) | Major | Accept | read 3.3_memory.json and bench_memory.py in kamma/archive/20260710_gui2_perf_and_testing/benchmarks | spec Prior art; plan 0.1 |
| G1-02 | Options B, C, D rankable from known facts; E vs F depends on concurrency and effort, not on MB | Major | Accept in part | reasoning; the fixed-vs-per-user split is still measured, so E is rankable. The ranking table gets an effort/risk column and the owner decides E vs F | spec What it should do 6 |
| G1-03 | Fresh-process-per-component does not reproduce the real split; the old App may stay in memory and inflate 1.25 GB | Major | Accept | read gui2/main.py claim_session comment; tech.md note that Flet keeps a closed session up to an hour | spec 2, 4; plan 2.x, 4.x |
| G1-04 | Probe is brittle if it imports private gui2 internals; keep it out of shipped code | Major | Accept | read bench_common.py (force_throwaway_db_globally patches every get_db_session binding) | spec Constraints; plan 1.1 |
| G1-05 | Book-growth measure is open-ended | Major | Accept | read gui2/books.py (cached_property on module-level sutta_central_books) | spec 3; plan 2.3 |
| G1-06 | 1.25 GB is a single warm reading, not a fresh-start figure | Nit | Accept | read results.md Addendum B | spec 4; plan 4.2 |
| G1-07 | Server agent cannot start a clean instance | Nit | Accept in part | contrib_6 rules were per-thread; this thread lets the agent restart alice's unit, with the maintainer's yes at that step | plan executor rules |
| G1-08 | ulimit -v caps address space, not memory; false failures | Blocker | Accept | systemd-run 255 present, cgroup memory controller listed, user manager running (checked on this machine) | spec Constraints; plan 1.2 |
| G1-09 | 1.5 GB is not a realistic cap for the corpus load; a capped run gives no number | Blocker | Accept | 3.3_memory.json shows the corpus step alone reaches 873 MB RSS; peak not recorded there | spec Constraints; plan 1.2, 2.1 |
| G1-10 | Laptop and server run different workloads (db 2194 MB vs lean build; role; providers; agy) | Major | Accept | ls -l dpd.db; generate_components_server.py drops the frequency steps; ai_manager.py gating read | spec 5; plan 3.x |
| G1-11 | RSS is the wrong metric for option E; sharing needs PSS/USS | Major | Accept | psutil memory_full_info exists; psutil in pyproject | spec 1; plan 1.1 |
| G1-12 | Warm-up peak and steady state are conflated (allocator keeps freed memory) | Major | Accept | reasoning from glibc behaviour; measure before/after gc.collect and malloc_trim | plan 1.1 |
| G1-13 | One run is not trustworthy | Major | Accept | feedback_memory_probe_caps.md says run once; that rule was for unbounded bombs. This probe is capped, so three runs, and the user is told | spec Constraints; plan 1.1 |
| G1-14 | Running loaders on the 8 GB shared server is risky | Major | Accept in part | server db differs (G1-10), so one capped run there is needed. Mitigation: cgroup cap 1.5 GB, alice stopped, 5526 MB available per Addendum B, maintainer's yes | spec 5; plan 3.x |
| G1-15 | Book-growth order and shared state | Major | Merged into G1-05 | same point | - |
| G1-16 | 2.5 GB second-tab claim is unmeasured | Nit | Accept | comment only; becomes a measured hypothesis | spec 4; plan 4.3 |
| G1-17 | Output must record the measured state | Nit | Accept | reasoning | plan 1.1 |
| G1-18 | probe_warmup.py cannot be reused (opens a port, needs a browser) | Nit | Accept | read its first 40 lines | spec Constraints |
| G1-19 | Constructing ToolKit may write files; probe the components, not ToolKit | Major | Accept | toolkit.py constructors read; history/daily_log write on save, not on construction (checked), but the managers differ. Never build ToolKit or App; add an mtime guard | spec Constraints; plan 1.1 |
| G1-20 | db write guard exists only for the contributor role; decon cache commits to db_info | Major | Accept | read db_helpers.py and tools/cache_load.py save_decon_no_headwords_cache (commits when not read-only) | plan 1.1 |
| G1-21 | AIManager reads config.ini and may start a probe thread | Major | Accept | read ai_manager.py 56-100. Phase 0 reads each provider constructor for network or subprocess calls before any run | plan 0.2 |
| G1-22 | ulimit -v caveat (second statement) | Major | Merged into G1-08 | same point | - |
| G1-23 | Spell checker singleton; add_to_dictionary writes a file | Major | Accept | read tools/spelling.py | plan 1.1 |
| G1-24 | Brief claims need re-checking (2.5 GB, disk size vs memory size, SpeechMarks writes) | Nit | Accept | measure, do not scale from disk size; never call save or regenerate_from_db | spec Constraints |
| G1-25 | Server-agent steps: PID ambiguity, no environ, machine-readable lines, ranking script | Nit | Accept in part | unit runs `uv run --no-sync python gui2/main.py`, so MainPID is uv. Accept literal PID command, no environ, JSON lines. Reject the ranking script: ranking needs effort and risk judgement | plan executor rules |

Counts (from the table): 25 raw findings: Blocker 2, Major 16, Nit 7. Accepted 19, accepted in part 4, merged as duplicates 2, rejected 0, escalated 0.

Rejected inside a finding: Goldfish 1's bottom line says to drop the per-component probe and only re-run bench_memory.py. Kept the isolated probe, because the benchmark measured only the corpus, and PSS/USS and an `unattributed` reconciliation row need isolated runs. Goldfish 2's idea of a ranking script (G1-25) is rejected for the reason in its row.

No escalation: every fork had one defensible answer from the repo or from a rule already set by the owner.
