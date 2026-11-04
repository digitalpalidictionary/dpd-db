# Plan: Contributor Web Server

**Thread:** 20261023_contrib_1_web_server
**Spec:** `spec.md` in this folder — read it first; it contains the full context,
all decisions, and all known unknowns.
**Part 2 spec (Phases 4–7):** `pull_spec.md` in this folder; its reviews are in `egm_pull/`.
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
- **New code placement**: server-side scripts in `scripts/server_contrib/` (dir exists
  in the project tree); gui2 changes minimal and role/env-gated. Tests mirror
  source paths under `tests/`.
- **Legacy git-based onboarding flow is kept, marked legacy, not fixed** —
  see spec "Fate of the existing onboarding machinery". Its known defects are
  documented in the spec and must NOT be silently "fixed while we're here".
- **One long-running contributions PR**, not a PR per day.

**SUPERSEDED (2026-10-30) by `20261030_contrib_5_hardening` — read its spec
before Phase 3:**
- "JSON authoritative; db is scratch" → contributors never write the db
  (contrib_2), and their process opens it read-only (contrib_5).
- "Key-level snapshot reconcile" and "Rebuild gated by the absorption
  invariant" → reconcile on a positive "processed" signal, the PR branch reset
  to main each night from a worktree, rebuild whenever main moved;
  `absorption_check.py` is deleted.
- Per-user files on the server live in `DPD_GUI2_DATA_DIR`, outside the clone.
- Each contributor's env file also sets `DPD_GUI2_DATA_DIR` and `DPD_GUI2_TABS`.
  `add_contributor.sh` and the nginx template are written in contrib_5.
- Order: contrib_2 → contrib_5 → contrib_3 → contrib_4 → this Phase 3.

## Model Strategy

| Phase | Model | Why |
|---|---|---|
| 1, 2 (done) | Sonnet | Done |
| 3 Server provisioning | Sonnet | Runbook commands, using contrib_5's scripts |
| 3B Security check | **Opus** | Analysis only: review the live nginx, auth and firewall setup before real users |
| 4–7 Pull script, key, timer, runbook | Sonnet | Planned 2026-11-04 from `pull_spec.md`; design done, execution is mechanical |
| 8 Cycle proof, onboarding, wrap | Sonnet | Rehearsal, drills, docs, onboarding calls |

## Phase 1 — Local groundwork in gui2 (no server required) — *Sonnet*

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

## Phase 2 — Sync & maintenance-window machinery (local, testable without server) — *Sonnet*

All scripts in `scripts/server_contrib/`: pure-function cores + thin CLI mains,
unit-tested against tmp dirs / scratch git repos in `tests/scripts/server_contrib/`.

- [x] 2.1 `scripts/server_contrib/contrib_reconcile.py`: snapshot-based key-level
      merge. Reads `last_pushed/<file>.json` snapshots, computes
      `final = local − (last_pushed − main_version)`, writes result + refreshes
      the snapshot. Pure core:
      `reconcile(local: dict, pushed: dict, upstream: dict) -> dict`.
      → verify: `uv run pytest tests/scripts/server_contrib/test_contrib_reconcile.py`
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
      DONE (2026-07-19): `scripts/server_contrib/contrib_reconcile.py` — pure
      `reconcile(local, pushed, upstream)` drops a key iff pushed AND removed
      upstream AND `local[key] == pushed[key]` (keep-if-changed rule applied);
      helpers `load_json_dict`/`write_json_dict` (empty → `{}`, matching the
      gui2 managers), `upstream_from_git` (`git show ref:path` → {} if
      absent/invalid), `contributor_files` (globs `additions_*`/`corrections_*`,
      excludes `_added`), `reconcile_all` (writes result + refreshes snapshot),
      thin argparse `main`. Tests `tests/scripts/server_contrib/test_contrib_reconcile.py`
      (15): all plan cases (processed all/some/none, local-added, both, empty),
      keep-if-changed + drop-only-when-unchanged, json helpers, glob exclusion,
      and two scratch-git end-to-end (`reconcile_all` incl. upstream-absent).
      ruff+format+pyright clean.
- [x] 2.2 `scripts/server_contrib/contrib_push.py`: commit `gui2/data/*_{user}.json`
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
      `tests/scripts/server_contrib/test_contrib_push.py` (4): scratch repo + bare remote —
      push lands on `contributions`, snapshot mirrors file, second call no-op;
      `_added` excluded; no files → nothing to push. ruff+format+pyright clean.
- [x] 2.3 `scripts/server_contrib/absorption_check.py`: `git fetch origin main`;
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
      `tests/scripts/server_contrib/test_absorption_check.py` (9): work-file filter,
      empty-blob variants, pure core, and scratch-repo non-empty→skip /
      all-empty→allowed (with a non-empty `_added` proving it's ignored) /
      no-files→allowed. ruff+format+pyright clean.
- [x] 2.4 `scripts/server_contrib/maintenance_window.py` orchestrator:
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
      `tests/scripts/server_contrib/test_maintenance_window.py` (4): all three paths on a
      scratch repo+bare remote+fake sqlite — happy→REBUILT, skip→SKIPPED,
      forced-failure→FAILED with db (marker) AND contributor file restored;
      `--no-systemd` log assertions. ruff+format+pyright clean.
- [x] 2.5 Server config template `scripts/server_contrib/config_server.template`:
      regenerate/exporter flags OFF for audio, anki, deconstructor
      regeneration (premade path per `[generate] deconstructor` mechanism).
      Document per COMMANDS entry of `scripts/bash/generate_components.py`
      (lines 14–69): runs / no-ops / must-skip on server. Decide the
      `uv run pytest tests/` entry (recommendation: replace with the 2.4
      health check in the server run — CONFIRM WITH USER at review).
      → verify: local run of `generate_components.py` under the template
      config on a scratch db copy (`cp dpd.db /tmp/...` per project perf rule)
      completes; record wall-clock as the local baseline number IN THIS FILE.
      DONE (2026-07-19): `scripts/server_contrib/config_server.template` written
      (secrets → `<FILL IN>` placeholders; audio + anki + all exporter make_*
      OFF; db_rebuild + generate.deconstructor ON; search_index OFF; validated
      it parses via configparser). Per-command doc `scripts/server_contrib/config_server.md`
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
      `scripts/server_contrib/generate_components_server.py` runs only the steps that
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
      `tests/scripts/server_contrib/test_generate_components_server.py` (5): dropped
      steps absent, essential present, no pytest, go-before-loader +
      tables-before-headwords ordering. `spelling_mistakes` KEPT (pass2pre
      filtering — gui2 reads it indirectly, not via a lookup.spelling attr).
      VALIDATION NOTE: lean list is a strict in-order subset of the proven full
      run, but a real server run in 3.3 must confirm no kept step depended on a
      dropped one (the spelling case showed hidden pass2pre deps).
      OPERATOR DOCS (2026-07-19): `scripts/server_contrib/README.md` added — ties all the
      Phase 2 scripts together: the nightly-window flow diagram, how to run the
      orchestrator (prod + local `--no-systemd --no-push` dry-run), a per-script
      table (push/absorption/reconcile/lean-rebuild/config template) with
      standalone invocations, the `last_pushed/` snapshot explanation, and a note
      that the pre-existing `update-dpd.sh` belongs to the separate dpdict.net
      webapp server, NOT this system. (Phase 3.1 `SERVER_SETUP.md` provisioning
      runbook and Phase 8.3 contributor-facing docs are still separate.)
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

## Phase 3 — Server provisioning & deployment — *Sonnet*

⚠️ STOP — needs user decisions at phase start: provider (Contabo Mumbai /
Hostinger India-or-Singapore / Hetzner Singapore — table in spec) and
domain/subdomain. The user signs up and pays; agent proceeds once SSH access
exists.

- [x] 3.1 Provision: Ubuntu 24.04 LTS, 16 GB. Minimal hardening: ssh keys
      only, ufw (22/80/443), unattended-upgrades. Install git, Go, nginx,
      certbot, uv. Write every command into `scripts/server_contrib/SERVER_SETUP.md`
      as a copy-paste runbook (assume a future from-scratch rebuild).
      → verify: `ssh server 'uv --version && go version && nginx -v'`.
      Done in practice (2026-10), verified 2026-11-02: Go 1.22.2, nginx 1.24.0,
      uv at `~/.local/bin/uv` (not on non-login PATH; the unit uses the full
      path), HTTPS live. The runbook file itself was not kept up — the
      surviving record is this thread plus the memory threads' artifacts.
- [ ] 3.2 Repo access: deploy key (read-write) on the server; branch
      protection on main (require PR) so the key cannot land on main; clone +
      init only `resources/sc-data` and `resources/dpd_submodules` (the
      `REQUIRED_SUBMODULES` list in
      `scripts/onboarding/contributor_setup.py`); generate server config.ini
      from the 2.5 template; user enters his DeepSeek/OpenRouter key(s)
      manually (never committed).
      The `contributions` branch must stay unprotected: the nightly push
      resets it to main and uses `--force-with-lease` (contrib_5).
      → verify: from server, `git fetch` works; a force-with-lease push to a
      test branch works; push to main rejected by protection.
      ⚠️ FINDING 2026-11-03 — the deploy key bypasses branch protection.
      Verified on the server: `core.sshCommand = -i ~/.ssh/dpd_deploy`, and that
      key IS the repo write deploy key (`dpd contrib6 temp server`, id
      168360647, `read_only=false`). A test push from a throwaway clone landed
      on main with exit 0 while "Changes must be made through a pull request"
      was enabled. GitHub deploy keys are not subject to branch protection, so
      protection alone does NOT stop the server key as 3.2 intended. The test
      commit was removed and main restored to 8af6e887 by the maintainer.
      Fix available: the server must push with a credential branch protection
      applies to (a non-admin account's key or PAT). **Owner decision
      2026-11-03: accept the risk for now** — protection still guards against
      every other actor, and the server key stays able to write main. Revisit
      if the server's trust model changes or on the next security pass.
      Status 2026-11-03: clone, deploy access and pulls verified in daily use;
      the contributions push is proven working (branch 1490f742). Main is now
      protected: PRs required with 0 approvals, `enforce_admins=False` so the
      maintainers keep direct push, force-pushes and deletions off. Effect on
      people: only Devamitta has push without admin, so only he moves to PRs
      (or gets admin if that is preferred later); the other outside
      contributors are read-only and already arrive by PR. `contributions`
      stays unprotected, as the nightly `--force-with-lease` push requires.
- [x] 3.3 First db + THE MEASUREMENT: rsync the user's local dpd.db up (fast
      start), AND run one full server rebuild (`db_rebuild_from_tsv.py` +
      `generate_components.py`) to measure real wall-clock — this number fixes
      the window schedule. Decision rule (from spec): if > ~3 h, windows use a
      maintainer-pushed db instead (add `just contrib-push-db` rsync recipe)
      and server rebuild becomes a later upgrade. RECORD the number and the
      decision IN THIS FILE.
      → verify: measured time recorded; server dpd.db passes the 2.4 health
      check.
      MEASURED 2026-11-03: db rebuilt from tsv + lean components =
      **49 min** (07:06→07:55) and **55 min** (11:28→12:23) on the 2-core
      server, health check passing both times. Decision: comfortably under the
      ~3 h limit, so the windows keep rebuilding on the server — no
      maintainer-pushed db, no `just contrib-push-db` recipe. The first db was
      the window's own rebuild; headwords 89,774, lookup 1,179,891, db 883 MB.
      Status 2026-11-02: the first db is up (the app has served from it since
      2026-10; 89,774 headwords verified against the live file). A full server
      rebuild has never run — the wall-clock measurement and the
      rebuild-vs-pushed-db decision move into 3.6's first manual window run.
- [x] 3.4 systemd template unit `dpd-gui@.service` (reads
      `/etc/dpd/<user>.env`: username, role, `DPD_GUI2_DATA_DIR`,
      `DPD_GUI2_TABS`, port — the file `add_contributor.sh` writes) + nginx
      from contrib_5's `scripts/server_contrib/nginx_contrib.conf.template`,
      using the path-prefix or subdomain form that contrib_4 Phase 4 proved;
      HTTPS via certbot on the chosen domain.
      → verify: from an outside network, two test URLs serve the GUI over
      HTTPS after a password prompt; wrong password rejected; each password
      opens only its own URL; both sessions work simultaneously; RSS per
      instance recorded IN THIS FILE.
      PARTLY DONE — single user only. Alice serves over HTTPS with password
      and the right tabs, and her RSS figures (warm 774.1, one book 879.2) are
      in `kamma/archive/20261102_contrib_mem_wordfinder_lazy/artifacts/`.
      ⚠️ BLOCKER FOUND 2026-11-03 (3.5 drill): **two contributors cannot work
      at once behind path prefixes.** Flet 1.0.1 serves its web shell with
      ABSOLUTE asset paths (`/python.js`, `/flutter_bootstrap.js`,
      `/main.dart.wasm`, `/ws`, `/assets/`, …). The temporary shim
      `/etc/nginx/dpd/zz_root_asset_shim.conf` maps every one of those root
      paths to a HARD-CODED alice realm and alice port 8551 (its own comment:
      "while this shim exists, root-level asset paths always answer as ALICE;
      multi-user prefixes need the native fix (ASGI root_path)"). A second
      user's page therefore 401s on `/python.js` and never boots — reproduced
      with `drilltest`: authenticated HTML returned 200, then the console
      showed `401 @ /python.js`, `401 @ /manifest.json`, and the app stayed at
      74 MB with no db load. So the earlier "both sessions work simultaneously"
      claim was never true: only alice was ever verified. Real fixes, owner to
      choose: (a) native `root_path` support in gui2 so each instance serves
      prefixed assets — the shim's recorded plan; (b) a subdomain per
      contributor, so root paths are per-host (needs wildcard DNS + cert).
      Until one lands, the server is a ONE-contributor server.
      FIXED 2026-11-03 (option a, no gui2 code change). Flet 1.0.1 already
      mounts the app under `FLET_WEB_APP_PATH` and rewrites the shell to match
      (`<base href="/<user>/">`, `webSocketEndpoint="/<user>/ws"`;
      `flet/app.py` `__get_page_name`, `flet_web/fastapi/flet_static_files.py`).
      Changes: `Environment=FLET_WEB_APP_PATH=%i` in `dpd-gui@.service`, and
      `proxy_pass http://127.0.0.1:@PORT@;` (no trailing slash, so the prefix
      reaches the instance) in `nginx_contrib_user.conf.template`; test
      `test_each_instance_lives_under_its_own_prefix` fails with either change
      reverted. Proved first with two throwaway Flet apps on the laptop.
      On the server: unit reinstalled + daemon-reload, `alice.conf` proxy_pass
      changed, `zz_root_asset_shim.conf` moved out of the include dir (backups
      of all three in `/root/mem/prefix_fix_20261103/`), nginx reloaded, alice
      restarted. alice: `/alice/`, `/alice/python.js`, `/alice/main.dart.wasm`
      200 locally; root `/python.js`, `/assets/`, `/preview/x` now 404 publicly.
      Two throwaway users `probe2` (8556) and `probe3` (8557) added with the NEW
      `add_contributor.sh` (htpasswd came out `root:www-data 640` with no hand
      fix). Over public HTTPS: no login 401, wrong password 401, own path 200,
      the other user's path and `/alice/` and `/status` 401. Two headless
      browsers logged in at the same time: each loaded 29 files from the host,
      none outside its own prefix, 0 console errors, one live websocket per
      instance, both rendered the full Pass1Auto/Pass1Add screen.
      RSS with a session open: 792,000 KB and 791,800 KB (db loaded; the failed
      drilltest stopped at 74 MB); alice idle with no session 89,276 KB.
      The server has 7.9 GB RAM (not 16 GB), so three loaded instances use
      about 2.4 GB. Both probes removed afterwards.
      Not yet checked behind the prefix: the web preview page (its URL is
      relative to `<base href>`, so it should resolve to `/<user>/preview/`).
      Check it in 8.1. alice herself was not opened in a browser (her password
      is the owner's); the owner confirms on next login.
- [x] 3.5 Onboard a test user with contrib_5's
      `scripts/server_contrib/add_contributor.sh` (the "<10 minutes to onboard
      #3" script), then remove them with the documented removal steps.
      → verify: new URL live with the right tabs; after removal the URL refuses
      and no unit or env file is left.
      DRILL RUN 2026-11-03 with a throwaway account `drilltest` (port 8555,
      tabs `Transl,DB`, throwaway password). Onboarding exposed TWO real bugs:
      (1) **`add_contributor.sh` writes the htpasswd mode 640 but leaves it
      root:root**, so the nginx worker cannot read it and the new URL returns
      500 until someone runs `chown root:www-data` by hand (alice's file was
      fixed that way at some point; the README admits it "is not checked
      locally"). Reproduced: 500 → `chown root:www-data` → 200. The script
      should set nginx's group itself.
      (2) The multi-user blocker recorded at 3.4: even with correct auth the
      second user's app cannot boot.
      Verified during the drill: unauthenticated 401, authenticated 200, right
      tabs in the env file, service active, wrong password 401. Removal path
      (the actual point of 3.5) tested per README steps — outcome recorded
      below.
      REMOVAL DONE 2026-11-03: `systemctl disable --now dpd-gui@drilltest`, its
      env, htpasswd and nginx files deleted, nginx reloaded. `/etc/dpd/` and
      `/etc/nginx/dpd/` hold only alice's files; no drilltest data file. The
      same removal ran for `probe2`/`probe3` (3.4): the URL answers 404 once
      the nginx reload finishes (a check in the first seconds can still see
      the old workers' 401/403). Bug (1) fixed in commit 081d27ca; its test
      fails with the `chgrp` removed (checked 2026-11-03).
      Onboarding reminder: add each new user's `--instance dpd-gui@<user>` to
      the cron line, or the window never stops that instance.
- [x] 3.6 Cron the maintenance window at 01:00 IST + a failure surface the
      user will actually see: window script appends to a status file served at
      an authed nginx path (`/status`) — no mail stack.
      → verify: force one run of each path ON THE SERVER: happy (main moved →
      rebuild), main unchanged (no rebuild), dirty tree (pull refused),
      rollback (deliberately break the rebuild); `/status` reflects each.
      DONE 2026-11-03. Cron installed (`0 1 * * *`, server clock is IST):
      `cd /root/dpd-db && uv run --no-sync scripts/server_contrib/maintenance_window.py
      --data-dir /var/lib/dpd/contrib_data --instance dpd-gui@alice
      --status-file /var/lib/dpd/status.txt >> /root/mem/window_cron.log`.
      Failure surface: the window rewrites the status file at the end of every
      run (outcome, time, commit, that run's ERROR/WARNING lines) and nginx
      serves it at `/status` behind alice's login (block kept in
      `scripts/server_contrib/nginx_status.conf.template`).
      All four paths run on the server, each confirmed in `/status` from a
      browser:
      - happy: `rebuilt` twice (07:06–07:55, 49 min; 11:28–12:23, 55 min), health
        check passed both times, WAL re-applied, alice restarted.
      - main unchanged: `skipped` in 9 s (12:24), problems 0.
      - dirty tree: `failed` with `working tree is dirty, window refused:
        ['scripts/server_contrib/README.md']`; alice stayed up; file restored.
      - rollback: corrupt contributor JSON in a scratch data dir with
        `--no-systemd --no-push` and a copied db: `failed` with the JSON error,
        then `restored db from dpd_test.db.prev`, `restored working tree`,
        `restored contributor files`; live db and alice untouched.
      The push path also works: `contrib: submit data 2026-11-03` reached the
      `contributions` branch (1490f742) carrying alice's 2 entries.
      Found and fixed during the drill: the status file listed an earlier run's
      error (commit 1befe821).

## Phase 3B — Security check before real users — *Opus*
⚠️ MODEL SWITCH REQUIRED (Opus): analysis only.
- [x] 3B.1 Review the live server, read-only: `nginx -T` output, each
      htpasswd file's owner and mode, the env files, `ufw status`, listening
      ports (`ss -tlnp`: gui2 instances on 127.0.0.1 only), certbot renewal,
      the deploy key's scope, and that no secret is in the clone
      (`git status`, `config.ini` mode). Check that one user's password cannot
      open another user's path, and that no hidden tab is reachable.
      → verify: findings written here; every real issue fixed (Sonnet) before
      Phase 4.
      REVIEW RUN 2026-11-03 (Opus, read-only, after the 3.4 prefix fix).
      Real issues, none fixed yet (owner to approve):
      1. **Root can log in over ssh with a password.** `sshd -T`:
         `passwordauthentication yes`, `permitrootlogin yes`; root has a
         password set (`passwd -S` = P). `50-cloud-init.conf` says `yes` and
         sorts before `60-cloudimg-settings.conf` (`no`); sshd keeps the
         first value. 3.1 wanted keys only. Fix: `PasswordAuthentication no`
         in `50-cloud-init.conf`, `sshd -t`, reload ssh, then prove key login
         still works from the laptop before closing the session.
      2. **The firewall is off** (`ufw status`: inactive; 3.1 wanted
         22/80/443). Exposure today is small: only nginx :443 and sshd :22
         bind publicly. But any later service on 0.0.0.0 would be public.
         Fix: `ufw allow 22,80,443/tcp`, then `ufw enable`.
      3. **Certificate renewal may fail.** Renewal uses `authenticator =
         nginx` (an http-01 challenge on port 80), and nginx listens only on
         443. Not proved either way. The cert is valid to 2027-01-29 and
         renewal starts ~30 days before. Check: `certbot renew --dry-run`
         (staging server, edits nginx for the challenge for a moment).
      4. `config.ini` (holds the API keys) is mode 644. Only root can log in,
         so the risk is low. Fix: `chmod 600`.
      Passed: gui2 instances bind 127.0.0.1 only (8551; probes 8556/8557
      when up); htpasswd `root:www-data 640`, env and nginx user files 600;
      each password opens only its own path, `/status` only with alice's
      (tested with probe2/probe3); no hidden tab is reachable: hidden tabs are
      not in the tab bar, Alt+jump keys check `_visible`, and the read-only
      tabs (DB, √, Infl) refuse in the save method itself, so Ctrl+S is
      refused too; Ask AI is a no-op on the server; `config.ini` is
      gitignored and the clone is clean apart from the window's
      `_contrib_worktree/` and `dpd.db.prev`; unattended-upgrades on;
      opencode listens on 127.0.0.1 only. Deploy key: accepted risk (3.2).
      FIXES APPLIED 2026-11-03 (owner approved; backups in
      `/root/mem/security_fix_20261103/`; a second ssh connection was held
      open as a safety line throughout; alice never restarted):
      1. New `/etc/ssh/sshd_config.d/01-dpd-keys-only.conf`
         (`PasswordAuthentication no`, `KbdInteractiveAuthentication no`,
         `PermitRootLogin prohibit-password`); sorts first, so it beats
         `50-cloud-init.conf` and survives cloud-init rewriting that file.
         `sshd -t` ok, ssh reloaded. `sshd -T`: passwordauthentication no,
         permitrootlogin without-password. Fresh key login (no control
         socket): ok. Password-only login: `Permission denied (publickey)`.
         The provider's web console still takes the root password.
      2. `ufw allow 22/tcp, 80/tcp, 443/tcp`, `ufw --force enable`, with a
         5-minute `systemd-run` timer to `ufw disable` as a dead-man switch,
         stopped once checks passed. Active, default deny incoming, v4+v6.
         Fresh ssh login ok, public `/alice/` 401, local alice 200, outbound
         `git ls-remote` to GitHub ok, port 8551 closed from outside.
      3. `certbot renew --dry-run`: "all simulated renewals succeeded". The
         nginx authenticator opens port 80 for the challenge by itself, so
         the worry was wrong; no nginx change needed. Port 80 must stay
         allowed in ufw for this. Site config unchanged afterwards.
      4. `chmod 600 /root/dpd-db/config.ini`.
      3B.1 is complete; no real issue left open except the accepted deploy
      key risk.

## Phases 4–7 — the daily pull and the new-server runbook (merged from thread `20261104_contrib_pull`, 2026-11-04)

The design and its reasons are in `pull_spec.md` in this folder. Its three review gates are in `egm_pull/` (brief, gate1, gate2, gate3). These phases were planned after Phase 3B and finish the product: contributors add words, and the words reach the maintainer's laptop by themselves.

### Decisions and executor rules for Phases 4 to 8

#### Architecture decisions

- **New code is one script**, `scripts/server_contrib/contrib_pull.py`. It imports `reconcile_all` from `contrib_reconcile.py` and `merge_all` + `SharedFiles` from `merge_contrib_files.py`, and `DELIVERED_KINDS` from `tools/contrib_entry.py`. It writes no filter of its own. (Gate 1, R1.2 and R3.1.)
- **No class, no framework.** Plain functions, one `main()`. The unit and the justfile call it with no arguments, so it needs no flags except `--dry-run`.
- **The remote source is one string** (`user@host:<path>/` or a local folder). Tests pass a local folder as the source and `rsync` copies from it the same way; no mock of rsync is needed. The ssh options travel in one `-e` argument, added only for a remote source.
- **All times are the laptop's local time.** The last run of the day is the one that starts at or after 22:30.
- **Status file and lock live in `logs/`** (gitignored). Never in the home folder.
- **Left out on purpose:** a lock in the editor, a registered-contributor list, staging of shared-file changes, a backup before each merge (git tracks the shared files), sanitising dictionary fields. See spec "What's not included" and `egm_pull/gate1.md`.

#### Executor rules (apply to every task in Phases 4 to 8)

- Run from the repo root `/home/bodhirasa/MyFiles/3_Active/dpd-db`. WHO is named per task: `AGENT` runs it; `OWNER` only where it says so.
- **Never** open or print `config.ini` or any `.ini`/`.env` file, and never edit them. Read the one setting only through `tools.configger.config_read("epitaka_server", "ssh")`.
- **Never** run `git add`, `git commit`, `git stash`, `git restore`, `git checkout --`, or `git reset`. The owner commits.
- Never `pkill`. Stop a process by its number, found with `ps -eo pid,args | grep "[p]attern"`.
- Any command that can take over 60 s runs in the background with a bounded wait (`timeout 600 bash -c 'until ...; do sleep 10; done'`).
- After every edit of a Python file under `scripts/`, run `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright <file>`. For files under `tests/` use `uv run pyright --project /dev/null <file>`. Do not run `ruff format` on `.json` fixtures.
- Before editing the server's `authorized_keys`, back it up. Append a line; never rewrite the file.
- Judge a server service by what the page or command returns, not by its log (the log lags by minutes: Python's output is buffered under systemd).
- If a `→ verify:` result differs from what the task says, stop, write the real output into this file under the task, and tell the owner. Do not improvise.
- The server is `epitaka`: `ssh -o BatchMode=yes epitaka '<command>'`. Never print its environment or htpasswd files. Never touch alice's data.


## Phase 4 — The pull script, tested with no server — *Sonnet*

- [x] 4.0 **Document the tools first** (workflow rule 2). In `kamma/tech.md` add a short section "Contributor pull": rsync over ssh with a restricted key, `systemd --user` timer, `contrib_pull.py`, status file in `logs/`. Date it 2026-11-04.
  → verify: `rg -n "Contributor pull" kamma/tech.md` returns one line.

- [x] 4.1 **Discover the rsync listing format.** AGENT. Run `rsync -r --list-only gui2/data/ | head -5` on the laptop and `ssh -o BatchMode=yes epitaka 'rsync -r --list-only /var/lib/dpd/contrib_data/ | head -8'`. Write both outputs, exactly, into this file under this task. Note whether sizes carry thousands separators and what the first column looks like for a link and for a regular file.
  → verify: the two outputs are pasted below this task and the parser rule (how to read size and type) is written in one sentence.
  **Result (2026-11-04):**
  Laptop `gui2/data/`:
  ```
  drwxrwxr-x          4,096 2026/11/01 17:41:01 .
  -rw-rw-r--          1,598 2025/12/21 19:55:12 README.md
  -rw-rw-r--        159,806 2026/11/01 17:41:01 additions_added.json
  -rw-rw-r--          2,733 2026/11/01 17:41:01 additions_alice.json
  -rw-rw-r--              2 2026/07/02 19:18:12 additions_deva.json
  ```
  Server `/var/lib/dpd/contrib_data/` (via `ssh epitaka`):
  ```
  drwxr-xr-x          4,096 2026/11/03 21:04:57 .
  -rw-r--r--         13,876 2026/11/03 21:04:57 additions_alice.json
  -rw-------             59 2026/11/03 21:01:28 checked_alice.csv
  -rw-r--r--            286 2026/11/03 21:04:57 daily_log_alice.json
  -rw-r--r--             82 2026/11/03 20:42:41 db_test_exceptions_alice.tsv
  -rw-r--r--            814 2026/11/03 21:04:57 history_alice.json
  -rw-------             26 2026/11/03 21:01:28 manual_corrections_alice.tsv
  ```
  Local test with a symlink, a name with a space and a sub-folder (`rsync -r --list-only`, no `-l`): the symlink IS listed, as `lrwxrwxrwx             13 2026/11/04 06:20:44 link.json` (no `-> target`); the sub-folder is listed as `drwxrwxr-x ... sub` and its file as `sub/b.json`; `evil name.json` is listed with its space.
  **Parser rule:** split each line on whitespace into at most 5 parts (mode, size, date, time, name); remove the commas from the size; the entry is a regular file only if the mode starts with `-`; skip the line whose name is `.`.

- [x] 4.2 **Make `write_merged_log` atomic.** In `scripts/server_contrib/merge_contrib_files.py`, change `write_merged_log` to write a temp file in the same folder and `os.replace` it onto `path`, removing the temp file if the write raises. Same pattern as `_write_atomic` in `scripts/server_contrib/contrib_reconcile.py`. Do not change the output format or sort order. Add a test to `tests/scripts/server_contrib/test_merge_contrib_files.py` (it exists): patch `json.dump` to raise, call `write_merged_log` on an existing log, assert the old file is unchanged and no `*.tmp` file is left.
  → verify: `uv run pytest tests/scripts/server_contrib/test_merge_contrib_files.py -q` passes. Then revert the change to `write_merged_log` only (copy the file to the scratchpad first, restore it in the same command) and confirm the new test fails; report the count of failures.

- [x] 4.3 **Write the checks as functions, test first.** Create `tests/scripts/server_contrib/test_contrib_pull.py` and `scripts/server_contrib/contrib_pull.py` with these functions (type hints, `Path`, `icecream` not `print`):
  - `kind_of(name: str) -> str | None`: returns the kind from `DELIVERED_KINDS` whose glob matches `name`, only if the user part (the text between the first `_` after the kind prefix and the extension) matches `^[a-z][a-z0-9_]{0,31}$` and `added` is not in the name; else `None`. Derive the user part by removing the kind's literal prefix and extension, not by a second regex over the whole name.
  - `user_of(name: str) -> str`: the user part, same rule.
  - `check_content(path: Path, kind: str) -> str | None`: returns a reason string or `None`. JSON kinds (`additions`, `corrections`): UTF-8, `json.loads`, catches `RecursionError`, top level is a dict and every value is a dict. Line kinds: UTF-8, no character below U+0020 except tab, CR, LF, each line at most 500 characters, file is empty or ends with `\n`; `variant_readings` and `spelling_mistakes` have exactly 2 tab-separated columns on every line; `db_test_exceptions` is `<name><TAB><digits>` on every line.
  - Tests (each one name = one behaviour): wrong extension for a kind (`checked_alice.json`) is refused; a name with `added` is refused; a user part with a capital, a leading digit, or 33 characters is refused; invalid JSON, a JSON list, a nested 100,000 deep `[` string, a value that is not a dict are each refused; a flag file with no final newline is refused; a 501-character line is refused; a NUL byte is refused; a good file of each kind passes. Build the passing cases by copying a few real lines/entries from `gui2/data/additions_alice.json`, `gui2/data/checked_alice.csv`, `gui2/data/manual_corrections_alice.tsv` and `gui2/data/db_test_exceptions_alice.tsv` (if that file does not exist locally, use the real format shown in `merge_contrib_files.py` `merge_test_exceptions`).
  → verify: `uv run pytest tests/scripts/server_contrib/test_contrib_pull.py -q` passes; with `kind_of` changed to ignore the extension the extension test fails (report the count).

- [x] 4.4 **Listing and copy.** In `contrib_pull.py` add:
  - `list_source(source: str, ssh: list[str]) -> list[tuple[str, int, bool]]`: runs `rsync -r --list-only [-e "<ssh>"] <source>` and parses `(name, size, is_regular_file)` using the rule from 1.1. A name that has a `/` in it (a sub-folder entry) is returned as-is and fails `kind_of`.
  - `copy_names(source: str, names: list[str], scratch: Path, ssh: list[str]) -> None`: writes the names to a temp file and runs `rsync --files-from=<tempfile> --no-links --no-perms --no-owner --no-group --timeout=60 [-e ...] <source> <scratch>/`. No `-a`.
  - `SSH_OPTIONS`: `["ssh", "-i", "<home>/.ssh/dpd_contrib_pull", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new", "-o", "IdentitiesOnly=yes", "-o", "ForwardAgent=no"]` built with `Path.home()`.
  - Tests with a local folder as source (no ssh): a folder with 3 good files, 1 symlink pointing to `/etc/hostname`, 1 file of 5 MB + 1 byte, 1 file named `evil name.json`: the symlink either does not appear in the `list_source` result or is marked not regular (record which in task 4.1; without `-l`, `rsync -r --list-only` may skip links with a message), and either way `select_names` does not return it; the listing reports sizes; `copy_names` called with only the accepted names copies exactly those and no symlink lands in scratch.
  → verify: `uv run pytest tests/scripts/server_contrib/test_contrib_pull.py -q` passes.

- [x] 4.5 **Per-contributor checking and the drop steps.** In `contrib_pull.py` add:
  - `select_names(listing: list[tuple[str, int, bool]]) -> tuple[list[str], dict[str, str]]`: returns the names to copy and a map `user -> reason` for every contributor with at least one bad name (not regular, over 5 MB, or `kind_of` is `None` but the name matches a delivered glob and a user part can be read from it). A name from which no user can be read (a `/` in it, a user part that fails the pattern) is never copied and is counted in the status as `ignored_names: N`; the first 80 characters of each go to `logs/contrib_pull.log`, never to the status file. If the listing has more than 200 entries raise `PullError("too many files")`. `PullError` is a small `Exception` subclass defined in the module.
  - `check_scratch(scratch: Path, bad: dict[str, str]) -> dict[str, str]`: runs `check_content` on every file in `scratch`; adds `user -> reason` to `bad` for the first failing file of each contributor; returns the new map.
  - `remove_users(scratch: Path, bad: dict[str, str]) -> None`: deletes every file in `scratch` whose `user_of` is in `bad`.
  - `drop_foreign_exceptions(scratch: Path) -> int`: for every `db_test_exceptions_*.tsv` in `scratch`, drops every line whose id is below `CONTRIB_ID_BASE` (import it from `gui2.database_manager`, as `contrib_reconcile.py` does), keeps line endings, rewrites atomically; returns how many lines it dropped.
  - Step order inside the run (written as a function `prepare(scratch: Path, repo: Path, bad: dict[str, str]) -> tuple[dict[str, str], int]`): `check_scratch` → `remove_users` → `contrib_reconcile.reconcile_all(repo, scratch)` → `drop_foreign_exceptions`; returns `(bad, dropped_count)`.
  - Tests (copy real snippets as in 4.3): (a) a processed word: put the list `[{"_source_key": "alice_1", "_source_hash": entry_hash(entry)}]` (a JSON list: `load_processed` raises on an object) in a temp repo's `gui2/data/additions_added.json`, put `entry` under key `alice_1` in the scratch `additions_alice.json` and a second entry under `alice_2`; after `prepare` only `alice_2` remains. (b) an entry edited after review (same key, different content so a different hash) stays. (c) one bad file for alice (broken JSON in `additions_alice.json`) removes all of alice's scratch files and leaves bob's untouched, and `bad` names alice. (d) a non-reserved exception line (`<real test name>\t123`) is dropped and counted; a reserved one (`\t10000005`) that a held addition holds survives. (e) 201 names raise `PullError`.
  → verify: `uv run pytest tests/scripts/server_contrib/test_contrib_pull.py -q` passes. Then change `prepare` to skip `reconcile_all` and confirm test (a) fails; restore in the same command.

- [x] 4.6 **Copy in, merge, gate, status.** In `contrib_pull.py` add:
  - `editor_running() -> bool`: uses `psutil.process_iter(["pid", "cmdline"])`, true if any process other than the current one has an argument in `cmdline` that ends with `gui2/main.py`.
  - `copy_in(scratch: Path, data_dir: Path) -> list[str]`: for every file in `scratch`, writes `<name>.tmp` in `data_dir` and `os.replace`s it onto `<name>`; returns the names.
  - `Status` dataclass and `read_status(path: Path) -> Status`, `write_status(path: Path, status: Status) -> None`: plain `key: value` lines (outcome, finished, last_success, then one line per contributor `user: <files> files, <entries> entries` or `user: skipped, <reason>`, then `lines_added: N`, `test_lines_dropped: N`). A missing or unreadable file gives a `Status` with no `last_success`. Writing is atomic (temp + replace). Never write the ssh target or the key path.
  - `run(source: str, repo: Path, shared: SharedFiles, status_path: Path, lock_path: Path, now: datetime, dry_run: bool) -> Status`: implements spec steps 1 to 7 in order, using the functions above and `merge_all(repo / "gui2" / "data", shared, Gui2Paths(repo).contrib_lines_merged_path)`. `run` never calls `SharedFiles.default()`: that method reads the real shared files from the current folder (`Gui2Paths()` and `DbTestManager()` are cwd-relative), so a test with a temp repo would change real data. `main` passes `SharedFiles.default()`; every test passes a `SharedFiles` whose six paths are files under `tmp_path` (copy how `tests/scripts/server_contrib/test_merge_contrib_files.py` builds one). Outcomes: `pulled`, `pulled with problems` (some contributor skipped), `skipped: <reason>`, `partial` (editor appeared before the merge), `failed: <reason>`. `last_success` is set to `now.date().isoformat()` only for `pulled` and `pulled with problems`, and carried forward otherwise. With `dry_run`, it does steps 1 to 4 against a scratch folder, writes nothing to `gui2/data`, and returns a status listing what it would copy; it does not touch `last_success`. The lock is `fcntl.flock(fd, LOCK_EX | LOCK_NB)` on `lock_path`; if it is held the outcome is `skipped: another run`.
  - `main() -> int`: reads the ssh target with `config_read("epitaka_server", "ssh")`; if empty returns 1 after logging `[epitaka_server] ssh is not set in config.ini`. Builds the source from the target plus the remote path constant `REMOTE_SOURCE_SUFFIX` (a placeholder `":"` until task 5.3 finds the form that works with the restricted key; its path is relative to the folder `rrsync` serves, so it must not hold `/var/lib/dpd/contrib_data`). Parses `--dry-run`. Calls `run`, then prints the status text (also for `--dry-run`, where it lists what would be copied, per contributor, and the counts dropped). Appends one line to `logs/contrib_pull.log`. If the outcome is not a success or skip, and `now` is at or after 22:30, runs `notify-send "DPD contributor pull" "<outcome>"` (a failure to notify is ignored and noted in the status). Returns 0 for success and skip, 1 otherwise.
  - After writing the tests, run `git status --porcelain shared_data db_tests gui2/data > <scratchpad>/before.txt` before and after the test run and compare: a test run must change nothing in those folders.
  - Tests: (a) a full run against a local source folder and a temp repo puts the expected files in the temp `gui2/data` and writes `last_success` = today; (b) a second run the same day returns `skipped: already done today` and changes no file; (c) with `editor_running` patched to true the run is `skipped: editor open`, nothing changes; (d) with a bad contributor, bob's files arrive and alice's local files are byte-identical to before, outcome `pulled with problems`; (e) a crash simulated by making `copy_in` raise after one file leaves `last_success` unchanged; (f) `--dry-run` changes no file in the temp `gui2/data` and leaves `last_success` alone; (g) the lock held by another file descriptor gives `skipped: another run`; (h) `now` at 22:30 with a failed run calls the notifier, at 21:59 it does not; (i) a missing status file does not stop the run; (j) a flag line the merge logged earlier is not merged twice (run twice on two days).
  → verify: `uv run pytest tests/scripts/server_contrib/test_contrib_pull.py -q` passes with no skips. Revert check: make `editor_running` always return false and confirm test (c) fails.

- [x] 4.7 **Phase gate.** `uv run ruff check --fix` and `uv run ruff format` on `scripts/server_contrib/contrib_pull.py`, `scripts/server_contrib/merge_contrib_files.py`, `tests/scripts/server_contrib/test_contrib_pull.py`, `tests/scripts/server_contrib/test_merge_contrib_files.py`; `uv run pyright scripts/server_contrib/contrib_pull.py scripts/server_contrib/merge_contrib_files.py`; `uv run pyright --project /dev/null tests/scripts/server_contrib/test_contrib_pull.py tests/scripts/server_contrib/test_merge_contrib_files.py`; `uv run pytest tests/scripts/server_contrib -q`; `just typecheck`.
  → verify: all five report no errors and the pytest line shows zero failures.
  **Phase 4 result (2026-11-04):** all five clean; `uv run pytest tests/scripts/server_contrib -q` = 165 passed; `just typecheck` = 0 errors. Revert checks: 4.2 reverted write = 1 failure; 4.3 ignore-extension = 1; 4.5 skip `reconcile_all` = 2; 4.6 each of the three editor checks removed in turn = 3, 2 and 1 failures.
  **Where the build differs from the plan text (Drift Gate):**
  - 4.4: the `select_names` test (symlink never selected) sits with 4.5 tests, because `select_names` belongs to 4.5.
  - 4.5: added `ignored_names(listing)`, because `select_names` has a fixed return type and the count of unreadable names needs its own function. `check_scratch` reasons start with the file name.
  - 4.6: a skipped run (already done today, editor open, another run) returns its reason and writes NEITHER the status file NOR the log line. Reason: the timer runs 30 times a day, and a skip would overwrite the last real result and add 29 log lines. A dry run writes nothing either and ignores the "already done today" and editor gates. `partial` and `failed` are written.
  - 4.6: the notice also goes out for `pulled with problems` (spec step 7), not only for failed and partial. The status gains an `ignored_names:` line and an optional `notice_error:` line.
  - 4.6: the plan's revert check ("make `editor_running` always false, test (c) fails") cannot work as written, since test (c) replaces `editor_running` with a stub. Real-function guard: the test that starts a process with a `gui2/main.py` argument (1 failure on revert). Gate guards: three timing tests added.
  - 4.6: "a test run must change nothing in shared_data, db_tests, gui2/data": checked with a timestamp marker and `find -newer` (no git command run); zero files changed.
  - `merge_all` report items that start with `skipped` are not counted in `lines_added`.

## Phase 5 — The restricted key and the first real pull — *Sonnet*

- [x] 5.1 **Make the key.** AGENT. On the laptop: `ssh-keygen -t ed25519 -N "" -C "dpd-contrib-pull" -f ~/.ssh/dpd_contrib_pull` (stop if the file exists). Do not print the private key. Print only the public key line.
  → verify: `stat -c '%a' ~/.ssh/dpd_contrib_pull` prints `600`; `cat ~/.ssh/dpd_contrib_pull.pub | wc -w` prints `3`.

- [x] 5.2 **Add the key to the server, restricted.** AGENT, with a safety line. Open a second ssh connection first and leave it open (`ssh -o ControlMaster=yes -o ControlPath=/tmp/claude-1000/cm-ep -o ControlPersist=30m -fN epitaka`). Back up: `cp -a /root/.ssh/authorized_keys /root/mem/authorized_keys.before_pull_20261104`. Append one line: `restrict,command="/usr/bin/rrsync -ro /var/lib/dpd/contrib_data" <the public key line>`. Never rewrite the file.
  → verify: `ssh -o BatchMode=yes epitaka 'wc -l < /root/.ssh/authorized_keys'` prints one more than before; a fresh login with the owner's normal key still works (`ssh -o ControlPath=none -o BatchMode=yes epitaka 'echo OK'` prints `OK`). Then close the safety line (`ssh -o ControlPath=/tmp/claude-1000/cm-ep -O exit epitaka`).

- [x] 5.3 **Prove the key can only read, and find the path form.** AGENT. From the laptop, with `-i ~/.ssh/dpd_contrib_pull -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new`:
  - `rsync -r --list-only -e "<those ssh options>" root@<host>:/ ` and `...:.` and `...:` — find which source form lists the folder. Write which form works into this file and set `REMOTE_SOURCE_SUFFIX` in `contrib_pull.py` to the form that works (with the trailing slash if needed).
  - `ssh <options> root@<host> 'id'` must be refused (no output, not `uid=`).
  - an rsync that tries to push a file (`rsync -e "<ssh>" /etc/hostname root@<host>:/`) must fail.
  - the host is read from `ssh -G epitaka`; do not print the config file.
  → verify: the listing form shows `additions_alice.json`; the `id` command prints no `uid=`; the push fails with an error. Paste all three results below this task.
  **Result (2026-11-04):** the three source forms `root@host:/`, `root@host:.` and `root@host:` all list the folder (first row `additions_alice.json 13,876`). `REMOTE_SOURCE_SUFFIX` stays `":"`, so no code change. `ssh ... 'id'` printed `/usr/bin/rrsync error: SSH_ORIGINAL_COMMAND does not run rsync` (no `uid=`). The push printed `/usr/bin/rrsync error: sending to read-only server is not allowed` then `rsync error: error in rsync protocol data stream (code 12)`. 5.2: `authorized_keys` went from 1 to 2 lines; backup at `/root/mem/authorized_keys.before_pull_20261104`; a fresh login with the normal key printed `OK`.

- [x] 5.4 **Dry run on the real files.** AGENT. First save a copy of the contributor files now in `gui2/data` to the scratchpad (outside the repo): `mkdir -p <scratchpad>/pull_backup && cp -p gui2/data/{additions,corrections,checked,manual_corrections,db_test_exceptions,variant_readings,spelling_mistakes}_*.* <scratchpad>/pull_backup/ 2>/dev/null; cp -p gui2/data/contrib_lines_merged.json <scratchpad>/pull_backup/; cp -p --parents shared_data/user_dictionary.txt shared_data/deconstructor/checked.csv shared_data/deconstructor/manual_corrections.tsv shared_data/deconstructor/variant_readings.tsv shared_data/deconstructor/spelling_mistakes.tsv db_tests/db_tests_columns.tsv <scratchpad>/pull_backup/`. Ask the owner to make sure the editor is closed. Run `uv run scripts/server_contrib/contrib_pull.py --dry-run`. It prints what it would copy, per contributor, and the counts dropped.
  → verify: the output lists alice's files; no file in `gui2/data` changed (`git status --porcelain gui2/data` is the same before and after; compare with a saved copy); the entries kept for alice equal the number of entries in the server's `additions_alice.json` minus the ones whose `(key, hash)` is in the local `additions_added.json` (check by reading both with a short Python one-off). If a processed word would come back, stop and report it.

- [x] 5.5 **First real pull.** AGENT, editor closed. Run `uv run scripts/server_contrib/contrib_pull.py`.
  → verify: exit code 0; `logs/contrib_pull_status.txt` says `outcome: pulled` and `last_success:` is today; `gui2/data/additions_alice.json` equals the server's file minus processed words; `git diff --stat gui2/data shared_data db_tests` lists only expected files; `uv run python -c "import json;json.load(open('gui2/data/contrib_lines_merged.json'))"` succeeds. Run it a second time: the outcome is `skipped: already done today`.
  **Result (2026-11-04):** dry run listed alice's 4 files and 10 entries, changed nothing (hash of the data folders before and after equal); an independent Python check of the server file minus processed `(key, hash)` pairs gave 10 kept, 0 processed. The 2 local alice entries were identical on the server. Real pull: exit 0, `outcome: pulled`, `lines_added: 5`; alice's additions equal the server file byte for byte; the second run said `skipped: already done today`; the merged-lines log loads. Changed files (compared with the backup in the scratchpad): alice's additions, checked and manual corrections files, the merged-lines log, and the shared `checked.csv` (+4 lines) and `manual_corrections.tsv` (+1 line). The review logs and the deva files are untouched. Backup: `<scratchpad>/pull_backup_real/`.
  Undo if wrong: copy the files from `<scratchpad>/pull_backup/` back by name, including the six shared files under their paths. The agent never uses a git restore command.

- [x] 5.6 **Phase gate.** `uv run pytest tests/scripts/server_contrib -q` and `just typecheck`.
  → verify: zero failures, zero type errors.

## Phase 6 — The timer, the recipes, the docs — *Sonnet*

- [x] 6.1 **Unit templates.** Create `scripts/server_contrib/dpd-contrib-pull.service` and `scripts/server_contrib/dpd-contrib-pull.timer`.
  - Service: `Type=oneshot`; `WorkingDirectory=@REPO@`; `Environment=PATH=@HOME@/.local/bin:/usr/local/bin:/usr/bin:/bin`; `Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus`; `ExecStart=@UV@ run --no-sync scripts/server_contrib/contrib_pull.py`. No other lines.
  - Timer: `OnCalendar=*-*-* 08..22:00,30:00`; `Persistent=true`; `WantedBy=timers.target`.
  → verify: `systemd-analyze verify` on both files after filling the placeholders with the real values prints nothing; `systemd-analyze calendar '*-*-* 08..22:00,30:00'` lists the next elapse times and the first one is at :00 or :30.

- [x] 6.2 **Recipes.** In `justfile` add above `contrib-merge` the comment `# Replaced by contrib-pull (the daily timer). Do not run both.`; add recipe `contrib-pull` (`uv run scripts/server_contrib/contrib_pull.py`) and recipe `contrib-pull-install`: fills `@REPO@` (the repo root), `@HOME@`, `@UV@` (output of `command -v uv`) into the two templates, writes them to `~/.config/systemd/user/`, runs `systemctl --user daemon-reload` and `systemctl --user enable --now dpd-contrib-pull.timer`. Keep each recipe to a few lines.
  → verify: `just --list | rg contrib-pull` shows both; `just --dry-run contrib-pull-install` prints the steps without running them.

- [x] 6.3 **Install and prove it with the unit's own environment.** AGENT. Run `just contrib-pull-install`. Then `systemctl --user list-timers dpd-contrib-pull.timer --no-pager` and `systemd-run --user --wait --collect --property=WorkingDirectory=<repo> --property=Environment="PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin" $(command -v uv) run --no-sync scripts/server_contrib/contrib_pull.py --dry-run`. Do not run the real pull here; the `systemd-run` command passes `--dry-run` as its last argument so it adds no state.
  → verify: the timer is listed with a `NEXT` time; the `systemd-run` command exits 0 and its output (shown with `journalctl --user -u run-*.service -n 20 --no-pager`) shows the script found `uv` and read the setting; `systemctl --user show dpd-contrib-pull.timer -p NextElapseUSecRealtime --no-pager` prints a time. The service `dpd-contrib-pull.service` first runs at the next scheduled time; it is proved in 8.5.

- [x] 6.4 **Notice test.** AGENT. From inside `systemd-run --user --wait` with the unit's `DBUS_SESSION_BUS_ADDRESS`, run `notify-send "DPD contributor pull" "test notice"`.
  → verify: exit code 0. Ask the owner only if no notice can be confirmed by exit code: ask "did a notice appear on screen". If it fails, record that the status file is the only signal.

- [x] 6.5 **README.** In `scripts/server_contrib/README.md` add a section "The daily pull" with: what it does in 6 lines, where the status file and log are, the manual command (`just contrib-pull`), how to read `outcome:`, how to undo a bad run (the OWNER can `git restore <file>` a named shared file; the contributor files can be pulled again), and a link to `NEW_SERVER_RUNBOOK.md`. Add the new files to the file table at the end of the README.
  → verify: `rg -n "The daily pull|NEW_SERVER_RUNBOOK" scripts/server_contrib/README.md` returns both.

- [x] 6.6 **Phase gate.** `uv run pytest tests/scripts/server_contrib -q`; `just typecheck`; `git status --porcelain` shows only files this thread touched plus the previously uncommitted ones from the server thread (list them).
  → verify: tests pass and the file list is written under this task.
  **Results 6.1 to 6.4 (2026-11-04):** `systemd-analyze verify --user` on the filled units prints nothing; the calendar gives 08:00, 08:30 ... 22:30 then 08:00 next day. `just --list` shows `contrib-pull` and `contrib-pull-install`. Installed: next run 08:00 IST today (it will skip, today is done). The `systemd-run` dry run exited 0 and the journal shows the script's output (`alice: would copy 4 files, 10 entries`). The installed `dpd-contrib-pull.service` was started once by hand: exit 0, `outcome: skipped: already done today`, no file written. Notice test: `notify-send` in a user unit with the bus address exits 0; the owner confirmed the notice popped up on screen.
  **6.6 Files touched by this thread's Phases 4 to 6 (listed by hand, no git command run):** `kamma/tech.md`, `kamma/threads/20261023_contrib_1_web_server/plan.md` and `handoff.md`, `scripts/server_contrib/contrib_pull.py` (new), `scripts/server_contrib/merge_contrib_files.py`, `scripts/server_contrib/dpd-contrib-pull.service` (new), `scripts/server_contrib/dpd-contrib-pull.timer` (new), `scripts/server_contrib/README.md`, `justfile`, `tests/scripts/server_contrib/test_contrib_pull.py` (new), `tests/scripts/server_contrib/test_merge_contrib_files.py`. Data changed by the first real pull: `gui2/data/additions_alice.json`, `checked_alice.csv`, `manual_corrections_alice.tsv`, `contrib_lines_merged.json`, `shared_data/deconstructor/checked.csv`, `shared_data/deconstructor/manual_corrections.tsv`; new `logs/` files are ignored. Previously uncommitted from the server thread: spec.md, plan.md, handoff.md, `scripts/server_contrib/README.md`, `artifacts/`, `egm_pull/`, `pull_spec.md`.

## Phase 7 — The new-server runbook — *Sonnet*

Read first: `scripts/server_contrib/README.md`, `scripts/server_contrib/server_setup.sh`, `scripts/server_contrib/nginx_contrib.conf.template`, `scripts/server_contrib/nginx_contrib_user.conf.template`, `scripts/server_contrib/nginx_status.conf.template`, `scripts/server_contrib/add_contributor.sh`, `scripts/server_contrib/dpd-gui@.service`, `scripts/server_contrib/config_server.md`, and the plans `kamma/threads/20261101_contrib_6_e2e_server_test/plan.md` and `kamma/threads/20261023_contrib_1_web_server/plan.md` (the 2026-11-03 notes hold the fixes that older text lacks). The document is `scripts/server_contrib/NEW_SERVER_RUNBOOK.md`.

- [x] 7.1 **Skeleton.** Write the top of the file: purpose in 3 lines; the audience rule ("assume you know nothing about this project"); the executor rules from the spec (never print a secret file or environment; detach anything over 60 s with `setsid nohup ... &` and a bounded wait; never `pkill`; one change then its check; back up a system file before editing; on any mismatch stop and report the exact error); a table of placeholders (`NEW_IP`, `DOMAIN` = `<NEW_IP with dots as dashes>.sslip.io`, `SSH_TARGET` = `root@NEW_IP`, the contributor list) with how to obtain each; a legend of WHO values (`OWNER`, `AGENT`); the 12-step list as a table of contents. Mark the whole file's status line: `Not rehearsed end to end on a fresh machine; steps marked UNTESTED were not run.`
  → verify: the headings for steps 1 to 12 exist (`rg -c "^## Step" scripts/server_contrib/NEW_SERVER_RUNBOOK.md` prints `12`).

- [x] 7.2 **Steps 1 to 5** (order, ssh, firewall, packages, config, first build). For every step write: `WHO`, the exact command lines, `CHECK` (a command) and `EXPECT` (exact output). Take every command from a script or from the 2026-11-03 notes in the server thread: the keys-only drop-in file (`01-dpd-keys-only.conf` with its three lines and why it must sort first), the safety timer for the firewall (`systemd-run --on-active=5min --unit=dpd-ufw-deadman /usr/sbin/ufw disable`, cancelled only after a fresh login works), `timedatectl set-timezone Asia/Colombo`, swap (read the size from the README and `server_setup.sh`), `scripts/server_contrib/server_setup.sh`, `config.ini` entered by the OWNER (mode 600, the agent never reads or prints it; list which sections the server config template needs from `config_server.md`), and the first database build run detached with a bounded wait.
  → verify: each step has the four labels (`rg -c "^\*\*WHO" scripts/server_contrib/NEW_SERVER_RUNBOOK.md` is at least 12); every command that names a script or file path exists (`ls` each one); every EXPECT that can be read on the live server (for example `sshd -T` values, `ufw status`, the zone) was checked read-only against `epitaka` and the result noted next to it. Steps not checkable that way are marked `UNTESTED`.

- [x] 7.3 **Steps 6 to 9** (service, nginx, certificate, contributors, deploy key, cron, restricted key). Cover: the unit (`FLET_WEB_APP_PATH=%i` already in the template), the site file and the per-user files made by `add_contributor.sh` (path prefix, no trailing slash on `proxy_pass`), the sslip.io name needing no DNS, certbot with port 80 open and the `certbot renew --dry-run` check, the status block and the maintainer's own login (the file `/status` uses), moving the old server's `/var/lib/dpd/contrib_data`, htpasswd files and env files with `rsync` before it closes, running `add_contributor.sh` for each new one (the htpasswd group is set by the script), the deploy key with both `git remote set-url --push` and `core.sshCommand`, the full cron line with `--data-dir`, `--status-file`, one `--instance dpd-gui@<user>` per contributor and the `PATH=` line above it, and the restricted pull key line (`restrict,command="/usr/bin/rrsync -ro /var/lib/dpd/contrib_data" <pub key>`) with the key fetched from the laptop's `~/.ssh/dpd_contrib_pull.pub`.
  → verify: same three checks as 4.2. Also confirm by reading the live server that the cron line, the unit, the site file and one user file match what the runbook says (`crontab -l`, `systemctl cat dpd-gui@alice`, `nginx -T` lines for the status block and the user block).

- [x] 7.4 **Steps 10 to 12** (laptop side, outside check, cutover and retirement). Step 10: the OWNER changes `[epitaka_server] ssh` in `config.ini` to the new `user@host` (the agent must not edit it); the agent then runs `just contrib-pull` once. Step 11: the page of each contributor loads at the new address, `/status` says `rebuilt`, the first pull brings a test word; give the exact `curl -u` commands using a password read from a file the agent does not print. Step 12: tell contributors the new address; on the OLD server stop the cron job first (so two servers never push the `contributions` branch), keep a backup of the old data folder, then decommission.
  → verify: same three checks as 4.2.

- [x] 7.5 **Link and folder docs.** Add a one-line link to the runbook at the top of `scripts/server_contrib/README.md` ("Setting up a new server: see `NEW_SERVER_RUNBOOK.md`"). If `docs/technical/project_folder_structure.md` lists `scripts/server_contrib/` files, add the new files there.
  → verify: `rg -n "NEW_SERVER_RUNBOOK" scripts/server_contrib/README.md` returns a line; `rg -n "contrib_pull" docs/technical/project_folder_structure.md` returns a line if that file lists the folder, else the task notes "file does not list this folder".

- [x] 7.6 **Phase gate.** Re-read the runbook from the top as if you knew nothing. Write under this task every place that needed a guess and fix each one.
  → verify: the list is written under this task, each item names the edit that fixed it, and a second read-through finds no new item.
  **Results Phase 7 (2026-11-04):** `NEW_SERVER_RUNBOOK.md` written (12 `## Step` headings, 12 `**WHO` lines, status line as specified); linked at the top of the README and in its file table; `project_folder_structure.md` lists only folders (`server_contrib` is there), so it needs no change. Every script, template and path the runbook names exists (`ls`). Read-only checks on `epitaka`: time zone, `sshd -T` values, `ufw status`, swap, cron line, git push URL and `core.sshCommand`, nginx site and status block, file modes and groups, `certbot` timer and certificate, status page text, public 401 on `/alice/` and `/status`, `rrsync` restriction proved in 5.3. Run locally: the nginx name fill and the `/status` insertion script on a scratch copy (output equals the live site's block), and the detached launch plus wait-loop quoting with a fake `ssh`.
  **UNTESTED (marked in the file):** swap creation, the web package install, unattended-upgrades install, the first certificate (standalone with stop/start hooks; the live server uses the nginx authenticator and how it was first issued is not recorded), deploy key creation and its GitHub write access, and everything on a truly fresh machine.
  **Places that needed a guess, and the fix:** (1) the heading count was 13 because of a `## Steps` heading: renamed to `## The 12 steps`. (2) The site file said the server name appears three times; it appears four: corrected. (3) Step 3c EXPECT had a confusing second sentence: rewritten. (4) The cron step and the old server's cron could both push `contributions`: 8d now says to do it after 12c while the old cron runs. (5) Step 11 used password files with no way to make them: command added. A second read of Steps 1 to 4 found nothing new.

## Phase 8 — End-to-end cycle proof, real onboarding and wrap — *Sonnet*
⚠️ MODEL SWITCH REQUIRED (Sonnet): mechanical execution resumes.

- [x] 8.1 Full-cycle rehearsal, maintainer playing contributor: add 2–3 real
      words via the web GUI → the next morning's pull (Phase 6) copies them to the
      laptop, no merge → maintainer processes the queue in desktop gui2 → data-update
      commit to main → next window rebuilds → words present in server db,
      contributor JSONs emptied by reconcile, nothing lost.
      → verify: every arrow evidenced (pull status file, `additions_added.json` entry,
      server db query for the new lemma, empty contributor JSON).
      **8.1 evidence so far, 2026-11-04:** (1) the owner added 10 words as alice on 2026-11-03 (server file last written 21:04); the first real pull at 06:30 brought all 10. (2) At 07:48 the owner saved one NEW word on the web page (`anekasataṭhāna`, key `alice_10000012`, id 10000012, with an exception line `construction: needs na` / 10000012); the pull at 07:49 (status file moved aside, editor closed) brought it: `outcome: pulled`, `alice: pulled 4 files, 11 entries`; alice's additions file equals the server's byte for byte; the reserved-id exception line was kept and not merged into the shared tests file (`lines_added: 0`, no shared file changed against the backup). This also proves a real word saves on the web page (problem 25 in the problem children thread). (3) 2026-11-04 ~08:30 the owner processed alice's words in Pass2Add: `additions_added.json` now has 52 rows, the last three `alice_10000010`, `alice_10000011`, `alice_10000012`, all with a hash; `anekasataṭhāna` is in the local db as id 90386; the exception for it was added to the real test as 90386 (the editor printed `Added exception 90386 to test 'construction: needs na'`); alice's local file keeps only `alice_10000002` and `alice_10000003`, the two words that were already headwords (problem 12). Seen in the owner's start-up output, not caused by this thread: `[Errno 98]` on 127.1.1.1:8080 (an older `exporter.webapp` uvicorn from Nov 1 holds the port, harmless) and Chromium zygote "Broken pipe" lines when links open in the existing browser. (4) The owner clicked Reject on the two leftovers (Reject was there; it shows only right after the queue button loads a word): review log 54 rows, the last two `rejected` with hashes; alice's local file empty. (5) Commit pushed; GitHub `main` = 6df9a1b6 with the 54-row log. (6) Manual window run on the server 2026-11-04 13:47 to 14:22 (35 min, started detached with cron's PATH, `setsid nohup`, pid file, bounded wait): stop alice, pull (HEAD 34ee153f to 6df9a1b6), `reconciled: {additions_alice: 0, checked_alice: 0, manual_corrections_alice: 0, db_test_exceptions_alice: 0}`, `contrib_push: pushed 1 changed files`, db rebuilt from tsv 13:48, components generated 14:22:31, health check passed, WAL re-applied, alice restarted. `/var/lib/dpd/status.txt`: `outcome: rebuilt`, commit 6df9a1b6, `problems: 0`. `last_built_commit` = HEAD = 6df9a1b6. Server db: 89,783 headwords, `anekasataṭhāna` present as id 90386, 0 rows with a reserved id (10000000 and up), file 925,519,872 bytes. Alice's files on the server: `additions_alice.json` is `{}` (2 bytes), the flag files are 0 bytes. A copy of the data folder taken before the run: `/root/mem/contrib_data.before_manual_window_20261104`. ALL ARROWS EVIDENCED.
- [~] 8.2 Failure drills: (a) browser closed mid-edit + laptop-sleep
      reconnect; (b) a second tab for the same user (must be refused) and how
      long a closed tab blocks a new one; (c) a night where main did not move
      (no rebuild) and a night with an unmerged PR (nothing dropped). Document observed behavior + the contributor guidance ("if the
      page goes grey, reload") IN THIS FILE and in 8.3's doc.
      → verify: written results for all three drills; no data loss in any.
      RUN 2026-11-03 with throwaway user `probe4` (port 8558), headless
      browsers, removed afterwards (no probe file left in contrib_data):
      (a) browser closed: the websocket count drops to 0 at once; a new tab
      loads the app fine. The unsaved form is gone (a new session starts at
      Pass1Auto). Network off for 25 s, then on: the page comes back as a
      NEW session (element refs changed), one websocket, again the empty
      Pass1Auto screen. So an unsaved word is lost on any reconnect.
      A real laptop sleep was not tried.
      (b) second tab: the plan's "must be refused" is wrong. The NEWEST tab
      takes the session and works; the OLD tab is retired and shows "This app
      is already open in another tab or window." A closed tab never blocks a
      new one (the new tab always takes over).
      (c) FIRST CRON RUN 2026-11-04 01:00: outcome `failed`, 48 s. The push
      worked (contributions branch commit 78d9dcc9, 4 gui2/data files for
      alice) but the rebuild died with `No such file or directory: 'uv'`:
      cron's default PATH has no `/root/.local/bin`, and `maintenance_window.py`
      runs `uv` by name (lines 125 and 133). Rollback worked (db, tree and
      contributor files restored, alice restarted, active). Fixed on the
      server by a `PATH=/root/.local/bin:...` line at the top of the root
      crontab (old crontab in `/root/mem/security_fix_20261103/crontab.before`);
      README cron line updated. PROVED 2026-11-04 04:11 by a manual run under
      `env -i` with cron's PATH and shell: `rebuilt` in 30 min (04:11→04:41),
      health check passed, problems 0, last_built_commit 34ee153f, alice
      active, contributions branch pushed again (4 files). Not yet proved:
      the real 01:00 cron run itself (due 2026-11-05). 3.6's "happy path verified" ran by hand, so it never met
      cron's environment.
      Not run: a real word saved from Pass1Add. Typing into Flutter fields
      through the browser tool did not take (`fill` on the lemma field left
      "buddha 1"), so the cloned word was refused as a duplicate ("buddha 1
      already in db", shown under lemma_1). That refusal itself works.
      Preview behind the prefix: `/probe4/preview/preview_alice.html` returned
      200 (60 KB), root `/preview/preview_alice.html` 404. The page URL is
      relative, so it should resolve to `/<user>/preview/…`; the click path
      itself (button → new window) is NOT proved. A missing preview file under
      the prefix answers 200 with the app shell (3.8 KB), not 404.
      ⚠️ CONFIRMED GAP: all instances share `gui2/assets/preview/`, and the
      files are named `preview_<user>.html`, so `probe4` could fetch
      `preview_alice.html` through its own prefix. Content is a dictionary
      entry not yet saved; low risk. Not fixed (needs a gui2 change, owner to
      decide): a per-user assets folder or an unguessable file name.
      Noticed, not investigated: each fresh session logs `decon cache refresh
      failed: attempt to write a readonly database` (INSERT into db_info). The
      contributor server opens the db read-only on purpose, so this is
      probably expected, but nobody has said so. Also, the service log lags
      by minutes (Python stdout is buffered under systemd), so judge a session
      by the screen, not by the log.
- [x] 8.3 DROPPED 2026-11-04 (owner): no written contributor page and nothing in the docs or in `scripts/onboarding/README.md`. The owner makes an onboarding video that guides each contributor through everything. The draft stays in `artifacts/web_gui_draft.md`, marked archived. Original task text follows. Contributor-facing instructions (DRAFT in `artifacts/web_gui_draft.md`, not published; two TODOs for the maintainer): ONE paragraph + screenshots at
      `docs/contributing/web_gui.md`, written for the real audience: the URL,
      the password, "bookmark it", who to call. Add banner to
      `scripts/onboarding/README.md`: non-technical contributors use the web
      version (legacy flow stays documented below it).
      → verify: user approves the text; ideally one non-technical reader test.
      **CHANGED 2026-11-04 (owner):** the page is NOT public and does NOT go into the docs. It holds a private address and login, so it is sent privately to each contributor. `docs/contributing/web_gui.md` and the banner in `scripts/onboarding/README.md` are dropped. The draft in `artifacts/web_gui_draft.md` stays as the working text and keeps being updated. The two TODOs in it are the owner's to fill.
- [ ] 8.4 **Changed 2026-11-04:** onboarding is the owner's video, not a text page; the address will move to a new domain (planned `contrib.dpdict.net`; the runbook already covers another domain: its A record must point at the server before the certificate step, and Step 12 tells contributors the new address). The tabs each contributor sees are set per user in their env file (`DPD_GUI2_TABS`), so the video covers them. Onboard contributor #1 (real person, India or Singapore) over a
      call; watch, note friction, fix. Then contributor #2 without watching.
      → verify: #1 completes a real Pass1 word unaided after the call;
      #2 onboards with zero live help.
- [ ] 8.5 **The first scheduled pull** (from the pull work). AGENT, the morning after Phase 6 is installed, after 08:00: read `logs/contrib_pull_status.txt` and `logs/contrib_pull.log`; check `systemctl --user list-timers dpd-contrib-pull.timer --no-pager`.
      → verify: the status shows `outcome: pulled` or `skipped: already done today` with `last_success:` of that day, with no step taken by the owner. If the laptop was off at 08:00, the log shows the run at wake-up. Also run 8.1's loop with the pull: the words reach the editor's queue with no manual merge.
- [x] 8.6 **Review.** Read `egm_pull/gate3.md` and confirm each Blocker and Major is fixed in Phases 4 to 7 (its disposition table has no `Accept` row with an empty "Where fixed"). Ask the owner whether to run `coderabbit review --agent` (`--uncommitted --include-untracked --dir scripts/server_contrib`, and a second pass on the tests folder). Run it and a from-scratch audit of the plan as parallel reviewers, with no edits to the tree meanwhile. Apply only findings checked against the code.
      → verify: each finding is recorded here with its decision.
      **8.6 part 1 done 2026-11-04 (Gate 3 check):** G3.1 `run` takes a `SharedFiles` argument and every test builds one from copies under `tmp_path`; a full `tests/scripts/server_contrib` run changed no file in `shared_data`, `db_tests`, `gui2/data` or `logs` (timestamp check). G3.2 undo is by copying back from the scratchpad backup (made in 5.4, six shared files included); no git restore was run. G3.3 test (a) uses a JSON list and passes. G3.4 `main` prints the status, also for `--dry-run` (seen in 5.4). G3.5 verified on the transient `run-*.service` unit and on the real service started once by hand (6.3). G3.6 `ignored_names` counts them. G3.7 `REMOTE_SOURCE_SUFFIX` was a placeholder; 5.3 proved `":"` works. G3.9 symlinks are listed with an `l` mode (4.1) and refused. G3.11 the listing is unfiltered and `select_names` filters; the spec text was left as is. **8.6 part 2, 2026-11-04 (owner said yes):** CodeRabbit (`--uncommitted --include-untracked --dir scripts/server_contrib`, free CLI allowance, 6 findings, not reused) and a pi DeepSeek review (`deepseek-v4-pro`, thinking max, read-only, smoke-tested first: PONG in 2 s; the review took about 5 min, no hang) ran in parallel with no edits meanwhile. The pi input was the source files read directly, no git. Decisions, each checked against the code:
  - FIXED: header-less variant/spelling file silently lost its first row (merge slices line 1 unconditionally): `check_content` now requires the header (DeepSeek M1). Empty field in a two-column line refused (m8).
  - FIXED: `ValueError` (a JSON error from the merged-lines log) escaped `run` as a traceback: now a recorded `failed` (M2).
  - FIXED: no deadline on the listing: listing gets `--timeout=60`, every rsync call has a 300 s limit, ssh gets `ConnectTimeout=30` (CodeRabbit major, m9). Copy gets `--max-size` (m5).
  - FIXED: a day pulled with problems never got its notice (the 22:30 run is skipped as already done): `pulled with problems` now notifies at once; `failed`/`partial` still at 22:30 (CodeRabbit major, reworded). Spec step 7 and README updated.
  - FIXED: the ignored-name log line is redacted (m4) and not written in a dry run (m10).
  - FIXED in the runbook: the old deploy key is no longer deleted before the old cron stops (it is deleted in 12f); the wait loop waits for a fresh PID file (`rm -f` first, then `test -s`); step 11c warns that 12c wipes a test word; README maintainer section marked as replaced.
  - New tests: header missing, empty field, problem notice at once, failed run before 22:30 silent, remote command carries the fixed ssh options and the deadline, local source has no `-e`, hanging rsync = failed, merge JSON error = failed, corrupt merged log = failed, dry run writes no log, deleted shared line does not come back (guards the log wiring). Revert checks: header check removed = 2 failures; `ValueError` removed = 1; problem notice made late = 1; deadline removed = 1.
  - REJECTED: DeepSeek m3 (non-UTF-8 names crash the run): wrong. rsync prints odd bytes as `\#377`, so decoding never fails; the name is ignored and counted (test added). n2 (DEL character): the spec says below U+0020. n1 (fsync): same pattern as the existing atomic writers, laptop power cut on a tiny log; not worth the extra code.
  - NOTICED, NOT TOUCHING (existing code, not this thread's change): `merge_user_dictionary` and `merge_two_column` rewrite the shared files in place, so a kill mid-write can truncate them (git holds the old copy; the merged-lines log would then call the lost lines handled) (m6). `DbTestManager.save_tests` prints an `OSError` and returns, so a failed write of the tests file looks like success (m7). Both are worth a small follow-up thread; the pull makes them more exposed because the merge now runs daily.
  - Not done from n3: a test that `main()` writes `notice_error` back to the status file.
- [ ] 8.7 Thread wrap: update `kamma/tech.md` (+ `conductor/tech-stack.md` if
      needed) with server facts (provider, IP, ports, window time, runbook
      location, the pull: script, timer, key, status file); `docs/technical/project_folder_structure.md` if
      `scripts/server_contrib/` description changed; final lint/type/test sweep;
      list here the uncommitted files for the owner's commit.
      The spec's two-week success criterion starts counting; thread finalize
      per `/kamma:4-finalize` when review passes (skip the GitHub step: never comment on or close issue #215).
      → verify: docs updated; `uv run pytest tests/` clean; `just typecheck` clean.
      **8.7 progress 2026-11-04:** `kamma/tech.md` has the pull note and a server-facts note (provider left out: not recorded anywhere I could read). Full sweep: `uv run pytest tests/ -q` = 2840 passed, 12 deselected, 1 FAILED: `tests/scripts/server_contrib/test_maintenance_window.py::TestHappyPath::test_status_file_reports_a_failure_and_its_reason` (`problems: 0`, expected `problems: 1`). Not reproduced: the same file passed 3 times alone and `tests/scripts` passed 2 times together (327 tests); neither the test nor `maintenance_window.py` was touched by this thread. Unexplained, recorded as problem 27; do not call it environment noise without more runs. `just typecheck` 0 errors. Still open for 8.7: the final uncommitted-file list (after 8.1, 8.4 and 8.5) and finalize.
      **Blind read of the runbook 2026-11-04** (a fresh agent with no context, read-only; 20 points; verdict "not ready"). Checked against the files and the live server; all applied: (1) the new server never got its cron job (8d was skipped, nothing came back to it): new Step 12c2. (2) the certificate hook starts nginx with no site, so `systemctl start` in 7d did nothing: now `restart`. (3) Step 10 pointed the daily pull at the new server before cutover, so an older copy could overwrite newer laptop files: Step 10 now says do it after 12c, or stop the timer first. (4) 12c copied over data that live new instances held: instances stopped, the new data moved aside (not deleted), then copied. (5) copied users have passwords the owner never typed: 11a checks only the 401 for them; new users use the same password in the file. (6) long waits are killed by the tool shell: sliced waits of 110 s with `JOB_ENDED`/`STILL_RUNNING`. (7) swap step had no fstab backup and no re-run guard. (8) recovery text for `authorized_keys` was garbled: restore the backup copy. (9) STEP 6A EXPECT WAS WRONG: I had written "checked on epitaka" without running it; `systemctl cat` prints `%i` unexpanded. Fixed after running it on the server. (10) placeholders must be replaced: one line added. (11) 7a or 7b, never both. (12) config template: placeholder text, `umask 077`, `shred`. (13) apt lock timeout. (14) owner confirms the scripts are on `main`. (15) `grep -c` exit status. (16) newline check on `authorized_keys` (live: `0a`). (17) keep the entry count before the test. (18) `mkdir -p ~/backups` and the server count. (19) password reaches `curl` through stdin; rule 10 names the one allowed read. (20) restart cron after the zone change. Tested locally: the curl stdin form, and the sliced wait for a finished and a running job.

## Explicitly deferred (do NOT do in this thread)

- Multi-user shared-memory gui2; >3 contributors; packaged desktop app.
- Fixing or deleting the legacy `scripts/onboarding/` flow (known defects are
  listed in the spec — leave them).
- Any dpdict.net change.
- Pass2 tab polish beyond "doesn't break in web mode" (record-only in 1.5).
