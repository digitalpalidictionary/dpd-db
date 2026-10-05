# Review: 20261005_server_update_cleanup

**Verdict: PASSED** (2026-10-05)

## Files Changed
- audio/db_release_download.py — temp-dir download, row test, atomic swap, non-zero exit on failure
- tests/audio/test_db_release_download.py — new, 2 tests
- scripts/server_dpdict/update-dpd.sh — moved; pipefail, update_tmp + trap, uv cache prune, tested dpd.db swap
- scripts/server_contrib/* — moved from scripts/server/, import paths updated, dpdict note dropped from README
- tests/scripts/server_contrib/* — moved from tests/scripts/server/, imports updated
- justfile — dpdict-push path
- docs/technical/project_folder_structure.md — folder tree
- kamma/threads/20260719_contributor_web_server/{spec,plan}.md — paths

## Findings
- CodeRabbit (`--agent --uncommitted --include-untracked`, 36 files): 0 findings.
- Sonnet from-scratch audit: no real defects. Three MINOR, accepted, not acted on:
  steps are not one unit (audio swap can land before a main-db failure);
  theoretical stale `dpd.db-wal` (same exposure as before); SIGKILL leaves one `audio/db/tmpXXXX`.

## Fixes Applied
- spec.md: corrected the overstated "live dbs stay as they were" sentence.

## Test Evidence
- Revert check: old flow restored → 2 of 2 new tests fail for the right reasons; restored → pass.
- `uv run pytest tests/` — 1972 passed, 12 deselected.
- ruff, ruff format, pyright clean on all touched Python files; `just typecheck` 0 errors.
- `bash -n` clean; row check exits 0 on the real dpd.db, 1 on a missing db.

## Open
- Task 3.2 (real server run) — deferred by the user to the next server update. Not blocking.
