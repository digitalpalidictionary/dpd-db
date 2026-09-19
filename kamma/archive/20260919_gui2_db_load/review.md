## Thread
- **ID:** 20260919_gui2_db_load
- **Objective:** Reduce gui2 `DatabaseManager.initialize_db()` db-loaded wait (baseline 6.90 s median; target ≤ 4 s).

## Files Changed
- `gui2/database_manager.py` — decon cache read/fallback/self-heal in `get_all_decon_no_headwords`; eager detector build removed from `initialize_db`; double-checked lazy detector init; docstring corrections (`is_db_loaded`, `get_relationship_detector`)
- `gui2/main.py` — warm-up thread pre-builds the relationship detector off the critical path
- `tools/cache_load.py` — `load_/save_/invalidate_decon_no_headwords_cache` (db_info JSON cache; invalidate supports in-session no-commit)
- `tools/lookup_sync.py` — `sync_lookup_column` deletes the cache in-session before any commit when `headwords`/`deconstructor` syncs (atomic invalidation, both ORM and raw-SQL paths)
- `scripts/build/decon_cache_update.py` — new pipeline step rebuilding the cache after the last lookup writer
- `scripts/bash/generate_components.py` — hook for the cache rebuild step
- `tests/tools/test_decon_no_headwords_cache.py` — 12 tests: round-trip, corrupt/absent, overwrite, invalidation on both sync paths, non-invalidation for unrelated columns
- `tests/gui2/test_database_manager_corpus.py` — updated `initialize_db` test; new test that initialize_db leaves detector and corpus unloaded
- `kamma/threads/20260919_gui2_db_load/{spec,plan}.md`, `artifacts/` — records and benchmark harnesses

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `gui2/database_manager.py` | stale `get_relationship_detector` docstring claimed eager build in initialize_db | perpetuates the exact confusion the Phase 4 correction documented | fixed |
| 2 | minor | `gui2/database_manager.py` | `is_db_loaded` docstring overstated ("full corpus load") | corpus no longer loads before the flag flips | fixed |
| 3 | minor | `tools/lookup_sync.py` | invalidation committed separately from the sync — crash in between left changed data + intact cache | one hole in the invalidation story | fixed: delete now in-session before any commit, lands atomically with the first data commit |
| 4 | minor | `gui2/database_manager.py` | self-heal cache write could abort initialize_db (write lock, insert race) | a pure-optimisation failure must not gate db_loaded | fixed: try/except, log and continue |
| 5 | minor | `gui2/database_manager.py` | lazy detector check-then-set not thread-safe; warm-up makes the race reachable | redundant ~3 s build + frozen click on race | fixed: double-checked `_detector_init_lock` |
| 6 | minor | `tests/tools/test_decon_no_headwords_cache.py` | raw-SQL invalidation path untested | that's the path production uses for headwords | fixed: parametrised orm/raw_sql |
| 7 | nit | `tools/lookup_sync.py` | over-invalidation on no-op syncs | cost is one slow gui2 launch per no-op | rejected: result counts are unknown before the write; simplicity wins |
| 8 | nit | `tests/gui2/test_database_manager_corpus.py` | stale docstring + dead RelationshipDetector monkeypatch | re-perpetuated the eager-build misunderstanding | fixed: docstring updated, dead stub removed, new lazy assertion test |

CodeRabbit (1 minor): move detector pre-build before the tab warm-up loop — rejected: tabs are the first click surface and the detector is only needed on synonym focus; ordering either way leaves the same lazy-build fallback, which finding 5's lock makes safe.

## Fixes Applied
- Findings 1–6, 8 (see above). 7 rejected with reason.

## Test Evidence
- `uv run pytest tests/ -q` (whole project, slow deselected) → 1912 passed
- `uv run pytest tests/tools/test_decon_no_headwords_cache.py tests/gui2/ -q` → 310 passed
- `just typecheck` (pyrefly, repo-wide) → 0 errors
- `uv run ruff check` + `ruff format` + `pyright` on every touched file → clean
- Serial protocol (`artifacts/run_phase5_serial.py`, 3 headless xvfb launches) → db-loaded 0.85/0.93/0.93 s median 0.93 s post-review-fixes (was 6.90 s baseline; ≤ 4 s target met)
- Correctness: cached set == live set (724,852 keys); detector outputs identical across corpus variants (`artifacts/phase5_benchmark2.py`)

## Not Verified
- Fresh-install path (gui2 first launch on a db without the cache row) verified only via unit tests + throwaway-copy run, not on a real release db
- Concurrent two-process self-heal (unique-key insert race) reasoned about, not reproduced
- Timing figures are from this machine only (shared-load variance noted: 0.78–0.93 s across runs)

## Verdict
PASSED
- Review date: 2026-09-19
- Reviewer: independent reviewer subagent + CodeRabbit CLI + implementing session
