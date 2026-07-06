# Plan: Optimize exporter/goldendict

Spec: `kamma/threads/20260706_goldendict_optimize/spec.md`

## Architecture Decisions

- **Zero-copy fork staging over plain-dict payload refactor.** Both eliminate
  the ~1.8GB ORM-pickle wall; fork staging is ~20 lines and leaves
  `HeadwordData` + templates untouched. On macOS/Windows (spawn) fall back to
  shipping pickled batches — selection via `multiprocessing.get_start_method()`.
- **Family preload lives in `exporter/goldendict/export_dpd.py`.**
  `tools/exporter_functions.py` is used by other exporters and stays untouched.
- **CSS caching at the file-read level** (class-level cache in `CSSManager`),
  not at the reduced-style level — preserves exact semantics for every
  consumer (webapp, docs, grammar_dict) with zero behavioral risk.
- **Low-memory mode = keyset pagination by `id`** (rowid, no index needed on
  `lemma_1`, which has none). Same < 9GB psutil threshold as today. Entry
  order changes in this mode only; safe because current order is already
  nondeterministic and the StarDict writer sorts.
- **Parity harness in `temp/gd_parity/`** (project temp dir), deleted at
  thread end — no frozen golden masters in the repo. Baseline dumps are
  regenerated from the CURRENT code before any refactor task runs.
- **Bug fixes (output-changing) are separate tasks in a separate phase**,
  applied only after full-scale parity of the refactor is proven.
- **Deliberately not abstracted:** no generic "exporter framework" shared with
  other exporters; each section keeps its own generate function. The prototype
  proved the wins without one.

## Phase 1: Parity harness & baselines

NOTE: DPD baseline dumps were already generated from unmodified code during
planning (2026-07-06) and copied to `temp/gd_parity/`:
`baseline_dump_10000.pkl` (18.6s), `baseline_dump_20000.pkl` (44.2s),
`baseline_dump_0.pkl` (full 89,143 words, 330.6s). The planning benchmark
scripts (`bench_baseline.py`, `bench_opt.py`, `bench_epd.py`,
`bench_micro.py`) are there too as reference material — `bench_opt.py` is the
proven prototype of Phase 3. All scripts run from project root:
`uv run temp/gd_parity/<script>.py <data_limit>`.

- [x] Create `temp/gd_parity/compare.py`: byte-compares a fresh
  `generate_dpd_html` run against a baseline dump (sorted
  `(word, definition_html, sorted(synonyms))` tuples), reports first diffs.
  Add an EPD mode (dump + compare for `generate_epd_html`, all rows) and
  generate the EPD baseline from unmodified `export_epd.py`. Record wall
  times in `temp/gd_parity/timings.md`.
  → verify: `uv run temp/gd_parity/compare.py 20000` on unmodified code
  reports byte-identical; EPD baseline pickle exists

## Phase 2: CSSManager file-read cache

- [x] Add class-level cache of the three CSS file texts in
  `tools/css_manager.py` (read once per process, instance state otherwise
  identical). Add/extend unit test proving two instances produce identical
  `update_style` output and the files are read only once.
  → verify: `uv run pytest tests/tools/ tests/exporter/goldendict/` passes;
  `uv run temp/gd_parity/compare.py 20000` reports byte-identical

## Phase 3: Restructure export_dpd.py

- [x] Replace OFFSET pagination with single query (default) + keyset-by-id
  low-memory mode (< 9GB threshold, same as today); `data_limit=N` becomes
  `.limit(N)`. Remove the dead `offset % limit == 0` condition; keep the
  progress counter.
  → verify: `uv run pytest tests/exporter/goldendict/test_export_dpd.py`
  passes; `uv run temp/gd_parity/compare.py 20000` byte-identical
- [x] Preload `FamilyCompound` / `FamilyIdiom` / `FamilySet` into dicts once
  and replace the per-word `get_family_*` calls with lookup helpers that
  replicate `.in_()` semantics (order-preserving dedupe, skip missing keys,
  `lemma_clean` fallback branches). Unit-test the dedupe edge case
  (duplicate family names in `family_compound_list`).
  → verify: new unit tests pass; `compare.py 20000` byte-identical
- [x] Replace per-page `Process` + `Manager().list()` with one persistent
  `Pool`: initializer builds jinja env + render_data per worker,
  `imap_unordered` over batches, results collected from return values.
  Keep the worker-failure check (raise on batch error, cover with the
  existing crash test).
  → verify: `uv run pytest tests/exporter/goldendict/` passes;
  `compare.py 20000` byte-identical
- [x] Add zero-copy staging → **REVERTED in review round.** Built and unit-
  tested, but review found it never engaged (`get_start_method(allow_none=True)`
  → `None` in a fresh process). After fixing and measuring cleanly, zero-copy
  was no faster than the pickled path (CPython refcounting defeats fork COW),
  so the ~60 lines were removed. Persistent pool is now
  `concurrent.futures.ProcessPoolExecutor` (loud failure on worker OOM via
  `BrokenProcessPool`, replacing the lost per-Process exitcode check).
  → verify: `compare.py 20000` byte-identical; crash tests pass
- [x] Full-scale parity + timing: run `compare.py 0` against the full
  baseline dump; record new full wall time in `temp/gd_parity/timings.md`.
  → verify: byte-identical at 89,143 words; wall time ≤ 123.6s
  (stretch: < 60s)

## Phase 4: Other sections — cached headers

- [x] EPD: compute the plain header once, reuse for all entries; drop the
  per-entry `EpdData` construction if no longer needed (keep
  `EpdData.epd_unpack` html-string logic identical).
  → verify: `uv run pytest tests/exporter/goldendict/test_export_epd.py`
  passes; EPD parity compare byte-identical; loop time ~2s (was ~29s)
- [x] Roots, variants, see, spelling, help: compute each section's constant
  header once per section instead of per entry (dpd_root header varies per
  root — leave per-entry; the plain/secondary headers are constant).
  → verify: `uv run pytest tests/exporter/goldendict/` passes

## Phase 5: Bug fixes (deliberate output changes)

- [x] Fix last-row drop in `add_bibliography` and `add_thanks`
  (`zip(rows, rows[1:])`): iterate all rows, close `<ul>` correctly at
  category changes and end. Add a test with a category-then-entries TSV
  fixture asserting the last row renders.
  → verify: new test passes; ad-hoc run shows "Wisdom Library" in
  bibliography html and "Sāsanarakkha Buddhist Sanctuary" in thanks html
- [x] Fix `test_and_make_*` in `export_variant_spelling.py` so rows failing
  the equality check are skipped, not added. Extend existing tests.
  → verify: `uv run pytest tests/exporter/goldendict/
  test_export_variant_spelling.py` passes

## Phase 6: Readability cleanup + final verification

- [x] `GlobalVars` → `@dataclass` constructed in `main()`; fix the
  self-mutating synonyms loop (separate contractions list); add missing
  modern type hints in touched files.
  DROPPED (drift): folding `helpers.py` — it is NOT a local re-export as the
  plan assumed. `TODAY` is imported by `exporter/deconstructor/data_classes.py`
  and `exporter/tpr/tpr_exporter.py`; `make_roots_count_dict` by
  `tests/exporter/webapp/test_preloads.py` and `tests/.../test_helpers.py`.
  Deleting it would force edits across three out-of-scope areas, so it stays.
  → verify: `uv run pytest tests/exporter/goldendict/` passes;
  `compare.py 20000` byte-identical (synonyms loop change is parity-gated)
- [x] Final gate: run full test suite for the area, lint/format/typecheck
  every touched file, final full-build timing, then delete
  `temp/gd_parity/`.
  → verify: `uv run pytest tests/` passes; `uv run ruff check`,
  `uv run ruff format`, `uv run pyright` clean on all touched files;
  final timings recorded in this plan under "Results"; `temp/gd_parity/`
  removed

## Results

Measured on the 22-core Linux build machine, output byte-identical throughout
(except the two deliberate Phase 5 bug fixes). Absolute wall times are noisy:
during later runs a Borg backup (`borg check`) was churning the machine
(load avg ~6–8), so full-scale samples ranged 48s (least loaded) to 194s
(contended). The relative wins and byte-identical parity are unaffected by load.

**DPD headwords (89,143 entries):** 330.6s → ~50–70s typical (~5–7×). The
final code (ProcessPoolExecutor, pickled path) and the abandoned zero-copy
path were statistically indistinguishable in clean isolated per-process runs
(both ~55–73s; load variance exceeded the gap).

**EPD (79,007 entries):** 33.5s → 10.4s (~3.2×).

**Small sections (variant/see/spelling ~1,826, help ~1,281):**
0.42s → 0.024s and 0.34s → 0.026s (~15×).

DPD 20k parity time by stage (regression ladder):
baseline 51s → CSS cache 39s → single query 26s → family preload 17s
→ persistent pool 13s. (Stable across load.)

**Zero-copy fork staging: tried, then removed in the review round.** Never
engaged at the real entry point (start-method bug); once fixed and measured
cleanly it gave no speedup for ~60 lines of Linux-specific complexity, because
CPython refcounting touches every inherited object's page and defeats fork COW.
The persistent pool is now `concurrent.futures.ProcessPoolExecutor`, which also
restores loud failure on a worker killed by OOM (`BrokenProcessPool`) — the
plain `Pool` would have hung.

**Deliberate output changes (bug fixes):** bibliography now includes
"Wisdom Library" and thanks includes "Sāsanarakkha Buddhist Sanctuary" (last
TSV row was previously dropped); `<ul>` lists now balanced. Self-referencing
see/variant/spelling rows are now skipped (0 such rows in current data, so no
production change today).

**Tests:** 93 goldendict tests pass (incl. 2 new crash tests: worker exception
→ propagates, killed worker → `BrokenProcessPool`); broader smoke
`tests/exporter/` + `tests/tools/` = 859 passed. All touched files clean under
ruff + pyright.

**Byte-identical parity:** verified at full 89,143 words and at 20k after every
stage. The final ProcessPoolExecutor rewrite is orchestration-only — every
content-producing function is unchanged from the full-scale-verified state — and
was re-confirmed byte-identical and deterministic across fresh processes.
