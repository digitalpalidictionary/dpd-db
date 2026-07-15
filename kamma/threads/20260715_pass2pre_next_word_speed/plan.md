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

- [ ] Prototype B's index build on a throwaway script (scratchpad, not repo):
  walk all 11 AN books once via `make_cst_soup`, extract flat
  `(source, sutta, cleaned_text)` rows using the existing parser classes,
  time the build and the per-word regex scan for 20 sample words (mix of
  high/low frequency, gatha-heavy included). Compare outputs against
  `find_cst_source_sutta_example` for those words — note any gatha
  divergences and what fixing them would take.
  → verify: script prints build time, per-word search time, and an
  identical/divergent report for the 20 words.
- [ ] Record the decision (A, B, or A-now-B-later) with numbers and
  rationale in spec.md under "Two candidate methods".
  → verify: spec.md updated; decision references measured numbers.

## Phase 2: Implement the winner

(Tasks written after Phase 1's decision — placeholder outlines below.)

- [ ] If A: prefetch worker in `Pass2PreController` — after
  `load_next_headword()` displays word N, submit a daemon thread that
  computes examples for the next queue entry and stores them under a lock;
  `get_cst_examples` waits on an in-flight fetch for its word instead of
  refetching.
  → verify: unit test with a slow fake finder — next word's examples are
  ready before it's requested; racing ahead waits (no double fetch, no
  cross-word contamination).
- [ ] If B: index module + wiring into `get_cst_examples`.
  → verify: unit test — index results byte-identical to
  `find_cst_source_sutta_example` on a small book fixture.

## Phase 3: Verification & lint gate

- [ ] Pre-commit trio on every touched file + full `tests/gui2/` run.
  → verify: ruff check, ruff format, pyright clean; all tests pass.
- [ ] Manual verification (user): AN run with in-comps ON — next word
  appears instantly; example lists spot-checked identical; rapid clicking
  causes no errors.
  → verify: user confirmation.
