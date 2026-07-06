# Plan: Extend goldendict optimizations to the deconstructor (+ grammar)

Spec: `kamma/threads/20260706_deconstructor_grammar_optimize/spec.md`

## Architecture Decisions

- **Scope is narrow by evidence.** The six-pattern sweep is done; only the
  Python deconstructor exporter reproduces them at scale. Build logs confirm two
  real hotspots: deconstructor render loop **~255s** (primary, user's target) and
  grammar_dict "compiling html" **~84s** (measured secondary). Every other
  exporter is audited out. No shared "exporter framework" — each keeps its own
  generate fn.
- **Minimal-first ladder.** Win A (constant header once) is the smallest, safest,
  highest-confidence change and lands first. Win B (persistent pool) is added
  ONLY if Phase-1 measurement shows the content render still dominates after A.
- **Parity by streaming digest + capped-scale pickle**, not a full multi-GB
  pickle (deconstructor is ~10× goldendict's scale). Full input-order list is
  compared, because the downstream split is index-based (order-sensitive).
- **Pool preserves input order** (ordered batches, like goldendict) so the
  index-based half-split in `prepare_and_export_to_gd_mdict` is byte-identical.
- **grammar_dict is measure-gated**: its 84s is real, but the fix depends on the
  internal split — header-once hoist (minor), and/or a pool over the *distinct*
  grammar strings (render once in workers, map back onto 290k keys) if the
  distinct-render cost dominates; otherwise a written no-change finding.
- Harness in `temp/decon_parity/` (gitignored), deleted at thread end.

## Phase 1: Parity harness & measurement (DISCOVERY — no source edits)

- [x] Build `temp/decon_parity/dump.py`: run the UNMODIFIED
  `make_deconstructor_dict_data` at a `--limit N` and full scale; emit (a) a
  rolling SHA-256 digest over `(word, definition_html, tuple(synonyms))` in
  `dict_data` order, and (b) a full pickle at a capped mid scale (≤50k). Record
  wall time of the render loop. `compare.py` re-runs and diffs digest + pickle,
  reporting the first divergence.
  → verify: two unmodified runs at the same limit produce identical digests;
  mid-scale pickle round-trips.
- [x] Attribute the deconstructor loop cost **on current (post-CSS-cache) code**:
  measure the header-rebuild portion (`DeconstructorData._generate_header`) vs
  content `minify(render)` vs `_make_synonyms`, in isolated fresh-process
  micro-benchmarks. Record in `temp/decon_parity/timings.md`. Baseline from logs
  was ~255s pre-CSS-cache — confirm what remains. This decides whether Phase 3
  (pool) is needed on top of the Phase 2 header hoist.
- [ ] Attribute the grammar_dict 84s: count distinct grammar strings, measure
  render cost per cache-miss vs per-row overhead (cache lookup + dict insert),
  plus `make_data_lists`, in a fresh process. Decide grammar's fate (Phase 4
  header hoist and/or distinct-string pool, or a written no-change finding).
  Note machine load with each timing.
  → verify: `timings.md` has attributed costs for both exporters; Phase 3/4
  go/no-go decisions recorded with their measured justification.

## Phase 2: Deconstructor — constant header once (smallest change)

- [x] Hoist the constant header out of the per-entry path. Compute the
  deconstructor header string once (it has no per-entry variables) and reuse it;
  stop rebuilding it (fresh `CSSManager()` + template render + `update_style` +
  `squash_whitespaces`) for every row. Keep the exact same header bytes as
  `DeconstructorData.header` produces today. Adjust `DeconstructorData` /
  `data_classes.py` so the header is injected once rather than regenerated in
  `__init__`.
  → verify: `temp/decon_parity/compare.py` digest byte-identical at full scale
  AND mid-scale pickle byte-identical; loop wall time recorded (expect a large
  drop from the ~1M+ eliminated header rebuilds).
- [x] Add/extend a focused unit test asserting the header is computed once and
  is byte-identical to the previous per-entry value for a couple of sample rows.
  → verify: `uv run pytest tests/exporter/deconstructor/` passes (create the
  test dir/file mirroring source layout if absent).
  DONE: `tests/exporter/deconstructor/test_data_classes.py` (header constant +
  DeconstructorData contract); 8 tests pass; ruff+pyright clean.

## Phase 3: Deconstructor — persistent ProcessPoolExecutor — BUILT, MEASURED, SKIPPED

Tested empirically (not speculated) per the user's instruction. Prototype in
`temp/decon_parity/pool_bench.py`: picklable per-row payload, worker builds
jinja env + template + header once + speech_marks via initargs, in-order
assembly (index-based half-split preserved). BYTE-IDENTICAL at full scale.

- [x] Built + measured the pool. Result: render ~27-30s → ~14s (~2×) but
  end-to-end only ~1.5× (~49s → ~29s) because the query+payload setup (~15s) is
  serial/shared and result IPC limits the render win. Net ~13-15s absolute.
- [x] Decision: **SKIP.** Marginal absolute gain on an already-fast build does
  not justify pool machinery + crash tests on a 4-line loop. Recorded in
  `temp/decon_parity/timings.md`. (No source change; no crash tests needed.)

## Phase 4: grammar_dict — reduce the ~84s render (CONDITIONAL on Phase 1)

Only the change Phase 1 justifies. If the 84s is the export stage or otherwise
not worth touching, SKIP with a written finding.

- [x] Header hoist: `generate_grammar_header(jinja_env)` computes the constant
  "primary" header once; `GrammarData(lookup_entry, header)` takes it injected.
  Phase 1 showed `_generate_header` was 270µs/row and ~all of GrammarData's cost
  (`_process_grammar` 0.09s/30k, render 3.7s total); a pool was NOT warranted.
  → verify: grammar parity **byte-identical** — diffed the new `entry_html`
  against the pre-edit code (git HEAD) over all 285,344 distinct grammar strings,
  **0 diffs**; `tests/exporter/grammar_dict/` 8 pass; compile loop
  **85.5s → 4.43s (~19×)**, load ~2.2.
- [x] Distinct-string pool: NOT NEEDED — render is only 3.7s; header hoist alone
  captures the full win. Skipped by measurement.

## Phase 5: Final gate

- [x] Full area test suite + lint/format/typecheck on every touched file; Results
  filled below. Harness (`temp/decon_parity/`) KEPT for now so the user can
  re-verify / manually run the exporter; delete at `/kamma:4-finalize`.
  → verify: `uv run pytest tests/exporter/ tests/tools/` → **863 passed, 16
  deselected**; ruff + pyright clean on all 4 touched source/test files.

## Results

Machine: 22-core Linux. Absolute times noisy (load ~1.3-4.6 across runs); trust
ratios. All output **byte-identical** (order-insensitive on the nondeterministic
`add_niggahitas` synonyms).

**Deconstructor** (`exporter/deconstructor/`) — constant header was rebuilt
861,713× at ~232µs (~90% of the loop). Hoisted to once per run:
- Render loop: **~255s → 27s (~9.4×)**; parity 0 diffs / 50k vs unmodified code.

**grammar_dict** (`exporter/grammar_dict/`) — grammar cache is ~98% misses
(285,344 distinct / 290,771 rows), so the constant "primary" header was rebuilt
~285k× at ~270µs (~all of the cost). Hoisted to once per run:
- Compile loop: **85.5s → 4.43s (~19×)**; parity 0 diffs across all 285,344
  distinct grammar strings vs pre-edit code (git HEAD).

**Combined build saving: ~255s + ~85s ≈ 340s → ~31s (~309s off the makedict
run).**

**Deconstructor pool (Phase 3): built, measured, SKIPPED.** Byte-identical but
only ~1.5× end-to-end (~49s → ~29s, ~13-15s absolute) — the serial query/payload
setup (~15s) and result IPC cap the gain. Not worth the pool machinery on a
now-4-line loop. Details in `temp/decon_parity/timings.md`.

**Tests:** `tests/exporter/ tests/tools/` → 863 passed, 16 deselected. New:
`tests/exporter/deconstructor/test_data_classes.py`,
`tests/exporter/grammar_dict/test_data_classes.py`. ruff + pyright clean.

**Files changed:** `exporter/deconstructor/data_classes.py`,
`exporter/deconstructor/deconstructor_exporter.py`,
`exporter/grammar_dict/data_classes.py`, `exporter/grammar_dict/grammar_dict.py`
(+ 2 new test files). GitHub issue: #157.
