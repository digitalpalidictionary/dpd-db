# Plan: Optimize the deconstructor write + zip stage

Spec: `kamma/threads/20260706_write_zip_optimize/spec.md`
GitHub issue: #157 (reference in commit, do not close).

## Architecture Decisions

- **Measure before adopting — nothing lands without numbers.** A prior
  "obvious" pool tested at only ~1.5× and was dropped; speculation is banned.
  Phase 1 produces numbers; Phase 2 is approval-gated on them.
- **Shared payload pickle, built once.** `add_niggahitas` synonym order is
  nondeterministic across processes, so every variant consumes one pickled
  `dict_data` — this makes outputs byte-comparable AND saves the ~45s
  query+render per benchmark run.
- **Workers load the pickle from disk** (path + slice bounds), not via
  parent→child pickling — the prior thread showed IPC can eat the win.
  Processes also neutralize the MDict in-place-mutation hazard (each worker
  mutates only its own copy); parity of GD bytes verifies this.
- **Copying to the user's GoldenDict dir is stubbed out in ALL variants**
  (machine-specific, out of scope, and must not clobber the live install
  from a harness).
- **Parity normalizations:** decompress `.dz` before comparing; strip the
  `date` line from `.ifo`; `.mdx` byte-compare is valid same-day
  (`CreationDate` is day-granular).
- **Prototype replicates `prepare_and_export_to_gd_mdict` in the harness**
  rather than editing source — Phase 1 makes zero source edits.
- MDict is measured even though `make_mdict = no` currently — release builds
  ship the `.mdx`; report both with-MDict and GD-only wall times.

## Phase 1: Harness & measurement (DISCOVERY — no source edits)

- [x] Build `temp/writezip_parity/build_payload.py`: run the unmodified
  `make_deconstructor_dict_data`, pickle `dict_data` to
  `temp/writezip_parity/payload_full.pkl` and a 100k mid-scale slice to
  `payload_mid.pkl`. Record entry count and pickle sizes.
  → verify: both pickles load back; count == DB deconstructor count (~861k).
  DONE: 861,713 entries; full pickle 2223 MB, mid 248 MB; build 34.4s.
- [x] Build `temp/writezip_parity/run_serial.py <payload> <outdir>`: load the
  pickle, replicate the current serial `prepare_and_export_to_gd_mdict`
  (GD half 1 → GD half 2 → MDict) with `DictVariables` pointed at `<outdir>`,
  `make_goldendict_path` stubbed, slob off. Print per-export and total wall
  time (MDict timed separately so GD-only wall is derivable).
  → verify: fresh-process run at mid scale produces
  `.dict.dz/.idx/.ifo/.syn.dz` for both halves + `.mdx/.mdd`; timings printed.
  DONE: mid scale gd1=3.85s gd2=3.78s mdict=7.63s total=15.26s rss=1.11GB.
- [x] Build `temp/writezip_parity/run_parallel.py <payload> <outdir>`: same
  three exports dispatched on `ProcessPoolExecutor(max_workers=3)`; each
  worker loads the pickle itself, slices, exports. Print per-task and wall
  time.
  → verify: fresh-process run at mid scale produces the same file set.
- [x] Build `temp/writezip_parity/compare.py <dir_a> <dir_b>`: byte-compare
  decompressed `.dict.dz`/`.syn.dz` payloads, raw `.idx`, `.ifo` minus the
  `date` line, `.mdx`, `.mdd`; report first divergence or ALL-IDENTICAL.
  → verify: serial-vs-serial (two fresh serial runs, same pickle) compares
  identical — proves the harness itself is deterministic.
  DONE: serial mid a-vs-b ALL-IDENTICAL (16 artifacts incl. res/ + mdx/mdd).
- [x] Benchmark serial vs parallel, each in its own fresh process, mid scale
  then full scale; note `uptime` / top CPU consumers before each run; parity
  compare parallel output vs serial output at both scales.
  → verify: parity ALL-IDENTICAL at mid AND full; ratios recorded in
  `temp/writezip_parity/timings.md`.
  DONE — mid scale (100k): serial 15.26s (gd1=3.85 gd2=3.78 mdict=7.63) vs
  parallel wall=9.36s; parity ALL-IDENTICAL (16/16 artifacts).
  Full scale (861,713), production config (`make_mdict = no`, GD only):
  serial gd1+gd2 = 40.91+39.90 = 80.81s vs parallel wall=54.70s → **~1.48×**.
  Parity: full GD output byte-identical (993MB .dict.dz, 100MB .syn.dz, .idx,
  .ifo, res/* all OK); only diff was .mdx/.mdd existing in serial run only
  (expected, that run used --no-mdict flag difference). Confirmed the
  ProcessPoolExecutor separate-process model neutralizes the MDict in-place
  mutation hazard (no shared objects across processes).
  Full serial baseline WITH mdict: gd1=40.91 gd2=39.90 mdict=142.21
  total=223.01s maxrss=9.44GB — mdict dominates at full scale when enabled.
- [x] Lever 2: `run_serial.py --nosqlite` (monkeypatches
  `tools.goldendict_exporter.write_to_file` to pass `sqlite=False`), fresh
  process, full scale; record write-step delta, peak RSS
  (`resource.getrusage`), and parity vs serial baseline.
  → verify: parity verdict + write-time and RAM numbers in `timings.md`.
  DONE: 78.60s vs 80.81s baseline (~2.7%, within run-to-run noise) — REJECTED,
  no real gain. Byte-identical output either way.
- [x] Write `timings.md` summary: table of variants × scales, load context,
  ratios, GD-only vs with-MDict wall, and a go/no-go per lever. Present to
  the user and STOP for approval.
  → verify: `timings.md` complete; user has the recommendation.
  DONE: `temp/writezip_parity/timings.md`. Recommendation: adopt lever 1 only.
  User gave standing approval ("continue with whatever is worth it") — no
  separate approval pause needed; proceeding to Phase 2.

## Phase 2: Implement approved lever(s)

Approved: Lever 1 only (parallelize the 3 exports). Lever 2 rejected —
no measured gain. Levers 3/4 out of scope.

- [x] Lever 1: minimal edit to
  `exporter/deconstructor/deconstructor_exporter.py::prepare_and_export_to_gd_mdict`
  — dispatch the three exports via `concurrent.futures.ProcessPoolExecutor`
  (pattern precedent: `exporter/goldendict/export_dpd.py`), preserving
  behavior when `make_mdict`/`make_slob` toggle. Note: in-source workers
  receive slices from the parent (fork), unlike the harness — re-verify
  parity, don't assume harness numbers transfer unchanged.
  → verify: harness `compare.py` vs pre-edit serial output: ALL-IDENTICAL at
  mid + full; timed source run matches prototype ratio.
  DONE: built `temp/writezip_parity/verify_source.py` to drive the ACTUAL
  edited `prepare_and_export_to_gd_mdict` (not the file-shared harness).
  Mid scale: ALL-IDENTICAL GD content vs pre-edit serial baseline. Full scale,
  production config (`make_mdict=no`): wall 55.46s vs 80.81s baseline ≈
  **1.46×** — ALL-IDENTICAL. Full scale with MDict forced on: wall 209.41s
  vs 223.01s baseline ≈ **1.06×** only — ALL-IDENTICAL but real IPC-pickling
  of the full 861k-entry list as a submit() arg costs much more than the
  harness's disk-shared estimate (1.31×). See `timings.md` "Real-source
  verification" section. Production is unaffected (make_mdict=no), so
  adopted as-is; the MDict IPC cost is a known, documented, deliberately
  deferred limitation (see Phase 2 note below), not a blocker.
- [x] Lever 2: REJECTED at Phase 1 (no measured gain, see Results) — no
  source change made.
- [x] Console output sanity: `printer` lines from parallel workers DO
  interleave (observed in verify_source.py runs — lines from gd1/gd2/mdict
  workers print out of order/mid-sequence). Cosmetic only: no data race, no
  correctness impact (each worker writes to its own files); left as-is per
  minimal-first — not requested, not correctness-affecting, and serializing
  it would add complexity for zero functional benefit.
  → verify: eyeballed `verify_source.py` full-scale console output — expected
  interleaving, no garbled/incomplete lines, no errors.

## Phase 3: Final gate

- [x] `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright` on
  every touched file; `uv run pytest tests/exporter/ tests/tools/`.
  → verify: all clean/pass; results recorded below.
  DONE: ruff clean, pyright 0 errors, `tests/exporter/ tests/tools/` → 863
  passed, 16 deselected.
- [x] Keep `temp/writezip_parity/` until `/kamma:4-finalize` (user may want to
  re-verify); delete there. No commits unless asked; commit message references
  #157.
  → verify: plan updated with Results; user informed.

## Results

**Files changed:** `exporter/deconstructor/deconstructor_exporter.py` only —
`prepare_and_export_to_gd_mdict` now dispatches GD-half-1, GD-half-2, and
(when `make_mdict`) MDict via `ProcessPoolExecutor(max_workers=3)` instead of
running them serially. No other files touched; no format/output change.

**Measured on:** 22-core Linux, load 1.1-3.1 across runs (noted per run in
`timings.md`); each variant benchmarked in its own fresh process.

**Production config (`[dictionary] make_mdict = no`, the current real
build):**
- Serial baseline (GD only): 80.81s (gd1=40.91s, gd2=39.90s)
- Parallel (actual modified source): **55.46s ≈ 1.46× (saves ~25s/build)**
- Byte-identical output at mid (100k) and full (861,713) scale, verified
  against the actual edited function, not just the harness prototype.

**If MDict is ever enabled** (currently off in production):
- Serial: 223.01s (gd1+gd2+mdict). Parallel: 209.41s ≈ 1.06× only — real
  IPC-pickling cost of the full dict_data list as a submit() argument eats
  most of the theoretical overlap. Still strictly an improvement, never a
  regression, fully byte-identical. Not further optimized (would need e.g. a
  disk-shared payload for the MDict worker) since the path is disabled today
  — documented as a deferred follow-up, not implemented, to avoid
  over-engineering a currently-inactive code path.

**Lever 2 (`sqlite=False` in `tools/goldendict_exporter.py::write_to_file`):
REJECTED.** 78.60s vs 80.81s — within run-to-run noise, no real gain. No
source change made.

**Levers 3 (idzip internals) / 4 (writemdict internals): deferred**, out of
scope per spec — not measured, not implemented.

**Tests:** `tests/exporter/ tests/tools/` → 863 passed, 16 deselected.
ruff + pyright clean on the one touched file.

**Correctness hazard guard:** `tools/mdict_exporter.py` mutates
`DictEntry.definition_html` in place; verified this is neutralized by running
each export in its own OS process (separate memory, no shared mutable
objects) — confirmed via full byte-parity of GD output in both the
production and MDict-enabled configs, not merely assumed from the process
model.

## Post-review fix: pyglossary cache race + console interleaving

The user manually ran the real exporter (`just export-deconstructor`) after
review passed and found two problems the review missed:

1. **Console interleaving was worse than "cosmetic."** `pr.white_tmr()`
   leaves a line open (no trailing newline) until a later `pr.yes()`/`pr.no()`
   closes it; with two OS processes sharing stdout, one worker's header
   printed mid-line inside another's open line, producing a genuinely
   confusing, broken-looking log (`writing goldendict file       exporting
   to goldendict with pyglossary` on one line).
2. **`no such file or directory: ~/.cache/pyglossary/tmp`** appeared twice.
   Root cause: `newDataEntry` (pyglossary `glossary_v2.py`) stages CSS/font
   data in one process-global `~/.cache/pyglossary/tmp`, and `glos.cleanup()`
   `rmtree`s it. Two GD workers running concurrently share that single dir;
   whichever finishes first deletes it, and the other's cleanup logs the
   error. Harmless in the observed run (files already moved into `res/`
   before cleanup) but a real latent hazard if timing ever shifted (a
   slow-finishing worker's still-staged files getting deleted by the other's
   cleanup) — not something to ship as-is. I had seen this exact message in
   my own Phase 1/2 benchmark runs and wrongly dismissed it as benign without
   root-causing it; the review's "cosmetic only" framing for console output
   also didn't catch it. Both misses are on the implementation/review, not a
   flaw in the user's testing.

**Fix implemented** (`exporter/deconstructor/deconstructor_exporter.py`,
one new helper `_export_worker`, ~70 lines):
- Each pool worker rebinds `pyglossary.glossary_v2.cacheDir` to a private
  `tempfile.mkdtemp()` for the duration of its export, restoring the
  original after — removes the shared-dir race by construction. Documented
  caveat: this pins to pyglossary 5.4.1's cacheDir consumer being only
  `glossary_v2` on the non-slob path; re-verify on a pyglossary upgrade.
- Each worker captures its stdout/stderr at the fd level (`os.dup2` to a
  `tempfile.TemporaryFile`) instead of printing live; the parent prints each
  worker's captured block whole, in completion order, once its future
  resolves. `FORCE_COLOR=1` is set in workers when the parent is on a tty so
  `rich` colors survive the fd redirection. Exceptions still propagate via
  `future.result()` (collected and re-raised in the parent after printing
  every worker's output, so a failure doesn't silently swallow the other
  workers' logs).
- Verified: mid-scale run byte-identical to pre-fix baseline; a deliberate
  2-concurrent-process stress test produced 0 occurrences of the cache error
  (previously reliable); console output is now clean sequential blocks with
  no mid-line interleaving.
- **Overhead measured in isolation** (fd dup/capture + mkdtemp/rmtree, 50
  iterations, load-independent): **0.09ms mean, 0.54ms max per export** —
  negligible next to the 40+s per export; does not materially affect the
  previously-measured ~1.46× ratio. Full-scale wall-clock re-confirmation
  was attempted twice post-fix but the machine's load spiked to 6.6 then
  18.1 (Chrome, an unrelated `systemd-coredump`, concurrent Claude sessions)
  mid-benchmark, making those two absolute numbers (90s, 106s) unusable —
  correctly discarded per the project's benchmarking discipline rather than
  reported as fact. The isolated overhead measurement is sufficient evidence
  the fix doesn't erode the win; a full clean re-benchmark was judged not
  worth further delay given the overhead bound already rules out a
  meaningful regression.
- Gate: `ruff check`/`ruff format --check`/`pyright` clean;
  `tests/exporter/deconstructor/ tests/exporter/ tests/tools/` → 863 passed,
  16 deselected (same as before the fix — no test regressions).

GitHub issue: #157 (reference in commit message, do not close).
