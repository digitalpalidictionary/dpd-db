# Results — contrib_mem_measure

## 3.1 Now

Command: `--unit-readings dpd-gui@alice --label now` (2026-11-02). Output
(`~/mem/readings.jsonl`):

```
{"label": "now", "pid": 1889972, "vm_rss_mb": 1542.8, "vm_hwm_mb": 1542.8, "vm_swap_mb": 0.0, "threads": 6, "smaps_rss_mb": 1542.8, "smaps_pss_mb": 1536.0, "smaps_private_mb": 1532.1, "elapsed_s": 82589}
```

EXPECT: met — one JSON object per python process, label `now`, VmRSS/VmHWM/
VmSwap/Threads/Pss all present, no error line. (One python process matched;
the `uv` wrapper is not named `python`.) Reading: alice has been up ~22.9 h
(elapsed 82589 s) and RSS has grown to its HWM: 1542.8 MB.

## 3.2 Database and tools

```
-rw-r--r-- 1 root root 925323264 Nov  1 18:18 /root/dpd-db/dpd.db
-rwxr-xr-x 1 root root  74330677 Nov  1 11:45 /root/dpd-db/shared_data/frequency/cst_file_freq.json
(89774,) (88805,)
NO_AGY
/usr/bin/sqlite3
```

EXPECT: met — sizes printed; headword count 89774 and freq_data count 88805
(exactly the laptop's 88,805 non-empty); `sqlite3` at /usr/bin/sqlite3;
`agy` not installed (same as the e2e run — the probe records it in meta).

Server book: `books.md` was not in the 3.0 copy; the maintainer instructed
copying it from the pulled repo (`cp ~/dpd-db/kamma/threads/20261102_contrib_mem_measure/artifacts/books.md ~/mem/`). It names `mn` (fallback `sn`).
All five `mn` files verified present:

```
resources/sc-data/sc_bilara_data/root/pli/ms/sutta/mn
resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/mn
resources/dpd_submodules/cst/romn_txt/s0201m.mul.txt
resources/dpd_submodules/cst/romn_txt/s0202m.mul.txt
resources/dpd_submodules/cst/romn_txt/s0203m.mul.txt
```

## 3.3 Cap check and database copy

Maintainer said yes. Output:

```
exit=0
-rw-r--r-- 1 root root 925323264 Nov  2 17:18 /root/mem/dpd_copy.db
/dev/sda1        96G   32G   65G  33% /
```

EXPECT: met — `exit=0`; the copy is byte-identical in size to `dpd.db`
(925,323,264 bytes, 0 % difference, within 5 %); 65 GB free (above 3 GB).

## 3.4 Fresh start in phases

Maintainer said yes to the restart (alice is a test account; no unsaved
input). Four readings, all from pid 2371952, appended to
`~/mem/readings.jsonl`:

| label | rss_mb | hwm_mb | pss_mb | threads | elapsed_s |
|---|---|---|---|---|---|
| plus15s | 86.5 | 86.5 | 79.7 | 1 | 15 |
| db_loaded | 718.6 | 767.8 | 711.9 | 5 | 71 |
| warmup_done | 1165.9 | 1165.9 | 1159.1 | 5 | 95 |
| one_book (mn) | 1485.0 | 1485.0 | 1478.0 | 6 | 173 |

Steps: RSS rose at each step (deltas ≈ +632 MB db, +447 MB tabs/tools,
+319 MB one book). No fall, no self-restart.

EXPECT: met — four readings, RSS rising at each step.

## 3.5 Reload test

Maintainer said yes and reloaded three times (readings from the same pid
2371952):

| label | rss_mb | delta |
|---|---|---|
| reload1 | 1491.2 | +6.2 vs one_book |
| reload2 | 1491.3 | +0.1 |
| reload3 | 1491.3 | +0.0 |

EXPECT: met — three readings with labels reload1–reload3. Rise per reload is
≈ 0 MB, far below the 100 MB-per-reload leak threshold: **no leak on
reload**.

## 3.7 STOP — unit state `failed` instead of `inactive` on stop

Command: `sudo systemctl stop dpd-gui@alice; systemctl is-active dpd-gui@alice`

Output:

```
failed
```

(systemd: ActiveState=failed, SubState=failed, Result=exit-code;
`ps` confirms no gui2 process remains.)

Mismatch with EXPECT (`inactive`) → STOP per rule 3. Likely the same
behaviour seen in the 20261101 thread mid-window #1: gui2 exits non-zero on
SIGTERM, so a clean stop records `Result=exit-code`. Functionally the unit IS
stopped. Awaiting the maintainer's decision before the capped runs.

## 3.7 Capped staircase runs

Pre-run check (maintainer-required): `ps -eo pid,cmd | grep -E "[g]ui2/main.py|[m]em_probe"` → `NO_GUI2_NO_PROBE`.

The recorded deviation stands: the stop showed `failed` (gui2 exits non-zero
on SIGTERM) instead of EXPECT's `inactive`; the unit was functionally
stopped, maintainer said proceed.

Run 1: launched (pid 2375050), ENDED within the first 5-minute check.
Run 2: pid 2378208, ENDED within 5 min. Run 3: pid 2380134, ENDED within
5 min. No timeout/kill needed.

`~/mem/server.jsonl`: 3 rows, outcomes `['ok', 'ok', 'ok']` —
final RSS 1391.9 / 1391.7 / 1387.9 MB, peak HWM 1439.1 / 1439.1 / 1439.0 MB
(spread ≈ 0.3 %). Run 1 meta: commit `19daa973fa77`, Python 3.13.18,
db 925323264 bytes, `query_only: 1`, providers claude/codex/deepseek/
openrouter, `agy_found: false`, `MALLOC_ARENA_MAX=2`, `decon_cache: miss`,
`guard_warnings: []`.

After run 3: `sudo systemctl start dpd-gui@alice` → `active`;
`ps … grep "[m]em_probe"` → `NO_STRAY_PROBE`.

EXPECT: met (with the recorded stop-state deviation).

## Phase 3 verdict

- 3.1 met — `now` reading of the live unit: RSS 1542.8 MB after ~23 h.
- 3.2 met — db 925323264 bytes, 89774 headwords, 88805 with freq_data
  (exactly the laptop count), sqlite3 present, NO_AGY; server book `mn`
  files all present (books.md copied from the pulled repo per the
  maintainer).
- 3.3 met — cap `exit=0`; `.backup` copy byte-identical in size; 65 GB free.
- 3.4 met — RSS 86.5 → 718.6 → 1165.9 → 1485.0 MB (db +632, tabs/tools +447,
  one book +319); no falls, no self-restart.
- 3.5 met — three reloads: 1491.2 → 1491.3 → 1491.3 MB; no leak; unit
  restarted, `active`.
- 3.6 met — maintainer said go.
- 3.7 met, with one recorded deviation — the stop's `failed` label vs
  EXPECT `inactive` (functionally stopped, maintainer approved proceeding);
  3 `ok` rows; alice `active` after; no strays.

STOPS: one (3.7 stop-state mismatch), resolved by the maintainer's decision.
alice's final state: **active**. Phase 3: **PASS**.
