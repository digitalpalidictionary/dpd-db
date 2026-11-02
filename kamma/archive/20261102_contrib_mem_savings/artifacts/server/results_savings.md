## 4.2

$ git log -1 --format=%h
247a8429

$ git status --porcelain
(no output — working tree clean)

$ ls ~/mem/mem_probe.py
/root/mem/mem_probe.py

$ systemctl is-active dpd-gui@alice
active

## 4.3 (run2, commit 247a8429)

| reading | before MB | after MB |
|---|---|---|
| plus15s | 86.5 | 86.5 |
| db_loaded | 718.6 | not taken (warm-up follows 9 s later) |
| warmup_done | 1165.9 | 943.3 |
| one_book (mn, no missing words) | 1485.0 | 1045.7 (peak 1113.4) |
| pass1add | n/a | 1045.7 |

Note: run1 (labels without _run2) is invalid, 2059.4 MB at warmup_done, because two extra browser sessions were open.
