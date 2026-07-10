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

- [ ] 4.1 Cache one Engine per db path in `db/db_helpers.py`; audit non-GUI
      callers for compatibility
- [ ] 4.2 `DatabaseManager.new_db_session()` closes the previous session;
      verify stale-read semantics preserved (external commits still visible)
- [ ] 4.3 Re-run 3.3/3.4 probes; record before/after
- [ ] CHECKPOINT: full suite green + user smoke test. → after the user
      confirms the smoke test passed, run `/cm` to draft the message; user
      commits before Phase 5 starts.

## Phase 5 — DB tab fix (Theme D — user priority) — shaped by 3.5

**MODEL: Fable — remind the user to switch before starting this phase.**

- [ ] 5.1 Extract pure logic from `filter_component.py` (`parse_id_filter`,
      query building, column widths, cell diff) + tests (findings F6)
- [ ] 5.2 Sensible default limit + paging controls (decide default from 3.5)
- [ ] 5.3 Cell rendering: read-only Text cells with edit-on-demand (or
      alternative chosen from 3.5 evidence)
- [ ] 5.4 Single commit per save batch; ONE detector invalidation per batch
      (not per row); stable row keys (headword id, not list index)
- [ ] 5.5 Remove double `new_db_session()` per apply; move query+build
      off the UI thread
- [ ] 5.6 Re-run 3.5; record before/after
- [ ] CHECKPOINT: user verifies lockups and weird states are gone. → after
      confirmation, run `/cm` to draft the message; user commits before
      Phase 6 starts.

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
