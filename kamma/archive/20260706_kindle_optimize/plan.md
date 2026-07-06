# Plan: Optimize the kindle exporter (speed, readability, testability)

Spec: `kamma/threads/20260706_kindle_optimize/spec.md`
GitHub issue: #157 (reference in commit, do not close).

## Architecture Decisions

- **Measure before optimizing.** Kindle is flagged in the goldendict handoff
  as a light export that may not need speed work; static reading does not
  rank targets (lesson 2026-07-06). Phase 1 attributed cost per stage; only
  measured wins were implemented.
- **Readability fixes land regardless of numbers** because one is a project
  rule violation (ORM mutation in `KindleData._make_html_friendly`) and the
  rest are dead code / duplication. All verified byte-identical.
- **ORM mutation fix shape:** `_HtmlFriendlyHeadword` wraps the real
  `DpdHeadword`, exposing the 12 html-friendly values precomputed in a dict
  and delegating everything else via `__getattr__` — templates keep reading
  `i.<attr>` unchanged, output stays byte-identical, and the session's ORM
  object is never dirtied.
- **Scope expanded beyond kindle-only during Phase 1** (drift, recorded
  here per the drift gate): profiling found the dominant render-loop cost
  was `DpdHeadword.lemma_ipa` (aksharamukha transliteration) in the SHARED
  `db/models.py`, used by 6 other exporters (goldendict, tpr, mobile, pdf,
  txt, webapp). Discussed with the user, who confirmed: fix it now rather
  than rediscover it per-exporter later. Fixed with two stacked, verified
  byte-identical changes in `db/models.py`.
- **Parity harness:** `temp/kindle_optimize/` (gitignored). Redirected the
  ProjectPaths epub attrs to a temp copy of the epub skeleton so the
  git-tracked `titlepage.xhtml`/`content.opf` were never touched. Baseline
  and modified runs both under `PYTHONHASHSEED=0`. Compared all generated
  xhtml bytes; excluded the two datetime-bearing files.
- **Benchmark hygiene:** each variant run in its own fresh process; `uptime`
  checked before each run; ratios reported, load noise flagged (an early
  125s "querying dpd db" number at load ~16 turned out to be pure
  contamination — a clean re-run at load ~3-5 gave 5.0s for the same code).
- **Tests:** unit-style, following
  `tests/exporter/deconstructor/test_data_classes.py` (SimpleNamespace rows
  cast to `DpdHeadword`, no DB, no golden masters, nothing slow).

## Phase 1: Baseline & attribution (DISCOVERY — no source edits)

- [x] Build `temp/kindle_optimize/run_full.py`: runs the real
  `render_dpd_xhtml` + `render_epd_xhtml` + abbreviations + titlepage + zip
  against a temp copy of the epub skeleton, per-stage wall timings printed.
  → verify: DONE. `git status` confirmed the tracked epub skeleton was
  never touched by any harness run.
- [x] Attribute cost: isolated the DB query stage, the
  `make_words_in_deconstructions` stage, and the render loop with
  standalone profiling scripts (`profile_query.py`, `profile_lookup.py`,
  `profile_wid.py`, `profile_render_loop.py` (cProfile),
  `profile_ipa_realtime.py`, `profile_getmembers.py`).
  → verify: DONE — see Results for the full cost table and root causes.
- [x] Decision recorded and confirmed with the user: adopt both measured
  levers (single-column deconstructor query; `lemma_ipa` memoization +
  getmembers cache), plus all readability fixes.
  → verify: DONE, decision made before any source edit; scope expansion to
  `db/models.py` explicitly confirmed with the user first.

## Phase 2: Implement (parity-gated)

- [x] Readability/rule fixes in `exporter/kindle/data_classes.py`: removed
  ORM mutation (`_HtmlFriendlyHeadword` wrapper), dropped unused `pth`
  param from `KindleData`/`render_ebook_entry`, single `html_friendly`
  (module-level in `data_classes.py`, imported by `kindle_exporter.py`,
  duplicate removed from `kindle_exporter.py`), no blind try/except, added
  missing type hints (`Environment`, `Any`, `cast`).
  → verify: byte-identical parity confirmed (see below).
- [x] Speed lever 1: `tools/deconstructed_words.py::make_words_in_deconstructions`
  now queries only `Lookup.deconstructor` instead of full ORM rows, and
  parses JSON directly. 8.94s → 1.73s in isolation (~5.2×); byte-identical
  output set, proven via unit tests against an in-memory Lookup table.
  → verify: DONE.
- [x] Speed lever 2: `db/models.py` — `_lemma_ipa_transliterate` module-level
  `lru_cache`-wrapped function memoizes the transliteration result by
  `lemma_clean` text (catches homonyms sharing a clean lemma); a one-time
  monkeypatch caches aksharamukha's `transliterate.getmembers` reflection
  scan (constant for the process lifetime, real measured cost 6.9s/62,833
  calls). Combined: 18.05s → 8.27s in isolation (~2.18×); verified 0 diffs
  across all 62,833 real `lemma_ipa` values (baseline vs patched).
  → verify: DONE.
- [ ] ~~Compact the `ebt_books` list~~ — DROPPED. `ruff format` always
  explodes a list literal that doesn't fit one line back to one-item-per-
  line regardless of manual grouping (confirmed empirically); fighting the
  formatter for a purely cosmetic change has no net effect and isn't worth
  it (cf. kamma lesson 2026-06-06 re: formatter reverting manual grouping).
  → verify: N/A, item dropped, no behavior/format change made.

## Phase 2b: Independent review (8-angle, high effort) and fixes

Ran `/code-review high` (8 parallel fresh-context finder agents: line-by-line,
removed-behavior, cross-file, reuse, simplification, efficiency, altitude,
CLAUDE.md conventions) against the diff. 4 of 8 angles independently
converged on the same core issue. Findings acted on:

- [x] **Redesigned `_HtmlFriendlyHeadword` proxy → flat dict.** 4 angles
  (reuse, simplification, altitude, efficiency) independently flagged the
  `__getattr__`-based proxy as over-engineered relative to the established
  sibling pattern (`DeconstructorData`/`GrammarData`: flat plain data, no
  ORM proxy) — it required a `cast(DpdHeadword, self.i)` hack, added
  per-attribute-access overhead, and eagerly computed all 12 fields even
  for the ~29.5% of headwords with no `meaning_1` (confirmed via
  `sqlite3 dpd.db`: 26,310/89,143 rows). Replaced with `_make_friendly(i)
  -> dict[str, str]`, computed only when `meaning_1` is truthy;
  `KindleData.i` now holds the real, never-wrapped `DpdHeadword`, and
  `make_grammar_line(self.i)` needs no cast. Updated `ebook_grammar.jinja`
  and `ebook_example.jinja` to read the 12 escaped fields from a new
  `friendly` dict (Jinja resolves `friendly.attr` as dict-item lookup)
  instead of `i.attr`; non-friendly fields (`i.lemma_ipa`, `i.root_key`,
  `i.source_1`, etc.) still read straight off the real object.
  → verify: full-scale re-run byte-identical to the original baseline
  (`ALL-IDENTICAL, 80 files, 2 excluded`); 36.92s clean re-run, consistent
  with the pre-review 37.64s measurement — the redesign is not a
  regression, it's simpler with the same speed.
- [x] **Fixed a real latent crash risk:** `html_friendly()` lost its
  try/except when deduplicated; `save_abbreviations_xhtml_page` calls it on
  values from `read_tsv_dict()` (`csv.DictReader`, `restval=None` for a
  short/ragged row) with no guard — 3 independent angles (A, B, C) found
  this. Fixed with an explicit `isinstance(value, str)` skip at that call
  site (matches the guard style already used in `_make_friendly`), rather
  than resurrecting a blind `try/except Exception`. Dormant today
  (0 ragged rows in the current `abbreviations.tsv`), but no longer a
  silent-corruption-vs-crash coin flip either way.
- [x] **Fixed a factually-wrong comment:** the `getmembers` monkeypatch
  comment claimed the reflection scan is "never" used with real pre/post
  options — false; `tools/translit.py`, `tools/sinhala_tools.py`, and
  `audio/bhashini_class.py` all call `transliterate.process()` with real
  options elsewhere in this codebase (3 angles: A, altitude, C flagged
  this). Rewrote the comment to state the real justification: `PreProcess`/
  `PostProcess` never register functions dynamically anywhere in this
  codebase, so the scan is constant for the process lifetime regardless of
  caller — the monkeypatch is still correct, just was mis-explained.
- [x] **Type hints:** added `-> None` to `KindleData.__init__`, `set[str]`
  (not bare `set`) to both `make_words_in_deconstructions` and its sibling
  `make_deconstructor_words_set` (touched-file lint ownership), and a
  return type on the test file's `_env()` helper.
- Findings considered and NOT acted on (with reasoning):
  - **lru_cache test-pollution risk** (`_lemma_ipa_transliterate` is a
    process-wide cache keyed by text; a test mocking
    `transliterate.process` differently for the same text could leak
    across tests). Checked: no current test does this (only
    `tests/exporter/mobile/test_mobile_exporter.py` stubs the aksharamukha
    *module* via `sys.modules.setdefault`, which is a no-op once the real
    package is already imported by `db.models` — true in every real
    collection order). `tests/db/test_models_lemma_ipa.py` already calls
    `cache_clear()` defensively. Judged low/unreachable risk; no
    autouse-fixture machinery added for a problem that doesn't exist today
    (avoids over-engineering).
  - **`html_friendly`/proxy-pattern duplication with `exporter/goldendict`'s
    `_NewlineView`** (reuse angle): the two have different escaping needs
    (kindle: `<br/>` + angle-bracket escaping for strict XHTML; goldendict:
    bare `<br>`, no escaping). Real, but a cross-exporter consolidation is
    a separate, bigger follow-up — out of this thread's scope.
  - **`tools/deconstructed_words.py` duplicates `Lookup.deconstructor_unpack`'s
    JSON-parse logic** (reuse/simplification angles): true, but the
    duplication is one line, exists specifically to avoid the ORM-row
    construction cost the fix targets, and extracting a shared helper for
    one line adds more indirection than it removes.
  - **Archive dir stale caller** (`archive/exporter/kindle/kindle_exporter.py`):
    confirmed dead code, excluded from lint/tests/imports; no action.

## Phase 3: Tests

- [x] `tests/exporter/kindle/test_data_classes.py` (9 tests, rewritten
  after Phase 2b's proxy→flat-dict redesign): `html_friendly` unit cases,
  `_make_friendly()` semantics (friendly transform, only the 12 named
  attrs, non-string skip, source never mutated), `KindleData` contract (no
  `pth` attr, friendly dict skipped when `meaning_1` falsy, `&amp;`
  escaping, no source mutation end-to-end, examples rendered
  html-friendly).
- [x] `tests/tools/test_deconstructed_words.py` (3 tests, in-memory
  SQLite `Lookup` table): collects words from all splits, ignores rows
  with no deconstructor, empty table → empty set.
- [x] `tests/db/test_models_lemma_ipa.py` (3 tests): non-empty
  result, homonyms sharing `lemma_clean` get identical (memoized)
  `lemma_ipa`, cache hit-counting on repeat calls.
  → verify: `uv run pytest tests/exporter/kindle/ tests/tools/test_deconstructed_words.py tests/db/test_models_lemma_ipa.py` →
  15 passed, fast (<1s total), no DB file needed.

## Phase 4: Final gate

- [x] `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright` on
  every touched file (`db/models.py`, `exporter/kindle/data_classes.py`,
  `exporter/kindle/kindle_exporter.py`, `tools/deconstructed_words.py`,
  plus the 3 test files) — all clean, 0 errors, after Phase 2b's fixes.
- [x] Full-scale parity re-run + timing comparison, fresh processes, POST
  review-redesign: 36.92s clean run vs the original 58.25s baseline
  (**~1.58× faster**), byte-identical across all 80 generated xhtml files.
  → verify: DONE, `temp/kindle_optimize/compare.py` reported
  `ALL-IDENTICAL (80 files, 2 excluded)` against the pre-review baseline.
- [x] Full suite run: `uv run pytest tests/` → 1204 passed, 9 failed
  (pre-existing, unrelated — see below), 16 deselected. Kept
  `temp/kindle_optimize/` for user re-verification; no commits made.

## Results

**Baseline (clean load ~3-5, full scale 89,143 headwords / 79,007 EPD
rows / 20,299 EBT deconstructor rows):** 58.25s total kindle-XHTML build
(render_dpd_xhtml 52.87s + render_epd_xhtml 1.91s + abbreviations 0.01s +
titlepage/opf 0.00s + zip_epub 3.46s).

**Root-cause cost table (render_dpd_xhtml, baseline):**

| Stage | Time | Cause |
|---|---|---|
| main render loop | ~24.5s | 72% is `lemma_ipa` (aksharamukha) |
| `make_words_in_deconstructions` | 11.5s | full-ORM query for 861,713 rows, only 1 column needed |
| DB query + sort | 5.0s | plain `.query().all()`, no fix needed (not the bottleneck it first appeared — an early noisy run showed 125s here, pure system-load contamination) |
| text sets (CST+SC) | 2.7s | file parsing, out of scope |
| inflections dict | 2.0s | set intersections, out of scope |
| chunked deconstructor lookup | 0.7s | already correctly chunked |

**Applied fixes (both proven byte-identical):**
1. `make_words_in_deconstructions`: single-column query. 8.94s → 1.73s
   (~5.2×) in isolation.
2. `lemma_ipa`: memoize by `lemma_clean` text + cache aksharamukha's
   `getmembers()` reflection. 18.05s → 8.27s (~2.18×) in isolation, across
   all 62,833 real headwords with `meaning_1`.

**Final (full scale, same machine, fresh process, post-review-redesign):**
36.92s total (render_dpd_xhtml 31.73s + render_epd_xhtml 1.93s +
abbreviations 0.01s + titlepage/opf 0.00s + zip_epub 3.25s).

**Overall: 58.25s → 36.92s ≈ 1.58× faster, byte-identical output.**

**IMPORTANT SCOPE NOTE, added after user feedback on a live run:** this
1.58× applies ONLY to the query+render+zip XHTML-generation phase measured
above. The full `just export-kindle` command also runs `make_mobi()`
(the `kindlegen` binary converting epub→mobi), which the user's own real
run showed taking ~229s — roughly 85% of the command's total ~272s wall
time. `kindlegen` is an external, unmodified, unbenchmarked black box
(explicitly out of scope per this spec's "What's not included"); it does
not get faster because the epub it's compiling was produced faster, since
the epub content is byte-identical either way. The measured 1.58× is real
and reproducible, but is easy to misread as "no difference" if compared
against total command wall time rather than the Python stage alone — this
should have been stated more clearly when first reporting the numbers.

**Readability/correctness fixes (zero speed impact, but rule/dead-code/
review fixes):**
- `KindleData` no longer mutates the ORM-tracked `DpdHeadword` object.
  First cut used an `__getattr__` proxy (`_HtmlFriendlyHeadword`); an
  independent 8-angle review (4 of 8 angles convergently) found this
  over-engineered relative to the sibling `DeconstructorData`/`GrammarData`
  pattern, so it was redesigned to `_make_friendly(i) -> dict[str, str]`
  (flat dict, computed only when `meaning_1` is truthy) with the two jinja
  templates reading the 12 escaped fields from that dict instead of `i`.
  Removes a `cast()` hack and per-attribute-access proxy overhead; still
  byte-identical.
- Fixed a real latent crash risk the review found: `html_friendly()` lost
  its try/except when deduplicated, and `save_abbreviations_xhtml_page`
  called it unguarded on values from `csv.DictReader` (which yields `None`
  for a short/ragged TSV row) — added an explicit `isinstance` guard at
  that call site instead of resurrecting a blind try/except.
- Fixed a factually-inaccurate code comment on the `getmembers` monkeypatch
  (it claimed the reflection result is "never" used with real options
  elsewhere, which is false — `tools/translit.py` etc. do; the real
  justification is that `PreProcess`/`PostProcess` never register
  functions dynamically anywhere in this codebase).
- Removed unused `pth` param from `KindleData.__init__` and
  `render_ebook_entry`.
- Removed the duplicated `html_friendly`/`_html_friendly` (one in
  `kindle_exporter.py`, one in `data_classes.py`, both with a pointless
  blind `try/except`) — single implementation in `data_classes.py`.
- Added missing/modernized type hints throughout the touched files,
  including `set[str]` (not bare `set`) on both functions in
  `tools/deconstructed_words.py`.
- `ebt_books` list compaction: attempted, reverted — `ruff format` always
  explodes it back to one-per-line; not worth fighting the formatter for a
  cosmetic no-op.

**Tests:** 15 tests across 3 files (`tests/exporter/kindle/`,
`tests/tools/test_deconstructed_words.py`, `tests/db/test_models_lemma_ipa.py`),
all fast, no DB file required, no golden masters.

**Pre-existing, unrelated issue found (NOT fixed, out of scope):**
`tests/exporter/analysis/` has 9 failing tests (`test_analyzer.py`,
`test_analysis_analyzer.py`, `test_analyze_sentence.py`) — reproduced
identically on a clean `git stash` (i.e. present on unmodified `main`,
unrelated to any change in this thread). Flagged to the user; not
investigated or fixed here since it's outside kindle-exporter scope.

**Files changed:** `db/models.py`, `exporter/kindle/data_classes.py`,
`exporter/kindle/kindle_exporter.py`, `tools/deconstructed_words.py`, plus
3 new test files. `temp/kindle_optimize/` kept until finalize (gitignored,
not part of the commit).

GitHub issue: #157 (reference in commit message, do not close).
