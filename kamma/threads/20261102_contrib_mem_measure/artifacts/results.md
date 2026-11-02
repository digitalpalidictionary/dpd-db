# Results: where one contributor gui2 instance spends its memory

**Thread:** 20261102_contrib_mem_measure · **Issue:** #215 · **Date:** 2026-11-02
Sources: `laptop.jsonl` (54 probe rows, all ok), `server/server.jsonl` (3 rows, all ok), `server/readings.jsonl` (8 labels), `server/results.md` (the server agent's log). Tables are made by `make_tables.py` from those files and pasted below unchanged.

## What the numbers say

- One instance on the server holds **1,165.9 MB** when warm and **1,485.0 MB** after one Pass1Auto book (`mn`). Alice's live instance, up about 23 hours, held 1,542.8 MB (VmHWM equal to RSS). The earlier figure of 1.25 GB was too low.
- The server steps were: process only 86.5 MB, database load +632.1 MB, tab views and managers +447.3 MB, first book +319.1 MB. Reloading the page three times added 6.2, 0.1 and 0.0 MB. There is no reload leak.
- The biggest single piece is the headword load: 676.4 MB alone (laptop, isolated). The lookup sets built by `initialize_db` add 121.2 MB. The word finder adds 172.1 MB. The inflection lists add 234.8 MB. Everything else is small (see the component table).
- The inflection lists are not built by the app warm-up. They are built the first time someone uses Pass1 (`gui2/pass1_auto_controller.py:120`). So most of the +319.1 MB for "one book" is the inflection lists (234.8 MB) plus the book itself (about 58.6 MB).
- The probe and the server agree. Server staircase total 1,391.7 MB (runs: 1,391.9, 1,391.7, 1,387.9). Laptop staircase total 1,385.6 MB. The laptop database is 2.3 GB and the server's is 925 MB, but both have the same 89,774 headwords and 88,805 rows with frequency data, so the memory is the same.
- Read as raw, "unbuilt remainder" is −225.8 MB: the staircase builds more than the app has at warm-up. That is the inflection lists (230.5 MB in the staircase). Without them the remainder is **4.7 MB**, about 0.4 % of the warm RSS. So tab views and Flet add almost nothing. The 20 % rule is not triggered and no `tracemalloc` follow-up is needed.
- About 89 % of the summed isolated deltas is read-only data, the same for every user (shared_read_only 1,204.6 MB against per_user 145.4 MB, sum 1,350.0 MB). That is why option E (one process) is the big lever.

## Projection and ranking

At today's size a box of 8 contributors needs about 12.9 GB with one book each (table below). This is the figure that matters for the server choice. Option E would bring it to about 3.5 GB. All E figures are upper bounds on the saving: the class of each row is a judgement from reading code, and the per-user CST word list in Pass1Auto is not split from the book rows.

The two E figures in the tables differ on purpose. The ranking table uses the spec's formula (read-only component rows × (N − 1)). The projection also stops each user from keeping their own copy of the books and of the Pass1 sets.

Option B has a range. The isolated relationship detector costs 15.6 MB and the staircase says 66.7 MB, so B is 223.1 MB per instance (isolated) or about 274 MB (staircase value). The real saving also depends on what contributors open, which was not measured. Option C's 234.8 MB is paid only after someone uses Pass1, which is every contributor in practice. The cost of a lookup query instead of an in-memory set was not measured.

## Component table (MB, laptop)

| Point | Isolated delta, median (min–max) | Staircase delta | PSS delta | Class |
|---|---|---|---|---|
| bare | 21.6 (21.6–21.8) | 21.7 | 14.3 | read-only — interpreter base; one copy per process (gui2/main.py:1-24) |
| imports | 49.7 (49.7–49.7) | 49.7 | 47.4 | read-only — module code; one copy per process (gui2/main.py:12-24) |
| db_manager | 6.1 (6.1–6.1) | 6.1 | 6.0 | per-user — holds one session and the own-edits overlay (gui2/database_manager.py:47-83) |
| initialize_db | 121.2 (121.1–121.2) | 121.1 | 121.2 | per-user — db-derived sets, but all_lemma_1 adds the user's own additions; most of it is identical (gui2/database_manager.py:215-222) |
| corpus | 676.4 (676.4–676.6) | 674.7 | 676.4 | read-only — full headword load, same for every user (gui2/database_manager.py:181-204) |
| inflections_lists | 234.8 (234.1–234.8) | 230.5 | 234.8 | read-only — derived from the corpus only (gui2/database_manager.py:346-364) |
| relationship_detector | 15.6 (15.5–15.9) | 66.7 | 15.5 | read-only — built from the corpus only (gui2/database_manager.py:781-799) |
| wordfinder | 172.1 (172.1–172.2) | 159.8 | 172.1 | read-only — one shared JSON file (tools/wordfinder_manager.py:35,51-53) |
| ai_manager | 34.4 (34.4–34.5) | 32.4 | 34.3 | read-only — providers from shared config; only small timing fields change (tools/ai_manager.py:58-107) |
| bold_search | 1.0 (0.9–1.0) ⚑ | 0.3 | 0.9 | per-user — holds one db session (tools/bold_definitions_search.py:16-19) |
| spellchecker | 17.1 (17.1–17.2) | 22.4 | 17.1 | per-user — loads the user's own dictionary file (tools/spelling.py:49-55) |
| book:an | 63.0 (62.9–63.3) | n/a | 62.9 | read-only — SC indexes are module-level (gui2/books.py:42-69); the CST list is per controller (gui2/pass1_auto_controller.py:290), not split here |
| book:sn | 59.8 (59.7–60.1) | n/a | 59.8 | read-only — SC indexes are module-level (gui2/books.py:42-69); the CST list is per controller (gui2/pass1_auto_controller.py:290), not split here |
| book:mn | 57.4 (57.3–58.0) | n/a | 57.4 | read-only — SC indexes are module-level (gui2/books.py:42-69); the CST list is per controller (gui2/pass1_auto_controller.py:290), not split here |
| book:vin3&4 | 52.6 (51.1–52.6) | n/a | 52.5 | read-only — SC indexes are module-level (gui2/books.py:42-69); the CST list is per controller (gui2/pass1_auto_controller.py:290), not split here |

## Reconciliation (MB)

| Row | Value | How |
|---|---|---|
| laptop staircase total | 1385.6 | median final RSS of the staircase runs |
| sum of isolated deltas | 1350.0 | `bare` + `imports` + 9 components |
| interaction gap | 35.6 | staircase total − sum of isolated deltas |
| server staircase total | 1391.7 | median final RSS, server runs |
| server warm RSS | 1165.9 | `warmup_done` reading, before any book |
| unbuilt remainder, raw | -225.8 | server warm RSS − server staircase total |
| inflection lists, staircase delta | 230.5 | built by the probe, not by the app warm-up |
| unbuilt remainder | 4.7 | server warm RSS − (server staircase total − inflection lists) |

## Projection (MB; baseline 1066 MB with no gui2 running)

| Users | Books each | Today | Option E |
|---|---|---|---|
| 8 | 1 | 12946.0 | 3530.0 |
| 8 | 4 | 13574.8 | 3608.6 |
| 16 | 1 | 24826.0 | 4730.8 |
| 16 | 4 | 26083.6 | 4809.4 |

Today: warm RSS plus the measured server step for opening books (the first book also builds the inflection lists). Option E: the read-only rows, the inflection lists and the books once, plus the per-user rows and the unbuilt remainder for each user. Each figure is an upper bound.

## Ranking of B to F (MB; effort and risk are judgement)

| Option | Saved per instance | At 8 users | At 16 users | Effort | Risk | Source |
|---|---|---|---|---|---|---|
| B | 223.1 | 1784.8 | 3569.6 | low | low | wordfinder + ai_manager + bold_search + relationship_detector |
| C | 234.8 | 1878.4 | 3756.8 | medium | medium | inflections_lists |
| D | 172.1 | 1376.8 | 2753.6 | medium | medium | wordfinder |
| E | n/a | 8432.2 | 18069.0 | high | high | read-only rows × (N − 1) |
| F | 0 | K × per-instance | K × per-instance | medium | low | K comes from the owner |

## Server readings (MB)

| Label | VmRSS | VmHWM | VmSwap | PSS | Private | Threads | Seconds up |
|---|---|---|---|---|---|---|---|
| now | 1542.8 | 1542.8 | 0.0 | 1536.0 | 1532.1 | 6 | 82589 |
| plus15s | 86.5 | 86.5 | 0.0 | 79.7 | 75.9 | 1 | 15 |
| db_loaded | 718.6 | 767.8 | 0.0 | 711.9 | 708.0 | 5 | 71 |
| warmup_done | 1165.9 | 1165.9 | 0.0 | 1159.1 | 1155.2 | 5 | 95 |
| one_book | 1485.0 | 1485.0 | 0.0 | 1478.0 | 1474.1 | 6 | 173 |
| reload1 | 1491.2 | 1491.2 | 0.0 | 1484.2 | 1480.3 | 4 | 257 |
| reload2 | 1491.3 | 1491.3 | 0.0 | 1484.3 | 1480.4 | 4 | 274 |
| reload3 | 1491.3 | 1491.3 | 0.0 | 1484.3 | 1480.4 | 4 | 295 |

| Step | RSS change |
|---|---|
| db load | 632.1 |
| tab views and managers | 447.3 |
| one book | 319.1 |
| reload 1 | 6.2 |
| reload 2 | 0.1 |
| reload 3 | 0.0 |

## Laptop versus server

- Staircase total: laptop 1385.6 MB, server 1391.7 MB.
- Database size: laptop 2301067264, server 925323264 bytes.
- AI providers built: laptop ['claude', 'codex', 'deepseek', 'gemini', 'nvidia', 'openrouter', 'zai'], server ['claude', 'codex', 'deepseek', 'openrouter'].


## Reload test (task 3.5)

Three reloads of alice's page, same process (pid 2371952): 1,491.2, 1,491.3, 1,491.3 MB after 1,485.0 MB. The rises are 6.2, 0.1 and 0.0 MB, far below the 100 MB threshold. A reload does not keep an extra copy of the app.

## Deviations and limits

- The server's `systemctl stop` left the unit in state `failed` instead of `inactive` (gui2 exits non-zero on SIGTERM). The maintainer approved going on (`server/results.md`, section 3.7).
- The deconstructor cache was a `hit` on the laptop and a `miss` on the server. On the miss, the contributor role blocks the cache write and gui2 swallows it, so the probe did not write to the database.
- The server built 4 AI providers and the laptop built 7. Each provider object is small (`ai_manager` 34.4 MB on the laptop).
- Server runs were 3 runs of the staircase. The laptop battery ran every point 3 times; one point (`bold_search`, about 1 MB) was flagged for spread and was re-run.
- The server staircase peaked at 1,439.1 MB (VmHWM), under the probe's 1,400 MB limit for RSS and the 1,500 MB cap.
- Not measured: the cost of a lookup query for option C, how many contributors are online at once for option F, and the per-user part of the Pass1Auto CST word list.

## Corrections for earlier threads (listed, not edited)

1. `kamma/archive/20261101_contrib_6_e2e_server_test/artifacts/server/results.md`, Addendum B: "One gui2 instance (warm, after book runs + additions): RSS 1.25 GB, peak VmHWM 1.25 GB". Measured now: 1,165.9 MB warm with no book, 1,485.0 MB after one book, 1,542.8 MB for alice after about 23 hours. The per-instance figure is about 1.5 GB, not 1.25 GB.
2. Same file, "steady state = OS ~0.5 GB + N × ~1.3 GB per warm gui2" and "2–3 contributors on this box": use N × about 1.5 GB. The advice "budget 1.5–2 GB per contributor instance" still holds; the measured value sits at its low end. The cap of 2 GB per instance (`MemoryMax`) leaves about 0.5 GB of room above the 1.54 GB seen after a day.
3. `kamma/threads/20261023_contrib_1_web_server/spec.md` lines 77–78: "Measured RSS: ~330 MB idle (server up, no session); ~2.5 GB with one connected session". Measured now on the server: 86.5 MB 15 s after a restart, 1,165.9 MB when warm, 1,485.0 MB after one book. The 2.5 GB figure was not reproduced.
4. Same file, line 79: "3 concurrent users ≈ 8 GB → 16 GB VPS". At about 1.5 GB each, 3 users need about 4.5 GB, 8 users about 12.9 GB with the 1,066 MB baseline, and 16 users about 24.8 GB (projection table). The 16 GB choice holds for about 8 users, not for 16.
5. `gui2/main.py:665`, comment: "a second browser tab would build a second copy of the app (~2.5 GB)". That figure was not measured. Reloads did not add a copy (+6.2, +0.1, +0.0 MB). Proposed edit for the maintainer: change the number or drop it.
6. `kamma/threads/20261030_contrib_x_problem_children/` (`spec.md`, `plan.md`): no memory figure found to contradict (`rg` for memory, GB, RSS and warm-up finds only a cache note at `spec.md:189`).
7. This thread's own `spec.md` section 5 defines `unbuilt remainder` as server warm RSS minus the server staircase total. That is −225.8 MB, because the app warm-up does not build the inflection lists. The table now also shows the remainder without them (4.7 MB). Spec text left as written; this note is the correction.

## Done check (spec "How we'll know it's done")

1. Laptop `--all` completed, every point three runs, no guarded change: met. `laptop.jsonl` has 54 rows, all `ok`, no `guard_warnings`.
2. Server readings in `artifacts/server/`, with phases, reload test and capped runs: met. `server/readings.jsonl`, `server/server.jsonl`, `server/results.md`.
3. `results.md` has the component table, both reconciliation rows, the projection and the B–F ranking: met (this file).
4. Every number is quoted from a probe output line or a server log: met. The tables come from `make_tables.py`; the narrative quotes table rows or `server/results.md`.
5. Contradictions listed, not edited: met (section above).
