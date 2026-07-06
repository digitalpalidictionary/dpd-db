# Spec: Optimize the kindle exporter (speed, readability, testability)

GitHub issue: #157 (refactoring umbrella — reference in commit, do NOT close).

## Overview

Follow-on from the archived threads `20260706_goldendict_optimize` and
`20260706_deconstructor_grammar_optimize` (see
`kamma/archive/20260706_goldendict_optimize/handoff_to_other_exporters.md`),
which optimized the goldendict, deconstructor, and grammar exporters with
byte-identical output. This thread applies the same discipline to
`exporter/kindle/kindle_exporter.py` + `exporter/kindle/data_classes.py`:

1. **Speed** — measure first (the handoff explicitly warns kindle is a light
   export that may not need optimizing), then apply only measured wins.
2. **Readability** — fix known code-quality issues found in static reading.
3. **Testability** — the old `test_kindle_exporter.py` golden-master test was
   deleted in the snapshot-test purge; the module currently has zero tests.
   Add unit tests in the style of
   `tests/exporter/deconstructor/test_data_classes.py`.

## Findings from static reading (hypotheses to verify, not conclusions)

Per lesson 2026-07-06: do NOT rank optimization targets from static reading —
measure. These are candidates:

- `KindleData.__init__` runs per headword (~89k) and per entry does:
  3 × `jinja_env.get_template()` lookups, 2 sub-template renders
  (grammar, examples), a summary build, and 12 getattr/setattr html-friendly
  replaces.
- `render_ebook_entry` / `render_deconstructor_entry` / `render_epd_entry`
  re-call `get_template()` per row (jinja caches compiled templates, so this
  is a dict lookup — likely small, measure anyway).
- Stage costs unknown: CST/SC text-set XML parsing, lookup chunk query,
  inflections dict (set intersections × 89k), the three render loops,
  xhtml writes, zip. `make_mobi` (kindlegen, external binary) is OUT of scope.

**Rule violations / readability issues to fix regardless of speed numbers:**

- `KindleData._make_html_friendly` MUTATES tracked ORM attributes via
  `setattr(self.i, attr, ...)` — direct violation of the project rule
  "Never mutate ORM objects; derived values must be computed separately."
  Fix must preserve byte-identical output (templates read the mutated
  values, and `ebook_example.jinja` mixes mutated `example_1` with
  unmutated `source_1`).
- `KindleData` stores `pth` but never uses it (same dead-param pattern
  removed from `DeconstructorData` in the previous thread).
- `html_friendly` exists twice: module function in `kindle_exporter.py`
  and `_html_friendly` method in `data_classes.py`, both with a pointless
  blind `try/except` around `str.replace` calls.
- 35-line vertical `ebt_books` list — compact without changing content.

## What it should do

1. **Phase 1 (discovery, no source edits):** baseline run of the real,
   unmodified render pipeline via a harness in `temp/kindle_optimize/`
   (gitignored), with ProjectPaths epub attrs redirected to a temp copy of
   the epub skeleton — a real run overwrites the git-tracked
   `titlepage.xhtml` / `content.opf`, which the harness must not touch.
   Capture per-stage timings + a saved copy of all generated xhtml as the
   parity baseline. Attribute the render-loop cost (KindleData vs
   template.render) before choosing fixes.
2. **Phase 2:** implement measured speed wins + all readability fixes above,
   parity-gated byte-identical against the baseline.
3. **Phase 3:** unit tests for the refactored `KindleData` contract and
   helpers (no golden masters, no slow CST parsing in default test run).
4. Report results; user commits everything at the end.

## Determinism facts that shape the harness (verified in code)

- Deconstructor entry order depends on `list(combined_text_set)` — set
  iteration order is str-hash-randomized, so **both** baseline and modified
  runs must run with `PYTHONHASHSEED=0` for byte-parity to be valid.
- `add_niggahitas` output is re-sorted through `pali_list_sorter` in this
  exporter, so inflection order is deterministic.
- `titlepage.xhtml` / `content.opf` embed `datetime.now()` — excluded from
  parity (or normalized).
- The jinja env has NO autoescape (`exporter/jinja2_env.py`), so moving
  strings between Python and templates does not change escaping.

## Assumptions & uncertainties

- Scale: 89,143 headwords; 79,007 EPD lookup rows; deconstructor rows are the
  EBT subset of 861,713 (actual count known only at run time).
- Machine: 22 cores, load ~4.5 from interactive apps (claude, chrome,
  goldendict) — no batch jobs, but absolute times are noisy; ratios are the
  deliverable. Benchmark each variant in its own fresh process.
- The `--script` transliteration variants (deva/sinhala/thai) share the same
  code path; parity is checked on the default path, and the changed code
  must be script-attr-agnostic.
- MOBI conversion (kindlegen) and epub zipping to `exporter/share/` are
  external/IO stages — measured for attribution but only optimized if they
  are both dominant AND trivially fixable; kindlegen itself is a black box.

## Constraints

- No source edits until the Phase 1 baseline is captured.
- Parity: byte-identical generated xhtml (letter files, epd files,
  abbreviations) vs baseline under pinned `PYTHONHASHSEED`.
- Harness lives in `temp/kindle_optimize/` (gitignored), deleted at finalize.
  No frozen golden masters in the repo.
- ruff check + ruff format + pyright + pytest gate on every touched file
  (TOUCH A FILE = OWN ITS LINT).
- No git commits, no GitHub writes except the finalize comment step.
- Do not touch `exporter/deconstructor/deconstructor_exporter.py` — it holds
  uncommitted changes from the still-open `20260706_write_zip_optimize`
  thread.

## How we'll know it's done

- Per-stage timing table (baseline vs optimized) in the thread's plan.md
  Results section, ratios included.
- Parity report: 0 byte diffs on all generated xhtml at full scale.
- `KindleData` no longer mutates ORM objects; dead `pth` removed; single
  `html_friendly`; tests exist and pass in the default suite.
- Full `tests/` suite green; ruff/pyright clean on touched files.

## Drift note (recorded during Phase 1)

Profiling found the dominant render-loop cost was `DpdHeadword.lemma_ipa`
(aksharamukha transliteration) in the shared `db/models.py`, used by 6 other
exporters (goldendict, tpr, mobile, pdf, txt, webapp), not kindle-specific.
Discussed with the user, who confirmed fixing it now (rather than
rediscovering it per-exporter in a future thread) was worth the scope
expansion. `db/models.py` was added to the touched-file set as a result,
with the fix verified byte-identical against all real values before landing.
See `plan.md` Results for the full writeup.

## What's not included

- kindlegen/MOBI conversion internals; epub zip format changes (mimetype
  ordering etc.).
- The kobo/mobile/tbw exporters (separate follow-ups if this one pays off).
- Parallelism unless attribution shows a single dominant parallelizable
  stage AND a simple pool wins at measured scale (prior threads showed
  IPC often eats the gain).
