# Spec — gui2 startup latency

Relates to #212 (flet 1.0 migration thread) only by proximity. **This is not a
migration regression** — see "What did not change" below. No dedicated issue.

Revised 2026-09-18 after two independent reviews. Their substantive findings
are folded in; the changes they forced are listed at the end.

## Overview

`gui2` takes ~15 s from launch to a loaded database. Two independent causes
were measured, both of which predate the flet 1.0 migration:

1. `gui2/books.py` builds its full SuttaCentral text index **at module import
   time**, on the main thread, before the window can paint. ~2.95 s every
   launch, whether or not the session ever opens pass1auto or pass2pre. This
   is real work removed from the critical path.
2. `gui2/main.py` starts `_warmup_in_background` and
   `_initialize_db_in_background` as two concurrent `page.run_thread` workers.
   Both are CPU-bound Python, so the GIL interleaves rather than parallelises
   them, and the database load — the thing the editor cannot work without —
   finishes later than it needs to.

Fix 1 removes work. Fix 2 removes nothing; it reorders. Both are worth doing,
for different reasons, and the success criteria below keep them separate.

## Measured baseline

All figures from this machine, warm page cache, 2026-09-18, via the harnesses
in `artifacts/`. **Every row is a single run.** Review correctly flagged that
run-to-run variance is understated here, and one row is unexplained (below).
Phase 1 regenerates this table as medians of three before anything is
compared against it.

Current behaviour, unmodified:

| stage | elapsed | duration |
|---|---|---|
| flet client connected | 0.61 s | — |
| `ToolKit` built | 3.93 s | 0.41 s |
| `build_ui` done | 3.95 s | 0.01 s |
| **first paint** (`App.__init__`) | **3.95 s** | **3.34 s** |
| all 16 tabs warmed | 7.74 s | 3.69 s |
| **database loaded** | **15.19 s** | **11.14 s** |
| everything done | 15.19 s | — |

Variants run to isolate each cause:

| variant | db load | db loaded at | all tabs warm at | everything done |
|---|---|---|---|---|
| unmodified | 11.14 s | 15.19 s | 7.74 s | 15.19 s |
| warm-up deferred until after the load | 8.29 s | 12.24 s | 14.46 s | 14.46 s |
| warm-up disabled entirely | 7.04 s | 11.03 s | n/a | n/a |
| `initialize_db()` alone, no GUI process | 6.21 s | — | — | — |

**What deferral actually buys.** The database is ready 3 s sooner (15.19 →
12.24). Time to everything-done is essentially unchanged (15.19 → 14.46) —
total CPU work is conserved, as it must be under the GIL. The warm-up's own
duration falls from 3.69 s to 2.22 s once it isn't interleaved, which is why
the total doesn't get worse. So this fix is about **priority, not throughput**:
the load the editor cannot work without stops sharing the interpreter with
speculative prefetch. Any claim that it "saves" 3 s of work is wrong.

**Unexplained discrepancy, carried forward deliberately.** The deferred
variant's load took 8.29 s where the disabled control took 7.04 s. If the
warm-up genuinely waits, those should match. Either the harness let the
warm-up start early, or single-run variance is larger than the ~±0.3 s assumed.
Phase 1 must resolve this with medians before Phase 3's threshold is trusted —
and Phase 3's target is the 7.04 s control, not the 8.29 s observation.

Breakdown of the 3.34 s before first paint: `ToolKit` accounts for 0.41 s and
`build_ui` for 0.01 s. The remaining ~2.9 s is the block of deferred view
imports at the top of `App.__init__`. Measured individually, importing
`gui2.pass1_add_view` costs 3.32 s, of which `gui2.books` is 2.95 s of *self*
time. Of that 2.95 s, directory scanning is 0.02 s — the rest is JSON parsing
and word indexing.

Two smaller items also sit inside `App.__init__` and will still be there after
the books fix: the daily-log counts read for the app bar, and the username
resolution at the end. Both look trivial, neither has been timed separately.
They are part of the ~0.4 s residual, so a post-fix first paint of 1.4 s is
expected, not a surprise.

Database load internals, measured standalone (warm): deconstructor lookup scan
1.51 s, full headword corpus load 3.19 s, relationship detector 1.12 s, the
five GUI pre-queries 0.36 s, remainder ~0.03 s.

## What did not change

Stated explicitly because the investigation started from "this got slower
since yesterday" and that premise was **not** confirmed:

- `gui2/toolkit.py` and `gui2/database_manager.py` are byte-identical to
  yesterday's pre-migration commit.
- `gui2/books.py` last changed 2026-04-30; the `resources/sc-data` submodule
  pointer last moved 2026-07-28.
- The background warm-up predates the migration (added 2026-07-17).

No code change was found that would have made startup worse this week. The one
visible difference the migration did introduce is that the rewritten tabs show
a progress ring while the app loads, so the existing wait is now advertised
where previously the window looked finished. That is a hypothesis for the
changed *perception*, not a measured cause.

## What it should do

**1. `gui2/books.py` — build the text index on first use, not on import.**

`SuttaCentralSource.__init__` currently calls `make_segment_dict()` and
`process_words()`, and the module-level `sutta_central_books` dict constructs
all 21 sources eagerly. After the change, constructing a source stores only its
identity and paths; `segment_dict` and `word_dict` become cached properties
that do the work on first access.

Verified by exhaustive grep (`segment_dict`, `word_dict`, `pali_file_list`,
`english_file_list`, `allowable_chars`, `cst_books`, `sutta_central_books`
across all `.py` outside `archive/`), the only attributes any caller outside
`books.py` touches are:

| attribute | consumers |
|---|---|
| `.cst_books` | pass1_auto_controller, pass2_pre_controller, pass2_auto_control (×2) |
| `.sc_book` | pass2_pre_controller |
| `.word_dict` | pass1_auto_controller, pass2_pre_controller |
| dict keys only | pass2_pre_controller, pass2_auto_control |

`segment_dict`, `pali_file_list`, `english_file_list` and `allowable_chars`
have no external consumers, so they are free to become lazy internals. Both
`.word_dict` reads sit inside user-initiated book processing, and both key
iterations are cheap.

That last point — that nothing in view construction or the warm-up touches
`.word_dict` — is the load-bearing assumption of the whole fix. If a view
constructor did touch it, the warm-up would pay the 2.95 s anyway and fix 1
would buy nothing on the common path. The grep says it doesn't. Phase 2 turns
that into evidence with a runtime check rather than leaving it a static
argument.

**2. `gui2/main.py` — run the warm-up after the database load, not against it.**

The database load is a prerequisite for editing anything. The warm-up is
speculative prefetch of tabs the session may never open, and clicking an
unbuilt tab already builds it on demand. Under the GIL the two compete, so the
prerequisite should run alone and the speculative work should yield to it.

`build_ui` currently starts both workers. Start only the database worker;
`_initialize_db_in_background` starts the warm-up from its `finally` block so
it runs whether the load succeeded or failed — preserving today's behaviour,
where the warm-up always runs and in fact usually runs *before* the load has
finished.

## Assumptions & uncertainties

- **Verified by reading the code or measuring:** every figure in the tables
  above; the consumer list for `SuttaCentralSource`; that
  `tests/gui2/test_pass2_pre_components.py` substitutes a duck-typed fake
  carrying only `.sc_book`, `.cst_books` and `.word_dict`, so a lazier real
  class cannot break it; that clicking an unbuilt tab already builds it on
  demand via `_on_tab_activated`.
- **Assumed, not verified:** that the ~3 s saved before first paint is paid
  back acceptably when a book is first selected in pass1auto or pass2pre. The
  work does not disappear — it moves to the first book selection, which is
  already a slow, explicitly-initiated operation. Nobody has timed that path
  with a cold index. Phase 4 does.
- **Assumed:** that the warm-up is safe to run when the database load has
  *failed*. Today's code already runs it concurrently with the load, i.e.
  usually before any data is available, and it survives — so the view builders
  evidently do not require a loaded database. But nobody has stated or tested
  that, and on failure the retry path can start a second load and hence a
  second warm-up while the first is still iterating tabs. Phase 3 exercises
  the failed-load path rather than reasoning about it.
- **Accepted risk:** `functools.cached_property` has had no internal lock
  since Python 3.12. If two threads first touched `.word_dict` simultaneously
  the index would be built twice — wasteful, not corrupting. Both call sites
  are user-initiated handlers on one book at a time, so this is judged not
  worth a lock. `ToolKit` does take an `RLock` for its lazy managers, so there
  is a precedent if review disagrees. Both reviewers saw this and agreed.
- **Known, not a defect:** a tab clicked while the warm-up is mid-build blocks
  on the shared build lock until the tab currently being built finishes — up
  to ~1.6 s, longer where one builder chains another. That is existing
  behaviour, not introduced here, and it is why Phase 3's interactive check
  allows a couple of seconds rather than expecting instant.
- **Not reproduced:** the user's original ~30 s. That measurement was taken
  with the database evicted from the OS page cache, so it reflects a cold
  read, not steady state. Warm, the number is ~15 s.

## Constraints

- No behaviour change. Same data, same tabs, same order of appearance — only
  when the work happens.
- Touching a file means owning its lint: `ruff check --fix`, `ruff format`,
  `pyright`, then the related tests. `gui2/` is pyright-excluded but not
  ruff-excluded and commonly carries pre-existing violations.
- Modern type hints throughout; `Path` over `os`.
- Do not `git stash`, `git checkout --`, `git restore` or `git reset --hard` —
  concurrent threads share this working tree.
- Measurement uses the harnesses in `artifacts/`, not edits to `gui2/main.py`.
- Every reported figure is a median of at least three runs.

## How we'll know it's done

1. A new test asserts that constructing a `SuttaCentralSource` leaves the
   index unbuilt and that touching `word_dict` builds it exactly once. It
   fails against current code.
2. First paint under ~1.5 s, median of three (from 3.95 s).
3. **Database loaded under ~8 s, median of three** (from 15.19 s). The load
   itself should approach the 7.04 s warm-up-disabled control; if it sits at
   8.3 s the Phase 1 discrepancy was real and must be explained, not accepted.
4. **A tab clicked immediately after the database loads builds in under ~2 s.**
5. **All tabs warm is reported but does not gate the thread.** It is expected
   to land around 11–12 s and must not be materially worse than today's
   15.19 s everything-done figure.
6. The warm-up line appears after the database line, never interleaved.
7. `uv run pytest tests/gui2/` passes; `just typecheck` clean.
8. Opening pass1auto or pass2pre and selecting a book still produces the same
   word list as before.

## What's not included

- The 7 s database load itself. Its three components are known (deconstructor
  scan, corpus load, relationship detector) but reducing them is a separate,
  larger piece of work.
- The stale uvicorn holding port 8080, which makes every launch log a bind
  error and leaves in-app word lookup served by an older process. Real, but a
  separate concern.
- The antigravity CLI probe, which spends 60 s on a background thread every
  launch and always fails on this machine. It blocks nothing — the timeout
  lands long after startup — but it is waste. Separate.
- `allowable_chars`, which has no consumer anywhere. Deleting it is unrelated
  cleanup.
- Any attempt to explain a week-on-week regression. None was found.
- Reinstating a flet 0.28 environment to A/B against the pre-migration build.

## Changes forced by review

Recorded so the reasoning isn't lost:

- The headline "usable in ~9 s instead of ~15 s" was removed. "Usable" was
  never defined and silently meant time-to-database-loaded, which hid that
  deferral moves the warm-up's cost rather than eliminating it. Success
  criteria are now three separate figures.
- Fix 2's justification was rewritten from a throughput claim to a priority
  one. Under the GIL two CPU-bound workers cannot inflate total CPU work; the
  11.14 s load duration was absorbing the warm-up's CPU, not suffering from it.
- The 8.29 s vs 7.04 s gap was accepted uncritically as the expected effect.
  It is now flagged as unexplained, and Phase 3's target is the control.
- The baseline table's single-run basis is now stated, and medians are
  required everywhere.
- One reviewer derived all-tabs-warm under deferral as ~15.9 s and concluded
  deferral might be worse on that metric. That figure was derived rather than
  read: the run was measured at 14.46 s. Phase 1 later showed the reasoning
  on both sides was off: the warm-up does **not** speed up off the critical
  path (3.66 s deferred vs 3.65 s contended — the 2.22 s figure was one run),
  so deferral lands 0.56 s **worse** on everything-done (14.46 → 15.02 s)
  while buying the 3.0 s earlier database. The reviewer's concern was right
  in substance; the metric is reported and does not gate the thread.
