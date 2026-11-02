# Plan: small memory savings for contributor gui2 instances

**Thread:** 20261102_contrib_mem_savings · **Spec:** `spec.md` in this folder (read it first)
**GitHub issue:** #215 · never write to the issue · commits reference `#215`
**Baseline:** `kamma/threads/20261102_contrib_mem_measure/artifacts/results.md` (server: 1,165.9 MB warm, 1,485.0 MB after one `mn` book; laptop isolated costs in `laptop_tables.md`).

## Architecture Decisions

- **Measure first, then a gate, then code.** Stage 1 (Phases 0 to 2) changes nothing in `gui2/` or `tools/`. Phase 3 starts only after the owner picks levers at the gate (task 2.6).
- **Throwaway prototypes, real code later.** `artifacts/lever_probe.py` builds each lever in a fresh process the way the real change would, so the saving is known before the code is touched. It copies the helper ideas of `kamma/threads/20261102_contrib_mem_measure/artifacts/mem_probe.py` (readings, watchdog, cap, db patch, guard). It does not import from that thread: no `sys.path` code.
- **Contributors only.** A lever is switched on by `is_headless_server()` (`tools/server_mode.py`, the same gate `db/db_helpers.py` uses for `PRAGMA query_only`). The desktop keeps today's code path.
- **One plain mechanism per lever.** L1 uses SQLAlchemy `load_only`. L2 uses one column query. L4 uses `sys.intern`. L5 uses one indexed query. No new dependency.
- **Equivalence is part of the number.** A saving counts only when the equivalence check for that lever is clean (`artifacts/equivalence.py`).
- **Memory-heavy comparisons run in two steps**: save the full-corpus outputs to a file once, then run the slim version and diff against the file. One process never holds two corpora.
- **No `git` command in any task.** The owner commits. Checks use `ls`, `find`, `rg` and the scripts.
- **Server only at the end** (Phase 4), through the server agent with the `herdr-remote` skill.

## Who does each step

- `LOCAL AGENT` — an agent in `/home/bodhirasa/MyFiles/3_Active/dpd-db` on the laptop. Runs the capped probe batch after the owner's one yes. Never commits.
- `OWNER` — decides at the gate, commits and pushes, opens the browser for the server steps, says yes to restarts.
- `SERVER AGENT` — the opencode agent on the server (host `epitaka`, pane `w1:p1` in the server's herdr; confirm with `herdr-remote` before sending). The local agent messages it; the owner may also paste.

## Where each task runs

| Phase | Machine |
|---|---|
| 0 Facts and columns | Laptop |
| 1 Write the scripts | Laptop |
| 2 Measure and gate | Laptop |
| 3 Build the chosen levers | Laptop |
| 4 Confirm on the server | Server (needs the owner's push, browser and yes) |
| 5 Results | Laptop |

## Rules for the SERVER AGENT (Phase 4 only)

1. Do only the steps marked `SERVER AGENT`, in order, one at a time. Copy each command exactly.
2. After each step check it against EXPECT. On a mismatch: STOP, write the command and its output in `~/mem/results_savings.md`, tell the owner, and try no fix.
3. Append results only to `~/mem/results_savings.md`. Never edit files inside `~/dpd-db` by hand.
4. Never print, open or grep `config.ini`, any `.env`, any htpasswd file or `/proc/<pid>/environ`.
5. `git pull` in `~/dpd-db` is allowed once, in task 4.2, and no other git command.
6. Restart or stop `dpd-gui@alice` only when the task says so and the owner has said yes. Space restarts at least 60 s apart.
7. Never use `pkill`, `killall` or `kill -9`. Never touch `~/epitaka-translator`.

---

## Phase 0 — Facts and columns (read-only) — WHO: LOCAL AGENT

- [x] 0.1 **Column map.** Write `artifacts/notes.md` with: (a) the 59 `DpdHeadword` columns from `db/models.py`, each marked `loaded` or `deferred` by `gui2/database_manager.py:181-204`; (b) the bytes per column (re-run the read-only size query of the spec on `dpd.db` with `mode=ro`); (c) `SearchType` values in `tools/wordfinder_manager.py`; (d) the exact columns `inflections_list_all` reads (`db/models.py`, search `def inflections_list_all`); (e) every caller of `load_corpus` and of the corpus list (`rg -n "load_corpus\(|_db_entries" gui2 tools --type py`).
      → verify: `notes.md` lists 59 columns with a flag each; the byte sizes for `freq_html` and `inflections_html` match the spec (694.9 and 265.0 MB, ±1 %); every line cites `file:line`.
- [x] 0.2 **Check the spec's "verified" lines still hold** against the current tree (another session may have changed a file). Re-read the cited lines; list any that moved or changed in `notes.md` under "Drift". Fix the spec at once if one is wrong.
      → verify: `notes.md` has a "Drift" heading with "none" or the corrections, and `spec.md` is updated for each correction.

## Phase 1 — Write and test the scripts — WHO: LOCAL AGENT

Run every command from `/home/bodhirasa/MyFiles/3_Active/dpd-db`. Other sessions share the tree: write only in `kamma/threads/20261102_contrib_mem_savings/` in this phase. Every script: type hints, `Path` not `os.path`, `ic` not `print` for debugging, no `sys.path` code, stdlib and `psutil` at the top, repo imports inside functions.

- [x] 1.1 **Find the columns the contributor consumers need.** Write `artifacts/find_columns.py --db <copy> --out <md>`. It loads the corpus with `load_only(<candidate columns>)` plus `raiseload("*")`, then runs, on that corpus: (1) `RelationshipDetector(rows)` and `find_synonyms` plus `find_phonetic_variants` on 2,000 sample headwords (fixed seed, including rows with empty `meaning_1`, multi-meaning rows and rows with empty `freq_data`); (2) the body of `make_inflections_lists` (`inflections_list_all` and `meaning_1`). On each `InvalidRequestError` that names a column, it adds the column and reruns, until a run raises nothing. Output `artifacts/columns.md`: the final set `S`, which consumer needs each column, and whether `S` still works without `freq_data`.
      → verify: `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright <file>` clean; running it ends with "0 raises" and `columns.md` lists `S`. If `freq_data` is needed, `columns.md` says on which path (`tools/synonym_variant.py:351-358`) and how many sample rows hit it.
- [x] 1.2 **Write the lever probe.** `artifacts/lever_probe.py` with: `--variant <name> --db <copy> --out <jsonl>` (one variant per process, readings at each step as in the earlier probe: RSS, PSS, USS, VmHWM, VmSwap, threads, plus `gc.collect()` and `malloc_trim` readings), `--all --db <copy> --out <jsonl>` (driver: a throwaway run, then 3 runs of every variant, 3 more for a variant whose spread is over 10 %, one system cap of 1.5 GB per process, a watchdog at 1.4 GB, a total limit of 40 minutes, stop on the first `capped`, `killed` or `error`), `--report <jsonl> --out <md>` (median, min, max, saving against the matching baseline), `--selftest`. The child sets `DPD_GUI2_ROLE=contributor-server`, `DPD_GUI2_USERNAME=memprobe`, a temp `DPD_GUI2_DATA_DIR`, patches every `get_db_session` to the copy before any engine is built, asserts `PRAGMA query_only` is 1, and records the guard (modification times of `gui2/data`, `gui2/storage`, the temp dir; warning for `shared_data`). Variants (each includes `bare` and `imports` readings first; delta = reading after minus reading before):
      - `corpus_full` — real `DatabaseManager.load_corpus()` (baseline).
      - `corpus_slim` — same query with `load_only(S)` from `columns.md`.
      - `corpus_slim_nofreq` — `S` without `freq_data`, only if 1.1 allows it.
      - `infl_today` — `corpus_full` then the real `make_inflections_lists()`.
      - `infl_direct` — no corpus; one query for `inflections`, `inflections_api_ca_eva_iti` (the columns from 0.1(d)) into `all_inflections` only.
      - `infl_direct_both` — same, plus the missing-meaning set.
      - `infl_none` — no set at all (the ceiling for L5).
      - `wordfinder_today` — real `WordFinderManager()`.
      - `wordfinder_interned` — the same load, then every word string replaced by `sys.intern(word)` in all per-file dicts (same keys and counts).
      - `detector_full` — `corpus_full` then the real `get_relationship_detector()`.
      - `detector_slim` — `corpus_slim` then `RelationshipDetector` on those rows.
      - `contributor_today` — the contributor staircase: imports, `db_manager`, `initialize_db`, corpus, inflection sets, word finder, AI manager (with `agy` removed from `PATH`), bold search, detector, spell checker.
      - `contributor_levers` — the same with slim corpus, direct inflection sets and interned word finder.
      - `contributor_lazy` — `contributor_today` without AI manager, bold search and detector (the ceiling for L6).
      - `corpus_reload` — `corpus_full`, then the real `get_relationship_detector()`, then `mark_corpus_stale()` and `load_corpus()` again: what a click on Pass1Add "refresh DB" does (`gui2/pass1_add_view.py:243-246`). Also `corpus_reload_slim` with the slim corpus. Notes in `notes.md`, "Finding".
      DRIFT 2026-11-02 (built differently from the list above; the behaviour in `spec.md` is unchanged):
      - The probe has 19 variants, not 14. Names: `corpus_full`, `corpus_slim`, `corpus_slim_nofreq`, `sets_today`, `sets_today_slim`, `sets_direct`, `sets_direct_both`, `detector_full`, `detector_slim`, `wordfinder_today`, `wordfinder_interned`, `reload_full`, `reload_slim`, `contributor_today`, `contributor_levers`, `contributor_levers_l5`, `contributor_lazy`, `warm_today`, `warm_levers`. The `*_slim` steps load with `load_only` and mark the corpus fresh, so `sets_today` and `detector` then use the slim rows, as the real change would.
      - `infl_none` is gone: its saving is the cost of `sets_direct` (the set itself). `contributor_levers_l5` is the composite without any set.
      - `warm_today` and `warm_levers` are the warm-up state (no inflection sets), to carry the saving to the server's warm figure; `contributor_*` is the state after Pass1 has built the sets.
      - The step names are labels: `step_delta(row, label)` is the reading with that label minus the reading before it.
      - The run count is 19 variants × 3 = 57 processes plus a warm-up (more for a variant with spread over 10 %). Task 2.1 asks for the yes with that number.
      - The database copy already exists from the earlier thread (made 2026-11-02, 89,774 headwords, same as the live file). Task 2.1 re-checks the count instead of copying again.
      AI provider objects are built as in the earlier probe (no network call in any constructor; see `kamma/threads/20261102_contrib_mem_measure/artifacts/notes.md`).
      → verify: lint and type check clean (`uv run pyright <file>`); `PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_savings/artifacts/lever_probe.py --selftest` prints `SELFTEST_OK`; with the cap raised to 5000 the cap check prints `SELFTEST_FAIL`; restored, `SELFTEST_OK`.
- [x] 1.3 **Write the equivalence script.** `artifacts/equivalence.py --db <copy> --step <full|slim|compare> --out <dir>`. `full` runs today's code on the sample and saves the results as JSON: (a) detector synonym and phonetic lists for the 2,000 sample headwords; (b) today's `all_inflections` as a sorted list; (c) the word finder results for 50 fixed queries of each `SearchType` (best-covered words from the CST word list). `slim` redoes (a) on the slim corpus, (b) from the direct query, (c) on the interned word finder, and saves them. `compare` diffs the two and prints PASS or FAIL with counts and 10 examples. A further check `lookup`: the number of words in `all_inflections` not found in `lookup` with a non-empty `headwords` column, the number the other way round, and the per-query time (median and total seconds) over 10,000 distinct words from `make_cst_text_list(["an1"], dedupe=True)`.
      → verify: lint and type check clean; `--step compare` on two identical files prints PASS; on a file with one value changed by hand prints FAIL with that value.
- [x] 1.4 **Phase check.** `rg -l "lever_probe|find_columns|equivalence" gui2 tools` prints nothing; `ls kamma/threads/20261102_contrib_mem_savings/artifacts` lists exactly `notes.md`, `columns.md`, `find_columns.py`, `lever_probe.py`, `equivalence.py`.
      → verify: both outputs as stated.

## Phase 2 — Measure and gate — WHO: LOCAL AGENT, OWNER at 2.1 and 2.6

- [x] 2.1 **WHO: LOCAL AGENT asks, OWNER answers once.** Through the question tool: 19 variants × 3 fresh processes (more for a point with spread over 10 %), one at a time; each capped at 1.5 GB by the system and 1.4 GB by the probe; stops after 40 minutes or on the first capped, killed or error row; reads a `.backup` copy of the database made in the session scratchpad (about 2.3 GB), never the live file; no network; writes only in this folder and temp dirs. Then run `sqlite3 dpd.db ".backup <SCRATCH>/dpd_copy.db"` (print the full scratchpad path) and check the headword counts match.
      → verify: `sqlite3 <SCRATCH>/dpd_copy.db "select count(*) from dpd_headwords"` equals the same query on `dpd.db`.
- [x] 2.2 **Find the columns, then smoke-test.** Run `find_columns.py` on the copy and fix `columns.md` into the variant list. Then run `lever_probe.py --variant corpus_full` once and `--variant corpus_slim` once.
      → verify: the `corpus_full` row is `ok` with a corpus delta within 5 % of 676.4 MB (the earlier thread's value); `query_only` is 1 in the meta; the guard reports no change in `gui2/data` and `gui2/storage`.
- [x] 2.3 **Run the batch.** `PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_savings/artifacts/lever_probe.py --all --db <SCRATCH>/dpd_copy.db --out kamma/threads/20261102_contrib_mem_savings/artifacts/laptop.jsonl` (in the background with `timeout 2700`; do not poll).
      → verify: every variant has 3 `ok` rows (a capped, killed or error row is the finding; the owner decides on a higher cap); the guard says no change; `ps --sort=-rss -eo pid,rss,cmd | head -5` shows no stray python.
- [x] 2.3b **Second batch: one lever at a time (added 2026-11-02 after batch 1).** Batch 1 (`laptop.jsonl`, 57 rows, all ok, no guard change) matched the earlier staircase (`contributor_today` 1,386.3 MB against 1,385.6 MB) but its step-by-step deltas disagreed with its whole-build totals, because the allocator reuses memory between steps. Three hypotheses failed: direct sets (L2) cost 276 MB against 234 MB, so the cost is the set, not cached lists; the interned word finder (L4) cost 30 MB more, because Python's JSON loader already shares repeated keys; and the refresh does not double the corpus (+172 MB, the session reuses the objects the detector holds). So judge every lever on a whole build, one change at a time. New variants: `corpus_slim_noinfl`, `warm_slim`, `warm_slim_noinfl`, `warm_slim_nofreq`, `warm_interned`, `contributor_slim`, `contributor_sets_direct`. Run only these: `PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_savings/artifacts/lever_probe.py --all --only corpus_slim_noinfl,warm_slim,warm_slim_noinfl,warm_slim_nofreq,warm_interned,contributor_slim,contributor_sets_direct --db <SCRATCH>/dpd_copy.db --out kamma/threads/20261102_contrib_mem_savings/artifacts/laptop.jsonl`. Needs the owner's yes (21 processes plus a warm-up, same caps).
      → verify: every new variant has 3 `ok` rows; guard clean; no stray python.
- [x] 2.3c **Third batch (added 2026-11-02 after batch 2 and the first equivalence run).** Batch 2 (`laptop.jsonl`, 78 rows, all ok) settled: L1 slim corpus saves 137 MB; direct sets save 72 MB (of which about 41 MB is dropping the unused second set); the interned word finder costs 27 MB (dropped); no set at all saves 272 MB. The first equivalence run (`equivalence.md`) showed: the detector on the slim corpus, the direct set and the word finder are identical to today's; but the `lookup` table is **not** a replacement for the set (the set holds 1,627,687 words, the table 459,013 keys with headwords; 1,181,761 set words are not in the table; 1 of 1,402 words of a real text answered differently). So L5 is dropped as written. Two new levers: **L7b** load `freq_data` only for headwords with an empty meaning (the detector reads it only there, `tools/synonym_variant.py:351-353`; exact), and **L8** a compact set (sorted array of 64-bit hashes, 8 bytes per word, same answers up to a hash collision). New variants: `corpus_slim_split`, `sets_hash`, `warm_slim_split`, `contributor_hash`, `contributor_split_direct`, `contributor_split_hash`. New equivalence steps: `detector_split` and `sets_hash` (every member answers yes, 200,000 non-members answer no). Run: `lever_probe.py --all --only corpus_slim_split,sets_hash,warm_slim_split,contributor_hash,contributor_split_direct,contributor_split_hash` then `equivalence.py --step detector_split`, `--step sets_hash`, `--step compare`. Needs the owner's yes (18 processes plus a warm-up, and 3 equivalence processes, same caps).
      → verify: every new variant has 3 `ok` rows; `equivalence.md` has lines (d) and (e) with PASS or FAIL; guard clean; no stray python.
- [x] 2.4 **Run the equivalence checks.** `equivalence.py --step full`, then `--step slim`, then `--step compare`, then the `lookup` check, each in its own process, each under the same 1.5 GB cap.
      → verify: a PASS or FAIL line for each of (a), (b) and (c), and the lookup counts and timing, saved in `artifacts/equivalence.md`.
- [x] 2.5 **Make the table.** `lever_probe.py --report artifacts/laptop.jsonl --out artifacts/lever_results.md`: one row per lever with the saving in MB (median, min–max), the start-up peak, the equivalence result, and the three composed variants (`contributor_today`, `contributor_levers`, `contributor_lazy`). Add effort and risk columns by judgement and say so. Add the estimate for 3, 8 and 16 contributors from the earlier thread's formula (baseline 1,066 MB plus N × per-instance).
      → verify: every lever L1 to L6 has a row; every number is quoted from `laptop.jsonl` or `equivalence.md`; the saving of each lever is checked against the composed variants (the sum of single savings may exceed the composed one: say by how much).
- [x] 2.6 **GATE — WHO: OWNER decides.** Present the table in plain words. Ask through the question tool which levers to build (the proposal: every lever with a saving of at least 100 MB and a clean equivalence). Ask separately whether to drop `all_inflections_missing_meaning` (it has a test and no reader). Write the answers in `artifacts/decision.md`. Update `spec.md` and `plan.md` Phase 3 to the chosen levers.
      → verify: `artifacts/decision.md` exists and lists each lever as BUILD or SKIP with the owner's reason; Phase 3 below holds only the BUILD levers.

## Phase 3 — Build the chosen levers — WHO: LOCAL AGENT (after the gate only)

Tasks 3.1 to 3.6 are written now for every lever and pruned at the gate. Each: write the test first and watch it fail, make the change, then run the checks in 3.7. Contributor-only gate: `is_headless_server()` from `tools/server_mode.py`.

> DRIFT 2026-11-02 (Phase 3 as built; `artifacts/decision.md` has the gate):
> - 3.1 became the **split contributor corpus** (L1 + L7b): `DatabaseManager._load_contributor_corpus` in `gui2/database_manager.py`, 14 columns, plus `freq_data` only for headwords with an empty `meaning_1`.
> - 3.2 became the **compact sets** (L8): new `tools/hashed_words.py` (`HashedWords`) and `DatabaseManager._make_contributor_inflections_lists`. Both inflection sets are kept (the unused one too).
> - Both switch on `is_headless_server()` (`tools/server_mode.py`); the desktop path is unchanged.
> - Tests: `tests/tools/test_hashed_words.py` (new) and 8 new tests in `tests/gui2/test_database_manager_corpus.py`. 31 pass. Revert check: contributor branches off, 3 new tests fail; hash lookup broken, 5 tests fail.
> - 3.3 to 3.6 skipped. 3.7 is partly done (ruff and pyright clean on the 4 touched files, 31 tests pass); the wider checks are still to run. 3.8 and Phases 4 and 5 are to do.

- [x] 3.1 **L1 slim corpus.** In `gui2/database_manager.py`, `load_corpus` loads only `S` (from `columns.md`) when `is_headless_server()` is true; otherwise the query is unchanged. Tests in `tests/gui2/test_database_manager_corpus.py`: (a) contributor role — the dropped columns are in `sqlalchemy.inspect(row).unloaded`; the kept ones are not; (b) desktop role — only the five deferred columns are unloaded; (c) the detector gives the same synonym list on slim and full rows for a small fixture.
      → verify: `uv run pytest tests/gui2/test_database_manager_corpus.py`, all pass; revert the change, run again, report how many fail (expect (a) and nothing else, or the tests are too loose).
- [x] 3.2 **L2 direct inflection sets.** `make_inflections_lists` builds `all_inflections` (and the missing-meaning set unless 3.3) from one column query, not from objects, when `is_headless_server()`. The existing test must still pass for the desktop role and gain a contributor-role twin with the same assertions (`tests/gui2/test_database_manager_corpus.py:196-203`).
      → verify: both tests pass; revert check as in 3.1.
- [x] 3.3 (SKIPPED at the gate, see decision.md) **L3 drop the dead set (only if the owner said yes).** Remove `all_inflections_missing_meaning` from `gui2/database_manager.py:75,356-363` and its assertions at `tests/gui2/test_database_manager_corpus.py:202-203`. This removes behaviour that the code has: only do it on the owner's word.
      → verify: `rg -n "all_inflections_missing_meaning" gui2 tools tests` prints nothing; related tests pass.
- [x] 3.4 (SKIPPED at the gate, see decision.md) **L4 interned word finder.** In `tools/wordfinder_manager.py`, `load_cst_file_freq` returns the same data with one string per word (`sys.intern`). Applies to everyone if the equivalence check is clean (the data is identical, so there is no behaviour to keep apart); say so at the gate. Test: the dict equals the plain `json.load` result, and two files that share a word hold the same string object (`is`).
      → verify: new test mirroring `tools/wordfinder_manager.py` (check `ls tests/tools` first; create `tests/tools/test_wordfinder_manager.py` if absent) passes; revert check as in 3.1.
- [x] 3.5 (SKIPPED at the gate, see decision.md) **L5 lookup instead of a set (only if chosen).** Add a `DatabaseManager` method that asks `lookup` whether a word is a headword inflection; `Pass1AutoController.is_missing` (`gui2/pass1_auto_controller.py:273`) uses it when `is_headless_server()`. Test with the fixture db: same answers as the set for known and unknown words.
      → verify: `uv run pytest tests/gui2/test_pass1_auto_controller.py tests/gui2/test_database_manager_corpus.py` pass; revert check.
- [x] 3.6 (SKIPPED at the gate, see decision.md) **L6 lazy managers (only if chosen).** Remove the manager lines from the warm-up in `gui2/main.py:571-579` that the table says are worth it, for contributors only. Test in `tests/gui2/test_main.py` if the warm-up is testable; otherwise state how it was checked.
      → verify: tests pass; start-up readings in Phase 4 confirm.
> 3.7 result 2026-11-02: `uv run pytest tests/gui2 tests/tools`: 1433 pass, 2 fail. `just typecheck`: 0 errors.
> PRE-EXISTING — NOT CAUSED BY THIS THREAD: `tests/tools/test_configger.py::test_profile_matches_original_script_writes[uposatha_reset]` — expects `make_mobile` `no`, gets `yes` (`tools/configger.py` last changed in commit 7a0d638b, 2026-11-01, not touched here).
> FLAKY UNDER LOAD, NOT THIS THREAD: `tests/tools/test_tipitaka_db_deadline.py::test_four_ordinary_searches_at_once_do_not_time_each_other_out` — fails at load average 15, passes when run alone.

- [x] 3.7 **Phase check.** For every touched file: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright <file>` (for `gui2/` and `tests/`: `uv run pyright --project /dev/null <file>`). Then `uv run pytest tests/gui2` and the tests of every touched `tools/` file, and `just typecheck`. Note any test that was broken before.
      → verify: all clean; if `ruff format` rewrites many unrelated lines, revert that file's format and re-apply the edit without it.
> 3.8 result 2026-11-02: `contributor_real` 3 runs, all ok, no guard warnings, `query_only` 1: 909.0, 909.1, 908.9 MB (median 909.0). Prototype `contributor_split_hash` 904.6 MB. Difference 4.4 MB (0.5 %), inside 5 %. Today's build (`contributor_today`) 1,386.3 MB. Rows are in `artifacts/laptop.jsonl`.

- [x] 3.8 **Confirm the real code matches the prototype.** Add the variant `contributor_real` to `lever_probe.py` (real `DatabaseManager` in contributor role plus real managers) and run it three times under the cap.
      → verify: its total is within 5 % of `contributor_levers` from Phase 2; if not, find which lever differs before Phase 4.

## Phase 4 — Confirm on the server — WHO: OWNER, LOCAL AGENT, SERVER AGENT

- [ ] 4.1 **WHO: OWNER.** Commit the thread (the local agent suggests the message) and push. The server pulls from `origin`.
      → verify: `git log -1 --format=%h` on the laptop and the server show the same commit (the server agent reports its own in 4.2).
- [ ] 4.2 **WHO: SERVER AGENT.** Via `herdr-remote`: confirm the pane (`herdr pane read w1:p1` through `ssh epitaka '/root/.local/bin/herdr pane read w1:p1'`; the agent must be idle), then send: "Run `cd ~/dpd-db && git pull` once, then `git log -1 --format=%h`. Append the output to `~/mem/results_savings.md`. No other git command."
      → verify: the agent's report shows the same commit as the laptop; `git status --porcelain` on the server is clean apart from `?? ` files it already had.
- [ ] 4.3 **WHO: SERVER AGENT, owner's yes first.** Fresh start in phases, as task 3.4 of the earlier thread. The owner confirms alice has no unsaved input and says yes. One step at a time. Each reading is `cd ~/dpd-db && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ~/.local/bin/uv run --no-sync ~/mem/mem_probe.py --unit-readings dpd-gui@alice --label <label> >> ~/mem/readings_savings.jsonl`:
      1. Agent: `sudo systemctl restart dpd-gui@alice; sleep 15`, reading `plus15s`.
      2. Owner opens `https://187-126-118-33.sslip.io/alice/`, tells the agent when "Database loaded." shows. Reading `db_loaded`.
      3. Owner tells the agent when "All tabs and tools ready." shows. Reading `warmup_done`.
      4. Owner opens Pass1Auto and the book `mn` (Run, let one pass finish or press Stop), tells the agent. Reading `one_book`.
      5. Owner opens Pass1Add (the word finder loads there) and tells the agent. Reading `pass1add`.
      **EXPECT:** five readings. If a reading is lower than the one before it, or the unit restarts by itself: STOP.
- [ ] 4.4 **WHO: SERVER AGENT.** Append a table of the five readings to `~/mem/results_savings.md` under `## 4.3`, with the earlier thread's values beside them (86.5, 718.6, 1,165.9, 1,485.0).
      → verify: the section exists.
- [ ] 4.5 **WHO: OWNER.** Copy back: `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && mkdir -p kamma/threads/20261102_contrib_mem_savings/artifacts/server && rsync --bwlimit=400 -r epitaka:mem/results_savings.md epitaka:mem/readings_savings.jsonl kamma/threads/20261102_contrib_mem_savings/artifacts/server/`. (The local agent can run this when the owner says so.)
      → verify: `ls artifacts/server/` lists the two files.

## Phase 5 — Results — WHO: LOCAL AGENT

- [ ] 5.1 **Write `artifacts/results.md`:** the lever table (saving per lever, equivalence, built or skipped), the before and after server readings, the new projection for 3, 8 and 16 contributors (baseline 1,066 MB plus N × the new per-instance figure), and what is left (option E when there are more than 8 contributors). Say what the new per-instance figure is for one book and for the Pass1Add case.
      → verify: every number is quoted from `laptop.jsonl`, `equivalence.md`, or `artifacts/server/`; the before values equal those in the earlier thread's `results.md`.
- [ ] 5.2 **Done check.** Re-read "How we'll know it's done" in `spec.md`; mark items 1 to 5 met or not met in `results.md`, each pointing to the file that proves it.
      → verify: five lines, each with a file path.
- [ ] 5.3 **WHO: OWNER.** Commit the results. Run `/kamma:3-review`, then `/kamma:4-finalize`.
      → verify: `ls kamma/threads/20261102_contrib_mem_savings/artifacts` lists `results.md`, `lever_results.md`, `decision.md` and `server/`.
