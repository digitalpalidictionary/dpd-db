# Spec: Extend the goldendict optimizations to the rest of exporter/

## Overview

Follow-on to the finalized `20260706_goldendict_optimize` thread, which sped up
`exporter/goldendict/` ~5–7× with byte-identical output. That thread's handoff
(`kamma/archive/20260706_goldendict_optimize/handoff_to_other_exporters.md`)
asked for a sweep of the six anti-patterns across the rest of `exporter/`.

The sweep was done (see the census below). **The six patterns barely exist
outside goldendict.** The two exporters that are genuinely slow — confirmed from
the build logs in `logs/` — are:

- **Python deconstructor exporter** (`exporter/deconstructor/deconstructor_exporter.py`):
  renders a constant header + content template + `minify()` for **every
  deconstructed compound (~861k `Lookup` rows)** entirely serially. Measured
  render loop **~255s** (the biggest single item in the whole build; see
  Measured baseline below). The user's primary target.
- **grammar_dict** (`exporter/grammar_dict/grammar_dict.py`): "compiling html"
  measured **84–94s** for 290k rows despite render memoisation — a genuine
  second hotspot, not a trivial one.

Note on the user's recollection: they suspected the pain they attributed to
"grammar" was actually the goldendict DPD exporter (now fixed). The logs partly
disagree — grammar_dict's render is independently ~84s — so grammar stays in the
plan as a measured, gated target, and this data point is flagged to the user.

Everything else is either already correct, too small to matter, out of scope
(webapp runtime service), or non-Python (Go modules).

This is a deliberately narrow, minimal-first thread: fix the two real hotspots,
measure, and stop. Do not port machinery into modules that don't need it.

## Measured baseline (from `logs/`, runs 2026-06-26 & 2026-06-29)

Both runs **predate** the 2026-07-06 global CSS-cache fix (`tools/css_manager.py`),
so Phase 1 must re-measure on current code to see what that fix already removed
from the deconstructor's per-row header work.

| Section | Rows | Timer in log | Measured | Notes |
|---|---|---|---|---|
| deconstructor "making data list" | 861,713 | query+setup only | ~9s | timer closes **before** the render loop |
| deconstructor **render loop** | 861,713 | per-50k counter ~15s × ~17 | **~255s** | serial, no pool; biggest item in the build |
| grammar_dict **"compiling html"** | 290,764 | one block | **84–94s** | memoised render; second-biggest item |

`pr.counter` prints per-batch elapsed then resets (`bop()`+`bip()`), so the flat
~15s/50k is per-batch, not cumulative — hence ~255s total for the loop.

## Discovery census (Phase 1 pattern presence — done in planning)

Grep of every `exporter/*/**.py` (excluding `archive/`) for the six patterns:

| Pattern | Where present | Verdict |
|---|---|---|
| 1. OFFSET pagination (`.offset(`) | **nowhere** outside goldendict | nothing to do |
| 2. per-row family / `.in_()` in a render loop | webapp (runtime), goldendict (fixed). `.in_(chunk)` in kobo/kindle/sutta_central is **correctly chunked** — not the anti-pattern | nothing to do |
| 3. per-entry constant CSS/header render | **deconstructor** (`data_classes.py:15-20`, ~861k×); grammar_dict (once per distinct grammar string); variants **already** hoists header once | **fix deconstructor**; grammar header is minor (cache-miss only) |
| 4. `Manager().list()` + per-page `Process` | **nowhere** — but deconstructor (~255s) and grammar_dict (~84s) render fully **serially** (no pool at all) | **pool both** (measurement-justified); kobo/apple/kindle/pdf serial but not slow → leave |
| 5. `zip(rows, rows[1:])` last-row drop | **nowhere**. The `[1:]` slices in apple/tpr skip the *first* row deliberately; mobile's `zip` is parallel iteration | nothing to do |
| 6. self-mutating loop (append to iterated list) | **nowhere** — variants' `make_synonyms` mutates a separate local list; pdf/tbw `used_letters` appends are guarded tracking lists | nothing to do |

CSS file-read caching is already global (`tools/css_manager.py`, done in the
goldendict thread) — every consumer already benefits; no per-exporter action.

**Modules audited and ruled out** (no meaningful pattern, or out of scope):
kindle, kobo, mobile, tbw, txt, variants, sutta_central, anki, apple_dictionary
(serial but user confirms not a pain point; would need heavy ORM-pickle refactor
for uncertain gain), pdf (dominated by external `typst.compile`), webapp
(FastAPI runtime, not a batch build), deconstructor/frequency **Go** modules,
mcp, analysis (AI translation, not a dictionary render).

## What it should do

### Primary target — `exporter/deconstructor/deconstructor_exporter.py`

`make_deconstructor_dict_data` loops over ~1M+ rows and for each row:
1. builds `DeconstructorData(i, pth, jinja_env)`, whose `_generate_header`
   **re-instantiates `CSSManager()`, re-renders `deconstructor_header.jinja`,
   re-runs `update_style` + `squash_whitespaces`** — for a header with **no
   per-entry variables** (constant). This is anti-pattern #3 at 1M+×.
2. renders + `minify()`s the content template.
3. builds the synonyms list.
All serial.

Two transferable wins, applied smallest-first and each gated on measurement:

- **A. Constant header once (smallest change, highest confidence).** The header
  string is identical for every entry. Compute it once and reuse it as a
  constant prefix; drop the per-entry header rebuild. Byte-identical output.
- **B. Persistent `ProcessPoolExecutor` for the content render + synonyms**
  (mirrors goldendict `export_dpd.py`), **only if** Phase-1 measurement shows the
  content render still dominates after A. Worker initializer builds the jinja env
  + template once per worker; batches preserve input order; progress counter
  driven from `as_completed` at the current ~50000 cadence.

### Secondary target — `exporter/grammar_dict/grammar_dict.py` (measured ~84s)

The "compiling html" loop is a measured **84–94s** for 290k rows. Render is
memoised via `grammar_cache`, so the header rebuild in
`GrammarData._generate_header` fires only once per *distinct* grammar string, not
per row — the header hoist is therefore minor. The 84s is dominated by whatever
is left after memoisation: the ~290k per-row `grammar_cache` lookups + dict
inserts, and the full render of each *distinct* grammar string (cache misses).

Phase 1 attributes the 84s (distinct-string count, render cost per miss, per-row
overhead). Then the smallest justified change:
- **constant-header-once hoist** (trivial, safe) if it shows up at all; and/or
- **persistent `ProcessPoolExecutor`** over the *distinct* grammar strings (render
  each once in workers, then map results back onto all 290k keys) **only if** the
  distinct-render cost dominates and parallelism clearly wins.

If Phase 1 shows the 84s is actually the pyglossary export stage (out of scope),
`add_niggahitas` per word (`make_data_lists` was only 0.35s in the log, so
unlikely), or otherwise not worth touching, report that and stop — do not invent
work.

## Constraints

- **Byte-identical output** for every refactor task, verified by a parity
  harness at a mid scale AND full scale before the change is trusted. No
  deliberate output changes in this thread.
- **Order sensitivity (deconstructor):** `prepare_and_export_to_gd_mdict` splits
  `g.dict_data` in half **by index** (`half = len/2`). Any parallel path MUST
  preserve the original input order so the split point — and thus dict1/dict2
  membership — is identical. Parity is checked on the full `dict_data` list
  order, not just as a set.
- **Harness footprint:** the full deconstructor `dict_data` is ~1M+ entries of
  large HTML; a full pickle would be tens of GB. Compare via a **streaming
  digest** — hash each `(word, definition_html, tuple(synonyms))` in list order
  into one rolling SHA-256 — plus a byte-identical full-pickle compare at a
  **capped mid scale** (e.g. 50k). This is a justified deviation from
  goldendict's full-pickle harness (10× the scale). Harness lives in `temp/`
  (gitignored), deleted at thread end — no frozen golden masters in the repo.
- No new dependencies.
- Pre-commit gate: every touched file passes `ruff check`, `ruff format`,
  `pyright`, and related pytest.
- Do NOT re-add fork zero-copy staging (built, measured, removed in the source
  thread — CPython refcounting defeats fork COW). Pickle the batches.
- Benchmark each variant in its **own fresh process**; check `uptime` /
  `ps --sort=-%cpu` for background load before trusting absolute times.

## Assumptions & uncertainties

- The deconstructor render loop is measured at ~255s (pre-CSS-cache logs), but
  the CSS-cache fix landed 2026-07-06, so the **current** per-row cost and the
  split between header rebuild, content render+`minify()`, and synonyms is
  **unproven until Phase 1 re-measures on current code**. Win A is the
  guaranteed-safe floor; win B is conditional on that measurement.
- grammar_dict's 84s is measured, but its internal split (distinct-string render
  vs per-row overhead) is unproven — Phase 1 decides whether it gets a header
  hoist, a pool over distinct strings, or nothing.
- `minify`, `update_style`, `squash_whitespaces`, `add_niggahitas` semantics are
  untouched — only *where/how often* they run changes.

## How we'll know it's done

1. Parity harness proves byte-identical deconstructor output (digest + capped
   mid-scale pickle) before and after every change.
2. Deconstructor full render-loop wall time measured before and after; win
   reported as a ratio (load-independent) plus absolute times with a load note.
3. grammar_dict: either the header-once hoist lands parity-clean, or a written
   finding explains why no change was warranted.
4. `uv run pytest tests/exporter/` passes; lint/format/pyright clean on all
   touched files.

## What's not included

- The pyglossary / MDict write stage (`tools/goldendict_exporter.py`,
  `tools/mdict_exporter.py`).
- Any exporter ruled out in the census above (kobo, apple, pdf, kindle, mobile,
  tbw, txt, variants, sutta_central, anki, webapp, mcp, analysis).
- Go modules (`go_modules/`).
- Template (`.jinja`) or output-changing edits.
