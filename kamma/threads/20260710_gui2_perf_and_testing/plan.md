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

- [ ] 6.1 Single cached corpus: `make_inflections_lists`/`make_pass2_lists`/
      tests-tab derive from one load instead of three-plus
- [ ] 6.2 Move first corpus load off the UI thread (progress indicator on
      first tab click)
- [ ] 6.3 Serialize + debounce `invalidate_relationship_detector` (single
      worker; coalesce rapid saves)
- [ ] 6.4 Re-run 3.6; record before/after
- [ ] CHECKPOINT: full suite green + user smoke test of pass1/pass2 flows.
      → after confirmation, run `/cm` to draft the message; user commits
      before Phase 7 starts.

## Phase 7 — Lazy startup (Theme C) — items accepted per 3.2 numbers

**MODEL: Opus — remind the user to switch before starting this phase.**

- [ ] 7.1 Lazy ToolKit managers via `cached_property` (biggest measured first:
      wordfinder, AI manager, bold-definitions session, additions/corrections)
- [ ] 7.2 Lazy tab content on first selection in `main.py`
- [ ] 7.3 Drop `--reload` from `start_dpd_server()`; start after first paint
- [ ] 7.4 `DISTINCT` in pre-init queries; fix `get_all_family_sets` full scan
- [ ] 7.5 Re-run 3.2/3.3; record before/after
- [ ] CHECKPOINT: user smoke test — all tabs still function. → after
      confirmation, run `/cm` to draft the message; user commits before
      Phase 8 starts.

## Phase 8 — JSON write amplification (Theme E) — only where 3.7 shows real cost

**MODEL: Sonnet — remind the user to switch before starting this phase.**

- [ ] 8.1 Drop redundant `load()` calls in `pass2_auto_file_manager` getters
- [ ] 8.2 Batch/deferred writes for high-churn managers if numbers justify
- [ ] 8.3 Re-run 3.7; record before/after
- [ ] CHECKPOINT: full suite green. No manual test needed. → run `/cm` to
      draft the message for this final phase; user commits.

## Dead code

Running log — append here whenever a phase turns up unreachable/dead code.
Not a phase, not fixed in this thread; see `spec.md` § Dead code for the
same list with more detail.

- `dpd_fields_functions.find_stem_pattern` — dead masc "rāja masc" / fem
  "mātar fem" branches (Phase 1.1)
- `dpd_fields_functions.make_compound_construction_from_headword` — dead
  `dvanda` branch when grammar contains "comp" (Phase 1.1)

## Deferred / out of scope (revisit after this thread)

- View `Protocol` for controllers + extraction of pass1/pass2 controller logic
  (findings F6/F8)
- Sandhi `Data` class session injection + tests
- N+1 batching in `get_related_dict_entries`/`get_headwords`;
  `_search_and_fill_sanskrit` LIKE fix (small, can ride along with Phase 6 if
  convenient)
- Wordfinder inverted index (beyond lazy loading)
