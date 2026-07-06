# Review: optimize goldendict exporter

**Verdict: PASSED** (after one blocking finding was fixed)

Reviewed independently by a fresh Claude Fable subagent (clean context, not a
fork), covering the full diff, the byte-identical claim, both bug fixes, the
multiprocessing rewrite, and the lint/type/test gates. Verdict was
"Needs changes" for one blocking issue; that issue was fixed and re-verified,
and the review's own follow-up (crash-handling regression) was also addressed.

## Files Changed

- `exporter/goldendict/export_dpd.py` — OFFSET pagination → single query +
  keyset low-mem mode; per-word family queries → preloaded dicts; per-page
  `Process` + `Manager().list()` → persistent `concurrent.futures.ProcessPoolExecutor`;
  self-mutating synonyms loop rewritten as a single-pass comprehension.
- `exporter/goldendict/export_epd.py` — constant plain header computed once.
- `exporter/goldendict/export_variant_spelling.py` — constant header once;
  self-referencing rows now skipped (`continue`) instead of added.
- `exporter/goldendict/export_help.py` — constant secondary header once;
  `zip(rows, rows[1:])` last-row-drop fixed with `list_open` tracking.
- `exporter/goldendict/main.py` — `GlobalVars` → `@dataclass` + factory.
- `tools/css_manager.py` — class-level cache of the three CSS file reads.
- `tests/tools/test_css_manager.py` (new), `tests/exporter/goldendict/test_export_dpd.py`,
  `test_export_help.py`, `test_export_variant_spelling.py`.

## Findings

**BLOCKING — zero-copy fork path never engaged.**
`generate_dpd_html` gated the fork zero-copy path on
`get_start_method(allow_none=True)`, which returns `None` in a fresh process
(the start method isn't fixed until first actual multiprocessing use). So every
real run silently took the pickled fallback and the flagship optimization was
dead on arrival. The prior full-scale "zero-copy verified" timings had actually
run the pickled path. Reproduced empirically by both the reviewer and the
author.

**Non-blocking — worker hard-crash regressed from raise to hang.** The old
per-`Process` `exitcode != 0` check raised on crash; `multiprocessing.Pool` +
`imap_unordered` silently hangs on a worker killed by OOM/segfault.

**Non-blocking — progress counter degraded in the (then-unreachable) zero-copy
path; spec wording on `data_limit` + low-mem word set; a weak OR assertion in
the CSS test.** Minor.

## Fixes Applied

1. **Investigated the blocking bug and removed the zero-copy path entirely.**
   Fixing the one-line gate made the path run for the first time; clean,
   isolated per-process measurements at full scale showed it was no faster than
   the pickled path (both ~55–73s; machine-load variance exceeded any gap),
   because CPython refcounting touches every inherited object's page and defeats
   fork copy-on-write for object-graph access. The ~60 lines of Linux-specific
   staging machinery (`_render_zero_copy`, `_render_index_range`,
   `_use_fork_zero_copy`, `_index_bounds`, `_WORKER_DB_DATA`) were removed. The
   pickled path is now the sole, cross-platform path.
2. **Switched the persistent pool to `concurrent.futures.ProcessPoolExecutor`,**
   which raises `BrokenProcessPool` when a worker is killed outright — restoring
   the loud-failure guarantee the old exitcode check gave (fixes the
   non-blocking crash regression). Two new tests cover it.

## Test Evidence

- Byte-identical output verified at 20k after every stage and at full 89,143
  words; the final ProcessPoolExecutor rewrite is orchestration-only (every
  content-producing function unchanged) and was re-confirmed byte-identical and
  deterministic across fresh processes.
- 93 goldendict tests pass (incl. new crash tests: worker exception →
  propagates; killed worker → `BrokenProcessPool`).
- Broader smoke: `tests/exporter/` + `tests/tools/` = 859 passed.
- `ruff check`, `ruff format --check`, `pyright` clean on all touched files.

## Verified-correct (from the review)

Family-preload parity vs the old `.in_()` queries (incl. the duplicate-family
edge case), 1:1 join, keyset paging equivalence, low-mem entry-order safety
(StarDict/MDict/slob all sort on write), synonyms single-pass equivalence,
constant-header invariance, bibliography/thanks last-row fix, see/variant/
spelling skip fix, `helpers.py` fold correctly dropped (used by out-of-scope
exporters), CSS cache immutability, and all project style rules.

## Note

Absolute full-scale wall times were noisy during the review round because a
Borg backup (`borg check`) was churning the machine (load avg ~6–8); samples
ranged 48s–194s. The relative ~5–7× win and byte-identical parity are
load-independent; the 20k regression ladder (51s → 13s) was stable throughout.

## Post-finalize fix (2026-07-06)

User running the real exporter saw the DPD progress counter print only once
(at 0/89,143, after all rendering) — a regression from the old per-page
counter, caused by the single-query high-mem mode having just one "page". Fixed
in `generate_dpd_html`: split each page into `num_logical_cores * 4` finer
batches, submit them, and drive the counter from `as_completed` at the original
~5000-word cadence so progress streams live. Verified live at 40k
(5,448 → 40,000 streaming); count lands exactly, so output is unchanged; 90
goldendict tests pass; lint clean.
