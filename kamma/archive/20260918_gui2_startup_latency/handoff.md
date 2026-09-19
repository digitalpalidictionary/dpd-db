# Handoff — gui2 startup latency

State as of 2026-09-18 evening, after the Claude Code session hit its weekly
limit and this session resumed.

## Done

- **Phase 1 complete** — defect proven (`tests/gui2/test_books.py`: 2 failed /
  1 passed against eager code), baselines regenerated as medians-of-three, the
  8.29 vs 7.04 s discrepancy resolved as single-run variance, the spec's
  "warm-up drops to 2.22 s" claim disproven and corrected in `spec.md`.
- **Phase 2 complete** — `gui2/books.py`: `segment_dict` / `word_dict` are now
  `functools.cached_property`; construction stores identity + paths + eager
  file lists only. All verifies pass (3/3 new tests, 296 gui2 tests,
  importtime: books self 65,548 µs, pass1_add_view cumulative 418 ms). Warm-up
  proven not to build the index via `artifacts/probe_warmup.py` (clean across
  all 21 sources). Lint clean.
- **Phase 3 nearly complete** — `gui2/main.py`: warm-up chained from
  `_initialize_db_in_background`'s `finally`; `build_ui` starts only the db
  worker. Three headless (xvfb) measurement runs recorded in
  `artifacts/phase3_serial.log`: first paint 1.20 s, db loaded 8.11 s
  (duration 6.90 s), all tabs warm 11.12 s, warm-up strictly after db load
  every run. Lint clean.

## Incident to know about

The first Phase 3 edit added the serialisation comment but **forgot the
actual `self.page.run_thread(self._warmup_in_background)` call** — the
warm-up silently never started. Diagnosed via `artifacts/timed_gui_diag2.py`
under `xvfb-run` (desktop windows kept getting closed mid-measurement, which
masked the diagnosis). Fixed and re-verified. If review sees anything odd
around the `finally` block, this is why.

## Remaining (all need the user at the real GUI)

1. **Phase 3 task 2** — click a late tab (Tests/Roots/CT) while the loading
   bar is still showing; confirm real content within ~2 s (up to ~1.6 s wait
   on the shared build lock is pre-existing, not a hang).
2. **Phase 3 task 3** — failed-load path: throwaway config pointing at a
   missing db file (never move the real db), confirm failure snackbar + warm-up
   still runs + retry on click; restore config immediately.
3. **Phase 4 task 1** — post-change figures: the three headless runs in
   `phase3_serial.log` already meet every target; re-measure on the real
   display only if review asks.
4. **Phase 4 tasks 2–3** — pass1auto first-vs-second book selection timing
   (>~5 s first selection = follow-up); pass2pre word list unchanged vs
   pre-change (inspection).
5. **Phase 4 task 4** — `uv run pytest tests/` + `just typecheck`.
6. **Phase 4 task 5** — ask user for `coderabbit review --agent --dir gui2
   --include-untracked`.

## Notes for the next session

- Measurement harnesses: `timed_gui.py` (baseline), `timed_gui_diag.py` /
  `timed_gui_diag2.py` (diagnostics), `run_phase3_serial.py` (3× driver,
  headless via xvfb-run, auto-kills each window after its last stamp). Always
  kill the whole process group — killing the `uv run` PID orphans the venv
  python and the flet client.
- Other sessions' uncommitted files in the tree: `exporter/kindle/epub/.../
  titlepage.xhtml`, `gui2/data/pass2_exceptions.json` — not ours, don't touch.
