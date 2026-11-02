# Lever results (MB, laptop, fresh process per run)

## Step cost per variant (delta of the last step)

| Variant | Last step | Delta, median (min–max) | Runs |
|---|---|---|---|
| corpus_full | corpus_full | 677.0 (676.5–677.2) | 3 |
| corpus_slim | corpus_slim | 430.0 (430.0–430.9) | 3 |
| corpus_slim_nofreq | corpus_slim_nofreq | 325.5 (324.5–326.6) | 3 |
| sets_today | sets_today | 234.3 (234.1–234.7) | 3 |
| sets_today_slim | sets_today | 272.6 (272.6–274.6) | 3 |
| sets_direct | sets_direct | 276.2 (276.2–277.0) | 3 |
| sets_direct_both | sets_direct_both | 316.9 (315.8–318.0) | 3 |
| detector_full | detector | 15.5 (15.1–15.5) | 3 |
| detector_slim | detector | 123.0 (122.0–124.1) | 3 |
| wordfinder_today | wordfinder_today | 172.1 (172.1–172.2) | 3 |
| wordfinder_interned | wordfinder_interned | 201.8 (201.7–201.8) | 3 |
| reload_full | reload_full | 172.6 (171.7–172.7) | 3 |
| reload_slim | reload_slim | 285.0 (284.0–287.3) | 3 |
| contributor_today | spellchecker | 22.4 (22.4–22.5) | 3 |
| contributor_levers | spellchecker | 24.8 (24.8–24.9) | 3 |
| contributor_levers_l5 | spellchecker | 24.8 (24.8–24.9) | 3 |
| contributor_lazy | spellchecker | 26.6 (26.6–26.7) | 3 |
| warm_today | spellchecker | 22.5 (22.5–22.5) | 3 |
| warm_levers | spellchecker | 24.8 (24.8–24.9) | 3 |
| corpus_slim_noinfl | corpus_slim_noinfl | 427.3 (426.4–427.3) | 3 |
| warm_slim | spellchecker | 24.9 (24.8–24.9) | 3 |
| warm_slim_noinfl | spellchecker | 24.6 (24.6–24.7) | 3 |
| warm_slim_nofreq | spellchecker | 24.9 (24.8–24.9) | 3 |
| warm_interned | spellchecker | 22.5 (22.5–22.5) | 3 |
| contributor_slim | spellchecker | 24.9 (24.8–24.9) | 3 |
| contributor_sets_direct | spellchecker | 22.5 (22.5–22.5) | 3 |
| corpus_slim_split | corpus_slim_split | 347.0 (346.9–347.0) | 3 |
| sets_hash | sets_hash | 59.0 (58.0–59.0) | 3 |
| warm_slim_split | spellchecker | 24.6 (24.6–24.6) | 3 |
| contributor_hash | spellchecker | 22.5 (22.4–22.5) | 3 |
| contributor_split_direct | spellchecker | 24.6 (24.6–24.7) | 3 |
| contributor_split_hash | spellchecker | 24.6 (24.6–24.6) | 3 |

## Saving per lever (before − after, median; range in brackets)

A negative number means the lever costs memory.

| Lever | Saving |
|---|---|
| L1 slim corpus (warm build, sets not built) | 137.0 (136.8–137.1) |
| L1 slim corpus, with the sets still built (Pass1 used) | 139.4 (139.2–139.4) |
| L1 slim corpus without the two inflection columns (needs L5) | 143.1 (143.0–143.3) |
| L7 ceiling: also without freq_data (would change detector results) | 241.8 (241.8–242.0) |
| L2 direct sets instead of today's sets | 72.2 (72.0–72.2) |
| L3 missing-meaning set (step cost of the direct build) | 40.7 (38.8–41.8) |
| L4 interned word finder (warm build) | -26.6 (-26.6–-26.5) |
| L5 no inflection set at all (whole build; the lookup table is NOT equivalent, see equivalence.md) | 272.0 (271.8–272.0) |
| L7b freq_data only for headwords with no meaning, no inflection columns (warm build) | 222.1 (222.1–222.2) |
| L8 compact inflection set (whole build) | 259.3 (259.1–259.3) |
| L1 + L7b + direct sets | 294.5 (294.3–294.6) |
| L1 + L7b + compact set | 481.7 (481.5–481.7) |
| L1 + L5 together (slim without inflection columns, no set) | 415.1 (414.9–415.2) |
| L6 lazy managers (AI, bold search, detector never built) | 95.5 (95.3–95.5) |
| Refresh DB: extra memory, full corpus | 172.5 (171.6–172.7) |
| Refresh DB: extra memory, slim corpus | 284.9 (283.8–287.4) |

## Whole contributor build (final RSS and start-up peak)

| Variant | Final RSS | Peak (VmHWM) |
|---|---|---|
| contributor_today | 1386.3 (1386.2–1386.3) | 1432.0 (1431.9–1432.5) |
| contributor_levers | 1203.5 (1203.4–1203.5) | 1245.7 (1245.2–1248.3) |
| contributor_levers_l5 | 1003.8 (1003.8–1003.8) | 1003.8 (1003.8–1003.8) |
| contributor_lazy | 1290.8 (1290.8–1290.9) | 1432.5 (1432.0–1432.6) |
| warm_today | 1114.3 (1114.3–1114.4) | 1201.5 (1200.9–1201.8) |
| warm_levers | 1003.8 (1003.8–1003.9) | 1003.8 (1003.8–1003.9) |
| warm_slim | 977.3 (977.3–977.5) | 977.3 (977.3–977.5) |
| warm_slim_noinfl | 971.2 (971.1–971.3) | 971.2 (971.1–971.3) |
| warm_slim_nofreq | 872.5 (872.4–872.5) | 872.5 (872.4–872.5) |
| warm_interned | 1140.9 (1140.9–1140.9) | 1201.3 (1200.7–1201.5) |
| contributor_slim | 1246.9 (1246.9–1247.0) | 1246.9 (1246.9–1247.0) |
| contributor_sets_direct | 1314.1 (1314.1–1314.2) | 1459.1 (1459.1–1459.4) |
| warm_slim_split | 892.2 (892.2–892.2) | 892.2 (892.2–892.2) |
| contributor_hash | 1127.0 (1127.0–1127.1) | 1292.9 (1291.7–1293.4) |
| contributor_split_direct | 1091.8 (1091.7–1091.9) | 1163.0 (1161.9–1163.2) |
| contributor_split_hash | 904.6 (904.6–904.7) | 967.2 (966.0–967.8) |

## Estimate for the server (saving measured on the laptop)

| Contributors | Today | L1 only | L1+L7b+direct sets | L1+L7b+compact set |
|---|---|---|---|---|
| 3 | 5521 | 5103 | 4638 | 4076 |
| 8 | 12946 | 11831 | 10590 | 9092 |
| 16 | 24826 | 22596 | 20114 | 17119 |

Per instance after one book: L1 only 1346 MB, L1+L7b+direct sets 1190 MB, L1+L7b+compact set 1003 MB (today 1485.0 MB).
Server baseline 1066 MB; today's figures from `contrib_mem_measure/artifacts/server/results.md`. The earlier thread found the laptop and the server agree to 5 MB.
