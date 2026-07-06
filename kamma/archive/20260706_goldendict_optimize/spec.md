# Spec: Optimize exporter/goldendict — speed, readability, testability

## Overview

The GoldenDict/MDict HTML generation phase (`exporter/goldendict/`) takes 330.6s
for 89,143 headwords on a 22-core machine, despite the actual rendering work
being only ~28s of CPU time. A benchmarked prototype proved 123.6s with
byte-identical output, and further headroom exists. This thread restructures the
export pipeline for speed, readability, and testability, and bundles two small
output bugs found during investigation.

All performance claims below were measured on the live db (10k, 20k, and full
89k words) with byte-identical output verification. The parity harness is
recreated in `temp/gd_parity/` as the first task (the original benchmark
scripts lived in an ephemeral job directory).

Measured baseline numbers (2026-07-06, 22-core Linux machine):

| Scale | Current code | Prototype | Output |
|---|---|---|---|
| 10k words | 18.6s | 6.1s | byte-identical |
| 20k words | 44.2s | 16.1s | byte-identical |
| 89,143 words (full) | 330.6s | 123.6s | byte-identical |
| EPD 20k entries | 7.3s | 0.46s | identical, header constant |

## What it should do

### 1. Restructure `export_dpd.py` (measured: 330.6s → 123.6s, more expected)

- **Replace OFFSET pagination with a single query** (default mode). The current
  code re-runs the sorted join for every 5k page; deep pages cost 10–24s each
  (~200s total). One query costs 8.5s.
- **Low-memory mode preserved**: when `psutil` reports < 9GB total RAM (same
  threshold as today), paginate by keyset (`WHERE DpdHeadword.id > last_id
  ORDER BY id LIMIT n`) instead of OFFSET — bounded memory, no re-sort cost.
  `id` is INTEGER PRIMARY KEY (rowid), so this is fast with no new index.
  Note: entry order in `dict_data` changes in this mode; order is already
  nondeterministic today (Manager list append order) and the StarDict writer
  sorts on output, so this is safe.
- **Preload family tables once** instead of 3 queries per word (~270k queries,
  ~43s serial → 0.10s): dicts keyed by `compound_family` / `idiom` / `set`.
  MUST replicate `.in_()` query semantics: order-preserving dedupe of
  `family_compound_list` etc. (edge case verified: words like
  `abhivādanapaccuṭṭhānaañjalikammasāmīcikamma` carry duplicate family names —
  the `.in_()` query returns each family once, so the dict lookup must dedupe
  while preserving first-occurrence order).
- **Persistent worker pool** replacing per-page `Process` spawns +
  `Manager().list()`. Worker initializer builds the jinja env and cached CSS
  once per worker; results come back as return values. Implemented with
  `concurrent.futures.ProcessPoolExecutor` (see the review-round note below) so
  a worker killed outright (e.g. OOM) surfaces as `BrokenProcessPool` and the
  build fails loudly rather than hanging — restoring the old exitcode check's
  guarantee.
- **Zero-copy fork staging — TRIED AND REMOVED (review round).** The plan
  originally added Linux fork copy-on-write staging to avoid pickling the
  dataset. Review found it never engaged at the real entry point
  (`get_start_method(allow_none=True)` returns `None` in a fresh process). Once
  fixed and actually measured in clean, isolated per-process runs at full
  scale, the zero-copy path was statistically indistinguishable from the
  pickled path (both ~55–73s; machine-load variance exceeded any gap) — because
  CPython refcounting touches every inherited object's page and defeats fork
  COW for object-graph access. It earned no speedup for ~60 lines of
  Linux-specific complexity, so it was removed. The pickled path is the sole,
  cross-platform path.
- **`config.ini` knobs unchanged**: `data_limit`, `show_id`, `make_mdict`,
  `make_slob` all keep working. `data_limit=N` becomes `.limit(N)` (same
  first-N-words-by-lemma_1 set as today).

### 2. Cache CSS/header work everywhere (measured: 0.25ms × ~170k entries)

- `CSSManager` reads 3 CSS files from disk on every instantiation, and every
  rendered entry instantiates one. Cache the file reads (class-level) —
  semantics unchanged for all other CSSManager consumers (webapp, docs,
  grammar_dict).
- EPD: the plain header is byte-identical for all 79k entries (verified: 1
  distinct header across 20k) — compute once, reuse. Measured 7.3s → 0.46s per
  20k entries (~29s → ~2s full).
- Same cached-header treatment for roots, variants, spelling, see, help
  sections (small, consistency).

### 3. Bug fixes (deliberate output changes, separate commits/tasks)

- `add_bibliography` / `add_thanks` in `export_help.py`: `zip(rows, rows[1:])`
  silently drops the last TSV row. Published dictionary is missing
  "Wisdom Library" (bibliography) and "Sāsanarakkha Buddhist Sanctuary"
  (thanks). Fix the loop so every row renders and lists close properly.
- `test_and_make_see_dict` / `variant` / `spelling` in
  `export_variant_spelling.py`: rows failing the `see == headword` (etc.)
  check print an ERROR but are still added to the dict. Fix so flagged rows
  are skipped. (Current data is clean, so no output change today.)

### 4. Readability / structure

- `GlobalVars` in `main.py` → `@dataclass` with construction in `main()`
  (established project pattern).
- Fix the self-mutating synonyms loop in `render_pali_word_dpd_html`
  (appends to the list being iterated) — separate output list, parity-checked.
- Remove dead condition `offset % limit == 0` (always true).
- Fold 6-line `helpers.py` re-exports into their users.
- Type hints throughout touched code (modern style per project rules).

### 5. Testability

- Rendering becomes a pure-ish function of preloaded data; family lookups
  become injectable dicts instead of live-session queries.
- Existing `tests/exporter/goldendict/` suite (1,210 lines) must keep passing.
- Add focused tests: family-dict dedupe semantics, keyset pagination
  equivalence, platform fallback selection, last-TSV-row rendering.
- Parity harness (temp scripts in `temp/gd_parity/`, discarded at the end —
  no frozen golden masters kept in repo): byte-identical output vs baseline
  dump, verified at 20k AND full 89k, run BEFORE applying the output-changing
  bug fixes. The full baseline dump is ~1.2GB on disk.

## Assumptions & uncertainties

- Fork start method is the Linux default and available on the build machine
  (verified: benchmarks ran with fork).
- Zero-copy staging is expected to cut the remaining ~106s render phase
  substantially, but the exact number is unproven until built — the 123.6s
  prototype is the guaranteed floor of improvement.
- Full-memory mode needs ~4–5GB RAM; free GitHub public runners have 16GB and
  no CI workflow currently runs this exporter — low-mem keyset mode is
  insurance for CI and other users' smaller machines.
- `minify`, `squash_whitespaces`, `extract_body` behavior untouched.
- The pyglossary/mdict write stage (`tools/goldendict_exporter.py`,
  `tools/mdict_exporter.py`) is out of scope — only the HTML generation phase.

## Constraints

- Output must be byte-identical to current, EXCEPT the two deliberate bug
  fixes (§3), which are applied and committed separately after parity is
  proven.
- No new dependencies.
- Must work on macOS/Windows via the spawn fallback path (untestable here;
  code path kept simple and covered by unit test of the selection logic).
- Pre-commit gate: every touched file passes `ruff check`, `ruff format`,
  `pyright`, and related pytest.
- `tools/exporter_functions.py` stays untouched (other exporters use it);
  the preloaded-dict lookups live in `exporter/goldendict/`.

## How we'll know it's done

1. Parity harness proves byte-identical output at full scale before bug fixes.
2. Full build time measured and reported (target: ≤ 123.6s proven, stretch
   < 60s with zero-copy).
3. `uv run pytest tests/exporter/goldendict/` passes.
4. Bibliography contains "Wisdom Library"; thanks contains "Sāsanarakkha
   Buddhist Sanctuary".
5. Lint/format/pyright clean on all touched files.

## What's not included

- `tools/goldendict_exporter.py` / `tools/mdict_exporter.py` internals
  (pyglossary write stage).
- Other exporters (kindle, kobo, mobile, tbw, webapp…).
- Template (`.jinja`) or JavaScript changes.
- CI workflow changes.
