# Plan — Daily ePitaka DPD update (local only)

Spec: `kamma/threads/20261006_epitaka_dpd_export/spec.md` (read it first —
it holds the verified schema, HTML samples and file paths).

## Architecture Decisions
- **One exporter file, plain functions, no GlobalVars class.** Follow the
  TPR exporter's shape (`exporter/tpr/tpr_exporter.py`: `main()` gate →
  build → write) but without its `GlobalVars`; pass the session and data as
  arguments.
- **HTML built in Python f-strings, not Jinja.** The target is a fixed,
  single-line HTML format with single-quoted attributes; templates would add
  whitespace handling for no gain. Reuse existing `DpdHeadword` properties
  (`construction_summary`, `degree_of_completion_html`, `meaning_combo_html`
  if it matches, root family data in `FamilyRoot`) wherever parity allows.
- **Write a fresh file, then install via `sqlite3.Connection.backup`.** In
  place DROP/CREATE (TPR style) would leave a stale `dpd_lookup_norm_v2`
  and 400 MB of free pages; a file copy over a WAL-mode db that the app has
  open can corrupt it. The backup API replaces the whole content through
  SQLite's own locking.
- **Search table prebuilt by ePitaka's own Dart tool**, not reimplemented
  in Python — the fold function must match the app byte for byte, and the
  tool runs the app's exact code.
- **Parity is proven against the existing upstream file**, saved once as a
  baseline before anything is installed.
- Not abstracted: no shared "SQLite dictionary writer" with TPR; no support
  for a release zip.

## Phase 1 — Builder at parity with the upstream file

- [x] 1.1 Save the baseline and write the parity harness
  - Copy the live file with the backup API (read-only source) to
    `exporter/epitaka/output/baseline_dpd-dictionary.db`. Add
    `exporter/epitaka/output/` to `.gitignore` next to `exporter/tpr/output/`.
  - Add paths to `tools/paths.py` (`epitaka_output_dir`,
    `epitaka_dpd_db_path`, `epitaka_baseline_db_path`), next to the tpr block.
  - Write `kamma/threads/20261006_epitaka_dpd_export/artifacts/parity.py`:
    attaches baseline + new output, and for `dpd_headwords` (by id, split
    headwords vs roots by `meaning_html` prefix) and `dpd_lookup` (by
    `lookup_key`) prints counts of identical / different / only-in-one, and
    for differences groups them by first differing HTML class/field and
    prints 3 samples per group with the relevant `dpd.db` source fields.
  → verify: baseline row counts equal 89,617 headwords and 1,281,838
    lookup rows; `git check-ignore exporter/epitaka/output/x` matches.
  - DONE 2026-10-06: baseline saved (89,617 / 1,281,838 / norm 1,281,838,
    integrity ok); ignore rule matches. DRIFT: the baseline was built from
    DPD data of 2026-05-01 (max headword id 89412; commit `babe7108` has
    exactly 88,864 headwords + 753 roots), not July. So `parity.py` got a
    `snapshot <tsv_dir>` mode that renders HTML from that commit's backup
    TSVs and compares exactly, plus an `output` mode for the built file.

- [x] 1.2 Headword `meaning_html`
  - In `exporter/epitaka/epitaka_exporter.py`, write
    `make_headword_html(i: DpdHeadword) -> str` reproducing summary,
    grammar, sanskrit, root, compound and example divs. Derive each rule
    from the baseline samples listed in the spec and from the existing
    helpers in `tools/meaning_construction.py`; read 20+ baseline entries
    covering: no meaning_1, meaning_lit, root words, compounds, no example,
    multi-line example, `(gram)`/abbrev pos, entries with `notes`.
  → verify: run parity; ≥ 99% of shared headword ids byte-identical; read
    every mismatch group and record in this plan, per group, the source-data
    change that explains it. Zero unexplained groups.
  - DONE: snapshot parity 88,864 / 88,864 byte-identical (100%). Rules found:
    every field `.strip()`ped; summary = `<i>pos</i>` + bold meaning_1,
    meaning_2, `(lit. …)`, `[root_key + suffix: root meaning]` (no ` + `
    when suffix empty); Root line = root_key + (headword root_sign, else the
    root's sign) + ` (root_base)` if any + ` - construction` if any;
    Compound `(…)` only when compound_construction set.

- [x] 1.3 Roots and lookup
  - `make_root_html(r: DpdRoot) -> str` incl. the family table; root ids =
    max headword id + 1 onward, ordered to match the baseline (check plain
    vs Pāḷi sort on the baseline ids 89413+).
  - Lookup rows: every `lookup` row; `headwords` = headword ids + mapped
    root ids (from the `roots` column) as a JSON int list, NULL if empty;
    `deconstructor` = JSON list or NULL. Match the baseline's JSON spacing
    (`[34626, 34627]`, `["adhi + asi"]`).
  - Create tables + the three indexes exactly as in the spec.
  → verify: parity over roots (compare by root key since ids shift) and
    lookup (compare `headwords` after mapping baseline ids → lemma_1 /
    root key on both sides): every difference group explained by data
    change; `sqlite3 <out> .schema` matches baseline schema minus
    `sqlean_define` and the norm table.
  - DONE: roots, snapshot mode with the May family tables rebuilt by
    `db/families/family_root.py` functions: 753 / 753 identical. Root ids in
    plain sort order (confirmed). Family tables = `FamilyRoot.html` in table
    insertion order (`ORDER BY rowid`), i.e. Pāḷi order of each family's
    first word; May data predicts the baseline order 753 / 753. Skt bracket
    omitted when sanskrit_root empty.
  - Output vs baseline (live data, 38 s build): schema identical minus
    `sqlean_define` and the norm table. Lookup: 1,035,776 of 1,268,312 shared
    keys identical; 13,526 keys only in baseline, 14,405 only in new (keys
    added/removed since May). Difference groups, all data change:
    split order only 167,159 (both files order splits by part count, ties in
    splitter order — 508,746 / 509,261 baseline lists and 504,519 / 505,057
    new lists sorted by part count; neither re-sorts, so the upstream copied
    `lookup.deconstructor` as stored); splits changed 55,561 / removed 869 /
    added 174 (splitter output changed); headwords added 6,453 (e.g. new
    vagga headwords on sutta codes), changed 1,966 (e.g. `kaṭuviya` split
    into homonyms), removed 146, order only 1,519 (baseline has 1,174 lists
    not in id order, live `lookup` now stores all but 1 in id order — the
    upstream copied the stored order).
    These lookup counts came from a separate scratch classification, not
    from `parity.py` (whose output mode puts all lookup differences in one
    group); the independent review re-derived them and they match.

- [x] 1.4 Tests
  - `tests/exporter/epitaka/test_epitaka_exporter.py`: build HTML for
    in-memory `DpdHeadword`/`DpdRoot` objects whose fields are copied from
    real rows (ids 34626, 7553, 7, 220, 22620, root `√acc 1`), asserting the
    exact baseline HTML strings; lookup-row conversion (NULLs, root id
    mapping).
  → verify: `uv run pytest tests/exporter/epitaka/`; then break one rule
    (e.g. drop the lit. clause), re-run, report how many fail, restore in the
    same command.
  - DONE: 12 passed. Removing the `(lit. …)` clause → 1 failed
    (`test_headword_meaning_2_and_lit`, the only sample with meaning_lit),
    on the HTML assertion; file restored, 12 passed again. Test inputs come
    from the 2026-05-01 data, so expected strings are the real baseline HTML.

- [x] 1.5 Phase check
  → verify: `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright`
    on every touched file; `just typecheck` clean.
  - DONE: ruff, ruff format, pyright 0 errors on the exporter, test,
    `tools/paths.py`, `parity.py`; `just typecheck` 0 errors.

## Phase 2 — Config, search-table prebuild, install, daily wiring

- [x] 2.1 Config gate
  - `tools/configger.py` `DEFAULT_CONFIG`: `[exporter] make_epitaka = no`;
    new section `"epitaka": {"db_path": "", "repo_path": ""}`. Not in any
    profile.
  - The user explicitly asked for the db path in `config.ini` (an
    exception to the global no-.ini rule, scoped to these three keys only).
    Set them with `config_update`, touching nothing else:
    `[exporter] make_epitaka = yes`, `[epitaka] db_path =
    /home/bodhirasa/.local/share/com.dn.epitaka/dpd-dictionary.db`,
    `[epitaka] repo_path = /home/bodhirasa/MyFiles/3_Active/epitaka`.
  - `main()`: return early (before loading dpd.db) if the flag is off, or
    `db_path` empty, or its parent folder missing — red message.
  → verify: test for each early-exit case (monkeypatched `config_read`),
    asserting the db is never opened.
  - DONE: defaults added (`make_epitaka` after `make_tpr`; `[epitaka]`
    after `[tpr]`); profiles and their fixtures untouched. `config.ini`
    diff = exactly the 3 keys. 3 parametrized gate tests pass; removing the
    folder check fails exactly the missing-folder case (restored).

- [x] 2.2 Prebuild the search table
  - `subprocess.run(["dart", "run", "tool/build_dpd_norm.dart", <abs out
    path>], cwd=repo_path, check=False)`; resolve `dart` with
    `shutil.which` (it is on PATH here); if missing print red and skip.
    On non-zero exit print the tool's stderr in red and skip.
  → verify: run it once on the Phase 1 output; record wall time here;
    `SELECT COUNT(*)` of `dpd_lookup_norm_v2` equals `dpd_lookup`, and the
    index `dpd_lookup_norm_v2_idx` exists.
  - DONE: 6.6 s wall (tool reports 5.1 s); norm rows 1,282,717 = lookup
    rows, max src_rowid 1,282,717, index present. The tool leaves the
    output in WAL mode (no `-wal` left). Captures output; red on failure.

- [x] 2.3 Install
  - `install(out: Path, dest: Path)`: `sqlite3.connect(out).backup(
    sqlite3.connect(dest))`, close both. Then `pr` reminder to restart
    ePitaka.
  - Refuse to install if `exporter/epitaka/output/baseline_dpd-dictionary.db`
    does not exist (protects the only upstream copy).
  → verify: test on scratch copies (tmp_path) that the destination ends
    with the new content and no `-wal` contents from the old file survive
    (`PRAGMA integrity_check` = ok). Do NOT touch the live file in tests.
  - DONE: `test_install_replaces_wal_destination` (old content still in
    an open connection's WAL, autocheckpoint off) and
    `test_install_refuses_without_baseline` pass. Live file not touched.

- [x] 2.4 Wire into the daily build
  - `scripts/bash/makedict.py`: add `exporter/epitaka/epitaka_exporter.py`
    after the TPR line. `justfile`: `export-epitaka` recipe after
    `export-tpr`. `exporter/epitaka/README.md` short, matching
    `exporter/tpr/README.md` sections.
  → verify: `just --list | grep epitaka`; read the makedict list.
  - DONE: `export-epitaka` listed; makedict runs it right after TPR.

- [x] 2.5 Phase check
  → verify: lint/format/pyright on touched files, `just typecheck`,
    `uv run pytest tests/exporter/epitaka/ tests/tools/`.
  - DONE: ruff/format/pyright clean on the 4 touched Python files;
    `just typecheck` 0 errors; 702 passed, 7 deselected.

- [x] 2.6 Close and reopen ePitaka around the install (added after review,
  user request)
  - `app_processes()` (psutil, exact name `epitaka`), `close_app(procs,
    timeout)` → terminate + `psutil.wait_procs`, True if all exited;
    `open_app()` → `subprocess.Popen(["gtk-launch", "epitaka"],
    start_new_session=True)`. In `main()`: after build + prebuild, close if
    running; if it won't close, red message and skip install; after
    install, reopen if it had been running. Drop the "restart ePitaka"
    reminder.
  - Parity script opens both dbs read-only (review finding 3).
  → verify: tests with fake processes for close (exits / times out) and
    main ordering (close → install → open; nothing reopened when not
    running; no install when close fails); lint/pyright/typecheck. Live
    check by the user: run the export with ePitaka open.
  - DONE locally: psutil finds the running app (pid, name `epitaka`, exe
    `/opt/epitaka/epitaka`). 5 new tests (real `sleep` child closes; a
    SIGTERM-ignoring child reports not closed; main order for running /
    not running / won't close). Disabling the skip-install guard fails
    exactly `test_main_skips_install_when_app_will_not_close` (restored).
    Parity opens both dbs read-only; a write is refused. ruff/pyright clean,
    `just typecheck` 0 errors, 707 passed. Live check 2026-10-06: user ran
    the export with ePitaka open; it closed, installed and reopened fine.

## Phase 3 — Live run and docs

- [x] 3.1 Live run (user runs it)
  - Ask the user to close ePitaka, run `just export-epitaka`, then open
    the app.
  → verify: the app shows no search-table build progress; a headword added
    after July (pick one: `SELECT lemma_1 FROM dpd_headwords WHERE id >
    89412 ORDER BY id LIMIT 3` in dpd.db) is found; typing it without
    diacritics finds it. Record the export's total time here.
  - DONE 2026-10-06: user ran `just export-epitaka` from the dpd-db root
    and confirmed it works, with no noticeable search-table build at launch.
    Test words: `ṭhānametaṃ` (id 89414, added after the baseline) and
    folded `thanametam`. Total export time not reported by the user; the
    build stage measured 38 s and the prebuild 6.6 s.

- [x] 3.2 Docs
  - Add a dated note to `kamma/tech.md`: where the ePitaka file lives, the
    norm-table behaviour, backup-API install, baseline file.
  - Update `docs/technical/project_folder_structure.md` for
    `exporter/epitaka/`.
  → verify: re-read both notes against the code paths they name.
  - DONE (before 3.1, which waits on the user): tech.md note re-read against
    the exporter and the app's `_normPrepareEntry` (rebuild when
    `normMax > lookupMax || normCount > lookupCount`); folder list entry added.
  - Smoke gate: `uv run pytest tests/` → 1,989 passed, 12 deselected.
