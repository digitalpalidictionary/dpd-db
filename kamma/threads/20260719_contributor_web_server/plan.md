# Plan: Contributor Web Server

**Thread:** 20260719_contributor_web_server
**Spec:** `spec.md` in this folder — read it first; it contains the full context,
all decisions, and all known unknowns.
**GitHub issue:** [#215](https://github.com/digitalpalidictionary/dpd-db/issues/215)
— commits reference `#215`.

## Architecture Decisions (made during planning — do not relitigate)

- **Instance-per-contributor, not multi-user refactor.** ~2.5 GB/session
  measured 2026-07-19; 3 users fit a 16 GB VPS. Shared-memory work deferred
  until ~10 users.
- **Env-var overrides, not per-instance clones.** One repo clone on the server;
  each systemd unit sets `DPD_GUI2_USERNAME`, `DPD_GUI2_ROLE`, `DPD_API_PORT`.
  Overrides are read in code with config.ini as fallback — desktop behavior is
  byte-identical when the env vars are unset.
- **JSON files are authoritative; db is scratch.** The existing architecture
  already says this (`Gui2Paths.for_user`); we strengthen it (uuid keys)
  rather than invent a new store.
- **Key-level reconcile script, not git merge**, for `gui2/data/*_{user}.json`:
  server adds keys, upstream removes keys — a snapshot-based set operation is
  conflict-free by construction.
- **Rebuild gated by the absorption invariant** (all contributor JSONs in
  origin/main empty), checked before any destructive step. Skip = normal.
- **Phases 1–2 are fully local** (code + tests, no server, no money) and
  independently valuable. Server work starts in Phase 3 only after they pass.
- **New code placement**: server-side scripts in `scripts/server/` (dir exists
  in the project tree); gui2 changes minimal and role/env-gated. Tests mirror
  source paths under `tests/`.
- **Legacy git-based onboarding flow is kept, marked legacy, not fixed** —
  see spec "Fate of the existing onboarding machinery". Its known defects are
  documented in the spec and must NOT be silently "fixed while we're here".
- **One long-running contributions PR**, not a PR per day.

## Phase 1 — Local groundwork in gui2 (no server required)

- [x] 1.1 Audit `gui2/corrections_manager.py` + ALL per-user state in
      `gui2/data/` (daily log, pass1/pass2 queue files, history). Produce a
      table IN THIS FILE: path → per-user-keyed? → written by contributor
      session? → action needed. Files to inspect:
      `gui2/corrections_manager.py`, `gui2/paths.py`, the daily-log module
      (locate via `rg -l "daily_log" gui2/`), pass1/pass2 controllers.
      → verify: table complete; every writable file has a per-user or
      safely-shared verdict; zero "unknown" rows.

  **AUDIT RESULT (2026-07-19).** `Gui2Paths.for_user` (`gui2/paths.py:50-60`)
  routes ONLY 4 files per-user: `additions`, `additions_added`, `corrections`,
  `corrections_added`. Every other file in `gui2/data/` is shared by all
  instances. Non-atomic `json.dump` from 3 concurrent processes to a shared
  file can interleave and corrupt it, so any file a contributor session writes
  must be per-user or provably safe.

  | File (gui2/data/) | Per-user now? | Written by contributor (Pass1) session? | Verdict / action |
  |---|---|---|---|
  | `additions_{u}.json` | yes | yes (Pass1Add save) | OK — authoritative record; uuid-key fix in 1.2 |
  | `additions_added.json` | yes (`_added_{u}`) | no (primary review side) | OK — not written by contributor |
  | `corrections_{u}.json` | yes | yes (correction save) | uuid-key fix in 1.2; **also fix source_key removal (below)** |
  | `corrections_added.json` | yes (`_added_{u}`) | no (primary review side) | OK |
  | `daily_log.json` | **no** | **yes** (`pass1_add_controller.py:180` increments every Pass1 save) | **ROUTE PER-USER** — add to `for_user` (1.3) |
  | `history.json` | **no** | **yes** (`history.py:add_item` on every navigation) | **ROUTE PER-USER** — add to `for_user` (1.3) |
  | `filter_presets.json` | **no** | maybe (if a contributor saves a filter preset) | ROUTE PER-USER — cheap, add to `for_user` (1.3) |
  | `example_stash.json` | **now per-user** | Pass2Add (`_click_stash` / example stash mgr) | ROUTED per-user in `for_user` (CR3, 2026-07-19) — contributor-reachable, shared → clobber |
  | `commentary_stash.json` | **now per-user** | Pass2Add (commentary stash) | ROUTED per-user (CR3) |
  | `headword_stash.json` | **now per-user** | Pass2Add (`_click_stash`) | ROUTED per-user (CR3) |
  | `pass2_*.json` / `pass2_auto_failures.txt` | n/a | no (build/primary artifacts; read-only inputs to Pass2) | safely shared read-only; no contributor write in Pass1 |
  | `pass1_auto_{book}.json` | **no** | **YES** (Pass1Auto read-modify-writes the per-book queue as items are consumed — `pass1_file_manager.py:29-54`; its `threading.Lock` is intra-process only, useless across the 3 instance processes) | **DECISION: C (operational)** — maintainer decided (2026-07-19): two people won't work the same book on the same server; assign different books. Left shared, NOT per-user (per-user would duplicate work). A code comment marks the concurrent-same-book corruption hazard to fix if it ever happens. Corrected from an earlier wrong "read-only" verdict. |
  | `in_commentary_exceptions.txt`, `find_words_*` | n/a | no | safely shared read-only |
  | `dpd_operations.log` | no | append-only log | non-critical; shared append OK |

  **Zero "unknown" rows.** Two hazards surfaced that add scope to later tasks:

  - **H1 — corrections is NOT source_key-agnostic (unlike additions).**
    `CorrectionsManager.update_corrections` keys by `str(word.id)`
    (`corrections_manager.py:64`) AND `save_processed_correction` removes the
    processed key by `str(word_data["id"])` (`:107-108`). Additions already
    threads a `source_key` through `get_next_addition`/`save_processed_addition`;
    corrections does not. So the uuid-key change (1.2) MUST also add a
    `source_key` return to `get_next_correction` and a `source_key` param to
    `save_processed_correction`, else uuid-keyed corrections can never be
    removed from the contributor file. → folded into **task 1.2**.
  - **H2 — `for_user` must route `daily_log`, `history`, `filter_presets`
    per-user** to avoid concurrent-write corruption of shared files. → folded
    into **task 1.3** (see updated 1.3 text).
- [x] 1.2 UUID keys for additions AND corrections (1.1/H1 confirmed corrections
      has the same hazard, and worse — see below):
      - Additions: `AdditionsManager.add_additions` keys by `str(uuid.uuid4())`
        instead of `str(word.id)`; the id is already inside the entry
        (`word_dict["id"]`). Primary-side flow (`get_next_addition` →
        `source_key` → `save_processed_addition`) is already key-agnostic
        (verified in 1.1) — no change needed there.
      - Corrections: `CorrectionsManager.update_corrections` keys by
        `str(uuid.uuid4())`. BUT the primary side is NOT key-agnostic today, so
        also: `get_next_correction` must return a `source_key` (like additions),
        and `save_processed_correction` must take a `source_key` param and use it
        for `_remove_key_from_file` instead of `str(word_data["id"])`
        (`corrections_manager.py:107-108`). Update the single call site of
        `save_processed_correction` accordingly.
      - Backward compat: existing id-keyed entries in the maintainer's live
        files must still process (removal is by whatever key the queue popped,
        so old id-keyed entries still remove correctly).
      → verify: `uv run pytest tests/gui2/` — add
      `tests/gui2/test_additions_manager.py` AND
      `tests/gui2/test_corrections_manager.py`: add → uuid key present, id
      inside entry; a mixed old/new-key file processes cleanly through the
      primary queue functions and the processed key is removed from the origin.

  **DEDUP-BY-ID ADDED (2026-07-19, maintainer decision B).** Found during 1.5:
  pure-uuid keys made every re-save of the SAME word a NEW entry (alice's testa
  accumulated 7 entries; 6 empty + 1 real "really just that"). The reviewer's
  queue would then process the same not-yet-created word id multiple times and
  hit duplicate-lemma errors. Maintainer: "definitely don't want multiple
  histories of a single edit, just the last one."
  FIX 1 (dedup): `add_additions` / `update_corrections` reuse an existing entry's
  key when a stored entry already has the same db id (`_key_for_id`) → one live
  entry per word, latest wins. `is_not_in_additions` delegates to `_key_for_id`.
  FIX 2 (key scheme — maintainer: uuid overkill, "user + id is enough"): new
  entries key by `"{username}_{id}"` (e.g. `alice_89814`), NOT uuid4. The key
  only needs to be unique across the MERGED pool of all contributor files —
  username makes it unique across contributors, id+dedup makes it stable per
  word. `_username()` derives the name from the file (additions_{u}.json → u;
  primary additions.json → "1"). The cross-wipe id-recycling case uuid guarded
  is already prevented by the rebuild invariant + push-before-rebuild. Backward
  compatible: `_key_for_id` reuses an existing entry's key even if it is an OLD
  uuid, so live uuid-keyed entries still dedup; only new entries use
  {username}_{id}.
  Tests: key == "alice_42"/"bob_42"; resave-same-id updates in place; different
  ids → separate entries. LIVE VERIFIED dedup (2026-07-19, clean restart + empty
  files): alice and bob each refined a word repeatedly, INCLUDING re-editing an
  entry already in the corrections file — each stayed at exactly ONE entry, key
  reused, latest content only ("...too too too" / "...one one one"), per-user
  files separate. KEY-FORMAT LIVE VERIFIED (2026-07-19, clean restart): on disk
  `corrections_bob.json` → `key='bob_89814'` (one entry, `{username}_{id}`).
  NOTE for Phase 2 reconcile (2.1): reusing a stable key across edits means an
  edit made AFTER that key was pushed AND processed upstream could be dropped by
  the snapshot reconcile (`final = local − (last_pushed − main_version)`). Rare
  (rebuild invariant + edit-then-process race); flagged in 2.1 — NOT a reason to
  revert dedup. With {username}_{id}, the reconcile's cross-contributor key
  uniqueness now holds by construction.
- [x] 1.3 Env-var overrides: `DPD_GUI2_USERNAME` in `gui2/toolkit.py:52` and
      `gui2/user.py`; `DPD_API_PORT` in `tools/fast_api_utils.py`
      (`start_dpd_server` currently hardcodes 127.1.1.1:8080 — collides when
      2+ instances run; verified 2026-07-19). Flet web port is already a CLI
      flag (`flet run -p`).
      ALSO (1.1/H2): extend `Gui2Paths.for_user` to route `daily_log`,
      `history`, and `filter_presets` per-user (`daily_log_{u}.json` etc.), same
      guard as the existing 4 files — a contributor session writes daily_log +
      history concurrently and shared non-atomic writes corrupt them. Desktop
      (username "1" / unset) paths stay byte-identical.
      → verify: launch two web instances (ports 8551/8552) with different
      usernames + API ports; both serve simultaneously; each writes its own
      `additions_{name}.json`, `daily_log_{name}.json`, `history_{name}.json`.
      STATUS (2026-07-19): CODE DONE + unit-verified.
      `tools/fast_api_utils.py` `_api_port()` (env `DPD_API_PORT`, default 8080);
      `gui2/user.py` `resolve_username()` (env `DPD_GUI2_USERNAME` → config);
      `gui2/toolkit.py:52` uses it; `gui2/paths.py` `for_user` now routes
      daily_log/history/filter_presets per-user. Tests: `tests/gui2/test_paths.py`
      (+4 cases), `tests/gui2/test_user.py`, `tests/tools/test_fast_api_utils.py`.
      LIVE VERIFIED (2026-07-19): alice (8551, API 8082) + bob (8552) ran
      simultaneously; each wrote its OWN `additions_/corrections_/daily_log_/
      history_{user}.json` with independent daily_log counts (alice pass2_update
      2, bob 1) — no shared-file contention. In server mode start_dpd_server
      no-ops so there is no uvicorn API-port collision at all (DPD_API_PORT diff
      is belt-and-suspenders). Contribution keys confirmed live: this test ran
      while the app still held the interim uuid4 scheme; the FINAL scheme is
      `{username}_{id}` (see 1.2), later re-verified on disk as `bob_89814`.
      Keys stay unique across the merged contributor pool and dedup old
      uuid-keyed entries via `_key_for_id`.
- [x] 1.4 Role mechanism: `DPD_GUI2_ROLE` env (fallback `[gui2] role` in
      config.ini). Three effective modes: primary (username "1", current
      behavior), `contributor` (desktop legacy: keeps Submit Data / Update
      buttons — current `is_not_primary()` behavior at `gui2/main.py:55-70`),
      `contributor-server` (web: NO Submit/Update buttons — sync is automated;
      desktop shell-out actions disabled per 1.5 findings).
      → verify: role=contributor-server web instance shows no Submit/Update
      buttons; role unset on desktop → behavior byte-identical to today
      (buttons appear for non-primary usernames).
      STATUS (2026-07-19): ROLE + BUTTON-HIDING DONE + unit-verified.
      `gui2/user.py` `resolve_role()` (env `DPD_GUI2_ROLE` → config `[gui2] role`)
      + `UsernameManager.is_server_contributor()`; `gui2/main.py` gates the
      Submit/Update buttons on `is_not_primary() and not is_server_contributor()`
      (desktop byte-identical when role unset). Tests: `tests/gui2/test_user.py`
      (`TestResolveRole`, `TestIsServerContributor`).
      LIVE VERIFY DONE (2026-07-19, web browser): role unset → Submit/Update
      buttons present; `DPD_GUI2_ROLE=contributor-server` → buttons gone. Both
      directions confirmed by the maintainer.
      PENDING: disabling desktop shell-out actions (GoldenDict lookup /
      `request_dpd_server` browser open) for contributor-server depends on the
      1.5 click-through findings (section B below).
- [x] 1.5 Web-mode click-through of contributor tabs (Pass1Auto, Pass1Add,
      Pass2Add + word-lookup popups) in a real browser
      (`uv run flet run --web -p 8550 gui2/main.py`); log every breakage
      (clipboard, file dialogs, shell-outs, fonts) IN THIS FILE with a
      works/fix/hide decision per item. Interactive — do it WITH the user.
      Pass1 items must end up works/fixed; Pass2 items may be recorded only.
      → verify: written checklist below this task; every Pass1 item
      works/fixed, every item has a decision.

  **WEB-MODE CLICK-THROUGH CHECKLIST (2026-07-19, role=contributor-server).**
  | # | Item | Observed | Decision |
  |---|---|---|---|
  | B3 | Pass1Add save | Word added; `additions_alice.json` + `daily_log_alice.json` created; db updated locally. BUT post-save `request_dpd_server()` fired `webbrowser.open("http://127.1.1.1:8081/?tab=dpd&q=<id>")` — opens on the SERVER, not the contributor's browser (and webapp not running). Port `:8081` confirms `DPD_API_PORT` override works. | **FIX** — gate `request_dpd_server` (and other shell-outs) off in contributor-server mode |
  | B4 | Pass1Auto save | Worked; consumed item written back to `pass1_auto_an.json`. This file is SHARED + read-modify-written across instances (see audit-table correction above). | **DECISION: C (operational)** — different contributors must work different books; enforced by maintainer book assignment (no code check). Same-book concurrent writes remain a known corruption risk, flagged in `pass1_file_manager.py`. Code-level per-book lock deferred (out of scope). |
  | B5 | Word lookup / GoldenDict (ctrl-c ctrl-c) | Opened GoldenDict on the maintainer's LOCAL desktop fine — but only because the test ran on his own machine. On the VPS this shell-out has no GoldenDict / no display; it will fail or no-op for the contributor. | **FIX** — same shell-out gate as B3 (disable in contributor-server mode) |
  | B6 | Clipboard copy of lemma after save | Not working in browser. Maintainer notes he wouldn't expect a browser to write his clipboard after save anyway. | **ACCEPT** — cosmetic convenience only; no data impact. Leave as-is (Flet web clipboard is best-effort). |
  | B9a | Word-lookup popup (Ctrl+F) | Works in web. | OK |
  | B9b | Missing-example popup (after add to db) | Works in web. | OK |
  | B9c | "Ask AI" popup (Ctrl+Shift+A) | Broken in web two ways: Chrome intercepts Ctrl+Shift+A (its tab-search), AND `launch_ai_search_window` spawns a native OS window via `subprocess.Popen([sys.executable, ai_search_window.py])` — no display on the server. Desktop-only by architecture. | **FIX (gate) + record** — gated off in server mode (see below); web-native in-page Ask AI is future work, out of scope. |

  **SHELL-OUT FIX APPLIED (2026-07-19)** — new `tools/server_mode.py`
  `is_headless_server()` (gated on `DPD_GUI2_ROLE == "contributor-server"`,
  desktop unset → False → unchanged). Gated at the SOURCE so all ~8 call sites
  are covered without touching them:
  - `tools/fast_api_utils.py`: `request_dpd_server` no-ops (was the B3/B5
    `webbrowser.open` to a dead port); `start_dpd_server` no-ops (its only
    consumer is now gated — avoids 3 dead uvicorn webapp instances = real RAM).
  - `tools/goldendict_tools.py`: `open_in_goldendict` returns early (covers
    pass1_auto/pass1_add/pass2_pre/pass2x/in_commentary/find_words call sites).
  - `gui2/ai_search_window.py`: `launch_ai_search_window` returns early
    (B9c — the native-window subprocess can't render in a browser / has no
    display on the server). Added 2026-07-19.
  Tests: `tests/tools/test_server_mode.py`, `tests/tools/test_fast_api_utils.py`,
  `tests/gui2/test_ai_search_window.py`
  (`TestServerModeGating`/`TestLaunchGatedInServerMode` — no-op in server mode,
  still spawns/opens on desktop).
  NOT gated (out of scope / desktop-only tab contributors don't use):
  anki subprocess (`global_tab_view.py`).
  RE-VERIFIED live (2026-07-19): after a REAL app restart (ctrl-5 page reload
  does NOT reload Python — flet keeps the process), Pass1Add save no longer
  attempts a browser pop-up.

  **B7 — "Cannot operate on a closed database" on save (found 2026-07-19).**
  Traceback: `sqlite3.ProgrammingError: Cannot operate on a closed database`
  during ORM `loading.py` `fetchall`/`chunks`. ROOT CAUSE: the engine uses
  `NullPool` + `check_same_thread=False` (`db/db_helpers.py:56-71`, with an
  explicit "Session is not thread-safe" warning). `initialize_db()` runs on a
  background thread and finishes with `load_corpus()`'s big `.all()` on the
  SHARED `self.db_session`; a save's `commit()` releases → NullPool CLOSES that
  connection out from under the still-running load. Maintainer's diagnosis was
  exactly right: "shouldn't be able to save until the db is loaded."
  FIX: `DatabaseManager.db_loaded` flag (False in `__init__`, set True at the end
  of `initialize_db()`) + `is_db_loaded()`; both save entry points gate on it —
  `pass1_add_controller.make_dpd_headword_and_add_to_db` and
  `pass2_add_view._click_add_to_db` show "Database still loading — please wait
  before saving." and return. General correctness fix (not server-gated);
  desktop unaffected (db loads before a user can click). Tests:
  `tests/gui2/test_database_manager_corpus.py` (`is_db_loaded` default False,
  flips True, `initialize_db` sets it).
  LIVE RE-VERIFIED (2026-07-19): save during load shows "Database still loading
  — please wait before saving."; after "Database loaded." normal save works and
  writes `additions_alice.json`.

  **B8 — "db takes FOREVER to load" was NOT a code regression (2026-07-19).**
  Root cause: leftover gui2 instances from repeated `flet run` restarts
  (ctrl-5 reloads the web page but never kills the Python process) + Anki, all
  resident at once → 13 GB swap in use, only 3.4 GB RAM free → the new
  instance's corpus load paged to disk. `pkill -f gui2/main.py` freed swap
  (13→8.5 GB) and RAM (3.4→10 GB free). A single clean instance: App init 3.2s,
  load fast, `FastAPI server started in 0.00s` (confirms the shell-out gate —
  start_dpd_server no-ops in server mode). CLEAN RSS ≈ **2.0 GB** at 1 min
  (pre full tab warm-up), consistent with the spec's ~2.5 GB/session — the
  earlier 5.3 GB was swap-inflated. VPS sizing (16 GB / 3 users) stands.
  OPERATIONAL NOTE for the server: instances are long-lived systemd units, so
  this leftover-process thrash cannot happen there; it was a dev-machine
  artifact of manual restarts.
- [x] 1.6 WAL: idempotent step in the server-setup path
      (`PRAGMA journal_mode=WAL` persists in the db file — do NOT hack it into
      normal desktop session creation). Confirm gui2 save paths hold no
      long-lived write transactions (`rg -n "commit\(\)" gui2/` and read the
      pass1/pass2 save flows).
      → verify: `sqlite3 <server-copy>.db "PRAGMA journal_mode"` → `wal`;
      two instances write additions concurrently with no "database is locked".
      AUDIT (2026-07-19): gui2 save paths are SHORT write transactions —
      `database_manager.py` `add_word_to_db` (add→commit), `update_word_in_db`
      (query→setattr→commit), `delete_word_in_db`, and the root ops all
      add/mutate then commit immediately with no user interaction held open
      inside the transaction. Safe for WAL (brief writer window; a busy_timeout
      lets 3 contributors serialize without "database is locked"). REMAINING:
      the WAL pragma is a server-setup step (Phase 2/3 config/setup path, NOT
      desktop session creation); concurrent-writer live verify needs two running
      instances — bundled into 1.5 / server phase.
      LIVE VERIFIED (2026-07-19): WAL is already applied by the engine's connect
      listener (`db/db_helpers.py:73-75` `PRAGMA journal_mode=WAL`), so the
      server db inherits it automatically — no separate setup step required.
      alice + bob saved ~simultaneously; NO "database is locked" in either
      terminal; both writes landed as valid JSON. Concurrent-writer requirement
      met for the 3-user target. (Server-setup path may still assert WAL
      explicitly for belt-and-suspenders in Phase 2/3.)
- [x] 1.7 Phase gate: `uv run ruff check --fix`, `uv run ruff format`,
      `uv run pyright` on every touched file; `uv run pytest tests/`.
      → verify: all clean, full suite passes.
      DONE (2026-07-19): ruff check + format clean on all touched files; pyright
      clean on all non-gui2 touched files (gui2/ is pyright-excluded per
      `.pre-commit-config.yaml`, but ruff-checked and clean). Full suite:
      **1616 passed, 17 deselected**. Files touched this phase — gui2:
      additions_manager, corrections_manager, pass2_add_view, user, toolkit,
      paths, main, database_manager, pass1_add_controller, pass1_file_manager,
      ai_search_window; tools: server_mode (new), fast_api_utils, goldendict_tools;
      tests: test_additions_manager, test_corrections_manager, test_paths,
      test_user, test_database_manager_corpus, test_ai_search_window,
      test_fast_api_utils, test_server_mode.

### Phase 1 review (2026-07-19) — parallel passes: from-scratch spec/plan audit + CodeRabbit

- **F1 (MEDIUM, fixed):** `is_headless_server()` read the env var ONLY, but
  `resolve_role()` read env OR config.ini — so a role set via config (spec point
  13's promised fallback) would hide the buttons yet leave shell-outs LIVE
  (browser pop-up / GoldenDict / dead uvicorn on the server). FIX: consolidated
  role resolution into `tools/server_mode.resolve_role()` (env → config), single
  source; `is_headless_server()` now calls it; `gui2/user.py` re-exports it.
  Tests: `test_server_mode.py` config-fallback cases.
- **F2 (LOW, partially fixed):** the `db_loaded` save gate covered only the two
  Pass1/Pass2 SAVE paths; other write paths could still hit the closed-db crash
  during the ~seconds-long load. FIX: also gated the contributor-reachable Pass2
  DELETE path (`pass2_add_view._click_delete_ok`). NOT gated (deliberately —
  out of contributor-server scope, low risk in the load window): roots tab,
  compound-type tab, sandhi find/replace, filter_component. Plan wording
  corrected from "general correctness fix" to "contributor save + delete paths".
- **F3 (LOW, no change — documented design):** dedup-by-id reuses a key by db id,
  which re-introduces the id-recycling overwrite hazard IF the rebuild invariant
  is ever violated. Correct as designed (invariant + push-before-rebuild);
  already noted under 1.2. Accepted, not reverted (maintainer decision).
- Audit CLEAN on: corrections source_key threading + the separate untouched
  `proofreader_manager.get_next_correction`; backward compat with old uuid keys;
  ORM no-mutation rule; desktop byte-identical when env unset; per-user routing
  wiring; shell-out completeness for contributor scope.
- **CodeRabbit (13 findings, validated against code before applying):**
  - CR-delete-gate (major) — already fixed (= audit F2). No change.
  - CR-stash-per-user (major, **applied**) — Pass2 stash files (headword/example/
    commentary) are contributor-reachable + shared → routed per-user in
    `for_user`, +test. (Was deferred in the 1.1 audit; promoted to fix.)
  - CR-spec-helper-ports (minor, **applied**) — spec item 2 updated: no FastAPI
    helper in server mode.
  - CR-spec-key-contract + CR-plan-uuid-note (major, **applied**) — spec items
    9/10 + plan notes updated to `{username}_{id}` + keep-if-changed reconcile.
  - CR-plan-B4 (major, **applied**) — B4 row now records decision C.
  - CR-plan-2.4-rollback (major, **applied**) — pinned-commit + full rollback
    staging folded into task 2.4.
  - CR-corrections-owner-check + CR-additions-owner-check (major, **skipped,
    invalid**) — `add_additions`/`update_corrections` are gated behind
    `is_not_primary()` at every call site and a contributor loads ONLY their own
    file, so the primary never calls them and cross-owner key reuse cannot occur.
  - CR-corrections-arg-validation (major, **skipped**) — origin_path & source_key
    are always set/cleared together at the sole call site (from
    get_next_correction); parity with the additions twin CR didn't flag. Adding a
    raise would be behavior-changing dead defense.
  - CR-pass1-cross-process-lock (major, **skipped**) — maintainer decision C
    (operational book assignment); code-level lock deferred, hazard commented.
  - CR-plan-pyright-gui2 (major, **skipped, invalid**) — gui2 AND tests ARE
    pyright-excluded per `[tool.pyright] exclude` in pyproject.toml; the note is
    factually correct.
  - CR-test-return-annotations (minor, **skipped**) — matches the file's existing
    convention (no `-> None` on its test fns); ruff + pyright clean.

## Phase 2 — Sync & maintenance-window machinery (local, testable without server)

All scripts in `scripts/server/`: pure-function cores + thin CLI mains,
unit-tested against tmp dirs / scratch git repos in `tests/scripts/server/`.

- [x] 2.1 `scripts/server/contrib_reconcile.py`: snapshot-based key-level
      merge. Reads `last_pushed/<file>.json` snapshots, computes
      `final = local − (last_pushed − main_version)`, writes result + refreshes
      the snapshot. Pure core:
      `reconcile(local: dict, pushed: dict, upstream: dict) -> dict`.
      → verify: `uv run pytest tests/scripts/server/test_contrib_reconcile.py`
      — cases: upstream processed all / some / none; local keys added during
      the day; both at once; empty files.
      DESIGN NOTE (from 1.2 dedup, added 2026-07-19): keys are now STABLE across
      re-edits of the same word (dedup-by-id reuses the key). The plain snapshot
      formula `final = local − (last_pushed − main_version)` would DROP a word
      that was pushed, processed upstream (key removed from main), then edited
      again locally under the same key. Add a case: key in last_pushed, absent
      in main, PRESENT+CHANGED in local → decide keep-local-edit vs drop. Likely
      rule: drop only if local == last_pushed (unchanged since push); keep if
      the local content differs (a fresh edit). Cover this in the tests here.
      DONE (2026-07-19): `scripts/server/contrib_reconcile.py` — pure
      `reconcile(local, pushed, upstream)` drops a key iff pushed AND removed
      upstream AND `local[key] == pushed[key]` (keep-if-changed rule applied);
      helpers `load_json_dict`/`write_json_dict` (empty → `{}`, matching the
      gui2 managers), `upstream_from_git` (`git show ref:path` → {} if
      absent/invalid), `contributor_files` (globs `additions_*`/`corrections_*`,
      excludes `_added`), `reconcile_all` (writes result + refreshes snapshot),
      thin argparse `main`. Tests `tests/scripts/server/test_contrib_reconcile.py`
      (15): all plan cases (processed all/some/none, local-added, both, empty),
      keep-if-changed + drop-only-when-unchanged, json helpers, glob exclusion,
      and two scratch-git end-to-end (`reconcile_all` incl. upstream-absent).
      ruff+format+pyright clean.
- [x] 2.2 `scripts/server/contrib_push.py`: commit `gui2/data/*_{user}.json`
      on the `contributions` branch, push, write snapshots. Stage by explicit
      file list (NEVER `git add -A` — project rule). Idempotent when nothing
      changed.
      → verify: unit test against a scratch git repo (tmp dir + local bare
      remote): push twice → second is a no-op; snapshots updated.
      DONE (2026-07-19): `push_contributions()` — `_ensure_branch` (switch/create
      `contributions`), explicit `git add` per `contributor_files()` (reused from
      2.1; `_added` excluded), `_nothing_staged` → no-op `PushResult(pushed=False)`,
      else commit (`contrib: submit data <date>`) + `git push origin contributions`
      + `write_snapshots` (snapshot = current file content). Tests
      `tests/scripts/server/test_contrib_push.py` (4): scratch repo + bare remote —
      push lands on `contributions`, snapshot mirrors file, second call no-op;
      `_added` excluded; no files → nothing to push. ruff+format+pyright clean.
- [x] 2.3 `scripts/server/absorption_check.py`: `git fetch origin main`;
      rebuild-allowed iff every `gui2/data/additions_*.json` /
      `corrections_*.json` blob in origin/main is empty (`{}`) or absent.
      → verify: unit test with scratch repo: non-empty file → skip;
      all empty/absent → allowed.
      DONE (2026-07-19): `absorption_allowed(project_root, ref)` → (allowed,
      blocking_files). `contributor_blobs` = `git ls-tree` + `git show` for each
      `additions_*`/`corrections_*` blob at ref (`_added` EXCLUDED — those are
      lists, never `{}`, so including them would permanently block rebuild);
      `is_empty_blob` treats `{}`/`[]`/blank as empty; pure `all_absorbed` +
      `blocking_files`; CLI exits 1 when skipped. `_added` files intentionally
      ignored by the invariant. Tests
      `tests/scripts/server/test_absorption_check.py` (9): work-file filter,
      empty-blob variants, pure core, and scratch-repo non-empty→skip /
      all-empty→allowed (with a non-empty `_added` proving it's ignored) /
      no-files→allowed. ruff+format+pyright clean.
- [x] 2.4 `scripts/server/maintenance_window.py` orchestrator:
      stop instances (systemctl) → contrib_push → absorption_check →
      [if allowed: `cp dpd.db dpd.db.prev` → `git pull --ff-only` + submodule
      update → `scripts/build/db_rebuild_from_tsv.py` →
      `scripts/bash/generate_components.py` → health check (db opens,
      headword/lookup row counts within sane bounds) → contrib_reconcile →
      re-apply WAL pragma] → [on ANY failure: restore dpd.db.prev, log ERROR]
      → start instances. Every branch logs to `logs/maintenance_YYYYMMDD.log`.
      Instance stop/start behind `--no-systemd` so the logic runs locally.
      → verify: local dry-run against a scratch setup exercises all three
      paths — happy, skip, forced-failure rollback — three logged runs shown.
      ROBUSTNESS (CodeRabbit review, 2026-07-19): (a) resolve ONE origin/main
      commit up front (`git rev-parse`) and use that SAME pinned commit for both
      absorption_check and the pull/rebuild — don't `git pull` a moving target
      between the check and the rebuild. (b) `cp dpd.db dpd.db.prev` alone is not
      a complete rollback: stage/record rollback state for EVERY mutated
      component — working tree + submodule commits, generated artifacts, the db,
      the snapshots, and reconcile outputs — and on ANY failure restore all of
      them before restarting instances (not just the db). Keep logging +
      health-check flow.
      DONE (2026-07-19): `run_maintenance(config, steps)` → `Outcome`
      (SKIPPED/REBUILT/FAILED). Order: stop instances → contrib_push → `_pin_commit`
      (fetch once + `git rev-parse origin/main`) → `absorption_allowed(ref=pinned,
      fetch=False)` → SKIP or [capture rollback → pull(pinned)+submodules → rebuild
      → generate → health_check → reconcile_all(pinned) → WAL] → start instances
      (finally). ROBUSTNESS (a): the SAME pinned commit drives both the absorption
      check and reconcile/pull. (b) `_capture_rollback` snapshots db (→dpd.db.prev),
      pre-pull `git HEAD`, AND all contributor files + `last_pushed/`; `_restore_
      rollback` restores db + `git reset --hard <pre>` + submodule update + the
      json files/snapshots on ANY failure. Heavy steps (pull/rebuild/generate/
      health_check) injectable via `WindowSteps` (defaults call the real git /
      `db_rebuild_from_tsv.py` / `generate_components.py` / db row-count check,
      floors `MIN_HEADWORDS`/`MIN_LOOKUP`). Instance ctl behind `--no-systemd`
      (log-only). Each run logs to `logs/maintenance_YYYYMMDD.log`. Tests
      `tests/scripts/server/test_maintenance_window.py` (4): all three paths on a
      scratch repo+bare remote+fake sqlite — happy→REBUILT, skip→SKIPPED,
      forced-failure→FAILED with db (marker) AND contributor file restored;
      `--no-systemd` log assertions. ruff+format+pyright clean.
- [x] 2.5 Server config template `scripts/server/config_server.template`:
      regenerate/exporter flags OFF for audio, anki, deconstructor
      regeneration (premade path per `[generate] deconstructor` mechanism).
      Document per COMMANDS entry of `scripts/bash/generate_components.py`
      (lines 14–69): runs / no-ops / must-skip on server. Decide the
      `uv run pytest tests/` entry (recommendation: replace with the 2.4
      health check in the server run — CONFIRM WITH USER at review).
      → verify: local run of `generate_components.py` under the template
      config on a scratch db copy (`cp dpd.db /tmp/...` per project perf rule)
      completes; record wall-clock as the local baseline number IN THIS FILE.
      DONE (2026-07-19): `scripts/server/config_server.template` written
      (secrets → `<FILL IN>` placeholders; audio + anki + all exporter make_*
      OFF; db_rebuild + generate.deconstructor ON; search_index OFF; validated
      it parses via configparser). Per-command doc `scripts/server/config_server.md`
      — full COMMANDS table (runs / no-op-via-config / must-skip) from a source
      audit: only #18/#31 (Go) are hard prereqs; #15/16 anki, #34/35/36 audio,
      #17/33 exporter all no-op via the template flags.
      BASELINE (2026-07-19, isolated git worktree + copied dpd.db + template
      config, `UV_NO_SYNC=1`, this dev machine): full generate_components rebuild
      (steps 2–37, pytest excluded) = **665s (~11 min)**, rc=0, all 36 steps
      clean. Dominant step by far: `go run go_modules/deconstructor/main.go` =
      **301s (45%)**; then transliterate_lookup_table 62s, transliterate_
      inflections 56s, suttas_update 38s, api_ca_eva 32s, inflections_to_
      headwords 26s, deconstructor_add 20s, grammar_to_lookup 20s. Disabled
      subsystems confirmed no-op: anki 0.4s×2, all 3 audio 0.4s each, variants
      0.3s, search_index 0.4s — template flags work. Server estimate = local ×
      2–3 (spec) ⇒ ~20–33 min rebuild; well under the 3h window fallback
      threshold (plan 3.3 decision), so an on-server rebuild stays viable. The
      REAL server number is still measured in 3.3.
      SETUP NOTES for reproducing the isolated run: a git worktree has only
      TRACKED files, so the pipeline needs these gitignored assets copied in
      before it runs — all 159 `__init__.py` (repo-wide .gitignore hides them;
      `tools.cst_source` etc. fail to import without them), `audio/db/dpd_audio.db`
      (pytest `tests/audio/test_audio_query.py` `sys.exit(1)`s at import if
      absent), and `shared_data/` (e.g. `frequency/cst_wordlist.json`).
      PYTEST-ON-SERVER FINDING (the #1 entry decision, now evidence-backed):
      the full `uv run pytest tests/` gate would ABORT the nightly rebuild on a
      headless server, because `tests/audio/test_audio_query.py` (and the two
      `tests/exporter/webapp/test_webapp_*` files) `sys.exit(1)` at import when a
      generated asset is missing — and the 1.2 GB audio db is absent on the
      audio-disabled server. Options documented in config_server.md: A) server
      pytest `--ignore=tests/audio --ignore=tests/exporter/webapp` (recommended);
      B) drop pytest, rely on the 2.4 health check; C) ship the assets (wasteful).
      DECISION PENDING maintainer confirmation at review; the fix touches the
      shared `generate_components.py`, so not coded unsolicited. (Also NOTICED —
      NOT TOUCHING: 4 golden-master render tests in
      `tests/exporter/goldendict/test_export_dpd.py` fail on any db/env delta;
      matches the project note to delete brittle snapshot tests rather than
      re-freeze — out of scope here.)
      LEAN REBUILD ADDED (2026-07-19, maintainer-directed scope addition): the
      server does NOT run the full `generate_components.py`. New
      `scripts/server/generate_components_server.py` runs only the steps that
      populate tables/columns gui2 reads (verified against gui2 source): logo,
      version, create/generate inflection tables, root_has_verb, sanskrit,
      family_root/word/compound/set/idiom, deconstructor go+add, api_ca_eva,
      inflections_to_headwords, lookup/see, lookup/spelling_mistakes. DROPPED as
      maintainer-confirmed unused by gui2 data entry (grep-verified no reads of
      lookup.grammar/.epd/.help, sutta_info, freq_html/ebt_count):
      transliterate ×2, grammar_to_lookup, epd_to_lookup, suttas_update,
      suttas_to_lookup, help_abbrev, ebt_counter, frequency go; plus
      exporter/release/config-mutation steps (anki, audio, variants,
      search_index, families_to_json, dealbreakers, config_uposatha_day). NO
      pytest on the server (lean db omits data the suite asserts on + the
      full-suite `sys.exit` audio break); the 2.4 health check is the gate.
      `maintenance_window._default_generate` now calls the lean script. Tests
      `tests/scripts/server/test_generate_components_server.py` (5): dropped
      steps absent, essential present, no pytest, go-before-loader +
      tables-before-headwords ordering. `spelling_mistakes` KEPT (pass2pre
      filtering — gui2 reads it indirectly, not via a lookup.spelling attr).
      VALIDATION NOTE: lean list is a strict in-order subset of the proven full
      run, but a real server run in 3.3 must confirm no kept step depended on a
      dropped one (the spelling case showed hidden pass2pre deps).
      OPERATOR DOCS (2026-07-19): `scripts/server/README.md` added — ties all the
      Phase 2 scripts together: the nightly-window flow diagram, how to run the
      orchestrator (prod + local `--no-systemd --no-push` dry-run), a per-script
      table (push/absorption/reconcile/lean-rebuild/config template) with
      standalone invocations, the `last_pushed/` snapshot explanation, and a note
      that the pre-existing `update-dpd.sh` belongs to the separate dpdict.net
      webapp server, NOT this system. (Phase 3.1 `SERVER_SETUP.md` provisioning
      runbook and Phase 4.3 contributor-facing docs are still separate.)
### Phase 2 review (2026-07-19) — parallel sonnet passes: correctness + spec-conformance (CodeRabbit stalled on free tier, re-run pending)

- **R1 (SEVERE — branch left on `contributions`, root cause NOT yet fixed):**
  `contrib_push._ensure_branch` switches the working tree to `contributions`
  and never switches back; the maintenance window then runs `git merge --ff-only
  origin/main` on `contributions`, which has diverged → ff-only fails → every
  real push run ends FAILED and never rebuilds. Tests missed it (all `push=False`).
  DEFENSIVE FIX APPLIED: outer `except` in `run_maintenance` now catches the
  pre-rebuild failure and logs "maintenance aborted before rebuild" + FAILED
  (was mislabelled "skipped"). ROOT-CAUSE FIX DEFERRED to a maintainer decision:
  the durable fix is a dedicated git WORKTREE for the `contributions` branch so
  the main tree never switches (a naive switch-back breaks on night 2 —
  "local changes would be overwritten" because live JSONs differ from the
  committed contributions version). Redesign of the push mechanism → needs
  sign-off before Phase 3. Tracked as the top open item.
- **R2 (MEDIUM, fixed):** `_restore_rollback` iterated the CURRENT data dir, so a
  contributor file deleted by a failed rebuild was never restored. Now iterates
  `rollback.data_backup` (ground truth). +regression test
  `test_deleted_contributor_file_is_restored`.
- **R3 (MEDIUM, fixed):** failures in push/pin/absorption escaped past `finally`
  and logged a misleading "skipped". Added outer `except` → logs + FAILED.
  +test `TestPrePushFailure`.
- **R4 (LOW, fixed):** `_pin_commit` swallowed `git fetch` failures silently →
  could pin a stale commit. Now logs a warning on fetch failure.
- **R5 (LOW, fixed):** `generate_components_server.py` called `check_db_exists()`
  at import (a test imports it) → `sys.exit(1)` off a built db. Moved into
  `__main__`.
- **R6 (conformance, fixed):** config template set `[generate] suttas/grammar/
  epd = yes`, contradicting the "dropped/unused" docs (inert today — lean script
  hardcodes its list — but drift). Set to `no` with an explanatory comment.
- **R7 (conformance, fixed):** rollback docstring overclaimed "every mutated
  component"; the gitignored build intermediates (`shared_data/changed_*`,
  `exporter/tpr/output/i2h.tsv`) are NOT captured. Docstring now states exactly
  what is/isn't captured and why leaving them stale is safe (full `db_rebuild`
  regen, gui2 never reads them).
- Audit CLEAN on: reconcile keep-if-changed logic, absorption semantics
  (`*_added` excluded), pinned-commit reuse, lean COMMANDS list vs plan, explicit
  -file staging (no `git add -A`), idempotency, type hints/pathlib.

- **CodeRabbit (run directly 2026-07-19, 11 findings; validated each vs code):**
  - CR-absorption-fail-open (**CRITICAL, fixed**) — `contributor_blobs`/
    `absorption_allowed` returned `{}` on any git error → `all_absorbed({})=True`
    → would authorize a rebuild/wipe on a git failure. Now RAISES on ls-tree/
    show/fetch errors (fails closed). +test `test_git_error_fails_closed`.
  - CR-rollback-fail-silent (**CRITICAL, fixed**) — `_restore_rollback` ignored
    `git reset`/submodule return codes and logged "restored" unconditionally.
    Now checks both and logs ERROR on failure.
  - CR-reconcile-fail-open (**major, fixed**) — `load_json_dict` returned `{}` on
    invalid JSON (could wipe a corrupt file); `upstream_from_git` returned `{}`
    on any git error (could drop all local keys). Both now RAISE (missing file
    still → `{}`; absent-at-ref still → `{}`). Test updated to assert raise.
  - CR-atomic-write (**major, fixed**) — `write_json_dict` now writes a temp file
    + `os.replace` (no half-written contributor files on crash).
  - CR-timeouts (**major, fixed**) — added `timeout=` to every subprocess in
    maintenance_window (`_run`/`_git_head`/`_pin_commit`/systemctl/rollback);
    STEP_TIMEOUT=3600, GIT_TIMEOUT=300. A hung git can no longer strand the
    window with instances stopped.
  - CR-systemctl-check (**major, fixed**) — `_systemctl` now inspects the return
    code and logs ERROR on failure instead of always logging success.
  - CR-prepopulated-index (**major, fixed**) — `contrib_push` now `git reset`s
    the index before staging, so a stray pre-staged file can't enter the commit.
  - CR-push-unpushed-commit / CR-push-reconcile-order / CR-ensure-branch-track
    (**3× major, DEFERRED**) — all part of the R1 push-branch redesign
    (worktree for `contributions`); folded into that pending decision, not
    half-fixed.
  - CR-absorption-ref-optional (**major, skipped**) — `--ref` defaults to
    `origin/main` already and the window passes an explicit pinned SHA; the
    ergonomic tweak adds no safety. Not worth the churn.

- [x] 2.6 Phase gate: lint/type/test all touched files + full pytest.
      → verify: clean.
      DONE (2026-07-19): ruff check + `ruff format --check` clean on all 8 Phase-2
      python files (4 scripts/server + 4 tests/scripts/server); pyright 0 errors/
      0 warnings on all 8. Full suite `uv run pytest tests/` = **1652 passed, 17
      deselected in 40.9s** on the live repo (the 4 goldendict golden-master fails
      seen in the isolated worktree were a copied-db/env artifact — they pass
      against the live db, so no regression).

## Phase 3 — Server provisioning & deployment

⚠️ STOP — needs user decisions at phase start: provider (Contabo Mumbai /
Hostinger India-or-Singapore / Hetzner Singapore — table in spec) and
domain/subdomain. The user signs up and pays; agent proceeds once SSH access
exists.

- [ ] 3.1 Provision: Ubuntu 24.04 LTS, 16 GB. Minimal hardening: ssh keys
      only, ufw (22/80/443), unattended-upgrades. Install git, Go, nginx,
      certbot, uv. Write every command into `scripts/server/SERVER_SETUP.md`
      as a copy-paste runbook (assume a future from-scratch rebuild).
      → verify: `ssh server 'uv --version && go version && nginx -v'`.
- [ ] 3.2 Repo access: deploy key (read-write) on the server; branch
      protection on main (require PR) so the key cannot land on main; clone +
      init only `resources/sc-data` and `resources/dpd_submodules` (the
      `REQUIRED_SUBMODULES` list in
      `scripts/onboarding/contributor_setup.py`); generate server config.ini
      from the 2.5 template; user enters his DeepSeek/OpenRouter key(s)
      manually (never committed).
      → verify: from server, `git fetch` works; push to a test branch works;
      push to main rejected by protection.
- [ ] 3.3 First db + THE MEASUREMENT: rsync the user's local dpd.db up (fast
      start), AND run one full server rebuild (`db_rebuild_from_tsv.py` +
      `generate_components.py`) to measure real wall-clock — this number fixes
      the window schedule. Decision rule (from spec): if > ~3 h, windows use a
      maintainer-pushed db instead (add `just contrib-push-db` rsync recipe)
      and server rebuild becomes a later upgrade. RECORD the number and the
      decision IN THIS FILE.
      → verify: measured time recorded; server dpd.db passes the 2.4 health
      check.
- [ ] 3.4 systemd template unit `dpd-gui@.service` (reads
      `/etc/dpd/<user>.env`: username/role/ports) + nginx: one basic-auth
      location per contributor → their Flet port; websocket headers
      (`proxy_http_version 1.1`, Upgrade/Connection); HTTPS via certbot on the
      chosen domain.
      → verify: from an outside network, two test URLs serve the GUI over
      HTTPS after a password prompt; wrong password rejected; both sessions
      work simultaneously; RSS per instance recorded IN THIS FILE.
- [ ] 3.5 `scripts/server/add_contributor.sh`: create env file + htpasswd
      entry + enable unit + reload nginx — the "<10 minutes to onboard #3"
      script. Also `remove_contributor.sh` or a documented removal procedure.
      → verify: run end-to-end for a test user: new URL live; then remove it.
- [ ] 3.6 Cron the maintenance window at 01:00 IST + a failure surface the
      user will actually see: window script appends to a status file served at
      an authed nginx path (`/status`) — no mail stack.
      → verify: force one scheduled run of each path ON THE SERVER: happy,
      skip (seed a non-empty additions file reachable by absorption_check —
      or simulate), rollback (deliberately break the rebuild); `/status`
      reflects each.

## Phase 4 — End-to-end cycle proof & real onboarding

- [ ] 4.1 Full-cycle rehearsal, maintainer playing contributor: add 2–3 real
      words via the web GUI → nightly push lands in the contributions PR →
      maintainer merges + processes the queue in desktop gui2 → data-update
      commit to main → next window rebuilds → words present in server db,
      contributor JSONs emptied by reconcile, nothing lost.
      → verify: every arrow evidenced (PR diff, `additions_added.json` entry,
      server db query for the new lemma, empty contributor JSON).
- [ ] 4.2 Failure drills: (a) browser closed mid-edit + laptop-sleep
      reconnect; (b) two sessions writing concurrently; (c) rebuild-skip
      night. Document observed behavior + the contributor guidance ("if the
      page goes grey, reload") IN THIS FILE and in 4.3's doc.
      → verify: written results for all three drills; no data loss in any.
- [ ] 4.3 Contributor-facing instructions: ONE paragraph + screenshots at
      `docs/contributing/web_gui.md`, written for the real audience: the URL,
      the password, "bookmark it", who to call. Add banner to
      `scripts/onboarding/README.md`: non-technical contributors use the web
      version (legacy flow stays documented below it).
      → verify: user approves the text; ideally one non-technical reader test.
- [ ] 4.4 Onboard contributor #1 (real person, India or Singapore) over a
      call; watch, note friction, fix. Then contributor #2 without watching.
      → verify: #1 completes a real Pass1 word unaided after the call;
      #2 onboards with zero live help.
- [ ] 4.5 Thread wrap: update `kamma/tech.md` (+ `conductor/tech-stack.md` if
      needed) with server facts (provider, IP, ports, window time, runbook
      location); `docs/technical/project_folder_structure.md` if
      `scripts/server/` description changed; final lint/type/test sweep.
      The spec's two-week success criterion starts counting; thread finalize
      per `/kamma:4-finalize` when review passes.
      → verify: docs updated; `uv run pytest tests/` clean.

## Explicitly deferred (do NOT do in this thread)

- Multi-user shared-memory gui2; >3 contributors; packaged desktop app.
- Fixing or deleting the legacy `scripts/onboarding/` flow (known defects are
  listed in the spec — leave them).
- Any dpdict.net change.
- Pass2 tab polish beyond "doesn't break in web mode" (record-only in 1.5).
