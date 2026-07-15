# Plan: pass2pre next-word loading speed

Thread: 20260715_pass2pre_next_word_speed

## Architecture Decisions

- **Benchmark before building** (project rule: re-derive numbers before any
  optimization spec). Phase 1 produces a measured decision between prefetch
  (A) and index (B), recorded in spec.md; Phases 2+ implement only the winner.
- **A's natural integration point**: `missing_examples_dict[word]` — the
  existing "already fetched" contract in `load_next_word` means prefetch
  results are consumed with zero changes to the load path.
- **B's boundary**: if chosen, the index lives in a new module under
  `tools/cst_source/` behind the existing `find_cst_source_sutta_example`
  signature (extra optional index arg or session object), keeping every other
  caller untouched.
- **Deliberately not doing both**: A hides the wait; if it fully hides it, B
  is unjustified complexity (laziness ladder rung 1).

## Phase 1: Benchmark & decide

- [x] Prototype B's index build on a throwaway script (scratchpad, not repo):
  walk all 11 AN books once via `make_cst_soup`, extract flat
  `(source, sutta, cleaned_text)` rows using the existing parser classes,
  time the build and the per-word regex scan for 20 sample words (mix of
  high/low frequency, gatha-heavy included). Compare outputs against
  `find_cst_source_sutta_example` for those words — note any gatha
  divergences and what fixing them would take.
  → verify: script prints build time, per-word search time, and an
  identical/divergent report for the 20 words.
  ✓ 2026-07-15: build 1.41s, search avg 34ms/max 124ms, 20/20 identical.
- [x] Record the decision (A, B, or A-now-B-later) with numbers and
  rationale in spec.md under "Two candidate methods".
  → verify: spec.md updated; decision references measured numbers.
  ✓ 2026-07-15: Method B chosen — eliminates the wait, no threading,
  gatha path precomputable (word-independent).

## Phase 2: Implement Method B (per-session corpus index)

- [x] New module `tools/cst_source/corpus_index.py`: `CstSourceIndex` class.
  `__init__(books)` builds once: per book, `make_cst_soup` + fresh
  `make_book_parser`, walk `head`/`p` elements in order, `parser.update(x)`,
  store flat rows `(source, sutta, cleaned_text, is_gatha, gatha_examples)`.
  Gatha examples precomputed at build (word-independent), cached per
  resolved gatha1 element, stuck-loop guard semantics preserved (row gets
  `[]`, same as `find_gatha_example`'s timeout path). Books without a
  parser produce no rows (baseline yields nothing for them).
  `find_examples(text_to_find)` replicates extractor semantics exactly:
  per book in build order, `re.findall` on cleaned text, gatha rows return
  precomputed examples / sentence rows via `find_sentence_example`,
  skip empty source/sutta, dedupe within book, concatenate across books.
  Export `CstSourceIndex` from `tools/cst_source/__init__.py`;
  `find_cst_source_sutta_example` untouched.
  DEVIATION (review, 2026-07-15): `.gitignore` ignores ALL `__init__.py`
  files, so the `__init__.py` export can never be committed — tracked files
  (controller, test) import `CstSourceIndex` directly from
  `tools.cst_source.corpus_index` instead; the `__init__.py` export remains
  as a local convenience only.
  → verify: fast unit test on hand-built rows (dedupe, gatha vs sentence
  path, empty-source skip) + slow parity test on a real book: index
  results == concatenated `find_cst_source_sutta_example` for sample
  words incl. gatha matches.
- [x] Wire into `Pass2PreController`: `self._cst_index: CstSourceIndex | None`
  reset in `find_words_with_missing_examples`; `get_cst_examples` builds it
  lazily on first use, then answers from `self._cst_index.find_examples()`.
  → verify: `tests/gui2/` pass; grep confirms no remaining per-word
  `find_cst_source_sutta_example` call in the controller.

## Phase 3: Verification & lint gate

- [x] Pre-commit trio on every touched file + full `tests/gui2/` run.
  → verify: ruff check, ruff format, pyright clean; all tests pass.
  ✓ 2026-07-15: trio clean on all 5 touched files (note: `tools/cst_source`
  is ruff+pyright-excluded in pyproject.toml, checked anyway); full suite
  1582 passed. Smoke gate: `uv run pytest tests/` green.
- [x] Manual verification (user): AN run with in-comps ON — next word
  appears instantly; example lists spot-checked identical; rapid clicking
  causes no errors.
  → verify: user confirmation.
  ✓ 2026-07-15: user confirmed — "blazing fast. i'm happy".
