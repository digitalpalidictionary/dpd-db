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
| server staircase total | n/a | median final RSS, server runs |
| server warm RSS | n/a | `warmup_done` reading, before any book |
| unbuilt remainder | n/a | server warm RSS − server staircase total |

## Projection (MB; baseline 1066 MB with no gui2 running)

| Users | Books each | Today | Option E |
|---|---|---|---|
| 8 | 1 | n/a | n/a |
| 8 | 4 | n/a | n/a |
| 16 | 1 | n/a | n/a |
| 16 | 4 | n/a | n/a |

Option E counts the books once. Each figure is an upper bound.

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

| Step | RSS change |
|---|---|

## Laptop versus server

- Staircase total: laptop 1385.6 MB, server n/a MB.
- Database size: laptop 2301067264, server n/a bytes.
- AI providers built: laptop ['claude', 'codex', 'deepseek', 'gemini', 'nvidia', 'openrouter', 'zai'], server n/a.

## Key numbers

KEY e_16_1=n/a
KEY e_16_4=n/a
KEY e_8_1=n/a
KEY e_8_4=n/a
KEY flag_ai_manager=no
KEY flag_bare=no
KEY flag_bold_search=yes
KEY flag_corpus=no
KEY flag_db_manager=no
KEY flag_imports=no
KEY flag_inflections_lists=no
KEY flag_initialize_db=no
KEY flag_relationship_detector=no
KEY flag_spellchecker=no
KEY flag_wordfinder=no
KEY four_books=137.2
KEY interaction_gap=35.6
KEY iso_ai_manager=34.4
KEY iso_bare=21.6
KEY iso_bold_search=1.0
KEY iso_corpus=676.4
KEY iso_db_manager=6.1
KEY iso_imports=49.7
KEY iso_inflections_lists=234.8
KEY iso_initialize_db=121.2
KEY iso_relationship_detector=15.6
KEY iso_spellchecker=17.1
KEY iso_wordfinder=172.1
KEY laptop_staircase_total=1385.6
KEY one_book=58.6
KEY opt_B=223.1
KEY opt_C=234.8
KEY opt_D=172.1
KEY opt_E_16=18069.0
KEY opt_E_8=8432.2
KEY per_user=145.4
KEY server_staircase_total=n/a
KEY server_warm_rss=n/a
KEY shared_read_only=1204.6
KEY sum_isolated=1350.0
KEY today_16_1=n/a
KEY today_16_4=n/a
KEY today_8_1=n/a
KEY today_8_4=n/a
KEY unbuilt_over_20pct=no
KEY unbuilt_remainder=n/a

## Comparison with the July benchmark (task 2.5)

July 2026 (`kamma/archive/20260710_gui2_perf_and_testing/benchmarks/results/3.3_memory.json`): bare 63.0 MB, corpus step 804.3 MB (`initialize_db` then loaded the corpus), total 873.4 MB after it. Today, in the staircase: bare 21.7 + imports 49.7 + db_manager 6.1 + initialize_db 121.1 + corpus 674.7 = 873.3 MB. The July "bare" of 63.0 MB is today's bare plus imports (71.4 MB here). The July corpus step of 804.3 MB compares with today's initialize_db plus corpus, 121.1 + 674.7 = 795.8 MB. The total is the same to 0.1 MB. The corpus became lazy, so the work is split in two steps, but the memory did not shrink: the lazy load only moves the cost, and the warm-up loads it anyway.
