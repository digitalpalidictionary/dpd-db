# Plan — gui2 db load time

Spec: `kamma/threads/20260919_gui2_db_load/spec.md`
Harnesses: reuse `kamma/threads/20260918_gui2_startup_latency/artifacts/`
(`timed_gui.py`, `run_phase3_serial.py` driver — headless via xvfb-run).
No GitHub issue.

## Architecture Decisions

- **Phase 1 decides; later phases only implement survivors.** The project's
  performance rule: re-derive every number and benchmark each mechanism on a
  throwaway db copy before implementing. A mechanism that doesn't benchmark
  is killed, and its phase is skipped with the reason recorded — never
  silently dropped.
- **App-level caching over schema change.** The deconstructor set, if cached,
  goes into the existing `db_info` key-value store with explicit
  invalidation — no new indexes on `lookup`, no db build pipeline changes
  (both explicitly out of scope in the spec).
- **Corpus row identity stays ORM.** Consumers hold `DpdHeadword` entities
  (the detector keeps references; views read attributes). A raw-dict
  projection would ripple through every consumer, so corpus optimisation is
  limited to query-level work (`load_only` / deferred columns), not
  re-typing the rows.
- **Lazy detector keeps the public surface.** `_relationship_detector`
  becomes a `cached_property`-style lazy attribute; existing
  `toolkit.db_manager.relationship_detector`-style access keeps working.
  Direct private-attribute readers found by the Phase 1 grep get fixed as
  part of the phase, not left to duck.

## Phase 1 — Re-profile and validate

- [ ] Re-derive the per-component timings on a throwaway copy.
      - `cp dpd.db /tmp/dpd_load_test.db` (never benchmark the live db).
      - Time each `initialize_db()` component separately, warm cache, three
        repetitions, medians.
      → verify: table of component → median seconds pasted into this plan,
      alongside the spec's 3.19/1.51/1.12 s figures. State the new total.

- [ ] Sweep the consumers.
      - Exhaustive grep (not from memory): every attribute read on
        `DpdHeadword` rows obtained via `load_corpus()` / `db_manager.db`,
        outside `db/models.py` — this bounds any `load_only()` column list.
      - Grep every reader of `_relationship_detector` / `relationship_detector`
        and every writer of `lookup.deconstructor` / `lookup.headwords`
        (invalidation points for a db_info cache).
      → verify: consumer lists pasted into this plan; any direct
      private-detector reader flagged for Phase 4.

- [ ] Benchmark the candidate mechanisms on the throwaway copy.
      - (a) deconstructor set: current ORM query vs raw SQL
        `session.execute(select(Lookup.lookup_key).where(...))` vs a
        round-trip from a pickled `db_info` cache (measure read cost only —
        build cost lands on the db build side, out of scope).
      - (b) corpus: current `load_corpus()` vs `load_only(<verified column
        list>)` vs additional `defer()` of rarely-read columns from the
        sweep.
      - (c) lazy detector: confirm no warm-up or view constructor touches it
        (from the sweep); no timing needed, just the read-path proof.
      → verify: benchmark table pasted here; each mechanism marked SHIP or
      KILLED with its measured numbers. Spot-check the winning variants
      produce identical sets/detector outputs to the current code.

## Phase 2 — Deconstructor scan fix

- [ ] Implement the surviving variant from Phase 1 (a). If it was a
      `db_info` cache: write the cache wherever lookup is rebuilt, invalidate
      on every writer found in the sweep, and load from cache on startup
      with a correct fallback to the live query when absent.
      → verify: `uv run pytest tests/gui2/` passes; a quick script prints
      identical set contents before/after; the component's timing in the
      Phase 1 table.

- [ ] Lint the touched file(s).
      → verify: `uv run ruff check --fix <files>`, `uv run ruff format
      <files>`, `uv run pyright <files>` all clean.

## Phase 3 — Corpus load fix

- [ ] Implement the surviving variant from Phase 1 (b).
      → verify: `uv run pytest tests/gui2/ tests/exporter/ -q` passes (views
      and exporter both touch corpus fields); the component's timing in the
      Phase 1 table.

- [ ] Lint the touched file(s).
      → verify: ruff + pyright clean on every touched file.

## Phase 4 — Lazy RelationshipDetector

- [ ] Move construction out of `initialize_db()` into a lazy accessor;
      fix any private-attribute readers from the Phase 1 sweep.
      → verify: `uv run pytest tests/gui2/` passes; a launch via
      `timed_gui.py` shows db-loaded stamp without detector time; opening a
      word with related entries still shows them (user inspection or a
      targeted test if one exists).

- [ ] Lint the touched file(s).
      → verify: ruff + pyright clean.

## Phase 5 — Measure and verify the whole

- [ ] Record post-change figures.
      → verify: three runs via `run_phase3_serial.py` (headless); paste all
      three; state the median db-loaded. **Target: ≤ 4 s median.** If
      missed, say so here and explain — do not round into a pass.

- [ ] Repo-wide checks.
      → verify: `uv run pytest tests/` passes (slow deselected); `just
      typecheck` clean.

- [ ] Ask the user for permission to run `coderabbit review --agent`, scoped
      to the touched files.
      → verify: permission asked, review run if granted, every finding fixed
      or recorded here with the rejection reason.
