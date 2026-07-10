# gui2 Review Findings — 2026-07-10

Consolidated from three independent review passes (speed, resource use, testability)
plus direct reading of `main.py`, `toolkit.py`, `database_manager.py`,
`filter_tab_view.py`, `filter_component.py`.

Row-count baselines: `dpd_headwords` ~83k, `lookup` ~600k.
Key file sizes: `shared_data/frequency/cst_file_freq.json` = 74 MB,
`gui2/data/pass1_auto_dhpa.json` up to 8 MB, `corrections_added.json` 2 MB.

---

## Theme A — DB engine/session hygiene

- **A1. New engine per call.** `db/db_helpers.py:32-60` — every `get_db_session()`
  runs `create_engine()` + `sessionmaker()` + event listener registration. No
  caching, no disposal.
- **A2. `new_db_session()` leaks the old one.** `gui2/database_manager.py:82-83`
  reassigns without `close()`. The orphaned session keeps its engine, pool, open
  SQLite handle (WAL, `check_same_thread=False`) and identity map alive until GC.
- **A3. Called on hot paths** — once per word open (`database_manager.py:547`),
  per related-entry lookup (`:255`), per filter apply (`filter_component.py:189`
  AND `filter_tab_view.py:437` — twice per apply), per CT search
  (`compound_type_tab_view.py:569,603,642,676`), per roots save
  (`roots_tab_view.py:275`), per test run (`tests_tab_controller.py:229`),
  per pass1 refresh (`pass1_add_view.py:245`). A long session accumulates
  hundreds of engines + bloated identity maps.
- **A4. Parallel long-lived sessions, each with its own engine:**
  `tools/bold_definitions_search.py:17`, `gui2/sandhi_find_replace_view.py:341`,
  per-call sessions in `tools/speech_marks.py:70`, `gui2/dpd_fields.py:1022`
  (this one is correctly closed).

**Fix direction:** one cached Engine per db path; `new_db_session()` closes the
previous session; consider `session.expire_all()` instead of full re-creation.

## Theme B — Full-table load discipline (~83k rows)

- **B1. Three independent full-table loads** into `db_manager.db`:
  `initialize_db` (`database_manager.py:104-115`), `make_inflections_lists`
  (`:225-249`), `make_pass2_lists` (`:288-312`). Each `.all()`s the whole table
  again and rebuilds sets by iterating every row. ~200-350 MB resident.
- **B2. First-tab-click freeze.** `main.py:204-209` `tab_clicked` →
  `initialize_db()` synchronously on the UI thread: 8 aggregate queries + 83k-row
  load + `RelationshipDetector` index build → multi-second freeze.
- **B3. Detector rebuild avalanche.** Every `add/update/delete_word_in_db`
  (`database_manager.py:614,631,647`) fires `invalidate_relationship_detector()`
  → a daemon thread that opens a new engine and reloads all 83k rows. No guard
  against overlapping rebuilds; N saves in quick succession = N concurrent
  full-table loads (2-3× memory spike each).
- **B4. Tests tab full reload** on every run AND every single-test rerun
  (`tests_tab_controller.py:270,831-834`).
- **B5. `RelationshipDetector` holds several full-corpus index dicts**
  (`tools/synonym_variant.py:406-421,788-815`) rebuilt from scratch each time.

**Fix direction:** one authoritative cached corpus, loaded off-thread; pass1/
pass2/tests derive their sets from it; detector rebuilds serialized/debounced
(single worker, coalesce rapid saves).

## Theme C — Eager startup

- **C1. All 15 tab views built before first paint** (`main.py:74-98`). Nothing
  renders until the last constructor returns.
- **C2. ToolKit builds ~25 managers eagerly** (`toolkit.py:37-75`), most backing
  tabs never opened in a given session. Then `pre_initialize_gui_data()` runs 5
  synchronous DB queries before the window shows.
- **C3. 74 MB JSON at every launch.** `tools/wordfinder_manager.py:51-53` loads
  all of `cst_file_freq.json` (likely 300-700 MB resident) for a feature only
  reachable via Ctrl+F. Every search then linearly scans the whole dict.
- **C4. Six AI SDK clients constructed at startup** (`tools/ai_manager.py:59-118`),
  only needed in pass1/pass2 auto tabs.
- **C5. `start_dpd_server()` spawns uvicorn with `--reload`**
  (`tools/fast_api_utils.py:7-20`) — dev-only file-watcher overhead, contends for
  CPU/disk/SQLite exactly during GUI init.
- **C6. ~12 managers read their whole backing file in `__init__`** (daily_log,
  history, corrections/additions glob+merge all contributor files, presets,
  pass2 exceptions/new-words, speech marks, spelling, variants, see, sandhi CSVs).
- **C7. `get_all_family_sets` full-column scan** + Python split/dedup
  (`database_manager.py:170-190`); `get_all_root/compound/word_families` fetch
  without `DISTINCT` (`:131-145`).
- **C8. `CustomSpellChecker` first construction** (pyspellchecker en dictionary
  load) pulled into the launch path via DpdFields.

**Fix direction:** lazy `cached_property` managers on ToolKit; lazy tab content
on first selection; drop `--reload`; background the pre-init queries.

## Theme D — DB tab (filter tab) slowdowns & lockups  ← user-reported

- **D1. Unlimited default.** `DEFAULT_LIMIT = 0` = all results; empty regex
  matches everything → default preset can pull all ~83k full ORM rows
  (`filter_component.py:233`).
- **D2. A multiline `ft.TextField` per cell** (`:306`), plus spellcheck per
  meaning cell (`:309`), for every row — enormous control tree serialized to the
  Flet frontend. This is the lockup.
- **D3. Everything synchronous on the UI thread:** query, column-width pass
  (iterates every cell twice, `:263-277`), table build, `page.update()`.
- **D4. Session churn ×2 per apply** (`filter_tab_view.py:437` +
  `filter_component.py:189`), old sessions never closed (Theme A); each apply
  also abandons the previous `FilterComponent` and its full control tree while
  `filtered_results` keeps detached ORM objects alive.
- **D5. Save avalanche:** per edited row, `update_word_in_db` →
  `invalidate_relationship_detector()` → full 83k-row background reload per row
  saved (Theme B3). Saving 10 cells = 10 concurrent full-table loads.
- **D6. Stale-index fragility:** `modified_cells` keyed by `row_index` into
  `filtered_results`; refresh re-queries and can reorder → "weird states".
- **D7. Commit duplication:** `_save_changes` commits per row via
  `update_word_in_db` then commits again at the end (`:392`).

**Fix direction:** default limit + pagination; read-only Text cells with
edit-on-demand (or an editing drawer); query + build off-thread; single commit;
one detector invalidation per save batch.

## Theme E — JSON file manager write amplification

- **E1.** `pass2_auto_file_manager.py:35-38` — full read + full write per item;
  getters re-read the whole file every call.
- **E2.** `pass1_file_manager.py:29-54` — whole per-book dict (up to 8 MB)
  rewritten on every change.
- **E3.** Same whole-file-rewrite pattern in history, additions, corrections,
  example stash, daily log, presets, pass2_pre managers, spelling, variants.
- **E4.** `additions/corrections` managers glob and merge every contributor file
  at startup and keep full `_added` history resident.

**Fix direction:** measure first — these may be fine at real file sizes. Drop
redundant re-reads; batch writes where churn is high.

## Theme F — Testability

- **F1. `Gui2Paths` not injectable** (`gui2/paths.py:7-8`) — no `base_dir` param
  (unlike `ProjectPaths`), so every manager writes to real `gui2/data/`.
  **Single biggest coverage multiplier:** add `base_dir`, mirror `ProjectPaths`.
- **F2. Hardcoded `temp/` writes** in `pass1_auto_controller.py:389,461`,
  `pass2_auto_control.py:340,583` — block testing prompt/response logic.
- **F3. Constructor side effects** (disk/DB I/O in `__init__`) in ~11 classes:
  DatabaseManager, ToolKit, DbTestManager, sandhi `Data`, HistoryManager,
  DailyLog, Additions/CorrectionsManager, Pass2Pre/Pass2AutoFileManager,
  SandhiFileManager. Current workaround pattern: `object.__new__` + set attrs
  (`tests/gui2/test_roots_db.py`).
- **F4. Already pure, just untested (zero-refactor wins):**
  - `dpd_fields_functions.py`: `find_stem_pattern` (large POS/ending matrix —
    ideal table-driven test), `make_lemma_2`, `make_construction`,
    `increment_lemma_1`, `clean_*`, `make_compound_construction_from_headword`,
    `make_dpd_headword_from_dict`.
  - `needs_example.py`: `has_only_late_examples`, `is_missing_sutta_example`.
  - `db_tests/db_tests_manager.py`: `integrity_check`,
    `error_test_each_single_row`, `run_test_on_all_db_entries` (the GUI's own
    DB-integrity runner — high value, untested).
  - `additions/corrections` free helpers: `_contributor_from_origin`,
    `_remove_key_from_file`.
- **F5. Testable after F1 lands (real `__init__` against tmp_path):**
  pass1_file_manager, pass2_pre_file_manager, pass2_auto_file_manager,
  filter_presets_manager, additions/corrections managers, history, daily_log.
- **F6. Needs extraction before testing:**
  - `filter_component.py`: `parse_id_filter`, `build_query`,
    `compute_column_widths`, cell-diff logic.
  - `sandhi_find_replace_view.py` `Data` class (`:336-451`): nearly a clean
    model; inject `db_session`/paths.
  - `pass1_auto_controller.py`: `build_pass1_prompt` (from `compile_prompt`
    `:258-391`), `parse_ai_json_response`, `is_missing` (`:224`).
  - `pass2_pre_controller.py`: `is_missing_example`, `make_all_words_dict`,
    `clean_examples_list`, `clean_quotes`.
- **F7. Existing conventions to match:** in-memory SQLite fixture
  (`test_roots_db.py:13-36`), `object.__new__` for heavy constructors,
  `ProjectPaths(base_dir=tmp_path, create_dirs=False)` for paths.
- **F8. Long-term:** view `Protocol` for controllers; lazy ToolKit doubles as
  the seam for injecting fakes (synergy with Theme C).

## Misc / lower severity

- N+1 query loops: `get_related_dict_entries` / `get_headwords`
  (`database_manager.py:251-344`) — per-id `.first()` in nested loops during
  pass1 auto. Batch with `id.in_(ids)`.
- `_search_and_fill_sanskrit` (`gui2/dpd_fields.py:1030-1034`) — leading-wildcard
  `LIKE '%x%'` per construction split then exact-matched in Python anyway.
  Replace with `lemma_clean IN (...)`.
- `DpdFields` re-sorts/re-copies option lists per instance (`dpd_fields.py:69-87`).
- Standalone utilities `gui2/utilities/*` also `.all()` the full table (low
  priority).
- Detached subprocesses (goldendict, anki, test runners) are fire-and-forget by
  design; no leak, no cleanup on exit either. Acceptable.
