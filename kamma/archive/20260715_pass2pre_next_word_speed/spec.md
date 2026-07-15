# Spec: pass2pre next-word loading speed

## Overview

In gui2's Pass2Pre tab, loading the next word takes 0.4–1.1s, and instrumented
timing (2026-07-15, AN run) shows the CST example fetch is the entire wait:

- headword resolution: 0.01s
- **example fetch (`get_cst_examples`): 0.42–1.14s** — regardless of result
  count (1 example took 1.14s; 183 took 0.42s; variation is regex cost)
- UI render: 0.01–0.02s

The user powers through hundreds of Yes/No decisions per session (especially
in the new "in comps" mode, which multiplies queue size ~4×), so this wait is
the dominant UX drag. The double-click IndexError (already guarded) was a
symptom: users click again because nothing happens.

## Current behaviour

`gui2/pass2_pre_controller.py::get_cst_examples()` calls
`tools/cst_source/extractor.py::find_cst_source_sutta_example(book, regex)`
once per CST book (AN = 11 books) per word. Each call:
1. re-reads the book's UTF-16 XML and re-parses it with BeautifulSoup
   (`tools/cst_source/loader.py::make_cst_soup` — no caching),
2. walks every `head`/`p` element, cleans its text (`clean_example`),
3. regex-searches the cleaned text, extracting sentence or gatha examples,
4. tracks source/sutta via a stateful per-book parser (`parser.update(x)`).

## Two candidate methods — decision by benchmark + engineering complexity

**A. Background prefetch.** While the user reviews word N, a daemon thread
fetches word N+1's examples into `missing_examples_dict[next_word]`.
`load_next_word` already skips fetching when an entry's examples are
pre-filled, so results integrate naturally. Latency per word is unchanged but
hidden; Next feels instant whenever review time > fetch time (almost always).
Complexity: thread lifecycle in the controller — an in-flight marker, a lock,
and the race where the user outpaces the prefetch (must then wait for the
in-flight fetch, not start a second one). No change to `tools/cst_source`.

**B. Per-session corpus index.** Build once per PreProcess run a flat list of
`(source, sutta, cleaned_text, element_ref_or_gatha_data)` per book by walking
the soups a single time; per-word search becomes a regex scan over in-memory
strings (~50ms expected). Eliminates the cost instead of hiding it — also
speeds up the first word and any future bulk callers. Complexity: gatha
examples currently need the live soup element (`find_gatha_example(x, ...)`),
so the index must either store enough gatha context or keep soups alive;
`tools/cst_source` is shared with other callers (scripts, exporter checks) and
must stay backward compatible; memory footprint of the flat text (~tens of MB
for AN) needs a sanity check.

Phase 1 benchmarks both (A is trivially "review time hides fetch time" — the
benchmark is B's build cost and per-word search time, plus a complexity
assessment of the gatha path). The decision and its rationale get recorded
HERE in this spec before implementation starts.

### DECISION (2026-07-15): Method B — per-session corpus index

Benchmark (scratchpad `bench_cst_index.py`, all 11 AN books, 20 sample words
mixing high/low frequency and gatha-heavy):

- **Index build: 1.41s one-off** (10,456 rows, ~3.0M chars ≈ single-digit MB —
  memory is a non-issue). 1.0s of that is ONE malformed gatha element in an6
  hitting `find_gatha_example`'s existing 1s stuck-loop guard; all other books
  build in 0.01–0.07s.
- **Per-word search: avg 34ms, max 124ms** (the max is `evaṃ`, 1865 results —
  real missing-example words are rare and sit at ~25ms). Baseline synchronous
  path: avg 0.48s per word. ~14× faster and under the <100ms goal.
- **Output: 20/20 words byte-identical** to `find_cst_source_sutta_example`,
  including 4 gatha words. The gatha "complexity" dissolved: a gatha example
  depends only on the element (the word argument is used only in an error
  message), so it can be precomputed at build time, cached per gatha1 element,
  with the stuck-loop guard reproduced exactly.

Rationale: B eliminates the wait for every word after the first (the first
word pays the ~1.4s index build, comparable to today's single fetch) rather
than hiding it, and — unexpectedly — is *simpler* than A: no background thread, no lock,
no user-outpaces-prefetch race. A is rejected as the more complex option with
a worse result. `find_cst_source_sutta_example` stays untouched for other
callers; the index is a new module beside it.

## What it should do (whichever method wins)

1. Clicking Yes/No/Pass on the last headword of a word shows the next word
   with its examples with no perceptible wait (< ~100ms) in the common case.
2. Examples shown are identical to today's (same finder semantics, same
   order, same gatha handling).
3. Works in both normal and "in comps" mode; SC words with preloaded segments
   are untouched.
4. No stale results: a prefetched/indexed result for a word must reflect the
   same regex the synchronous path would use (`\bword\b`).

## Assumptions & uncertainties

- Review time per word (seconds) >> fetch time (~1s), so A fully hides the
  wait in practice; B is only worth its complexity if the benchmark shows the
  index build is fast (< ~20s per book-set) and the gatha path is tractable.
- `find_cst_source_sutta_example` is pure/read-only per call (verified: fresh
  soups + fresh parser each call), so calling it from a background thread is
  safe; the only shared state to protect is `missing_examples_dict`.
- Flet handlers run on a thread pool already, so the controller is not
  thread-naive today.

## Constraints

- No behaviour change to example content or ordering.
- `tools/cst_source` public API stays backward compatible (other callers).
- Touched files pass ruff check, ruff format, pyright; tests for new logic.

## How we'll know it's done

- Instrumented timing shows next-word display < ~100ms in the common case on
  an AN run (measured the same way as the 2026-07-15 baseline).
- Byte-identical example lists vs. the synchronous path for a sample of words
  (unit test with a small book fixture; manual spot check on AN).
- No crashes/races when clicking through faster than fetches complete.

## What's not included

- Persisting any index to disk between sessions.
- Optimizing `make_cst_soup` for other callers.
- UI changes beyond removing the wait.
