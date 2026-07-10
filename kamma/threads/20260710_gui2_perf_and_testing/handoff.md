# Handoff — start Phase 7 (Lazy startup, Theme C)

**Model: Opus.** Run `/kamma:2-do gui2` in a fresh session.

## State

- Phases 1–6 complete, each committed by the user. Phase 6 committed as
  `#157 gui2: cached corpus load, off-thread init, coalesced detector`.
- Next task: 7.1 (first `[ ]` in plan.md). Phase 7 = lazy ToolKit managers,
  lazy tab content, drop uvicorn `--reload`, DISTINCT pre-init queries,
  then re-run bench 3.2/3.3.
- `db_tests/db_tests_columns.tsv` remains an unrelated pre-existing dirty
  file — always exclude from commits.

## Context the fresh session needs

- **User priority within Phase 7:** the user's felt wait is the AI manager
  init and the eager build of all 15 tab views (7.1/7.2) — do those first,
  as the plan already orders. Baseline (3.2): wordfinder 74MB JSON
  ~1.7–1.8s, AI manager 6-provider init ~1.0–1.1s,
  `pre_initialize_gui_data` 5 queries 0.3–1.6s; all other managers <100ms
  combined.
- **Phase 6 landed a corpus cache** in `gui2/database_manager.py`:
  `load_corpus()` (lock + generation counter) is the ONE full-table load;
  `mark_corpus_stale()` after any headword write; detector rebuilds go
  through a single debounced worker (`_detector_rebuild_worker`). Don't
  reintroduce direct `.all()` loads of DpdHeadword in gui2.
- `main.py tab_clicked` now runs `initialize_db()` off-thread
  (`_initialize_db_in_background`, guarded by `_db_init_started`). Lazy tab
  content (7.2) must not break this first-click hook.
- Six validations in `dpd_fields.py` skip when their set is still None
  (corpus loading window) — keep that pattern if touching validation.
- Benchmarks live in `kamma/threads/20260710_gui2_perf_and_testing/
  benchmarks/` (run from project root with PYTHONPATH=".:benchmarks dir";
  `bench_common.force_throwaway_db_globally()` protects the real dpd.db;
  throwaway copy already exists in the old session scratchpad — path in
  bench_common.py; recreate with `cp dpd.db <path>` if cleaned).
- Commit cadence: one commit per phase, `/cm` drafts only, user commits.
  Checkpoint needs a user smoke test (all tabs function) before `/cm`.
- Pre-commit gate: every touched file must pass `uv run ruff check`,
  `uv run ruff format`, `uv run pyright`, plus related pytest. `gui2/` is
  pyright-excluded in CI config but NOT ruff-excluded; fix pre-existing
  lint in any file you touch.

## plan.md task markers

Phases 1–6 all `[x]` including checkpoints; Phase 7 tasks 7.1–7.5 and
checkpoint `[ ]`; Phase 8 `[ ]`.
