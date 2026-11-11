# Laptop gui2 speed measurements (Phase 6)

Machine: laptop, uptime load average at measurement time: **1.89, 1.63, 1.47**
(1-minute load under 2 — numbers are clean).

Method: every timing is a fresh process; one warm-up run thrown away, 5 runs
reported (median, min–max).

## F1 — import time, view modules (`time_imports.py`)

| variant | median s | min s | max s |
|---|---|---|---|
| start (gui2.global_tab_view only) | 0.266 | 0.261 | 0.277 |
| all (15 view modules¹) | 0.452 | 0.450 | 0.459 |

¹ The plan listed 16 modules (5 at module top, 11 in `App.__init__`). Phase 4
moved `Pass1AddView` out of `App.__init__` into `_make_pass1_add`, so the
measured set is 5 + 10 = 15 — what `gui2/main.py` imported before first paint
**at measurement time, before task 6.2 moved the imports**. These figures are
the pre-change upper bound the F1 gate was judged on; after 6.2, module-top
imports none of the view modules (each builder imports its own), so the real
first-paint import cost is lower than the "all" row.

**saving bound = median(all) − median(start) = 0.186 s** — at or above the
0.15 s gate → **F1 built** (task 6.2).

## F1 before/after — `python -X importtime -c "import gui2.main"` (last column, cumulative µs of gui2.main)

- before: 338689, 330166, 337815 (median 337815)
- after: 106163, 110329, 106326 (median 106326) — **lower by ~232 ms**, F1 kept.

## F2 — `get_all_lemma_1_and_lemma_clean()` (task 6.3)

Six runs in one warm process (`time_lemmas.py`), `DPD_GUI2_ROLE` unset
(checked, 0):

| run | s |
|---|---|
| 1 (warm-up, thrown away) | 0.137 |
| 2 | 0.150 |
| 3 | 0.146 |
| 4 | 0.145 |
| 5 | 0.148 |
| 6 | 0.146 |

**median of the last five = 0.146 s** — at or above the 0.10 s gate →
**F2 built** (task 6.4).
