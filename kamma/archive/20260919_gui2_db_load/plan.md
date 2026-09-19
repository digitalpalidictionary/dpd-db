# Plan — gui2 db load time

Spec: `kamma/threads/20260919_gui2_db_load/spec.md`
Harnesses: reuse `kamma/archive/20260918_gui2_startup_latency/artifacts/`
(`timed_gui.py`, `run_phase3_serial.py` driver — headless via xvfb-run)
(the startup thread was archived after this plan was written).
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

- [x] Re-derive the per-component timings on a throwaway copy.
      - `cp dpd.db /tmp/dpd_load_test.db` (never benchmark the live db).
      - Time each `initialize_db()` component separately, warm cache, three
        repetitions, medians.
      → verify: table of component → median seconds pasted into this plan,
      alongside the spec's 3.19/1.51/1.12 s figures. State the new total.

  **Re-derived component table** (`/tmp/dpd_load_test.db`, warm cache,
  median of 3, `artifacts/phase1_profile.py`, 2026-09-19):

  | component | spec (2026-09-18) | re-derived |
  |---|---|---|
  | `load_corpus()` | 3.19 s | 1.898 s |
  | `get_all_decon_no_headwords()` | 1.51 s | 2.221 s |
  | `RelationshipDetector(corpus)` | 1.12 s | 0.687 s — measured here as a component, but at profiling time still INSIDE `initialize_db()` via the eager line (see Phase 4 correction) |
  | 8 small sets | ~0.4 s | 0.316 s |
  | **total** | **6.90 s** | **5.124 s** |

  The total at profiling time still included the eager detector line in
  `initialize_db()` — see the Phase 4 correction below. Remaining critical
  path at that stage: decon scan + corpus load + detector ≈ 4.8 s.

- [x] Sweep the consumers.
      - Exhaustive grep (not from memory): every attribute read on
        `DpdHeadword` rows obtained via `load_corpus()` / `db_manager.db`,
        outside `db/models.py` — this bounds any `load_only()` column list.
      - Grep every reader of `_relationship_detector` / `relationship_detector`
        and every writer of `lookup.deconstructor` / `lookup.headwords`
        (invalidation points for a db_info cache).
      → verify: consumer lists pasted into this plan; any direct
      private-detector reader flagged for Phase 4.

  **Corpus consumers** (rows from `load_corpus()` / `db_manager.db`):

  1. `tools/synonym_variant.py` (RelationshipDetector): `lemma_1`, `pos`,
     `meaning_1`, `root_key`, `family_root`, `family_word`, `construction`
     (via `construction_clean`), `root_base` (via `root_base_clean`),
     `freq_data` (via `freq_data_unpack`).
  2. `gui2/database_manager.py` internals: `make_inflections_lists`
     (`inflections`, `inflections_api_ca_eva_iti` via `inflections_list_all`,
     `meaning_1`); `make_pass2_lists` (`source_1`, `source_2`, `example_1`,
     `meaning_1` via `is_missing_sutta_example`; `suffix`; inflections);
     `make_compound_components_map` (`grammar`, `construction`, `suffix`,
     inflections).
  3. `gui2/tests_tab_controller.py` → `db_tests/db_tests_manager.py`
     `getattr(headword, test_column)` — **data-driven** from
     `db_tests/db_tests_columns.tsv`: 45 distinct columns (antonym, cognate,
     commentary, compound_construction, compound_type, construction,
     derivative, derived_from, example_1, example_2, family_compound,
     family_idioms, family_root, family_set, family_word, grammar, lemma_1,
     lemma_2, link, meaning_1, meaning_2, meaning_lit, neg, non_ia, notes,
     origin, pattern, phonetic, plus_case, pos, root, root_base, root_key,
     root_sign, sanskrit, source_1, source_2, stem, suffix, sutta_1, sutta_2,
     synonym, synonyms, trans, verb).

  **Consequence:** `load_only()` to a fixed column list is dead — the tests
  tab can read any of 45+ TSV-driven columns on corpus rows, and a missed
  column degrades to per-row lazy queries. Only the current 5 deferred HTML
  columns are provably unread by every consumer.

  **Detector readers:** public `get_relationship_detector()` only
  (`gui2/dpd_fields.py:1351,1392`); `invalidate_relationship_detector()`
  (`gui2/filter_component.py:463`). **Zero direct private
  `_relationship_detector` readers.**

  **lookup writers:** gui2 never writes `lookup`; only the db build pipeline
  does (`db/` modules, orchestrated via `db/app/create_app_db.py`).

- [x] Benchmark the candidate mechanisms on the throwaway copy.
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

  **Benchmark table** (`/tmp/dpd_load_test.db`, median of 3,
  `artifacts/phase1_benchmark.py`):

  | mechanism | median | verdict |
  |---|---|---|
  | (a) decon: current ORM query | 1.384 s | baseline |
  | (a) decon: core select | 1.387 s | KILLED — no faster |
  | (a) decon: pickle.loads cache | 0.139 s | see below — pickle form killed |
  | (a) decon: JSON cache read | 0.170 s | **SHIP** — matches db_info text-column precedent, no base64 needed |
  | (a) decon: pickle via base85 in text column | 1.376 s | KILLED — decode dominates |
  | (b) corpus: current query+defer | 2.157 s | baseline |
  | (b) corpus: execute(select)+defer | 2.102 s | KILLED — within noise |
  | (b) corpus: raw core projection | 5.579 s | KILLED — 2.6× slower |

  Spot-checks passed: cached set identical to live (724,852 keys);
  corpus variants produced identical snapshots (lemma_1 first 100,
  inflections/freq_data sums over first 1,000 rows).

## Phase 2 — Deconstructor scan fix

- [x] Implement the surviving variant from Phase 1 (a). If it was a
      `db_info` cache: write the cache wherever lookup is rebuilt, invalidate
      on every writer found in the sweep, and load from cache on startup
      with a correct fallback to the live query when absent.
      → verify: `uv run pytest tests/gui2/` passes; a quick script prints
      identical set contents before/after; the component's timing in the
      Phase 1 table.

  **Shipped:** JSON cache in `db_info` under key `all_decon_no_headwords`
  (JSON, not pickle: 0.170 s vs 0.156 s load, and it matches the db_info
  text-column precedent; pickle needed base85 → 1.4 s, killed).

  - `tools/cache_load.py`: `load_/save_/invalidate_decon_no_headwords_cache()`.
  - `tools/lookup_sync.py`: `sync_lookup_column` invalidates the cache
    whenever the `headwords` or `deconstructor` column syncs — this covers
    every writer found in the sweep (`inflections_to_headwords`,
    `suttas_to_lookup`, `deconstructor_output_add_to_db`); all other syncs
    touch unrelated columns.
  - `scripts/build/decon_cache_update.py` (new): rebuilds the cache; hooked
    into `generate_components.py` right after the last lookup writer
    (`db/epd/epd_to_lookup.py`).
  - `gui2/database_manager.py`: `get_all_decon_no_headwords()` reads the
    cache; on a miss falls back to the live query and refreshes the cache
    (self-heal), so a stale cache costs one slow launch, never a wrong set.

  **Verification:** set contents identical (724,852 keys, live vs cached);
  cached read 0.179 s vs live 1.186 s on the throwaway copy; invalidation
  fires only for headwords/deconstructor syncs; `tests/gui2/` 297 passed;
  new `tests/tools/test_decon_no_headwords_cache.py` 10 passed.

- [x] Lint the touched file(s).
      → verify: `uv run ruff check --fix <files>`, `uv run ruff format
      <files>`, `uv run pyright <files>` all clean.

  All clean (ruff check, ruff format, pyright 0 errors).

## Phase 3 — Corpus load fix — SKIPPED (mechanism killed)

Per the Architecture Decisions, a mechanism that doesn't benchmark is
killed and the phase skipped with the reason recorded:

- `load_only(<verified list>)` — killed in the consumer sweep: the tests
  tab reads 45+ data-driven columns on corpus rows; any missed column
  degrades to per-row lazy queries.
- raw core projection (`select(*cols)` + `DpdHeadword(**row._mapping)`) —
  benchmarked at **5.579 s vs 2.157 s** current: declarative constructor
  overhead exceeds the query-machinery saving.
- `execute(select(DpdHeadword))` — 2.102 s, within noise of 2.157 s.

No surviving mechanism → no change made; `load_corpus()` stays as-is
(Query + 5 deferred HTML columns, all provably unread by every consumer).

## Phase 4 — Lazy RelationshipDetector — CORRECTED, DONE IN THIS THREAD

**Correction (2026-09-19, after user asked what else can be improved):**
the record below claiming the detector was already lazy was **wrong** —
`initialize_db()` still contained the eager
`self._relationship_detector = RelationshipDetector(self.load_corpus())`
line. The git -S search had only shown when the line was *introduced*, not
removed, and the GUI arithmetic was misread. A fresh-process benchmark
(`artifacts/phase5_benchmark2.py`) settled it: the eager line costs
**0.79–0.91 s** on the db-loaded critical path.

What was done in this thread:

- Removed the eager construction from `initialize_db()`; the existing
  `get_relationship_detector()` lazy accessor (from #157) now serves reads.
- `gui2/main.py` `_warmup_in_background` now pre-builds the detector right
  after the db load, off the critical path, so the first synonym click
  doesn't pay for it either.
- Fast corpus hydration (`__new__` + `__dict__.update`) was benchmarked for
  the remaining corpus cost: 1.811–2.105 s vs 1.962–2.333 s ORM — marginal
  (~0.2 s), hydration is not the bottleneck (SQLite row decode is). KILLED,
  ORM entities stay session-attached.

→ verify: `uv run pytest tests/gui2/` passes; timed_gui launch shows the
  db-loaded stamp without detector time; related entries still work
  (accessor unchanged; detector output equality verified on samples in
  `phase5_benchmark2.py`).

- [x] Move construction out of `initialize_db()` into a lazy accessor;
      fix any private-attribute readers from the Phase 1 sweep.

- [x] Lint the touched file(s) (`gui2/database_manager.py`, `gui2/main.py`).
      → verify: ruff + pyright clean.

Harness: copy `timed_gui.py`/`run_phase3_serial.py` into this thread's
`artifacts/` with the archive path fix, and drive from there.

## Phase 5 — Measure and verify the whole

- [x] Record post-change figures.
      → verify: three runs via `run_phase3_serial.py` (headless); paste all
      three; state the median db-loaded. **Target: ≤ 4 s median.** If
      missed, say so here and explain — do not round into a pass.

  **Final figures (after the Phase 4 correction):** serial protocol
  (xvfb, three launches, `artifacts/phase5_serial.log`, 2026-09-19):
  db-loaded **0.78 / 0.82 / 0.85 s → median 0.82 s** (target ≤ 4 s: met).
  ALL TABS WARMED 8.32 / 9.24 / 9.10 s; baseline 2026-09-18: db-loaded
  median 6.90 s, warmed median 10.33 s — end-to-end warm also improved.

  Why db-loaded collapsed: `load_corpus()` (3.4-4.3 s cold) was only on
  the critical path because the eager detector line pulled it in. With
  the detector lazy, the corpus loads on demand (lock-guarded,
  generation-guarded — the #157 machinery) and the detector pre-builds
  in the warm-up thread. `db_loaded` now gates the sets + decon cache,
  which is all the save paths actually read.

  **Intermediate figures, decon cache only, detector still eager —
  target missed at that stage:** serial db-loaded 5.30 / 5.32 / 5.29 →
  median 5.30 s (baseline 6.90, −23%). The miss explanation (below) is
  what prompted the re-test that exposed the Phase 4 error:

  1. The target assumed the spec's component table would survive
     re-derivation. It didn't: the spec's corpus figure (3.19 s) was a
     warm-cache number. Under real launch conditions (fresh process,
     cold SQLite page cache) the same `load_corpus()` measures 3.4-4.3 s.
  2. The decon cache delivered its full benchmarked saving (−1.4 s).
  3. Every corpus mechanism in the plan benchmarked dead (see Phase 3).
     A post-kill extra benchmark (SQLite `mmap_size=1GB` on the
     connection) was also noise: 2.239 s vs 2.356 s baseline.
  4. The remaining floor was architectural: `load_corpus()` walks all
     ~1.4 GB of dpd_headwords pages to extract ~110 MB of read text.
     Fixing that means schema-level re-layout — out of scope for the db
     build pipeline. (Moot for db-loaded: the corpus is off the critical
     path entirely now.)

  Decon-cache-stage per-component GUI breakdown (cache hit,
  `artifacts/timed_gui_phase5.py`): lemma sets 0.28 s, pos 0.11 s, small
  sets 0.10 s, decon cache 0.23 s, load_corpus 3.42 s, eager detector
  0.79-0.91 s (`phase5_benchmark2.py`).

- [x] Repo-wide checks.
      → verify: `uv run pytest tests/` passes (slow deselected); `just
      typecheck` clean.

  1909 passed, 12 deselected (slow); pyrefly: 0 errors.

- [x] Ask the user for permission to run `coderabbit review --agent`, scoped
      to the touched files.
      → verify: permission asked, review run if granted, every finding fixed
      or recorded here with the rejection reason.

  Run during review (2026-09-19): 1 minor finding (move detector pre-build
  before tab warm-up) — rejected with reason, recorded in `review.md`.
  Independent reviewer subagent's 8 findings: 7 fixed, 1 rejected.
  Verdict PASSED — see `review.md`.
