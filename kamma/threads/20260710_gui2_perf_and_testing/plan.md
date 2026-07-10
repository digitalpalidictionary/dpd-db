# Plan: gui2 Performance, Resource Use & Testability (#157)

Task states: `[ ]` todo · `[~]` in progress · `[x]` done

Each phase ends with a checkpoint: report results to the user, decide together
what the numbers justify, then proceed. No refactor without a benchmark or test
backing it.

## Model assignments

Each phase names the model to run it with. **At the start of every phase, remind
the user to switch to that phase's model before doing any work.** Reviews run a
tier up from the writer (or a fresh session of the same tier for Fable).

| Phase | Model | Why |
|---|---|---|
| 1–3 | Sonnet | mechanical tests + simple benchmark scripting |
| 4–6 | Fable | SQLAlchemy session semantics, threading, Flet UI-thread risk |
| 7 | Opus | wide blast radius, individually simple changes |
| 8 | Sonnet | small mechanical fixes, if it happens at all |

## Commit cadence

One commit per phase, not one commit for the whole thread — but I never run
git myself. `/cm` only drafts commit message text; it does not stage or
commit anything. At each phase's CHECKPOINT:
- If the checkpoint requires a user smoke test (phases 4, 5, 6, 7), wait for
  the user to confirm the manual test passed before drafting anything.
- Once the phase's checks are satisfied (automated-only phases: 1, 2, 3, 8 —
  or manual test confirmed: 4–7), run `/cm` to draft a commit message from
  the actual diff, and note which files belong to this phase (call out any
  unrelated pre-existing dirty files so the user can exclude them).
- Hand the drafted message + file list to the user and STOP. The user runs
  `git add`/`git commit` themselves — I do not run any git write command
  (not even `git add`), regardless of how the conversation reads. See
  [[feedback_never_run_git_unprompted]].

## Phase 1 — Test safety net (zero-refactor)

**MODEL: Sonnet — remind the user to switch before starting this phase.**

- [x] 1.1 Tests for `gui2/dpd_fields_functions.py`: `find_stem_pattern`
      (table-driven over POS/ending matrix), `make_lemma_2`,
      `make_construction`, `increment_lemma_1`, `clean_lemma_1`, `clean_root`,
      `clean_construction_line1`, `make_compound_construction_from_headword`,
      `make_dpd_headword_from_dict`, `clean_text`, `remove_bold_tags`
      → verify: `uv run pytest tests/gui2/test_dpd_fields_functions.py` (99 passed)
- [x] 1.2 Tests for `gui2/needs_example.py`: `has_only_late_examples`,
      `is_missing_sutta_example`
      → verify: `uv run pytest tests/gui2/test_needs_example.py` (11 passed)
- [x] 1.3 Tests for `db_tests/db_tests_manager.py` core via `object.__new__`:
      `integrity_check`, `error_test_each_single_row`,
      `run_test_on_all_db_entries`
      → verify: `uv run pytest tests/db_tests/test_db_tests_manager.py` (11 passed)
- [x] 1.4 Tests for additions/corrections free helpers
      (`_contributor_from_origin`, `_remove_key_from_file`)
      → verify: `uv run pytest tests/gui2/` (14 passed, both modules)
- [x] CHECKPOINT: full suite green (`uv run pytest tests/` → 1372 passed,
      16 deselected); coverage gained: 135 new tests across
      `dpd_fields_functions` (find_stem_pattern, make_lemma_2,
      make_construction, increment/clean helpers, make_compound_construction_
      from_headword, make_dpd_headword_from_dict, clean_text,
      remove_bold_tags), `needs_example` (has_only_late_examples,
      is_missing_sutta_example), `db_tests_manager` core (integrity_check,
      error_test_each_single_row, run_test_on_all_db_entries), and the
      additions/corrections free helpers. Two dead branches in
      `find_stem_pattern` (masc "rāja masc", fem "mātar fem") and one in
      `make_compound_construction_from_headword` (dvanda unreachable when
      grammar contains "comp") documented as NOTICED — NOT TOUCHING.
      Commit cadence adopted retroactively after this phase and Phase 2 were
      already done — see Phase 2's checkpoint for the combined commit.

## Phase 2 — Testability infrastructure

**MODEL: Sonnet — remind the user to switch before starting this phase.**

- [x] 2.1 Add `base_dir` param to `Gui2Paths` (mirror `ProjectPaths`), derive
      all paths from it; no behavior change for default callers
      → verify: `uv run pytest tests/gui2/test_paths.py` (8 passed); converted
      `@dataclass` (class-body-evaluated defaults) to a plain `__init__` like
      `ProjectPaths`; `for_user()` gained an optional `base_dir` param; all 8
      existing call sites use no-arg `Gui2Paths()`/`for_user(username)`, so
      behavior is unchanged
- [x] 2.2 Route hardcoded `temp/prompts/...` writes in
      `pass1_auto_controller.py` and `pass2_auto_control.py` through
      `ProjectPaths`
      → verify: `ruff check/format`, `pyright`, import smoke test all clean.
      Used the already-available `self.db.pth` (DatabaseManager's
      `ProjectPaths` instance) rather than adding a new param — no new
      coupling needed. Also added `.mkdir(parents=True, exist_ok=True)`
      before each write: `temp/` is fully gitignored and not created by any
      setup step, so the old hardcoded-relative code silently depended on
      the directory already existing on disk; this was required for the
      paths to be usable under a tmp_path sandbox in tests. Removed the
      now-unused `Path` import in `pass1_auto_controller.py` (still needed
      in `pass2_auto_control.py` for other annotations, restored after
      ruff/pyright caught the removal was wrong there).
- [x] 2.3 File-manager tests against tmp_path (real `__init__`):
      `pass1_file_manager`, `pass2_pre_file_manager`, `pass2_auto_file_manager`,
      `filter_presets_manager`, `history`, `daily_log`
      → verify: 47 new tests passed. Used `Gui2Paths(base_dir=tmp_path)`
      directly for the two managers that take `paths: Gui2Paths`
      (`pass1_file_manager`, `pass2_pre_file_manager`); for the four that
      take `toolkit: ToolKit` (`pass2_auto_file_manager`,
      `filter_presets_manager`, `history`, `daily_log`), bypassed
      `ToolKit.__init__` via `object.__new__(ToolKit)` + set only `.paths`
      (and `.appbar_updater` for `daily_log`, a small local fake) — matches
      the `object.__new__` convention already established in
      `test_roots_db.py`. Considered a shared `conftest.py` fake but
      `tests/` has no `__init__.py` and uses `--import-mode=importlib`, so
      cross-file imports from `conftest.py` don't resolve; kept each test
      file self-contained instead.
- [x] CHECKPOINT: full suite green (`uv run pytest tests/` → 1427 passed,
      16 deselected). `Gui2Paths` is now injectable; 6 file managers gained
      real (non-`object.__new__`) constructor tests; two hardcoded `temp/`
      write sites routed through the existing `ProjectPaths` instance.
      No manual test needed (no runtime behavior change). Commit cadence
      adopted retroactively covering Phase 1 + Phase 2 together — when the
      user is ready, run `/cm` to draft the message for review; note that
      `db_tests/db_tests_columns.tsv` is an unrelated pre-existing dirty
      file to exclude. The user stages and commits themselves.

## Phase 3 — Benchmark harness + baselines

**MODEL: Sonnet — remind the user to switch before starting this phase.**

- [x] 3.1 Benchmark harness under
      `kamma/threads/20260710_gui2_perf_and_testing/benchmarks/`
      (`bench_common.py` + 6 scripts, `results/*.json`). Built via a fork
      (large, iterative, trial-and-error work). Real `flet.Page` can't be
      constructed standalone (needs a live Connection+event loop), so the
      "15 view constructors" sub-measurement was dropped in favor of timing
      each ToolKit *manager* construction individually — that's what
      actually drives startup cost. `force_throwaway_db_globally()` in
      `bench_common.py` monkeypatches every `get_db_session` binding so
      nothing can touch the real 2.2GB `dpd.db`; verified via mtime that it
      never changed across all runs. Post-fork cleanup: reordered imports in
      4 scripts to drop `# noqa: E402` (E402 is genuinely selected via the
      "E4" ruff prefix, not inert — the initial removal attempt was wrong
      until reordering fixed it properly); reran affected scripts to confirm
      identical behavior. All 7 files clean on `ruff check`, `ruff format`,
      `pyright`.
- [x] 3.2 Startup breakdown — total ~3.1–4.6s across runs (see note on
      variance below). Three items dominate (~95%+): wordfinder 74MB JSON
      load (~1.7–1.8s), AI manager 6-provider SDK init (~1.0–1.1s),
      `pre_initialize_gui_data` 5 queries (0.3–1.6s, most variance of the
      three). All other ~22 managers combined: under 100ms.
- [x] 3.3 Memory RSS + engine-leak probe — corpus load: 68.8 → 873.2 MB
      (+804 MB, ~83k rows). 50× `new_db_session()`: fd growth +100 without
      closing the previous session, **+79 even when closing it first** —
      confirms closing the session alone does not fix the leak; the Engine
      itself must be reused/disposed.
- [x] 3.4 Engine cost (N=200) — current (new Engine per call): 0.693 ms/call,
      +37 fds. Cached-engine prototype: 0.048 ms/call, +0 fds.
      **14.4× speedup, zero fd growth.**
- [x] 3.5 DB tab — limit 100: 171ms total. limit 1000: 565ms. limit 10000:
      4415ms. **limit 0 (the actual default): 37.4s** (query 9.1s + Flet
      control-tree build 28.3s) in this run; the original fork run measured
      56.7s (query 29.4s + build 27.3s) — page-cache/system-load variance
      changes the absolute split, but query and build are consistently
      comparable in cost, so fixing only one would not fix the freeze.
- [x] 3.6 Corpus load — `initialize_db()` 5.3s, `make_inflections_lists()`
      2.6s, `make_pass2_lists()` 3.4s (three separate full `.all()` loads of
      the same ~89k rows), `RelationshipDetector` build 0.5s. ~11.3s total
      redundant load cost that could be ~1 load.
- [x] 3.7 JSON write amplification — `Pass1FileManager.update()` on the
      7.6MB file: 139ms/edit. `Pass2AutoFileManager` on a synthetic 5000-entry
      (0.7MB) queue: 13ms/edit. Real but minor next to 3.2–3.6 — confirms the
      spec's "may be a no-op" framing for Phase 8.
- [x] CHECKPOINT: numbers confirm the DB tab (Phase 5) and engine/session
      hygiene (Phase 4) findings are unambiguous — measured, not judgment
      calls. Note on variance: absolute ms differ somewhat between the
      fork's original run and my re-verification run (page-cache warmth,
      system load ~1.6/22 cores at time of testing) — relative comparisons
      (14.4× engine speedup, query≈build cost split in the DB tab, 3×
      redundant corpus loads) are stable across both runs and are what the
      phase decisions below rely on. No manual test needed for this
      checkpoint. → presented numbers to user, decided which of phases 4-8
      to run next; once agreed, run `/cm` to draft the message for the
      harness + baseline recordings — the user commits before Phase 4 starts.

## Phase 4 — Engine/session hygiene (Theme A) — if justified by 3.3/3.4

**MODEL: Fable — remind the user to switch before starting this phase.**

- [x] 4.1 Cache one Engine per db path in `db/db_helpers.py`
      → `_get_cached_engine()`: per-resolved-path cache, `threading.Lock`
      around it (Flet handlers run in a thread pool), and a PID guard — a
      forked child clears the cache instead of reusing the parent's pooled
      SQLite fds (cross-process fd sharing corrupts the db). Caller audit
      (210 files): both transliterate scripts and the goldendict exporter
      open sessions only in the parent, children are pure computation;
      `db_rebuild_from_tsv.py` unlinks dpd.db before its first
      `get_db_session` in that process so no stale cached engine is
      possible; `audio/db_create.py` uses its own `get_audio_session`
      (untouched); webapp benefits (was harvesting `.bind` off a throwaway
      session). Semantics probe (scratchpad script): engine reuse, external
      sqlite3 commits visible to fresh sessions on a warm pool, fork guard
      rebuilds in child, WAL listener active — all verified.
- [x] 4.2 REVERSED after user smoke test: `new_db_session()` does NOT close
      the previous session. Two independent reasons, found live:
      (a) close-race — Flet handlers run in a thread pool; the DB tab's
      long filter query runs on the very session another tab's
      `new_db_session()` would close, killing it mid-fetch;
      (b) the user's smoke test crashed with `QueuePool limit of size 5
      overflow 10 reached, connection timed out, timeout 30.00` — the
      shared cached engine's bounded pool (15) exhausts because gui2 keeps
      many never-committed sessions alive, each pinning a connection for
      life. Before 4.1 each session had a private engine, so no shared
      limit existed. Fix: cached engine now uses **NullPool** — no bound to
      exhaust, each session opens its own cheap SQLite connection, released
      on close/GC. Regression probe: 20 transaction-holding sessions + a
      21st query = 0.4 ms (was 30s block → TimeoutError). A comment in
      `new_db_session()` records why close() must not be added back.
- [x] 4.3 Before/after (bench_memory / bench_engine, final NullPool shape):
      | probe | before (per-call engines) | after (cached engine + NullPool) |
      |---|---|---|
      | session+first-query cost | 0.693 ms | 0.491 ms |
      | 50× new_db_session fd growth | +100 (engines never freed) | +45 transient, 0 after GC |
      | 50× new_db_session RSS growth | +3.9 MB | +0.3 MB |
      | pool-exhaustion crash | impossible (private pools) | impossible (NullPool) |
      fd note: 3 fds per live SQLite/WAL connection (db + -wal + -shm);
      `close()` releases all 3 immediately (probe-verified). Abandoned
      sessions sit in reference cycles so they free on the CYCLIC collector,
      not refcount — transient sawtooth, fully reclaimed at gc.collect()
      (probe-verified, −1 fds). Correction to 4.2's original rationale:
      "deterministic on refcount" was wrong. Full suite green (1427 passed,
      3 runs across the phase).
- [x] CHECKPOINT: full suite green ✓; user re-ran the failing repro (DB tab
      search → commentary search in Pass2Add → Trans tab search) — works
      without error. `/cm` drafted; user commits before Phase 5 starts.

## Phase 5 — DB tab fix (Theme D — user priority) — shaped by 3.5

**MODEL: Fable — remind the user to switch before starting this phase.**

- [x] 5.1 Extract pure logic from `filter_component.py` into new
      `gui2/filter_logic.py`: `parse_id_filter`, `build_filter_conditions`
      (query building), `compute_column_widths`, `track_cell_change` (cell
      diff), plus `cell_value_str`, `validate_regex_patterns`,
      `group_changes_by_id` and pagination helpers (`effective_total`,
      `clamp_page_index`, `page_label`)
      → verify: `uv run pytest tests/gui2/test_filter_logic.py` (32 passed,
      incl. in-memory-SQLite execution of the built conditions). Discovery:
      `regexp_match` works on SQLite only because SQLAlchemy's pysqlite
      dialect registers a Python-level REGEXP function per connection (raw
      sqlite3 has none) — so regexp filters run a Python callback per row,
      and an empty pattern matches every row including NULL columns
      (documented in a test; count() over 89k rows ≈ 130 ms, cheap enough
      for pagination totals)
- [x] 5.2 Paging: `PAGE_SIZE = 100` in `filter_component.py` — every apply
      renders at most 100 rows regardless of the user's limit; prev/next
      buttons + "N–M of T" label; `query.count()` (capped by limit) drives
      the label; secondary `order_by(id)` keeps page boundaries stable on
      sort-column ties. `DEFAULT_LIMIT` stays 0 ("all results") because
      paging now bounds per-apply work — 3.5 showed 100 rows ≈ 171 ms —
      and presets store their own limit anyway, so changing the default
      constant would not have protected anything
- [x] 5.3 Read-only `CellText` (ft.Text) cells; tapping a cell swaps in the
      old editable `CellTextField` on demand (id and row-number cells not
      tappable). Spell-check on meaning columns preserved: red text on
      misspelled read-only cells, red border while editing
- [x] 5.4 Batch save rewritten: changes keyed `(headword_id, column)` (not
      row index), grouped via `group_changes_by_id`, applied to records
      fetched by id, ONE `commit()` + ONE `invalidate_relationship_detector()`
      per batch (was per-row `update_word_in_db` which commits+invalidates
      each row, plus a second commit at the end). Whole batch rolls back on
      any failure. Dropped as dead: write-only `_just_saved` flag and
      `_validate_data`/`validation_rules` (only rule was for the id column,
      which was already read-only and is now untappable)
- [x] 5.5 Duplicate `new_db_session()` removed from
      `filter_tab_view._apply_filters_clicked` and
      `tests_tab_controller._handle_test_failures` — the ONE call lives in
      `FilterComponent._apply_filters`. Query+build now run via
      `page.run_thread` kicked off in `did_mount()`, with a progress ring
      and a generation counter that discards stale runs when a newer apply
      supersedes them
- [x] 5.6 Re-run 3.5; before/after (same run, warm cache, throwaway db;
      bench_db_tab.py gained a "paged pipeline" section mirroring the new
      code path, results in `results/5.6_db_tab_after.json`):
      | scenario | before (old pipeline) | after (paged pipeline) |
      |---|---|---|
      | default apply (limit 0) | 31.9 s (query 5.6 s + build 26.4 s, 89k rows) | **357 ms** (count+fetch 346 ms + build 12 ms, 100 rows) |
      | limit 100 | 165 ms | 355 ms (count() adds ~200 ms for the pager label) |
      | deep page (offset 40k) | n/a | 3.0 s (SQLite OFFSET scan; runs off-thread behind the progress ring) |
      Extra find during 5.6: `CustomSpellChecker.check_sentence` generates
      edit-distance *suggestions* (`spell.candidates()`) per unknown word —
      the display cells only need a boolean, and meanings are full of Pāḷi
      terms the dictionary doesn't know, so build cost was 1.2 s/100 rows
      (≈ minutes over 89k rows in the old tab — a hidden chunk of the
      freeze). Added `CustomSpellChecker.has_misspellings()` (unknown()
      only, no suggestions) in `tools/spelling.py`, used for cell color and
      edit-border; the save gate keeps `check_sentence` (it reports the
      misspelled words). Build dropped 1.2 s → 12 ms per page.
- [x] CHECKPOINT: full suite green (1459 passed, 32 new); user smoke-tested
      the DB tab (paging, edit-on-demand, batch save, tab-switch mid-query)
      — "works nicely". `/cm` drafted; user commits before Phase 6 starts.

## Phase 6 — Corpus load discipline (Theme B) — shaped by 3.6

**MODEL: Fable — remind the user to switch before starting this phase.**

- [x] 6.1 Single cached corpus: `make_inflections_lists`/`make_pass2_lists`/
      tests-tab derive from one load instead of three-plus
      → verify: `uv run pytest tests/gui2/` (240 passed, 10 new in
      test_database_manager_corpus.py). New `load_corpus()` (cached,
      lock-guarded, generation counter) + `mark_corpus_stale()` on
      `DatabaseManager`; `initialize_db`/`make_inflections_lists`/
      `make_pass2_lists`/detector lazy path/tests-tab `load_db` + rerun all
      derive from it. Derived sets skip rebuilding when the corpus
      generation is unchanged. Unified defer list KEEPS `freq_data` loaded
      (RelationshipDetector's `has_textual_occurrence` reads it on rows
      that may outlive their session; deferring it risked per-row lazy
      loads/DetachedInstanceError — the old make_* loads deferred it, the
      old initialize_db didn't; verified no db test targets any deferred
      column). Staleness marked at every headword write path:
      add/update/delete_word_in_db, root rename/delete cascade,
      filter_component batch save, sandhi find-replace commits,
      global tab inflections update, and pass1_add "refresh db" button.
      Freshness semantics change (agreed direction): external-process
      writes are now picked up via the refresh button or restart, not by
      the previously-implicit reload-on-every-call.
- [x] 6.2 Move first corpus load off the UI thread (progress indicator on
      first tab click)
      → verify: ruff/pyright clean, 240 gui2 tests pass; manual smoke at
      phase checkpoint. `main.py tab_clicked` now kicks
      `initialize_db()` off via `page.run_thread` with a start-guard flag
      and "Loading database in the background..." / "Database loaded."
      snackbars (failure resets the guard so a retry is possible). The
      async window means the `initialize_db` sets can still be None while
      the user types, so the six direct set-membership validations in
      `dpd_fields.py` (lemma_1 dup ×2, pos, root family, word family,
      compound family) now skip gracefully instead of raising TypeError;
      `load_corpus()`'s lock means any pass1/pass2/tests action started
      during the window simply waits for (or shares) the one load.
      Known transient: `all_decon_no_headwords` (a lookup-table query, not
      corpus) may still be empty if pass2pre is started within seconds of
      the first tab click — self-heals, noted rather than engineered
      around.
- [x] 6.3 Serialize + debounce `invalidate_relationship_detector` (single
      worker; coalesce rapid saves)
      → verify: `uv run pytest tests/gui2/test_database_manager_corpus.py`
      (12 passed, 2 new worker tests); full suite 1471 passed. Rewritten as
      a single coalescing worker: pending/running flags under a lock; a
      1s debounce (`DETECTOR_REBUILD_DEBOUNCE_SECS`) lets a burst of saves
      become ONE rebuild; a save landing mid-rebuild queues exactly one
      more pass. N saves now cost at most one running rebuild + one queued
      (was N concurrent 83k-row loads with a 2-3× memory spike each). The
      worker keeps its private bg session/load — deliberately NOT
      load_corpus(), which would swap `self.db` under UI-thread users.
      Test infra note: in-memory SQLite needs StaticPool +
      check_same_thread=False for the worker thread to see the fixture db.
- [x] 6.4 Re-run 3.6; record before/after (bench_corpus.py gained cached +
      stale-reload sections; results in `results/6.4_corpus_after.json`;
      warm-cache run, system load ~3.9/22 cores — relative comparisons are
      the point, per the Phase 3 variance note):
      | call | before (each = full 89k load) | after (one cached load) |
      |---|---|---|
      | initialize_db (load + detector) | 5.3 s | 6.3 s (same work; load-noise) |
      | make_inflections_lists | 2.6 s | **0.67 s** (derive only) |
      | make_pass2_lists | 3.4 s | **1.3 s** (derive only) |
      | tests-tab db load | full undeferred `.all()` (heavier than 5.3 s, every run AND rerun) | **0.01 ms** (cached) |
      | repeat call, nothing changed | full reload each time | **~0 ms** |
      | stale reload + derive (after a write) | n/a | 2.7 s |
      The three-loads-that-could-be-one (11.3 s total) are now one load +
      two derives (8.2 s once, ~0 thereafter), and the first load runs off
      the UI thread (6.2). Set-derivation itself (~0.7–1.3 s) is the
      irreducible remainder, dominated by `inflections_list_all` string
      splitting — computed once per corpus generation and shared between
      pass1/pass2 via the row-level cached_property now that rows are
      reused.
- [x] CHECKPOINT: full suite green (`uv run pytest tests/` → 1471 passed,
      16 deselected; 12 new tests in
      `tests/gui2/test_database_manager_corpus.py`); ruff/pyright clean on
      all 10 touched files. User smoke-tested pass1/pass2 flows — works.
      User observation for Phase 7: the biggest remaining startup wait is
      the AI manager init and the eager GUI build, not the db — exactly
      items 7.1/7.2. `/cm` drafted; user committed.

## Phase 7 — Lazy startup (Theme C) — items accepted per 3.2 numbers

**MODEL: Opus — remind the user to switch before starting this phase.**

- [x] 7.1 Lazy ToolKit managers via `cached_property` (biggest measured first:
      wordfinder, AI manager, bold-definitions session, additions/corrections)
      → `gui2/toolkit.py`: converted 7 members to `@cached_property` —
      `ai_manager`, `wordfinder_manager`, `bold_definitions_search_manager`,
      `additions_manager`, `corrections_manager`, plus the two popups
      (`ai_search_popup`, `wordfinder_popup`) that force those managers at
      construction (`AiSearchPopup.__init__` calls `_build_model_options()`
      → `ai_manager`; `WordFinderPopup.__init__` grabs `wordfinder_manager`).
      Removed their eager construction from `__init__`; added
      `from __future__ import annotations` + a `TYPE_CHECKING` block so the
      return hints resolve without runtime import cost. Everything else stays
      eager (all <100 ms combined, and `daily_log`/`username_manager` are
      needed for the appbar at startup). NOTE: 7.1 alone yields no startup
      win because the eagerly-built tab views still force these managers in
      their controllers — the actual deferral is delivered by 7.2.
- [x] 7.2 Lazy tab content on first selection in `main.py`
      → all 15 tab views now build on first activation via a
      `_view_builders` thunk registry keyed by tab index + `_view()`
      memoization; tabs start with a `ft.Container()` placeholder, index 0
      (Global) is built eagerly. `_ensure_tab_built()` swaps the real view in
      once (tracked by `_mounted_tabs`, kept separate from the `_views`
      object cache so building Pass1Add's dependency — Pass1Auto's controller
      via `_view(2)` — doesn't wrongly mark tab 2 as mounted). Unified
      `_on_tab_activated` handler wired to BOTH `on_click` and `on_change`
      (idempotent guards make the double-fire harmless) and called explicitly
      from the Alt+Left/Right handlers (a programmatic `selected_index` change
      may not fire `on_change`). Preserved the Phase 6 first-click db-init
      hook as `_maybe_start_db_init()`. `_get_current_lemma` now reads from
      `self._views.get(index)` (only tabs 3/7) instead of dropped attributes.
- [x] 7.3 Drop `--reload` from `start_dpd_server()`; start after first paint
      → `tools/fast_api_utils.py`: removed `--reload`/`--reload-dir` (spawned
      a reloader supervisor + file watcher, pointless for the packaged GUI)
      and added the `-> None` hint. `main.py main()` reordered so
      `start_dpd_server()` runs AFTER `App(page)` has painted (`Popen` is
      non-blocking, so the server no longer sits ahead of the window on the
      startup path).
- [x] 7.4 `DISTINCT` in pre-init queries; fix `get_all_family_sets` full scan
      → the other 4 pre-init queries (`compound_types`, `plus_cases`,
      `verbs`, `roots`) already had `.distinct()`; only `get_all_family_sets`
      did a full column scan of every non-empty headword row (heavy
      duplication) before splitting in Python. Added `.distinct()` so the DB
      returns only unique `family_set` strings — identical component set,
      far fewer rows. Warm pre_init 290 ms vs 347 ms baseline.
- [x] 7.5 Re-run 3.2/3.3; record before/after (throwaway db, warm-cache;
      `bench_startup_after.py` → `results/7.5_startup_after.json`. Old
      `bench_startup.py` replicates the pre-7.1 all-eager body, so the new
      script builds the REAL now-lazy `ToolKit(None)` and forces each
      deferred manager. cold_init reported for transparency but is
      cold-cache disk noise on the 2.2 GB db — the deferral + warm pre_init
      are the stable numbers):
      | metric | before (all eager, 3.2/3.3) | after (Phase 7 lazy) |
      |---|---|---|
      | eager startup manager/query work | ~3081 ms | ~380 ms (warm pre_init 290 ms + cheap managers <100 ms) |
      | wordfinder 74 MB JSON load | in startup (1690 ms) | **deferred** (1553 ms on first wordfinder use) |
      | AI 6-provider SDK init | in startup (972 ms) | **deferred** (904 ms on first AI use) |
      | total deferred out of startup | — | **2461 ms** |
      | startup RSS | ~543 MB (all loaded) | **301 MB** |
      | RSS deferred until first use | — | **242 MB** (172 MB wordfinder + 70 MB AI SDKs) |
      | pre_init (warm) | 347 ms | 290 ms (7.4 DISTINCT) |
- [x] CHECKPOINT: full suite green (`uv run pytest tests/` → 1471 passed,
      16 deselected — same count as Phase 6, no regressions; 242 gui2 tests
      pass); ruff clean on all touched files (`gui2/toolkit.py`,
      `gui2/main.py`, `gui2/database_manager.py`, `tools/fast_api_utils.py`,
      `bench_startup_after.py`); pyright clean on the non-excluded
      `tools/fast_api_utils.py`. User smoke-tested — all tabs function (lazy
      build on click and Alt+arrow), Ctrl+A / Ctrl+F popups open, DB tab
      works. User observation: total time-to-work is unchanged because
      load + deferred = the old preloaded cost when a feature IS used; the
      win is faster first paint + skipped cost when unused. Chose to live
      with lazy for now; possible follow-up recorded below (background
      pre-warm). `/cm` drafted; user commits before Phase 8 starts.

## Phase 8 — JSON write amplification (Theme E) — only where 3.7 shows real cost

**MODEL: Sonnet — remind the user to switch before starting this phase.**

- [x] 8.1 Investigated, decided NOT to remove: `Pass2AutoControl` (batch AI
      processing over a whole book) and `Pass2AddView` (human review, one
      suggestion at a time) each hold their own separate
      `Pass2AutoFileManager` instance, both backed by the same
      `pass2_auto.json`. The file is the only channel between them — no
      in-process sharing of the dict — and this is a deliberately tested
      contract (`test_data_survives_reload_from_disk`). Flet dispatches each
      `on_click` handler on its own thread, so both tabs can be live at once:
      a long "process book" batch running on one thread while a person
      deletes/accepts suggestions on another. Every `load()` in
      `pass2_auto_file_manager.py` exists so each instance picks up what the
      other just wrote/deleted. Removing them (as 8.1 originally proposed)
      would let a stale in-memory save silently resurrect an item the other
      screen just deleted — a data-loss bug, not just a slowdown. 3.7 already
      measured the real cost as tiny (13 ms/edit at 5000 entries/0.7 MB), so
      per spec's own "may be a no-op" framing, left as-is. No code changed.
- [x] 8.2 Found and fixed one genuine redundant read outside 8.1's named
      file: `Pass1AutoController.add_word()`/`remove_word()`
      (`gui2/pass1_auto_controller.py`) — called once per word inside the
      `auto_process_book` batch loop. Each call did
      `self.file_manager.update(book, update_func)` (full read+modify+write,
      already returns the updated dict), then discarded that return value
      and called `self.file_manager.read(book)` again — a second, fully
      redundant full-file read of what it had just written. Unlike
      pass2_auto_file_manager (8.1), only one `Pass1FileManager`/
      `Pass1AutoController` is ever constructed per book — no second
      instance reads this file behind its back — so there's no cross-
      instance freshness reason for the extra read; it was just a dropped
      return value. Fixed both methods to assign `update()`'s return value
      directly instead of re-reading. No batching/deferral implemented —
      not justified: single-owner, already-in-memory data, no queue to
      coalesce.
      → verify: `uv run ruff check/format`, `uv run pyright` clean;
      `uv run pytest tests/gui2/` (242 passed, no regressions — no dedicated
      Pass1AutoController test file exists, but Pass1FileManager tests
      cover the manager itself).
- [x] 8.3 New benchmark `bench_pass1_controller_write.py` (controller-level,
      since 3.7 measured `Pass1FileManager.update()` in isolation, not the
      controller's extra read): on the real 7.63 MB `pass1_auto_dhpa.json`,
      before (update()+redundant read) 194.94 ms → after (fixed add_word())
      158.34 ms — **~19% cut** per processed word in the batch loop, matches
      the "drop one of three file ops" prediction. pass2_auto_file_manager
      left unmeasured again — 8.1 decided not to touch it (see 8.1 above),
      so no after-number to record; 3.7's 13 ms/edit stands unchanged.
- [x] CHECKPOINT: full suite green (`uv run pytest tests/` → 1471 passed,
      16 deselected — same count as Phase 7, no regressions). No manual test
      needed (no UI/behavior change, pure I/O reduction on a background
      batch loop). → run `/cm` to draft the message for this final phase;
      user commits.

## Dead code

Running log — append here whenever a phase turns up unreachable/dead code.
Not a phase, not fixed in this thread; see `spec.md` § Dead code for the
same list with more detail.

- `dpd_fields_functions.find_stem_pattern` — dead masc "rāja masc" / fem
  "mātar fem" branches (Phase 1.1)
- `dpd_fields_functions.make_compound_construction_from_headword` — dead
  `dvanda` branch when grammar contains "comp" (Phase 1.1)
- `gui2/wordfinder_widget.py` `WordFinderWidget` — never instantiated
  anywhere (`WordFinderPopup` is the live wordfinder UI); whole class is
  dead. Found while auditing wordfinder_manager consumers (Phase 7.1).

## Deferred / out of scope (revisit after this thread)

- View `Protocol` for controllers + extraction of pass1/pass2 controller logic
  (findings F6/F8)
- Sandhi `Data` class session injection + tests
- N+1 batching in `get_related_dict_entries`/`get_headwords`;
  `_search_and_fill_sanskrit` LIKE fix (small, can ride along with Phase 6 if
  convenient)
- Wordfinder inverted index (beyond lazy loading)
- **Background pre-warm of the deferred managers (possible Phase 7.6).**
  Phase 7 made `wordfinder_manager` + `ai_manager` lazy, which speeds first
  paint but relocates their ~2.5 s cost to a synchronous stall on first
  Ctrl+F / first AI-popup use — for a workflow that uses both every session
  the time-to-work is unchanged. Alternative: after first paint, warm them
  on a background thread (piggyback on the existing
  `_initialize_db_in_background` / `page.run_thread` path from Phase 6) so
  the load runs concurrently with the user's first seconds of work — fast
  paint AND no first-use stall, without eager-blocking startup. Watch the
  Python 3.13 `cached_property` no-lock race (a warmer thread and a user
  handler could both first-touch the same manager); guard with a lock or
  warm before the trigger is reachable. User is living with plain lazy for a
  few days first; revisit if the first-use stall is annoying.
