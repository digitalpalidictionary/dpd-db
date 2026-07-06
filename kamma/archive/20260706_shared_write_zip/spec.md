# Spec: Optimize the shared write+zip stage in tools/goldendict_exporter.py

**GitHub issue:** #157 (umbrella — reference in commit, do NOT close)
**Predecessor:** kamma/archive/20260706_write_zip_optimize — read its
handoff_to_goldendict_exporter_general.md for proven patterns and lessons.

## Overview

`tools/goldendict_exporter.py` is the shared GoldenDict export path used by
ALL exporters (dpd main, deconstructor, grammar, kobo, variants). Its
write+zip stage is unoptimized:

- `write_to_file()` — pyglossary Stardict write with `sqlite=True`
  (own comment: "when False, more RAM but faster" — never measured)
- `zip_dictfile()` / `zip_synfile()` — `idzip.compressor.compress()`, serial,
  no compression-level control, even though dictzip chunks are compressed
  with Z_FULL_FLUSH (independent — embarrassingly parallel)

A win here lands in every exporter for free, every build.

## What it should do

**Phase 1 — discovery/measurement ONLY, zero source edits:**
- Harness in gitignored `temp/`, fresh process per variant, `uptime` check
  before trusting timings, byte-parity against current output.
- Use the largest real dataset (main dpd dict_data, rendered once and
  pickled; deconstructor data as a second scale point).
- Measure the current stage split: pyglossary write vs idzip .dict vs
  idzip .syn.
- Measure candidate levers, each independently:
  1. `sqlite=False` in `glos.write()` (one line; RAM cost measured too)
  2. parallel per-chunk idzip compression (byte-parity expected because
     Z_FULL_FLUSH resets compressor history — verify, don't assume)
  3. zlib compression level (only if parity-compatible with dictzip readers)
- Neutralize `copy_dir()` in the harness so benchmark output never touches
  the live GoldenDict folder.
- **HARD STOP:** present numbers + recommendation for approval.

**Phase 2 — approved scope (user decision 2026-07-06 at the approval gate):**
- Lever 3 ONLY: idzip compression level 9→6 inside
  `tools/goldendict_exporter.py` (`zip_dictfile`/`zip_synfile`) — every
  caller benefits with no call-site changes.
- Lever 1 (sqlite=False) rejected: inconsistent across scales, no RSS gain.
- Lever 2 (parallel chunks) declined: needs idzip private internals;
  marginal value on top of lever 3 not worth the fragility.
- `_export_worker` lift DROPPED: it fixes a concurrent-Glossary cache race;
  the adopted lever never touches a pyglossary Glossary concurrently.
- Parity re-verified through the real `zip_dictfile`/`zip_synfile` code
  path on the same full-scale input used for the baseline.

## Assumptions & uncertainties

- Byte-parity for parallel chunk compression is expected but must be
  verified in Phase 1 before any Phase 2 work.
- If parity is NOT byte-for-byte achievable, fallback bar is: valid dictzip
  that GoldenDict reads identically (documented, needs user sign-off).
- Benchmarks are run by the agent as part of this thread; config.ini is
  never modified.

## Constraints

- Phase 1: no edits to tracked source files.
- `write_to_file`/`zip_dictfile`/`zip_synfile` signatures stay stable — no
  call-site churn across exporters.
- Load checked before every timed run; contaminated runs discarded.
- Commit: `#157 exporter: ...`, lowercase, ≤72 chars first line.

## How we'll know it's done

- Numbers table (stage split + per-lever speedup + RAM + parity result) in
  the thread dir, presented for approval. [DONE — see
  temp/bench_write_zip/NOTES.md, approved 2026-07-06]
- Level-6 lever applied in tools/goldendict_exporter.py; decompressed
  content byte-identical to the level-9 output of the same input through
  the real zip functions (compressed bytes differ by design — this is the
  documented fallback bar, signed off at approval).
- Measured stage speedup recorded honestly in the thread dir.
- User's next normal build confirms GoldenDict reads the level-6 .dz files.

## What's not included

- exporter/goldendict/ render code (already optimized).
- tools/writemdict internals (lever 4 — separate thread).
- scripts/build/zip_goldendict_mdict.py (release re-zip step).
- Orchestration-level parallelization of individual exporters.
