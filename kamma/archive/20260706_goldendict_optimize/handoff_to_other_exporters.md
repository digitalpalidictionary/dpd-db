# Handoff: apply the goldendict optimization lessons to the other exporters

This is a handoff FROM the finalized thread `20260706_goldendict_optimize`
(archived alongside this file) TO a future thread that extends its wins to the
rest of `exporter/`. Written for an agent with zero prior context.

## What the source thread did (the reference implementation)

`exporter/goldendict/` was optimized ~5–7× (330s → ~50–70s at full scale) with
byte-identical output. Read these in the same archive dir for the full picture:
- `spec.md` — goals and constraints
- `plan.md` — phase-by-phase changes + Results
- `review.md` — the independent review, the blocking bug found, and the
  post-finalize progress-counter fix

The committed reference code lives in `exporter/goldendict/` (esp.
`export_dpd.py`, `export_epd.py`, `export_help.py`,
`export_variant_spelling.py`, `main.py`) and `tools/css_manager.py`.

## The transferable patterns (what to look for and how to fix)

Audit every module under `exporter/` for these. Each is greppable; none should
be assumed present — verify per file.

1. **OFFSET pagination on a sorted join** — `.offset(` / `.limit(...).offset(...)`
   in a loop re-runs and re-sorts the whole query every page (deep pages cost
   10–24s each). Fix: one query in the default high-memory path; keyset-by-`id`
   (`WHERE id > last_id ORDER BY id`) only if a low-memory mode is needed.

2. **Per-row DB queries inside a render loop** — e.g. `get_family_*` /
   `.filter(X.in_(...))` fired once per entry (goldendict did ~270k). Fix:
   preload the small lookup tables into dicts once, replicate `.in_()` semantics
   (order-preserving dedupe; missing key → skip; verify against the old query).

3. **`CSSManager()` or header render per entry** — `tools/css_manager.py` now
   caches its 3 CSS file reads at class level (already fixed globally, benefits
   every consumer). Additionally, a header template with NO per-entry variables
   is constant — render it once per section, not per row (goldendict EPD:
   33s → 10s; small sections ~15×).

4. **`Manager().list()` + per-page `Process` spawns** — replace with a single
   persistent `concurrent.futures.ProcessPoolExecutor` (initializer builds the
   jinja env once per worker; results via `as_completed`). ProcessPoolExecutor
   raises `BrokenProcessPool` if a worker is OOM-killed, so the build fails
   loudly instead of hanging (plain `multiprocessing.Pool` hangs).

5. **`zip(rows, rows[1:])` look-ahead loops** — silently drop the last row.
   Found in `add_bibliography`/`add_thanks`. Grep `zip(` in every exporter that
   builds HTML from a TSV/list; replace with explicit open/close-list tracking.

6. **Self-mutating loops** — appending to a list while iterating it. Rewrite as
   a single-pass comprehension once you've confirmed no appended item re-matches.

## The safety net (MANDATORY before any refactor)

Rebuild the parity harness per exporter: run the exporter's `generate_*`
function on the UNMODIFIED code, dump `sorted((word, definition_html,
sorted(synonyms)))` to a pickle, then after each change re-run and byte-compare.
Keep it in `temp/` (gitignored), delete at thread end — no frozen golden
masters in the repo. Verify at a mid scale AND full scale before trusting it.

## The DON'Ts (hard-won)

- **Do NOT add fork zero-copy staging** (stage dataset in a module global, fork
  so workers inherit it COW). It was built, measured, and REMOVED here: CPython
  refcounting touches every inherited object's page and defeats copy-on-write,
  so it gave zero speedup for ~60 lines of Linux-specific complexity. Pickling
  the batches is simpler and just as fast.
- **Do NOT benchmark two implementations sequentially in one process** — the
  first run's heap/caches contaminate the second (it inverted a result here).
  One variant per fresh process. Check `uptime`/`ps --sort=-%cpu` for background
  load (a Borg backup skewed numbers 48s→194s) before trusting absolute times.

## Scope caveats — the lessons are NOT uniform

Audit first; do not assume every exporter has these bottlenecks:
- `webapp/` — a FastAPI *runtime* service, not a batch build. Different profile.
- `deconstructor/`, `frequency/` — Go (`go_modules/`), not Python.
- `kindle/`, `kobo/`, `mobile/`, `tbw/` — *light* exports; may be small enough
  that parallelism/preloading isn't worth it. Measure before optimizing.
- `grammar_dict/`, `sutta_central/`, `pdf/`, `apple_dictionary/`,
  `chrome_extension/`, `variants/`, `mcp/` — unknown; audit each.

## Recommended shape for the new thread

Phase 1 = **discovery, not edits**: grep the six patterns across `exporter/`,
produce a per-module table (pattern present? measured cost? worth fixing?).
Then one vertical, parity-gated slice per exporter that genuinely benefits —
smallest change first, byte-identical output, tests + lint gate each step.
Don't port optimizations into a module that doesn't need them.
