# Handoff: generalize the write/zip parallelization beyond the deconstructor

Written for a future thread, zero prior context assumed. This thread
(`20260706_write_zip_optimize`) only touched
`exporter/deconstructor/deconstructor_exporter.py` — the deconstructor is the
one exporter that splits into two GoldenDict halves, so it had 3 independent
exports (GD-half-1, GD-half-2, MDict) worth parallelizing. **No other
exporter was touched or measured in this thread.** This handoff exists
because the user expected work across the generic GoldenDict/MDict tooling
and asked for a handoff instead, given time spent.

## What's proven, reusable elsewhere

1. **The correctness pattern for parallelizing GD+MDict is now proven**:
   `tools/mdict_exporter.py`'s in-place mutation of `DictEntry.definition_html`
   is neutralized by running each export in its own OS process (separate
   pickled copies, no shared mutable state) — verified via full byte-parity,
   not assumed.
2. **The pyglossary shared-cache-dir race is real and NOT deconstructor-
   specific.** `pyglossary.glossary_v2.cacheDir` is a single process-global
   path (`~/.cache/pyglossary/tmp` on Linux); any two concurrent pyglossary
   exports in the same environment race on it. The fix (each worker rebinds
   `glossary_v2.cacheDir` to a private `tempfile.mkdtemp()`) currently lives
   **only** in `deconstructor_exporter.py`'s local `_export_worker` helper —
   it is NOT in `tools/goldendict_exporter.py`, so any other exporter that
   parallelizes GD+MDict today would hit the identical race and would need
   to duplicate the fix, or (better) the fix should be lifted into
   `tools/goldendict_exporter.py`/`tools/mdict_exporter.py` so every caller
   gets it for free. Same applies to the fd-level console-capture fix (worth
   generalizing into `tools/printer.py` or a shared wrapper if a second
   caller ever parallelizes).

## Other callers of `export_to_goldendict_with_pyglossary` / `export_to_mdict`
(current, non-archived code — found via grep, NOT measured):

- `exporter/goldendict/main.py` — the main DPD dictionary export. Single GD
  dict + MDict, run **serially** today (not split into halves like the
  deconstructor). This is likely the highest-value next target: it's the
  dictionary users actually browse day to day, and its `.zip` outputs
  (`dpd-goldendict.zip` ~268MB, `dpd-mdict.zip` ~316MB in `exporter/share/`)
  suggest a large MDict write. The prior `20260706_goldendict_optimize`
  thread optimized this exporter's *render* phase (330s → ~50-70s) but did
  **not**, as far as this thread found, separately measure or touch its
  write/zip stage — that thread's own handoff doesn't break out write/zip
  numbers for it. **Unverified hypothesis, not fact: measure this exporter's
  write/zip split before assuming it's worth parallelizing** — with only 2
  tasks (GD + MDict, no split-in-half), the ceiling is 2× at best, same
  caveat as this thread found for the deconstructor's MDict path (IPC-
  pickling the full dataset to the MDict worker can eat much of the win if
  the dataset is large).
- `exporter/grammar_dict/grammar_dict.py` — per the archived
  `20260706_deconstructor_grammar_optimize` thread, grammar's write/zip was
  already measured as small (~12s total: write 2.8s, zip .dict 5.7s, zip syn
  2.7s). **Not worth touching** — already checked by a prior thread.
- `exporter/kobo/kobo.py`, `exporter/variants/variants_exporter.py` — light
  exports per the `20260706_goldendict_optimize` handoff's own scope caveats
  ("may be small enough that parallelism isn't worth it"); unmeasured here.
- `exporter/tester/tester.py` — a test/dev utility, not a production export;
  skip.
- `exporter/archive/other_dictionaries_legacy/code/*` — archived/legacy code,
  out of scope by definition.

## Levers NOT explored by this thread, real for any large GD/MDict export

- **Lever 3 (idzip):** `tools/goldendict_exporter.py::zip_dictfile`/
  `zip_synfile` call `idzip.compressor.compress()` with no compression-level
  control and serial per-member compression, even though dictzip's member
  format is embarrassingly parallel. This is shared code — a fix here
  benefits every GD exporter, not just one. Higher effort (needs to
  reproduce idzip's exact member framing/index), but the ceiling is likely
  bigger than lever 1's ~1.46× since it's CPU-bound compression work
  applying to every dict, every build.
- **Lever 4 (writemdict):** `tools/writemdict/` (vendored, lint-excluded) is
  where the deconstructor's MDict write spent 142-164s at full scale — by
  far the single biggest number this thread measured. Never profiled
  internally. If MDict is ever turned on in production (`config.ini
  [dictionary] make_mdict`, currently `no`), or if the main DPD dict's MDict
  write is comparably large, this is where the next big, real win likely is.

## Hard-won lessons to carry forward (don't relearn these)

- **Measure before adopting, every time** — a "3 exports in parallel" lever
  measured at 1.46× for the deconstructor's real production config, but only
  1.06× once MDict's full-dataset IPC-pickling cost was accounted for via
  the *actual* source path (not just a harness). Don't assume a ratio
  transfers between exporters without re-measuring on the real code.
- **Fix the shared cache-dir race and console interleaving BEFORE claiming
  "parallelized" is done**, not after a live user run surfaces it. Both bugs
  were visible in this thread's own benchmark output and were wrongly
  dismissed as benign without root-causing — don't repeat that.
- **Watch machine load before trusting absolute timings** — two post-fix
  full-scale re-benchmarks in this thread were contaminated by unrelated
  Chrome/other-Claude-session/`systemd-coredump` load (6.6 and 18.1 load
  average) and were correctly discarded rather than reported. Always check
  `uptime`/`ps --sort=-%cpu` immediately before trusting an absolute number.

## Recommended first slice for a follow-on thread

Phase 1 = discovery only: measure `exporter/goldendict/main.py`'s write/zip
stage split (GD write/zip vs MDict write) in isolation, at mid + full scale,
the same way this thread did for the deconstructor, before deciding whether
2-way parallelization (GD ∥ MDict) is worth it there. If adopted, lift the
pyglossary-cache-isolation + output-capture pattern out of
`deconstructor_exporter.py::_export_worker` into `tools/goldendict_exporter.py`
so both call sites share one implementation instead of duplicating it.
