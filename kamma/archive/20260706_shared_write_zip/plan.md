# Plan: Optimize shared write+zip in tools/goldendict_exporter.py

**GitHub issue:** #157 (reference in commit, do not close)
**Spec:** ./spec.md

## Architecture Decisions

- Optimize inside `tools/goldendict_exporter.py` only — all exporters
  benefit with zero call-site changes. No orchestration-level parallelism.
- Harness lives in gitignored `temp/bench_write_zip/`; each timed variant
  runs in a fresh process; `uptime` checked before every timed run.
- Correctness bar (updated at approval gate): compressed bytes necessarily
  change with the level change, so parity = **decompressed content is
  byte-identical** to the same input compressed at the old level, plus
  round-trip `gzip.decompress()` verification. This is the spec's documented
  fallback bar, signed off with the lever-3 approval.
- Harness monkeypatches `copy_dir` to a no-op — benchmark output must never
  overwrite the live GoldenDict folder
  (`/home/bodhirasa/MyFiles/2_Resources/GoldenDict`).
- Dataset: main dpd `dict_data` (largest, rendered once → pickled to temp/),
  deconstructor real .dict/.syn content as second scale point. config.ini
  never modified.
- `_export_worker` lift: DROPPED at approval gate — not applicable to the
  adopted lever (no concurrent pyglossary `Glossary` use anywhere in it).
- NOTICED — NOT TOUCHING:
  `resources/other-dictionaries/vendor/dpd_tools/goldendict_exporter.py` is
  a vendored copy of the same module inside the other-dictionaries
  submodule; out of scope (submodule has its own update rules).

## Phase 1 — Discovery & measurement (no source edits)

- [x] Read idzip's compressor source to confirm chunk framing and whether
      per-chunk parallel compression can be byte-identical
      → verify: written note in temp/bench_write_zip/NOTES.md citing the
      exact idzip code lines (member header, chunk table, Z_FULL_FLUSH)
      — DONE, confirmed Z_FULL_FLUSH makes chunks independent
- [x] Build dataset pickles: render main dpd dict_data once, pickle to
      temp/bench_write_zip/; reuse deconstructor data list the same way
      → verify: pickles load in a fresh process, entry counts match source
      — DONE (mid 30k, full 89,143); used decompressed real .dict.dz/.syn.dz
      instead of re-rendering deconstructor for the zip-lever benchmarks
      (equivalent real data, avoids an extra ~minutes-long render)
- [x] Baseline stage split at full scale: pyglossary write (sqlite=True) vs
      zip_dictfile vs zip_synfile, fresh process, low load confirmed
      → verify: timings table in NOTES.md with load average recorded — DONE
- [x] Lever 1: sqlite=False write, fresh process; record time + peak RSS +
      byte-parity of resulting .dict/.idx/.syn vs baseline
      → verify: parity result + numbers in table — DONE, NOT ADOPTED
      (inconsistent direction across scale, no RSS difference)
- [x] Lever 2: prototype parallel per-chunk idzip compression in the
      harness; record time + byte-parity of .dict.dz vs serial idzip
      → verify: cmp reports identical, speedup recorded — DONE, byte-identical
      confirmed, 2.86-2.98x at 8 workers; optional stretch-goal (see NOTES.md
      scope note re: idzip private-API dependency)
- [x] Lever 3: compression-level variants if parity-compatible; else
      document why skipped
      → verify: numbers or skip-rationale in NOTES.md — DONE, round-trip
      byte-identical to plain content confirmed, 3.37x combined at level 6;
      STRONG ADOPT
- [x] HARD STOP: present numbers table + go/no-go recommendation per lever;
      await approval
      → verify: user approval received before any Phase 2 task — presented
      and APPROVED 2026-07-06 (lever 3 only; drift task dropped).
      **DRIFT FLAGGED:** the "lift _export_worker" Phase 2
      task (pyglossary cacheDir race + fd capture) does not apply to either
      adopted lever — both operate on already-written plain files via raw
      zlib, never touching a pyglossary Glossary instance concurrently. See
      NOTES.md "Scope note" section. Recommend dropping that task pending
      user decision.

## Phase 2 — Implement approved levers (approved 2026-07-06)

**Approved scope:** Lever 3 only (idzip compression level 9→6) in
`zip_dictfile`/`zip_synfile`. Lever 1 (sqlite=False) rejected — inconsistent
across scale. Lever 2 (parallel chunks) declined — depends on idzip private
internals for ~3x additional gain on top of an already-strong win.
**_export_worker lift task DROPPED** — confirmed not applicable (see
NOTES.md "Scope note"); neither adopted lever touches a pyglossary
`Glossary` instance concurrently, so the cacheDir race it fixes doesn't
occur here.

- [x] Preserve the "before" evidence: decompress the level-9 outputs still
      on disk from the Phase 1 baseline run
      (`temp/bench_write_zip/out_baseline_full/bench/bench.dict.dz` +
      `bench.syn.dz`, produced from `dict_data_full.pkl` by the REAL
      `zip_dictfile`/`zip_synfile`) and save the plain bytes as
      `before_dict.raw`/`before_syn.raw`
      → verify: files exist, sizes match the plain sizes logged in Phase 1
      — DONE: 855,761,583 / 408,418,009 bytes. Note: the on-disk baseline
      .dz files are from the sqlite=false variant run (same out dir,
      overwrote sqlite=true) — acceptable because both variants produced
      byte-identically-sized .dz outputs and sqlite only affects the write
      path; the after-run comparison uses sqlite=true anyway.
- [x] Add a module constant `IDZIP_COMPRESSION_LEVEL = 6` (with a short
      why-comment: synonym-list content is pathologically slow at
      Z_BEST_COMPRESSION for ~1-3% size gain) and a small
      `_idzip_compress()` helper in tools/goldendict_exporter.py that sets
      `idzip.compressor.COMPRESSION_LEVEL` around the call (try/finally
      restore); `zip_dictfile`/`zip_synfile` call the helper. Their
      signatures stay unchanged — no call-site churn.
      → verify: uv run ruff check --fix tools/goldendict_exporter.py &&
      uv run ruff format tools/goldendict_exporter.py &&
      uv run pyright tools/goldendict_exporter.py — all clean
      — DONE, all three clean
- [x] Real-source-path parity + timing after the edit: re-run
      `bench_baseline.py full true` in a fresh process (it imports the REAL
      zip_dictfile/zip_synfile from tools/, same pickled input as the
      Phase 1 baseline — same input, same code path, only the level change
      in between; no render nondeterminism in the comparison). Decompress
      the new .dict.dz/.syn.dz and byte-compare against
      before_dict.raw/before_syn.raw. Record new stage timings vs the 90.0s
      baseline in NOTES.md, load checked.
      → verify: cmp on decompressed content is identical; timings recorded
      — DONE: decompressed content byte-identical both files (855,761,583
      and 408,418,009 bytes); write+zip 90.0s → 35.94s (2.50x), zip stage
      3.36x, size cost +1.0% dict / +2.9% syn; load 1.80 at run time
- [x] Run test suite
      → verify: uv run pytest tests/ passes (note pre-existing failures)
      — DONE: 1204 passed, 9 failed — all 9 in tests/exporter/analysis/,
      confirmed pre-existing by running on a clean (stashed) tree with
      identical failures; unrelated to this change
- [ ] Live verification note: the user's next normal build
      (exporter/goldendict/main.py etc.) produces level-6 .dz outputs in
      exporter/share/ and the GoldenDict copy — confirm GoldenDict opens
      and displays entries normally. Agent does NOT run the production
      export unasked (it overwrites exporter/share/ and the live
      GoldenDict dir).
      → verify: user confirms next build + GoldenDict lookup works

## Wrap-up

- [ ] Update NOTES.md findings into thread dir; instruct user to run
      /kamma:3-review
      → verify: review.md produced by review step
