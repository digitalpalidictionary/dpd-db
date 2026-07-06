# Handoff: optimize the GoldenDict/MDict write + zip stage

Written for a future thread, for an agent with **zero prior context**. Two prior
threads (`20260706_goldendict_optimize`, `20260706_deconstructor_grammar_optimize`,
both archived under `kamma/archive/`) optimized the HTML **render** phase of the
exporters. This handoff targets the phase that now dominates: the pyglossary /
MDict **write + compression** stage in `tools/goldendict_exporter.py` and
`tools/mdict_exporter.py`.

## Why this is worth doing (measured, not guessed)

After the render optimizations, a live deconstructor run (`just export-grammar` /
the deconstructor export) breaks down like this:

**Deconstructor section total ≈ 2:16 (136s).** Of that, render + query ≈ 45s
(already optimized). The rest — **~90s — is write + zip**, and it is paid because
`exporter/deconstructor/deconstructor_exporter.py::prepare_and_export_to_gd_mdict`
runs three independent exports **serially**:

| Export | compiling | writing GD file | zip .dict | zip synonyms | ~subtotal |
|---|---|---|---|---|---|
| GoldenDict half 1 | 1.95s | 8.35s | 9.66s | **26.46s** | ~46s |
| GoldenDict half 2 | 1.33s | 6.81s | 8.36s | **27.03s** | ~44s |
| MDict (full 861k) | — | (MDictWriter) | — | — | ~tens of s |

`zipping synonyms` (idzip on the `.syn` file) is the single biggest item, ~26-27s
**each**, and the deconstructor is split into two GoldenDict dictionaries (it is
"too large for GoldenDict"), so every GD cost is paid twice.

Grammar_dict's write/zip is already small (~12s total: writing 2.8s, zip .dict
5.7s, zip syn 2.7s) — a single dict with tiny synonym lists. **The deconstructor
is the target; grammar/other small dicts are not worth touching.**

## The levers (in recommended order — smallest/safest first)

### 1. Run the 3 independent exports in parallel (highest value, lowest risk)
`prepare_and_export_to_gd_mdict` does GD-half-1 → GD-half-2 → MDict serially.
They write to different files and share nothing mutable except `g.dict_data`
(read-only during export — but note MDict's `replace_goldendict`/`add_h3_header`
MUTATE `definition_html` in place on the shared `DictEntry` objects; see the
CAVEAT below). Dispatch the three via `concurrent.futures.ProcessPoolExecutor`
(pattern already in `exporter/goldendict/export_dpd.py`). Expected: ~90s → ~45s
(bounded by the slowest single export). No output-format change.

**CAVEAT (correctness):** `tools/mdict_exporter.py::replace_goldendict` and
`add_h3_header` mutate `DictEntry.definition_html` on the SAME objects the
GoldenDict export reads. Today it's safe only because MDict runs last. If you
parallelize, the MDict worker must operate on a deep copy (or the mutation must
move to a pure transform that returns new strings). This is the one real
hazard — verify byte-identical GD output after parallelizing.

### 2. Flip `sqlite=True` → `sqlite=False` in `write_to_file` (cheap experiment)
`tools/goldendict_exporter.py::write_to_file` calls
`glos.write(..., sqlite=True)`; the inline comment says *"when False, more RAM
but faster."* The build machine has plenty of RAM. Measure write time and peak
RAM with `sqlite=False`; gate on `psutil.virtual_memory().total` like
`export_dpd.py` does if you want a low-mem fallback. Low risk, quick to test.

### 3. Speed up idzip compression of `.syn`/`.dict` (highest ceiling, most work)
`zip_synfile` / `zip_dictfile` call `idzip.compressor.compress(...)`, which:
- exposes **no compression-level parameter** (uses zlib's default), and
- compresses dictzip **members serially** (`_compress_member` in a loop over
  `MAX_MEMBER_SIZE` chunks).

The dictzip format is a gzip stream of **independent members** — so member
compression is embarrassingly parallel. Options, cheapest first:
  a. **Lower the zlib level.** idzip's public `compress()` hides the level, but
     `_compress_member` uses `zlib`. A thin vendored wrapper (or upstreamable
     patch) that threads a `compresslevel` through would let you trade `.syn`
     size for speed. The `.syn` is a synonym index; test how much size actually
     grows at level 1-3 vs the time saved.
  b. **Parallelize members.** Compress the independent members across a process
     pool and concatenate. Higher effort; must reproduce idzip's exact member
     framing + the `.dz` random-access index so GoldenDict still seeks correctly.
  c. **Question whether `.dz` is needed at all.** GoldenDict/StarDict can read an
     UNCOMPRESSED `.dict`/`.syn`. `write_to_file` already passes `dictzip=False`
     and the project compresses separately afterwards. INVESTIGATE (don't assume):
     does the distribution/release path (the shared `.zip`, the copy into the
     GoldenDict dir, downstream users) actually require `.dz`, or would shipping
     uncompressed `.dict`/`.syn` inside the outer `.zip` be acceptable? If the
     outer zip is what's distributed, the inner dictzip may be redundant work.

### 4. MDict write (`tools/writemdict/`) — measure before touching
`MDictWriter.write` does its own zlib compression of records. `tools/writemdict/`
is a vendored third party and is **lint/pyright-excluded** (see
`.pre-commit-config.yaml`), so edits there won't hit the gate but are also
higher-risk. Measure the MDict write time for the full 861k deconstructor first;
only dig in if it's a large slice. Parallelizing at the export level (lever 1)
may make this moot.

## The safety net (MANDATORY — same discipline as the prior threads)
- **Byte-identical output.** Build a parity harness in `temp/` (gitignored,
  deleted at thread end — NO frozen golden masters in the repo). Compare the
  produced `.dict`/`.syn`/`.dz`/`.mdx`/`.mdd` bytes (or a digest) before vs after.
  For lever 3a/3c the compressed bytes WILL differ — in that case assert the
  *decompressed* content is identical and that GoldenDict/an MDict reader still
  loads it. Verify at mid scale AND full 861k.
- **Benchmark each variant in its OWN fresh process** (never two sequentially in
  one process — it inverted a result in the goldendict thread). Check `uptime` /
  `ps --sort=-%cpu` for background load before trusting absolute times; report
  ratios.
- Pass the ruff/pyright/pytest gate on every touched file. `tools/writemdict/` is
  lint-excluded but everything else in `tools/` is not.

## Hard DON'Ts (carried from the prior threads)
- Do NOT add fork zero-copy staging — built, measured, removed; CPython
  refcounting defeats fork COW.
- Do NOT assume; the deconstructor Phase-3 render pool looked obvious but tested
  at only ~1.5× (IPC-bound) and was dropped. Measure every lever before adopting.

## Scope
- In scope: `tools/goldendict_exporter.py`, `tools/mdict_exporter.py`, and the
  call site `exporter/deconstructor/deconstructor_exporter.py::prepare_and_export_to_gd_mdict`.
- Probably out of scope: the render phase (already optimized), grammar/other
  small dicts (write/zip already cheap), and the Go deconstructor (splits
  generation, not this export).
- Related memory: `project_exporter_zip_bottleneck` in the project memory index.

## Recommended first slice
Lever 1 (parallelize the 3 exports) alone should roughly halve the deconstructor
write/zip stage with no format change and one real hazard to guard (the MDict
in-place mutation of shared `DictEntry.definition_html`). Do that first, prove
byte-identical, then decide whether levers 2/3 are worth the extra effort.
