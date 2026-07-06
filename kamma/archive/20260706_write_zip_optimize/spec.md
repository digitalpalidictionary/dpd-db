# Spec: Optimize the deconstructor GoldenDict/MDict write + zip stage

GitHub issue: #157 (refactoring umbrella — reference in commit, do NOT close).

## Overview

Follow-on from two archived threads (`20260706_goldendict_optimize`,
`20260706_deconstructor_grammar_optimize`) that optimized the HTML render
phase. The deconstructor export section now spends ~45s on query+render
(optimized) and **~90s on write + zip**, because
`exporter/deconstructor/deconstructor_exporter.py::prepare_and_export_to_gd_mdict`
runs three independent exports serially:

1. GoldenDict half 1 (`dpd-deconstructor`) — ~46s (write 8.4s, zip .dict 9.7s, zip .syn 26.5s)
2. GoldenDict half 2 (`dpd-deconstructor2`) — ~44s (write 6.8s, zip .dict 8.4s, zip .syn 27.0s)
3. MDict (full 861k) — tens of s (currently `make_mdict = no` in config.ini,
   but release builds produce the .mdx, so it stays in scope)

Full context: `kamma/archive/20260706_deconstructor_grammar_optimize/handoff_to_write_zip_stage.md`.

**The user's explicit instruction: at this stage, just test whether it's worth
it.** Phase 1 is discovery/measurement only — no source edits. Implementation
(Phase 2) happens only after the user approves the measured numbers.

## What it should do

1. **Measure lever 1 (primary):** run the three exports in parallel via
   `ProcessPoolExecutor`, prototyped entirely in a gitignored `temp/` harness.
   Expected ceiling: wall time ≈ slowest single export (~46s) instead of ~90s+.
2. **Measure lever 2 (cheap side experiment):** `sqlite=False` in
   `tools/goldendict_exporter.py::write_to_file` ("more RAM but faster").
   Record write-step time delta and peak RAM.
3. **Report** a go/no-go per lever with ratios, then stop for approval.
4. **Only if approved:** implement the winning lever(s) as a minimal source
   change in `exporter/deconstructor/deconstructor_exporter.py` (and
   `tools/goldendict_exporter.py` for lever 2 if adopted), parity-gated.

Lever 3 (idzip internals) and lever 4 (writemdict internals) are explicitly
deferred — only worth revisiting if levers 1–2 leave the stage dominated by a
single serial item and the user asks.

## Known correctness hazard (must be guarded)

`tools/mdict_exporter.py::replace_goldendict` and `add_h3_header` MUTATE
`DictEntry.definition_html` in place on the same objects the GoldenDict export
reads. Today safe only because MDict runs last. Under `ProcessPoolExecutor`
each worker operates on its own copy (separate process), which neutralizes the
hazard — but this must be *verified* by byte-parity of the GD output, not
assumed. If Phase 2 ever chooses threads instead of processes, the mutation
must first become a pure transform.

## Determinism facts that shape the harness (verified in code)

- `tools/niggahitas.py::add_niggahitas` returns `list(set(words))` — synonym
  order is nondeterministic across processes (str hash randomization). So the
  harness must build `dict_data` ONCE, pickle it, and feed the identical
  payload to every variant. Two independent full builds are NOT comparable.
- `DictInfo.date = make_timestamp()` (second granularity) lands in the
  `.ifo` — normalize the date line when comparing.
- idzip embeds the input file's mtime + name in the gzip header — compare
  *decompressed* payloads of `.dict.dz` / `.syn.dz`.
- `tools/writemdict` embeds `CreationDate` at day granularity — byte-compare
  is valid within the same day.

## Assumptions & uncertainties

- Machine: 22 cores, ~30 GB RAM (~15 available), load ~1.5–2.4 during recon —
  absolute times are noisy; ratios are the deliverable.
- Full payload pickle estimated ~1–2 GB (uncompressed .dict halves are
  ~33 MB dictzipped each); 70 GB free disk — fine. Three workers each
  transiently loading the pickle should stay well within RAM; measured anyway.
- `make_slob = no` and `copy_unzip`/GoldenDict-dir copying are excluded from
  timing in ALL variants equally (harness stubs `make_goldendict_path`), since
  copying is out of scope and machine-specific.
- The parallel prototype passes workers a pickle *path* + slice indices (not
  the objects) to avoid parent→child IPC pickling cost — the prior thread
  showed IPC can eat a pool's win.
- Uncertainty: whether `sqlite=False` changes entry ordering in pyglossary's
  Stardict writer — the parity compare will catch it; if output differs, the
  lever is rejected (or investigated) rather than adopted.

## Constraints

- **No source edits in Phase 1.** Harness lives in `temp/writezip_parity/`
  (gitignored), deleted at finalize. No frozen golden masters in the repo.
- Parity: byte-identical output (after the normalizations above) at mid scale
  (~100k entries) AND full scale (~861k) before any lever is adopted.
- Benchmark each variant in its OWN fresh process; check `uptime` /
  `ps --sort=-%cpu` before trusting absolute times; report ratios.
- Grammar_dict and all other exporters untouched.
- ruff/pyright/pytest gate on every touched source file (Phase 2 only;
  `tools/writemdict/` is lint-excluded but is not being touched).
- No git commits unless explicitly asked.

## How we'll know it's done

- `temp/writezip_parity/timings.md` records: serial baseline vs parallel vs
  sqlite=False, mid + full scale, fresh processes, load noted, ratios.
- Parity report: 0 diffs for `.dict` payload, `.idx`, `.syn` payload,
  normalized `.ifo`, `.mdx` for every measured variant.
- A clear go/no-go recommendation presented to the user; work stops there
  until approval.

## What's not included

- Slob output — explicitly dropped by the user ("forget slob, just
  goldendict mdict"); harness hardcodes `include_slob=False`.
- idzip member-level parallelism / compression-level tuning (lever 3).
- writemdict internals (lever 4).
- Dropping the inner dictzip (lever 3c) — requires a distribution-path
  decision by the user.
- grammar_dict or any other exporter.
- Render/query phase (already optimized).
