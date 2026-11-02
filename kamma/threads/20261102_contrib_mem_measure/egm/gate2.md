# Gate 2 — spec review (2026-11-02)

Backend: native subagents (`Agent`, general-purpose); same backend as Gate 1, no new smoke probe needed. Two Goldfish. No failed run.

## Raw findings

### Goldfish 1 — comprehension (naive reader)

**Restatement.** The thread writes a throwaway probe script, `mem_probe.py`, that measures the memory of one contributor gui2 instance. It takes isolated per-component readings, each in a fresh process, and one `staircase` run in start-up order. It adds server-side readings through a server agent, then writes `results.md` with a table and a ranking of options A to F. Several points stalled me.

**Blocker**

1. **"Phase 0" and "the plan's tasks" don't exist.** Spec lines 70, 81, 101, 157 and 164 rely on "Phase 0" and "this plan's tasks". The thread folder holds only `spec.md` and `egm/`; there is no `plan.md`. Phase 0 does real work: it picks the books, decides which AI providers get measured "by import only", and chooses the server book. A fresh implementer can't tell what Phase 0 is or when it runs. Fix: say "Phase 0 is defined in plan.md" and write that plan first, or inline the Phase 0 steps.

2. **The server side has no commands.** Section 4 names no host or access method, and no unit name beyond "alice's unit". Line 104 says "the same `staircase` run under the same cap" on the server, but not how `mem_probe.py` gets there or where its db copy comes from. The "server agent" is undefined: who or what is it, and what does it run? Line 157 says it "runs only the commands in this plan's tasks", which brings back the missing plan. Fix: list the exact commands, the user the probe runs as, the db copy source, and the output location.

**Major**

3. **The `capped` outcome is only half defined.** Line 69 lists `ok` or `capped`, and line 82 says the watchdog prints its last reading and calls `os._exit` at 1.4 GB. The spec doesn't say what a capped row contributes to the table. Does the median use it? Is its delta a lower bound? What if one of three runs is capped? What if the watchdog fires but the cgroup kills first (`MemoryMax` 1500M, `MemorySwapMax=0`) and no line is printed? Fix: define the row format (`capped`, last RSS, point reached), say a capped point is excluded from the median and reported as "greater than X", and say how a SIGKILL with no output is classified.

4. **The staircase versus isolated delta isn't operational.** Line 74 says the gap is "expected: shared imports are counted once". It doesn't define an isolated delta. Is it that point minus `imports`, or minus `bare`? The `wordfinder` row says only "loads `cst_file_freq.json`". Does `ai_manager` in isolation import the SDKs, so that it double-counts them? And `staircase` includes `book:<name>`: which books, and in what order relative to the other steps? "Real start-up order" is not given. The warm-up list was verified, but its steps are not listed. Fix: write out the staircase step order and the delta formula.

5. **The `unattributed` row is defined two ways.** Line 74 defines it as the staircase total minus the sum of the isolated deltas. Line 111 defines it as server warm RSS minus the sum of isolated deltas. The 20 % trigger applies to "warm RSS", which could be either. Fix: use one definition, or two named rows with the trigger tied to one.

6. **The server's contributor environment is not stated.** Line 138 verifies `DPD_GUI2_ROLE` and `PRAGMA query_only`. `db/db_helpers.py:74` sets the pragma through an engine `connect` listener. The `_engine_cache` is keyed by the resolved path, so patching `get_db_session` to a copy path must happen before the first engine is built. This ordering is not stated. The tests also don't say whether `DPD_GUI2_USERNAME` or `DPD_GUI2_DATA_DIR` are set. If not, `gui2/data/` may be touched by `UserPaths`. Fix: list the env vars the probe sets (`tech.md:91` names them) and the required order.

7. **The output table's columns lack definitions.** "Private or shareable across users" has no criterion. It could be a smaps `Shared_*` versus `Private_*` reading, or a judgement about whether option E could share it. "Staircase delta" per component is not defined for `book:<name>`. The 8 and 16 contributor figures are unspecified: which fixed baseline, whether OS, nginx and `uv` (22 MB) overhead is included, and how many GB available. Line 111's headroom isn't given either.

8. **The ranking's "MB saved per instance" has no method.** B, C, D and F are defined only by a single line each. Saving from C needs a measurement of the in-memory set versus a lookup query, which no measured point provides. D needs the frequency JSON cost, which only the `wordfinder` point gives. F saves nothing per instance. Fix: map each of A to F to the measured point that yields its figure, and say "n/a, effect only at N online" for F.

**Nit**

9. **"Median of 3 plus a throwaway warm-up"** (line 71) does not say whether the warm-up is per point or once overall, and "A" is the measurement itself, so ranking it makes no sense.

10. **The "sum of isolated deltas" for the 8 and 16 user comparison** isn't weighed against a server whose lean build may be lighter (lines 103 and 149). Which db (laptop or server) feeds the headline numbers is unstated.

11. **Dangling citations.** `egm/gate1.md` is cited (lines 124 and 182). I did not check it exists. Line 80's `gui2/storage/` is not confirmed. Line 78 cites `db/db_helpers.py:~76`, while the actual code is at line 74-78.

12. **A repeated rule conflict.** Line 83 says "one at a time", while line 71 asks for 3 runs of each of about 20 points. The count of laptop commands the user must run is never stated. It is at least 60 runs unless a driver script exists, and the spec doesn't say whether one does.

### Goldfish 2 — design critic

**Findings (spec.md, read against source)**

1. **Major: the staircase omits the largest per-user cost, so "what does one extra user cost" is not answered.**
   - The warm-up in `gui2/main.py:558-587` builds every tab view, then the wordfinder, popup, AI manager, bold search and detector.
   - The probe builds no `App`, tabs or Flet controls (spec line 42). The spec admits the Flet per-session cost is "unattributed" (line 152).
   - That unattributed remainder is the thing that scales with users. Step 4.2's server reads can't isolate it either: the db load starts on page connect (`main.py:540-556`), so "after the page opens" lumps corpus, tabs and Flet together.
   - Fix: add server reads at "page connected, before db load finishes" and after each warm-up phase. Alternatively run the probe's `App` build with a stub page.

2. **Major: PSS/USS cannot show what is "shareable across users" (E).**
   - Each user is a separate process, so a lone process has PSS close to RSS. The spec's column "private or shareable across users" (line 108) is therefore not measured. It is a code-semantics judgement.
   - Nothing in the spec checks whether the corpus can be shared. `DatabaseManager` holds per-user mutable state: `_own_edits` (`database_manager.py:56`), `sandhi_ok_list` (:77-84), and `mark_corpus_stale` after writes (:206).
   - Line 173 says gui2 "cannot host two" sessions. That is true within one process. Two processes on the server can run, and the real marginal cost is USS plus shared libs. Measure a second instance, or at least the `shared_clean` part of `smaps_rollup`.
   - Fix: classify each component as read-only or per-user by reading the code, and say so in the table.

3. **Major: the "contributor role skips the decon write" note is only true on a cache miss.**
   - `get_all_decon_no_headwords` (:321-343) returns early on a cache hit. It writes only on a miss, and a swallowed failure ends in `rollback()`.
   - A `.backup` copy of the laptop db likely has a warm cache, so that path is never exercised. It also differs from the lean server db.
   - Fix: record cache hit or miss per run.

4. **Major: the probe does not reproduce the real contributor instance.**
   - A bare `DatabaseManager()` has `_own_edits=None`, so the lemma additions at :218-222 and the per-user sandhi list are skipped.
   - Wiring `own_edits` needs per-user files, which the probe is forbidden to touch.
   - Fix: state the divergence, or feed a synthetic edits callable.

5. **Major: patching the db copy is under-specified.**
   - `database_manager.py:14` imports `get_db_session` by name. Patching `db.db_helpers` alone misses it. The same applies to every other module that imports the name.
   - `_engine_cache` keys on the resolved path (`db_helpers.py:~58`). The spec doesn't say whether it patches the cache or the function.
   - The detector worker (:827) also calls `get_db_session` directly.
   - Fix: list the patch targets, and assert `query_only` from the engine the loader actually uses.

6. **Major: the server capped run (step 4.5) is likely `capped`, and under-protected.**
   - The staircase adds wordfinder, books and so on to 1.25 GB, against a 1.4 GB watchdog. It will probably be killed before it yields a number.
   - Step 4.5 does not repeat the db-copy, role, query_only or mtime guards. It would run against the live lean `dpd.db`.
   - `systemd-run --user` with `MemoryMax` needs a delegated memory controller in that user manager. This was verified locally (line 144), not on the server.
   - Fix: run a reduced staircase (no books) on the server, copy the db, require the same guards, and probe cgroup delegation first.

7. **Major: server steps 4.2 and 4.3 can hurt alice.**
   - Restarting her unit destroys the warm state, including any unsaved form input. Only the maintainer's yes is required, not alice's, and no time window is given.
   - Three reloads on her production instance may leave stale `App`s alive for an hour (`main.py:676`). That leaves the instance heavier afterward, on an 8 GB box with 5.5 GB available.
   - Fix: use a scratch contributor unit, not alice's. Say how the leak is cleaned up (restart).

8. **Major: the run count contradicts the user rule.**
   - Roughly 12 points × (3 + 1 warm-up) plus 4 books × 4 plus staircase × 3 comes to about 70 processes. "Tell the user before each run" (line 83) means about 70 confirmations.
   - Fix: one driver script with one upfront confirmation and a hard total timeout, and no laptop-load check between runs beyond the recorded load average.

9. **Minor: the `spellchecker` point is a trap.**
   - `CustomSpellChecker.add_to_dictionary` (`tools/spelling.py:90-100`) writes `user_dict_path`. The spec bans it but covers only `gui2/data/`, `gui2/storage/` and `shared_data/`.
   - Fix: add the `user_dict_path` location to the mtime guard.

10. **Minor: `ai_manager` with `agy` stripped from PATH does not mirror the server.** Whether `agy` exists there is unknown. The flag is recorded, but the result is not comparable.

11. **Nit: the "median of 3" rule is not tied to variance.** There is no stated tolerance for deciding when the runs agree.

12. **Nit: `imports` has no defined list.** It says "modules gui2 imports at start", but gui2 imports lazily in places.

13. **Nit: the book cost depends on which books are open.** It is not in the 8/16 projection formula. State a per-user book assumption.


## Disposition

| ID | Finding | Severity | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| G2-01 | Phase 0 and the plan's tasks are cited but plan.md does not exist | Blocker | Accept | confirmed: thread folder had only spec.md and egm/ | plan.md written next; spec points to its Phase 0 |
| G2-02 | Server side has no host, unit, user, copy method or commands | Blocker | Accept | spec section 4 had none | spec 4 now names host, unit, user, copy and output locations; commands in plan |
| G2-03 | `capped` outcome only half defined (median, one of three capped, cgroup kill with no output) | Major | Accept | reasoning | spec 1 defines the capped row |
| G2-04 | Isolated delta and staircase order not defined | Major | Accept | gui2/main.py:558-587 warm-up order read | spec 1 formulas and order |
| G2-05 | `unattributed` defined two ways | Major | Accept | spec lines read | spec 5 splits into `interaction gap` and `unbuilt remainder` |
| G2-06 | Env vars and the order of patching the db not stated | Major | Accept | gui2/paths.py:70-95 read (DPD_GUI2_DATA_DIR, per-user paths) | spec 2 |
| G2-07 | Output columns lack definitions; 8/16-user baseline unstated | Major | Accept | results.md pre-state: 1066 MB used with no gui2 | spec 5 |
| G2-08 | Ranking has no method per option | Major | Accept | reasoning | spec 5 maps each option to a measured point |
| G2-09 | Warm-up per point or once; option A makes no sense in a ranking | Nit | Accept | reasoning | spec 1, 5 |
| G2-10 | Which db feeds the headline numbers | Nit | Accept | reasoning | spec 5 |
| G2-11 | Dangling citations (egm/gate1.md, gui2/storage, db_helpers line) | Nit | Accept | gate1.md exists; gui2/storage exists; db_helpers read at lines 74-82 | spec 2 line refs fixed |
| G2-12 | Run-count contradicts the 'tell the user before each run' rule | Nit | Merged into G2-20 | same point | - |
| G2-13 | Staircase omits tab views and Flet session cost, the part that scales with users | Major | Accept in part | main.py:540-587 read. Server phase readings added. Rejected: building App with a stub page (needs a live Flet page; not verified possible) | spec 4 |
| G2-14 | PSS/USS cannot show what is shareable; needs code classification | Major | Accept in part | DatabaseManager state read (_own_edits, sandhi_ok_list, mark_corpus_stale). Classify by code. Rejected: a second live instance on the server (about 2.5 GB more on a shared 8 GB box) | spec 5 |
| G2-15 | Decon-cache write happens only on a cache miss | Major | Accept | database_manager.py:316-334 read: cache hit returns early | spec 2 records hit or miss |
| G2-16 | Probe has no `_own_edits` or per-user sandhi list | Major | Accept | database_manager.py:218-222 read | spec 2 states the divergence |
| G2-17 | Patching the db copy: patch targets under-specified | Major | Accept | database_manager.py:14 imports the name; db_helpers engine cache keyed by path | spec 2: scan sys.modules, assert query_only on the session used |
| G2-18 | Server capped run likely `capped` and under-protected | Major | Accept | reasoning from 1.25 GB vs 1.4 GB watchdog | spec 4.5 reduced staircase, db copy, same guards, cgroup check first |
| G2-19 | Restart and reload test can hurt alice and leave stale Apps | Major | Accept in part | alice is the maintainer's own test account (results.md 'alice, played by the maintainer'). Maintainer's yes, his chosen time, a cleanup restart. Rejected: a scratch unit (needs new nginx and user setup) | spec 4 |
| G2-20 | About 70 processes vs 'tell the user before each run' | Major | Accept | count: 12 points x 4, 4 books x 4, cumulative 3, staircase 3 | spec 2: one driver, one upfront yes, total timeout |
| G2-21 | Spell checker point writes the user dictionary file | Minor | Accept | tools/spelling.py read | spec 2: explicit temp dictionary path, in the guard |
| G2-22 | `agy` stripped on the laptop does not mirror the server | Minor | Accept | reasoning | spec 4: check `command -v agy` on the server, record both |
| G2-23 | Median of three has no variance tolerance | Nit | Accept | reasoning | spec 1: flag when spread exceeds 10 % |
| G2-24 | `imports` has no defined list | Nit | Accept | reasoning | spec 1: `import gui2.main` |
| G2-25 | Book cost missing from the 8/16-user projection | Nit | Accept | reasoning | spec 5: one book and four books |

Counts (from the table): 25 raw findings: Blocker 2, Major 14, Minor 2, Nit 7. Accepted 21, accepted in part 3, merged 1, rejected 0, escalated 0.

Rejected inside findings: the stub-page `App` build (G2-13), a second live instance (G2-14) and a scratch unit (G2-19); reasons in their rows. No escalation: each fork had one defensible answer from the repo or from the owner's standing rules.
