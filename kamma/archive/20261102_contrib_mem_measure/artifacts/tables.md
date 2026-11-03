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

## Key numbers

KEY e_16_1=4730.8
KEY e_16_4=4809.4
KEY e_8_1=3530.0
KEY e_8_4=3608.6
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
KEY four_books_server=397.7
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
KEY server_book_step=319.1
KEY server_staircase_total=1391.7
KEY server_warm_rss=1165.9
KEY shared_read_only=1204.6
KEY step_db_loaded=632.1
KEY step_one_book=319.1
KEY step_reload1=6.2
KEY step_reload2=0.1
KEY step_reload3=0.0
KEY step_warmup_done=447.3
KEY sum_isolated=1350.0
KEY today_16_1=24826.0
KEY today_16_4=26083.6
KEY today_8_1=12946.0
KEY today_8_4=13574.8
KEY unbuilt_over_20pct=no
KEY unbuilt_remainder=4.7
KEY unbuilt_remainder_raw=-225.8
