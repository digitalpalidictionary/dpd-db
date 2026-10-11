# Plan: contributor edits kept in JSON, shown on top of the db

**Thread:** 20261007_contributor_edits_json · **Spec:** `spec.md` (read first)
**GitHub issue:** #215 — commits reference `#215`
**Prior thread:** `kamma/threads/20260719_contributor_web_server/` (spec + plan 1.1–1.6)

## Architecture Decisions
- **One save seam, one read seam.** All contributor/primary branching for
  saves lives in one function. The overlay lives in `DatabaseManager`'s
  single-word getters. Pass1Add/Pass2Add stop carrying their own db-vs-JSON
  logic. Whole-db queries are deliberately NOT overlaid.
- **Seam location:** new `gui2/save_router.py` (one function taking the
  toolkit, the word, the comment and whether it is an existing word). It is a
  separate module so it can be tested without Flet views.
- **Overlay = injected lookup**, set by ToolKit only when `is_not_primary()`.
  `DatabaseManager()` keeps its no-arg constructor, so user 1 is unchanged.
- **Gate server-only behaviour at the source** (`is_headless_server()` inside
  `open_tsv_for_editing`), as 20260719 did for GoldenDict.
- Not abstracted: no generic "user data layer" class. The additions and
  corrections managers stay the store.

## Phase 1 — Remaining per-user files
- [x] 1.1 `Gui2Paths.user_dictionary_path` (user 1 → `ProjectPaths().user_dict_path`;
      contributor → `gui2/data/user_dictionary_{u}.txt`, set in `for_user`).
      `CustomSpellChecker` (`tools/spelling.py`) takes optional
      `user_dict: Path | None`. It always loads the shared file, also loads
      `user_dict`, and writes `add_to_dictionary` to `user_dict` when given.
      Pass `toolkit.paths.user_dictionary_path` at `gui2/dpd_fields.py:70` and
      `gui2/filter_component.py:115` (read both constructors first). Add
      `gui2/data/user_dictionary_*.txt` to `.gitignore`.
      → verify: `uv run pytest tests/gui2/test_paths.py tests/tools/test_spelling.py`
      (create the spelling test if missing). A contributor add writes the
      per-user file only and the shared file is byte-identical; user 1 writes
      the shared file as today.
- [x] 1.2 `open_tsv_for_editing` in `tools/compound_type_manager.py` and
      `tools/phonetic_change_manager.py`: if `is_headless_server()`, raise
      `RuntimeError("not available on the server")`. The callers in
      `gui2/dpd_fields.py` already show RuntimeError text via `show_message`.
      → verify: unit test with `DPD_GUI2_ROLE=contributor-server` → raises and
      no subprocess is spawned (patch `subprocess`). Role unset → the old path runs.
- [x] 1.3 Phase gate: ruff check --fix, ruff format, pyright
      (`--project /dev/null` for gui2/tests files) on touched files + related tests.
      Report only, no commit.
      → verify: all clean. Paste the counts here.
      RESULT 1.3: ruff check clean, ruff format clean. `uv run pyright` on tools files: 0 errors.
      Baseline gui2 pytest before changes: 308 passed. Phase 1 related tests: 71 passed.
      PRE-EXISTING — NOT CAUSED BY THIS THREAD: `pyright --project /dev/null` on gui2/dpd_fields.py +
      gui2/filter_component.py reports 101 flet-typing errors (`_BaseControlType`, none on lines this
      thread touched). gui2 is excluded from the pre-commit pyright, so the hook does not see them.

## Phase 2 — Save seam, overlay, contributor delete
- [x] 2.1 `gui2/save_router.py::save_headword(toolkit, word, comment, is_existing) -> tuple[bool, str]`.
      User 1 → `db_manager.update_word_in_db` / `add_word_to_db` (unchanged).
      Contributor → an existing id in own additions (`additions_manager._key_for_id`)
      → `add_additions`; any other existing id → `corrections_manager.update_corrections`;
      new → `add_additions`. No db call. Returns (True, "").
      → verify: `tests/gui2/test_save_router.py` with fakes: user 1 calls the db
      methods only; a contributor calls the JSON methods only and the db fake
      records zero calls.
      DONE: 6 tests pass. A JSON write error (OSError) returns (False, message).
- [x] 2.2 Overlay in `gui2/database_manager.py`: `set_overlay(lookup)`.
      `get_headword_by_id` / `get_headword_by_lemma` return
      `make_dpd_headword_from_dict(entry)` (transient) when matched, corrections
      before additions. `get_all_lemma_1_and_lemma_clean` adds own additions'
      lemmas. `get_next_id` = max(db, own additions) + 1. ToolKit
      (`gui2/toolkit.py`) sets it after the additions/corrections managers
      exist, only if `is_not_primary()`. The lookup reads the managers' live
      dicts, so new saves show at once. Then read every `get_headword_by_*`
      caller (list in spec) for relationship use on the returned object, and
      log the findings here.
      DESIGN CHANGE (drift): `set_overlay(own_edits)` takes a callable returning
      `(corrections_dict, additions_dict)`. ToolKit passes a lambda, so the managers
      are built on first lookup. ToolKit gates on `username != "1"` (the same value
      that picks the per-user paths). Ids are compared as text in both overlay and
      `_key_for_id`, because form fields hold the id as int or str.
      CALLER FINDINGS: no `get_headword_by_*` caller in pass2_add_view, pass1_add_view,
      pass2_auto_control or dpd_fields reads `.rt/.fr/.fw/.it/.su`. They read plain
      columns, deepcopy, or compare `.id`. A transient word is safe for all of them.
      → verify: `tests/gui2/test_database_manager_overlay.py` on a temp sqlite db:
      own correction beats the db row; no entry → db row; own addition found by
      id and by lemma; next id skips own additions; no overlay → old results;
      the returned object has no session (`object_session(x) is None`).
- [~] 2.3 Wire the seam in: `gui2/pass1_add_controller.py::make_dpd_headword_and_add_to_db`
      (both branches; this also fixes a contributor re-edit writing no JSON)
      and `gui2/pass2_add_view.py::_click_add_to_db` (the update/add block at
      ~826-852). Keep every post-save step. Do not touch the user-1
      processed addition/correction blocks.
      DONE in code: both save sites call `save_headword`. Pass1 now keeps the id and origin
      logic and drops its own db/JSON branches. Live desktop run still PENDING (needs the user).
      → verify: `uv run pytest tests/gui2/`. Then a live desktop run
      (`uv run flet run gui2/main.py`) WITH the user: a Pass1Add add and a
      Pass2 edit as user 1 land in the db as before.
- [x] 2.4 Contributor delete (`pass2_add_view._click_delete_from_db` /
      `_click_delete_ok`): if `is_not_primary()`, then an own entry for the id →
      confirm → remove it from the additions/corrections JSON (add a small
      `discard(id)` to each manager) → reload from the db, or clear for an
      addition. No own entry → message "you can only discard your own edits".
      User 1 unchanged.
      → verify: unit tests for `discard` (right entry removed, others kept, file
      rewritten).
      DONE: 3 tests per manager. Added `CorrectionsManager.is_not_in_corrections` (mirrors
      the additions sibling). Pass2 view: `_has_own_edit`, `_discard_own_edit`. A discarded
      correction reloads the db row via the existing load button handler.
- [x] 2.5 Phase gate as 1.3 + `uv run pytest tests/`. Report only, no commit.
      → verify: full suite passes. Paste the counts here.
      RESULT 2.5: ruff check/format clean on all touched files. pyright (venv python) 0 errors on
      save_router, database_manager, toolkit, both managers and the 4 test files. Full suite:
      2022 passed, 12 deselected.
      PRE-EXISTING — NOT CAUSED BY THIS THREAD: pyright reports flet-typing errors in
      pass1_add_controller.py / pass2_add_view.py, and `item_to_history` "possibly unbound"
      (pass2_add_view.py ~852-865; it was only set in the else branch before this thread too).
      gui2 is excluded from the pre-commit pyright.
      NOTICED — NOT TOUCHING: `Pass1AddController.additions_manager` is now unused.
      NOTICED — NOT TOUCHING: `UsernameManager.is_not_primary()` is True when the username is
      None (desktop first run before the dialog). Such a session now saves to JSON only.

## Phase 3 — Live contributor check (local)
- [ ] 3.1 Back up `dpd.db` to the scratchpad first. Run
      `DPD_GUI2_USERNAME=alice DPD_GUI2_ROLE=contributor-server uv run flet run --web -p 8551 gui2/main.py`
      WITH the user. Pass1Add new word → `additions_alice.json` has it and
      `sqlite3 dpd.db "select count(*) from dpd_headwords"` is unchanged. Edit
      an existing word in Pass2 → correction JSON, db row unchanged, a reload
      shows own version. Re-edit own new word in Pass2 → saves. Delete own edit
      → db version returns. Delete a plain db word → refused. Add a spelling
      word → per-user file. Remove the test entries from alice's files after.
      → verify: every item logged here with the observed result.

## Phase 4 — Finish
- [ ] 4.1 Add a one-line note to 20260719 spec point 4: "superseded by
      20261007_contributor_edits_json: contributors no longer write the db".
      Update `gui2/README.md` (contributor saves go to JSON; user 1 unchanged).
      Run `just typecheck`, full pytest and `graphify update .`.
      → verify: all pass. Paste the counts here.
