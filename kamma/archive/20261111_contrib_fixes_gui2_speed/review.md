## Thread
- **ID:** 20261111_contrib_fixes_gui2_speed
- **Objective:** Fix the contributor-server faults from the #215 review (preview latch, rollback order, failed start, pull line check), cut server memory, and take only measured laptop speed gains.

## Files Changed
- `gui2/preview.py` — per-page preview latch (`_owner` + `retire_page`), retired pages cannot save
- `gui2/main.py` — takeover closes the old page's dialogs and (server only) releases the old app; `_session_app` registration; view imports moved into per-tab builder methods; `_released` guards in db-init/warm-up; `release_session` retires the preview latch
- `gui2/daily_log.py`, `gui2/filter_presets_manager.py` — damaged JSON → `.corrupt` + red line; saves via `.tmp` + `replace`
- `gui2/database_manager.py` — decon set skipped on server; `release_memory()` (+ `_released` flag, checked by `initialize_db` and the detector worker); `note_new_lemma()`
- `gui2/pass1_auto_controller.py` — `ai_manager` is now a `functools.cached_property`
- `gui2/pass1_add_controller.py` — new words call `note_new_lemma`, edits keep the full reread; pre-existing `book_to_process` type errors fixed with `cast` (no runtime change)
- `scripts/server_contrib/maintenance_window.py` — rollback: contributor files first, per-step guards, db copied to `.restoring` then `os.replace`; failed/timed-out start fails the run; `_systemctl` catches per unit and continues
- `scripts/server_contrib/contrib_pull.py` — rejects a lone `\r` (`carriage return inside a line`)
- `scripts/server_contrib/dpd-gui@.service`, `scripts/server_contrib/README.md` — `MemoryHigh=1500M` / `MemoryMax=2G` + docs bullet
- Tests: `tests/gui2/test_{preview,main,daily_log,filter_presets_manager,database_manager_decon_cache,database_manager_corpus,pass1_add_controller}.py`, `tests/scripts/server_contrib/test_{maintenance_window,contrib_pull}.py` — 30+ new tests, each seen failing first (pasted in `plan.md`)
- `kamma/threads/.../artifacts/` — `laptop_speed.md` (F1/F2), `detector_rebuild.md` (F3), probe scripts

## Findings

| # | Severity | Source | Location | What | Disposition |
|---|----------|--------|----------|------|-------------|
| 1 | major | own review | `gui2/main.py` `claim_session` | release sat inside the `previous is not page` guard: after a clean disconnect the held old app was never released (~500 MB leak on the server) | **Fixed** — moved outside the guard + regression test |
| 2 | major | DeepSeek #1 / CodeRabbit #3 | `gui2/database_manager.py`, `gui2/main.py` | retired app's background workers (db init, warm-up, detector worker) refill the freed memory; spec had accepted this race | **Fixed** — `_released` flag checked in `initialize_db`, `_detector_rebuild_worker`, `_warmup_in_background` (×2), `_initialize_db_in_background`; desktop-inert; 2 new tests |
| 3 | minor | DeepSeek #2 | `gui2/main.py` `release_session` | preview `_owner` kept a dead page (and its dialog graph) alive after a clean close | **Fixed** — `retire_page(page)` in `release_session` + test |
| 4 | minor | CodeRabbit #1 | `maintenance_window.py` `_systemctl` | one `systemctl start` timeout aborted the loop, leaving later contributors' editors down | **Fixed** — per-unit catch + continue + test |
| 5 | minor | CodeRabbit #2 | `gui2/main.py` `main` | an `App` that loses the session mid-build is registered nowhere and leaks | **Fixed** — released in the registration else-branch (server only) + test |
| 6 | minor | DeepSeek #3 | `tests/gui2/test_daily_log.py`, `test_filter_presets_manager.py` | atomic-save tests stayed green if `.tmp`+`replace` were reverted | **Fixed** — failing-write tests: with `json.dumps` raising, the previous file survives |
| 7 | minor | DeepSeek #4 | `tests/gui2/test_main.py` | stale test asserted the old hidden-Pass1Auto contract via lambdas not in the code | **Fixed** — removed; real coverage exists in the two `_make_pass1_add` tests |
| 8 | minor | DeepSeek #5 | `artifacts/laptop_speed.md` | "imports before first paint today" became false after task 6.2 | **Fixed** — clarified as the pre-change upper bound |
| 9 | nit | DeepSeek #6 | `daily_log.py`, `filter_presets_manager.py` | fixed `.tmp` name: two concurrent saves could interleave | **Skipped** — spec mandates the exact `AdditionsManager._save_dict` pattern (same exposure as existing code); saves are UI-event driven and rare |
| 10 | nit | DeepSeek #7 | `maintenance_window.py` rollback | "rollback of the database FAILED" logged when only the `-wal` unlink fails | **Skipped** — a leftover `-wal` replays over the restored db, so FAILED accurately describes a dangerous state |
| 11 | nit | DeepSeek #8 | `database_manager.py` `release_memory` | leaves `db_session` open | **Skipped** — plan says leave `db_session`; `new_db_session` deliberately never closes (in-flight query hazard on the shared engine); the OS releases on process exit |

## Fixes Applied
All of 1–8 above (12 edits, 10 new/changed tests). Rerun after fixes: full suite green, pyright clean, `just typecheck` 0 errors.

## Test Evidence
- `uv run pytest tests/gui2 tests/tools tests/scripts tests/db -q` (whole Python suite) → **2347 passed, 7 deselected** (slow-marked big-source tests excluded by default, as CI does)
- `just typecheck` (pyrefly, repo-wide) → **0 errors**
- pyright per touched file (`--project /dev/null` for gui2/tests, per repo rule) → clean; `gui2/main.py` at its documented 24-error baseline
- `uv run ruff check` + `ruff format --check` on all touched Python files → clean
- Every new behaviour test was seen to fail before its fix (outputs pasted in `plan.md`); revert checks for the gates (decon, AI, release, latch) recorded in `plan.md`
- `rg -n "/home/"` on the thread folder → clean (one artifact script rewritten before commit)

## Not Verified
- Live server behaviour (Phase 8): memory figures, two-tab takeover, preview-after-reload — runs on the host after the owner's push
- The `_released` guards are unit-tested; the real threaded race (takeover mid-load) was not reproduced live
- DeepSeek reviewed a diff taken before the review fixes landed (it noted this itself); every one of its findings was re-validated against the current tree by hand
- No manual GUI run on the laptop (plan forbids the agent starting gui2); the desktop-unchanged rule rests on the guard tests
- Independence: reduced — the same session implemented and co-reviewed; CodeRabbit and DeepSeek v4-pro (fresh context) were the independent passes

## Verdict
PASSED
- Review date: 2026-11-12
- Reviewer: own pass + CodeRabbit CLI + DeepSeek v4-pro (thinking high) via pi subagent
- Independence: reduced (same session as implementer; two external independent reviewers)
