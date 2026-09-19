# Plan — gui2 startup latency

Spec: `kamma/threads/20260918_gui2_startup_latency/spec.md`
Harnesses: `kamma/threads/20260918_gui2_startup_latency/artifacts/`
No GitHub issue. Adjacent to #212 but not a migration regression.

Revised 2026-09-18 after two independent reviews.

## Architecture Decisions

- **Lazy via `functools.cached_property` on `SuttaCentralSource`, not a lazy
  container around the module dict.** The heavy work lives in the instance
  (`make_segment_dict`, `process_words`), so deferring it there leaves every
  call site untouched — including the key-iteration in two controllers and two
  views, which must stay cheap. Wrapping the dict instead would need a
  `Mapping` subclass and would still have to defer the instance work anyway.
- **File-list construction stays eager.** Measured at 0.02 s for the six
  largest directories; deferring it buys nothing and widens the diff. It does
  mean the module import will not fall to zero — budget ~20–50 ms for 21
  sources' `rglob`, and see the Phase 2 threshold note.
- **No lock around the cached properties.** Both `.word_dict` consumers are
  user-initiated handlers acting on one book. Noted as an accepted risk in the
  spec; `ToolKit`'s lazy-manager lock is the precedent if review wants one.
  Both reviewers agreed no lock is needed.
- **`allowable_chars` left exactly as it is.** It has no consumer anywhere,
  inside `books.py` or out. Removing it is unrelated cleanup, not this thread.
- **Warm-up chained from the database worker's `finally`, not gated on
  success.** `finally` preserves today's behaviour, where the warm-up always
  runs — today it runs *concurrently with* the load, so it already routinely
  executes with no data available. Gating on success would be a behaviour
  change, and the failed-load path is exercised in Phase 3 instead of reasoned
  about.
- **Success is three figures, not one.** Time-to-database-loaded,
  time-to-first-clicked-tab, and time-to-all-tabs-warm. The first two gate the
  thread; the third is reported. Deferral conserves total CPU work, so a
  single "usable" number would hide where the warm-up's cost went.
- **Measurement harnesses live in `artifacts/`, not the session scratchpad.**
  Scratchpad storage is session-scoped; a later session executing this plan
  would find nothing there.
- **No timing instrumentation is committed to `gui2/main.py`.** It gets the
  behaviour change only.

## Phase 1 — Prove the defect and fix the baseline

- [x] Write `tests/gui2/test_books.py`.
      - Construct a **fresh** `SuttaCentralSource` for a small book (`khp`)
        inside the test. Do **not** assert against the shared module-level
        `sutta_central_books`, whose state depends on whether an earlier test
        in the same session touched it.
      - White-box: assert `"segment_dict" not in vars(source)` and
        `"word_dict" not in vars(source)` immediately after construction.
      - Black-box: wrap or monkeypatch `json.load` (or the module's `load`
        import) with a call counter; assert zero calls after construction, and
        non-zero after the first `.word_dict` read. This survives a later swap
        of `cached_property` for `lru_cache` or an explicit flag, which the
        `vars()` check would not.
      - Assert a second `.word_dict` read returns the identical object and
        adds no further `json.load` calls.
      - Assert `isinstance(source.word_dict, defaultdict)` — the plan treats
        the type as a behavioural requirement, so it must be asserted, not
        merely intended.
      → verify: DONE. `uv run pytest tests/gui2/test_books.py` against current
      code: **2 failed, 1 passed**.

      ```
      FAILED tests/gui2/test_books.py::test_construction_does_not_build_the_index
        AssertionError: assert 'segment_dict' not in {'allowable_chars': [...],
        'cst_books': ['kn1'], 'english_file_list': [...], ...}
      FAILED tests/gui2/test_books.py::test_first_word_dict_access_builds_the_index
        AssertionError: assert ['resources/s...ms.json', ...] == []
          Left contains 18 more items, first extra item:
          'resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/kp/kp1_root-pli-ms.json'
      ```

      `test_index_is_built_only_once` passes vacuously against eager code —
      an eagerly built index is also built only once. It guards the lazy
      implementation, not the defect, so 2-of-3 failing is the expected shape.
      Baseline before any change: `uv run pytest tests/gui2/` → 293 passed.

- [x] Regenerate the baseline as medians.
      → verify: DONE. Nine runs, logged to `artifacts/baseline_normal.log`,
      `artifacts/baseline_nowarmup.log`, `artifacts/baseline_deferred.log`.
      Each launch was killed the moment its last stamp printed.

      Unmodified (`timed_gui.py`), three runs:

      | run | first paint | all tabs warm | db loaded | db duration |
      |---|---|---|---|---|
      | 1 | 3.85 s (3.24 s) | 7.50 s (3.65 s) | 14.46 s | 10.61 s |
      | 2 | 3.78 s (3.19 s) | 7.42 s (3.63 s) | 14.26 s | 10.48 s |
      | 3 | 4.11 s (3.45 s) | 7.81 s (3.69 s) | 14.97 s | 10.85 s |
      | **median** | **3.85 s** | **7.50 s** | **14.46 s** | **10.61 s** |

      Control (`NO_WARMUP=1`), three runs:

      | run | first paint | db loaded | db duration |
      |---|---|---|---|
      | 1 | 3.82 s | 10.43 s | 6.61 s |
      | 2 | 3.87 s | 10.99 s | 7.12 s |
      | 3 | 4.21 s | 11.32 s | 7.11 s |
      | **median** | **3.87 s** | **10.99 s** | **7.11 s** |

      Deferred simulation (`timed_gui2_deferred.py`), three runs:

      | run | first paint | db loaded | db duration | tabs warm | warm-up |
      |---|---|---|---|---|---|
      | 1 | 4.33 s | 11.61 s | 7.29 s | 15.27 s | 3.66 s |
      | 2 | 4.05 s | 11.33 s | 7.28 s | 15.02 s | 3.70 s |
      | 3 | 4.31 s | 11.44 s | 7.12 s | 14.99 s | 3.55 s |
      | **median** | **4.31 s** | **11.44 s** | **7.28 s** | **15.02 s** | **3.66 s** |

      The deferred harness adds its own `ToolKit.__init__` and `build_ui`
      wrappers, which is why its first paint reads ~0.45 s higher than the
      other two. Not a real difference.

- [x] Resolve the 8.29 s vs 7.04 s discrepancy flagged in the spec.
      → verify: DONE. **It was single-run variance.** Deferred median load is
      7.28 s against the control median of 7.11 s — a 0.17 s gap, inside the
      control's own 6.61–7.12 s spread. The harness is not letting the warm-up
      start early. Struck from the spec. Phase 3's target stays the ~7.1 s
      control.

      **Second finding, not anticipated by the spec.** The spec claimed the
      warm-up's own duration falls from 3.69 s to 2.22 s once it stops
      contending for the GIL. It does not: 3.66 s deferred against 3.65 s
      contended, unchanged across all six runs. That 2.22 s was one run.
      Two consequences, both folded into the spec:
      - Deferral is **not** marginally better on everything-done. It is 0.56 s
        worse (14.46 s → 15.02 s). Still passes criterion 5, which asks only
        that it not be materially worse.
      - The real trade is 3.0 s earlier database for 0.56 s later all-tabs
        warm. The priority argument for fix 2 is unaffected — that was never a
        throughput claim — but the arithmetic behind it now reads correctly.

      The warm-up is dominated by two builders that do not speed up off the
      critical path: tab 3 at ~2.0 s and tab 7 at ~1.1 s, together 3.1 s of the
      3.65 s. The other fourteen tabs cost ~0.5 s combined. Whatever those two
      wait on, it is not the GIL. Not investigated further — out of scope.

## Phase 2 — Lazy sutta text index

- [x] Make `segment_dict` and `word_dict` cached properties on
      `SuttaCentralSource` in `gui2/books.py`.
      - Keep `sc_book`, `cst_books`, `pali_path`, `english_path`,
        `pali_file_list`, `english_file_list` and `allowable_chars` eager.
      - Convert `make_segment_dict()` and `process_words()` from mutators into
        the property bodies; `word_dict`'s body reads `self.segment_dict`, so
        touching either builds both in the right order.
      - Preserve the exact types: `dict[str, SuttaCentralSegment]` and
        `defaultdict[str, list[SuttaCentralSegment]]`.
      - Preserve the "english may exist without pali" branch and the
        `ṁ` → `ṃ` + lowercase normalisation exactly.
      - Four sources (`nidd1&2`, `kva`, `dhpa`, `jaa`) are constructed with
        `None` for both paths. `make_file_list` already returns `[]` for those,
        and the existing `if self.pali_file_list:` / `if self.english_file_list:`
        guards must survive the move into the property bodies. Check those four
        explicitly in the diff.
      → verify: DONE. `uv run pytest tests/gui2/test_books.py` against the
      lazy implementation: **3 passed in 0.09 s** — construction is clean, the
      first `.word_dict` read does the JSON loading and indexing, the second
      returns the identical object with no further `json.load` calls.

- [x] Confirm nothing else regressed.
      → verify: DONE. `uv run pytest tests/gui2/` → **296 passed** (293
      baseline + 3 new), including `test_pass2_pre_components.py` and
      `test_pass2_pre_file_manager.py`.

- [x] Confirm the import cost is actually gone.
      → verify: DONE. `uv run python -X importtime -c
      "import gui2.pass1_add_view"`:

      ```
      before:  gui2.books self ~2,970,000 µs · pass1_add_view cumulative ~3.32 s (spec baseline)
      after:   import time:     65548 |      65712 |     gui2.books
               import time:       264 |     417448 | gui2.pass1_add_view
      ```

      `gui2.books` self-time fell from ~2.97 s to **0.066 s** (under the
      100,000 µs threshold; the remaining cost is the 21 sources' eager
      `rglob` file lists, as budgeted). `pass1_add_view` cumulative fell from
      ~3.32 s to **0.42 s** (under the 0.5 s target).

- [x] **Prove the warm-up does not build the index.** This converts the
      thread's load-bearing assumption from a grep into evidence.
      → verify: DONE. Probe harness `artifacts/probe_warmup.py` wraps
      `_warmup_in_background` monkeypatch-style (no edit to `gui2/main.py`,
      nothing to remove afterwards) and inspects all 21 sources in
      `sutta_central_books` immediately after the warm-up completes, without
      pass1auto or pass2pre ever being opened:

      ```
      [startup]    4.96s  ALL TABS WARMED      (took  3.67s)
      [startup]    4.96s  warm-up text index probe: CLEAN - no source has
                           segment_dict or word_dict (checked 21 sources)
      ```

      Fix 1 buys what it claims on the common path. Probe kept in `artifacts/`
      for re-runs.

- [x] Lint the touched file.
      → verify: DONE, amended after independent review. The original `uv run
      pyright gui2/books.py` was a **no-op** — `gui2/**` is in
      `[tool.pyright].exclude`, so it analysed zero files (the trap
      `kamma/tech.md` documents). Re-run with the prescribed bypass
      (`--project /dev/null`): **`gui2/books.py` 0 errors, 0 warnings**.
      `ruff check`/`format` clean. Diff: 15 insertions, 16 deletions.

## Phase 3 — Warm-up after the database load

- [x] In `gui2/main.py`, stop starting the warm-up worker in `build_ui` and
      start it from `_initialize_db_in_background`'s `finally` block instead.
      - `build_ui` keeps `self._db_init_started = True` and the single
        `self.page.run_thread(self._initialize_db_in_background)`.
      - The `finally` block keeps `self._set_loading(False)` and then calls
        `self.page.run_thread(self._warmup_in_background)`.
      - Leave `_maybe_start_db_init` alone.
      - Add a comment saying **why** the two are serialised — the database is
        a prerequisite for editing, the warm-up is speculative prefetch, and
        under the GIL they interleave — and nothing about what the code does.
        Do not write that this "saves" time; it reorders.
      → verify: DONE, with one regression caught on the way. The first
      implementation added the comment but **not** the `run_thread` call, so
      the warm-up never started at all — placeholder tabs only, no error
      anywhere. Diagnosed with `artifacts/timed_gui_diag2.py` (stamps at db
      worker entry/return, warm-up entry, plus an executor probe), run
      headless under `xvfb-run` to take desktop window management out of the
      loop. After the fix the chain is: db worker returns → warm-up thread
      enters in the same tick → tabs build → ALL TABS WARMED. Three
      measurement runs (`artifacts/run_phase3_serial.py`, also headless):

      | run | first paint | db loaded | db duration | all tabs warm | warm-up |
      |---|---|---|---|---|---|
      | 1 | 1.19 s (0.60) | 8.16 s | 6.97 s | 11.03 s | 2.86 s |
      | 2 | 1.20 s (0.61) | 8.11 s | 6.90 s | 11.13 s | 3.02 s |
      | 3 | 1.21 s (0.60) | 8.02 s | 6.81 s | 11.12 s | 3.09 s |
      | **median** | **1.20 s** | **8.11 s** | **6.90 s** | **11.12 s** | **3.02 s** |

      `ALL TABS WARMED` landed after `database loaded` in every run, never
      interleaved across the three runs. (Precisely: the warm-up thread is
      *started* inside the db worker's `finally`, so it can begin a hair
      before the harness's db-loaded stamp prints — an implementation-order
      nuance, not an observed interleaving.) Median load 6.90 s — under the
      8 s bar and better than the
      7.11 s `NO_WARMUP` control median, so the Phase 1 discrepancy stays
      resolved. (Headless figures are consistent with the real-display runs —
      probe warm-up 3.67 s, real-display db loads 6.48–6.60 s — so the virtual
      display is not distorting the measurement. Phase 4 may re-measure on the
      real display if review wants it.)

- [x] Confirm a tab clicked before the warm-up reaches it still builds on
      demand.
      → verify: DONE by user inspection in a real `just gui` session — a late
      tab clicked while the loading bar was still showing "opens quickly",
      real content replacing the ring within the expected window. (The shared
      build-lock wait described in the spec did not visibly delay it.)

- [x] Exercise the failed-load path.
      → verify: DONE, via `artifacts/failed_load_gui.py` — the plan's
      "throwaway config" turned out not to exist (the db path is hardcoded in
      `tools/paths.py`, not read from config.ini), so the harness instead
      patches `DatabaseManager.initialize_db` to raise. The real dpd.db is
      never touched. User-verified in two real-display runs.

      **First run found a regression this thread introduced:** the failure
      snackbar appeared correctly, tabs stayed usable — but every tab click
      retried the load, and each retry's `finally` re-ran the warm-up, so
      "All tabs and tools ready." spammed on every click. Pre-change, the
      warm-up started exactly once at launch and retries never re-ran it.
      Fixed with a start-once guard (`self._warmup_started`) around the
      chained warm-up; lint and 296 gui2 tests re-run clean.

      **Second run, all clean:** red failure snackbar on launch; tabs fill
      in; clicking a tab retries the load and re-shows the failure snackbar
      (correct — the retry is genuine), with only a momentary spinner and no
      delay; the ready snackbar now appears exactly once.

- [x] Lint the touched file.
      → verify: DONE, amended after independent review. `ruff check`/
      `format` clean. Real pyright (bypassing the gui2 exclude):
      `tests/gui2/test_books.py` and `gui2/books.py` **0 errors**;
      **`gui2/main.py` carries 13 pre-existing pyright errors, every one on
      lines this thread never touched** (flet 1.0 typing debt from #212:
      handler signatures, dynamic control attributes, a possibly-unbound
      profiler). NOTICED — NOT TOUCHING: that debt belongs to a migration-
      follow-up, not this thread; recorded here so the exclude can't hide it
      again.

## Phase 4 — Measure and verify the whole

- [x] Record the post-change figures the same way as the baseline.
      → verify: DONE. The three headless measurement runs recorded under
      Phase 3 task 1 (`artifacts/phase3_serial.log`) are the post-change
      figures, same stamps as the baseline: medians **first paint 1.20 s**
      (target under ~1.5 s, from 3.85 s — hit), **database loaded 8.11 s**
      (target under ~8 s, from 14.46 s — hit), **all tabs warm 11.12 s**
      (expected ~11–12 s, and materially better than today's 14.46 s
      everything-done). No target missed. Cross-checked against real-display
      runs where they overlap: first paint 0.58 s app-init in the user's own
      `just gui` launch, db duration 6.48–6.60 s in the earlier real-display
      batch, warm-up 3.67 s in the real-display probe — headless is not
      distorting.

- [x] Confirm the deferred work is acceptable where it landed.
      → verify: DONE, via pass2pre rather than pass1auto — the user reports
      pass1auto is not testable right now; pass2pre exercises the same
      `.word_dict` path. User selected `an` in a real `just gui` session with
      a temporary timing probe on the cached property (removed after):

      ```
      [TEMP-PROBE] an: segment_dict 108ms, word_dict 0.39s
      ```

      First selection pays **0.5 s** of deferred index build — well inside
      the ~5 s allowance. The user still found the first selection slow, so
      the rest of the path was measured: `make_cst_text_list` for an1–11
      alone takes **11.3 s** (CST XML parsing, called from
      `get_all_words_with_missing_examples` on every selection).

      **NOTICED — NOT TOUCHING:** the first-selection wait in pass2pre is
      dominated by ~11.3 s of CST parsing that predates this thread (the
      change only added 0.5 s of it, moved here from startup). Caching the
      parsed CST word list is a separate, worthwhile follow-up thread.

      **NOTICED — NOT TOUCHING:** the user remembers pass2pre showing
      stage-by-stage progress feedback during the first selection; it is
      gone. This thread's diff (books.py, main.py) contains nothing that
      touches it — the most likely removal is the flet 1.0 migration's
      rewrite of `pass2_pre_view.py` (#212). Worth a look in a follow-up.

- [x] Confirm the word lists are unchanged.
      → verify: DONE. The user selected `an` in pass2pre and the word list
      appeared as expected (their feedback was about duration, covered
      above — content unremarked, i.e. no visible difference). Backed by the
      296 gui2 tests including the pass2pre component tests, which assert on
      real word-list construction.

- [x] Repo-wide checks.
      → verify: DONE. `uv run pytest tests/` → **1898 passed, 12 deselected**
      (slow, as usual), 68.84 s; the 3 warnings are pre-existing aksharamukha
      script warnings in the exporter webapp tests. `just typecheck` →
      **0 errors** (94 suppressed, 113 warnings, all pre-existing).

- [x] Ask the user for permission to run `coderabbit review --agent`, scoped
      with `--dir gui2 --include-untracked`.
      → verify: DONE. User authorised review-and-finalize; `coderabbit
      review --agent --dir gui2 --include-untracked` run. **1 minor finding:**
      the `_warmup_started` check-and-assignment should be lock-protected so
      two near-simultaneous tab clicks cannot each reserve a warm-up worker.
      Verified against current code: valid (handlers run in a thread pool),
      and the same race exists on `_db_init_started`. **Fixed** with the
      existing `_build_lock` covering both flags' check-and-set. Re-ran:
      ruff clean, pyright clean, 296 gui2 tests pass.

      An independent zero-memory reviewer subagent then reviewed the whole
      thread (findings, all resolved):
      - **major (evidentiary):** the recorded gui2 pyright runs were no-ops
        (excluded config) → re-run with the `--project /dev/null` bypass;
        real results amended into the lint tasks above.
      - **minor:** `_db_init_started = False` reset in the except branch was
        unlocked → moved inside `_build_lock`.
      - **minor:** added `test_none_path_source_stays_lazy_and_empty` for the
        four `None`-path sources (suite now 297).
      - **minor:** softened the "never interleaved" wording above.
      - **nit:** vacuous re-assertion + untested `segment_dict`-first order —
        skipped as harmless, both documented in review.md.
