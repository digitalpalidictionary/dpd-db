# Plan: contributor problem children

**Thread:** 20261030_contrib_x_problem_children · **Spec:** `spec.md`
**GitHub issue:** #215

Triage done 2026-11-05 with the owner, one item at a time. Each task below is a
decision the owner made. Code state was read the same day; nothing was run.
Do not write GitHub comments. Do not commit.

## Tasks to build

- [ ] 1 Item 2: wrap both `ft.Clipboard().set(...)` calls in `gui2/pass2_add_view.py` (~1066, ~1344) so a refused copy never stops the rest of a save.
- [ ] 2 Item 15: make `PREVIEW_DIR` (`gui2/assets/preview`) in `gui2/main.py` before `ft.run`. `write_preview()` makes it only after start.
- [ ] 3 Item 16: skip `save_decon_no_headwords_cache` in `gui2/database_manager.py` (~391) when the db is read-only, so no "refresh failed" warning prints.
- [ ] 4 Item 28: remove the helper web server start. Owner: gui2 no longer uses it (preview is internal code). Checked 2026-11-05: only `gui2/main.py:746` calls `start_dpd_server`; `request_dpd_server` is called only from `archive/`. Remove the call, the dead code in `tools/fast_api_utils.py`, and its tests (`tests/tools/test_fast_api_utils.py`, the two monkeypatches in `tests/gui2/test_main.py`). Keep the `justfile` webapp recipe. `exporter/wxt_extension/wxt.config.ts` lists `127.1.1.1:8080`; owner says the extension is not used against a gui2-started server.
- [ ] 5 Item 9 (cache): call `mark_corpus_stale()` in `rename_pattern_in_headwords` (`gui2/database_manager.py` ~795). Add a test.
- [ ] 6 Item 6: remove the unused `additions_manager` and its import from `gui2/pass1_add_controller.py` (lines 8 and 48 only; nothing else uses it).
- [ ] 7 Item 30: send the desktop notice on every "editor open" skip (`contrib_pull.py` ~476, ~526). Owner confirmed 2026-11-05: every time, as he asked. The "already done today" and "another run" skips are not covered.
- [ ] 8 Item 10: audio in the preview, DESKTOP ONLY. Today the play request (`/audio/<word>`, `exporter/webapp/main.py:348`, reads the 1.2 GB audio db) has no server behind the saved preview page. Needs a design before code: how gui2 on the laptop serves or embeds the audio. Hide the button on the server and for words with no audio. A new word has no audio. Owner wants to hear what problems come up.
- [ ] 9 Item 21: the nightly window deletes `dpd.db.prev` and `_contrib_worktree/` after a good run. A failed run keeps them. The old safety copies in the server's `/root/mem` are a one-off command for the owner, not a script step.
- [ ] 10 Item 9 (username): make `is_not_primary()` (`gui2/user.py`) and `resolve_username() or "1"` (`gui2/toolkit.py:52`) use one value. Add a test.
- [ ] 11 Read-only tabs (DB, √, Infl): grey out Save Changes instead of showing the "read only" message.
- [ ] 12 DB tab starter preset (contributors): one filter, `lemma_1`. Columns shown: id, pos, grammar, meaning_1, meaning_2, meaning_lit. Today the starter is root fields.
- [ ] 13 Alt shortcuts: turn them off in the WEB version only. The desktop app keeps them. Owner confirmed 2026-11-05. Maybe later a section to customize shortcuts. Keys in use: Alt+G T P E D S B R C I X, Alt+?, Alt+Left/Right (`gui2/main.py` `on_keyboard`). Chrome's official list confirms only Alt+Left/Right; Alt+D, Alt+E, Alt+F are from memory and unverified.
- [ ] 14 Item 27: investigate the one failure of `tests/scripts/server_contrib/test_maintenance_window.py::TestHappyPath::test_status_file_reports_a_failure_and_its_reason`. Read how the status writer (`maintenance_window.py` ~181-208) picks the day's log lines. Run the suite a few times.
- [ ] 15 Item 13: a contributor changes their own password. Owner wants it. A feature, not a fix: needs its own spec (login is nginx basic auth today).

For every file touched: `ruff check --fix`, `ruff format`, `pyright`, related tests, then `just typecheck`.

## Dropped, with the reason

- Item 1: project rules already give the working start command. Only old thread text shows the broken one.
- Items 3, 5, 7, 8: contributors see only Pass1 Add plus safe or read-only tabs (`gui2/contributor_tabs.py`). Pass2 and the db-write tabs are hidden. The db-manager write guard is not built; nothing needs it today.
- Item 4: contributor ids come from a reserved range (`CONTRIB_ID_BASE`, `get_next_id`). Owner: contributor ids are in the 100 000s, so a clash cannot happen. The real-merge test is dropped.
- Item 11: keep the `contributions` branch. The server already works this way.
- Item 12: Reject works as designed. Leave Delete as it is.
- Item 14: owner said no test run. Unit tests cover the paths.
- Items 17, 18, 25: fixed or settled (see spec).
- Item 19: owner accepts the risk (an unsaved entry, few trusted contributors).
- Items 20, 22, 23, 24: accepted trade-offs or tool limits.
- Item 26: minor, not asked.
- Item 29: owner: "from now on I will handle all Pass1 Auto; the tab itself is deleted from the server". Not checked in code that the tab is gone.

## Parked, not asked (low value; tabs are hidden)

- Item 6: duplicate word in the checked file; `item_to_history` "possibly unbound"; the pyright errors in gui2; per-user files and the nightly push (the file kinds list was not read in full).
- Item 9: an overlay correction that renames `lemma_1`; `update_db_fields` keeping old values; `get_next_id` on a non-numeric id; no header row in the variants and spelling files; the DB tab duplicate-lemma check ignoring the overlay; no tests for the Pass2 own-edit view methods.
- Item 9: `request_dpd_server` in a contributor save is moot once task 4 lands.
