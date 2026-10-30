## Thread
- **ID:** 20261030_contrib_5_hardening
- **Objective:** contributor hardening: login, per-user tabs, read-only db, safe nightly sync (#215)

## Files Changed
- `gui2/contributor_tabs.py`, `gui2/main.py`, `gui2/*_view.py`, `gui2/filter_*.py` — tab gating, read tabs, one-session guard (newest wins)
- `db/db_helpers.py` — `PRAGMA query_only` for the contributor role
- `gui2/save_router.py`, `gui2/paths.py`, `gui2/database_manager.py`, `gui2/*_manager.py`, `gui2/contributor_proposal.py` — own-file saves, `_changed`, reserved ids, Reject, proposal fields
- `tools/contrib_entry.py` — entry hash, one list of delivered file kinds
- `scripts/server_contrib/{contrib_reconcile,contrib_push,maintenance_window,merge_contrib_files}.py` — redesigned sync; `absorption_check.py` deleted
- `scripts/server_contrib/{add_contributor.sh,nginx_contrib*.template,README.md}`, `justfile` (`contrib-merge`), `db/backup_tsv/backup_dpd_headwords_and_roots.py` — login files, recipe, log commit
- tests under `tests/gui2`, `tests/scripts/server_contrib`, `tests/db`, `tests/tools`; docs `gui2/README.md`, `kamma/tech.md`

## Findings
Reviewers: a Sonnet subagent, a pi agent ("contributor sever review 2"), CodeRabbit (0 findings). Every claim below was checked against the code.
| # | Sev | Location | What | Resolution |
|---|-----|----------|------|------------|
| 1 | major | `add_contributor.sh` vs sync scripts | per-user data folder; the window globs one folder, so it found no files | FIXED: one flat `/var/lib/dpd/contrib_data`; test runs the script for two users |
| 2 | major | `save_router.changed_columns` | 9 columns the form never sets (dates, inflections, freq) always in `_changed` | FIXED: only supplied columns; revert-checked |
| 3 | major | `main.py claim_session` | retired tab kept its Ctrl+S handler | FIXED: handler removed; test asserts it |
| 4 | major | `maintenance_window._systemctl` | a failed stop was only logged | FIXED: window refused; revert-checked |
| 5 | minor | `_restore_rollback` | stale `-wal`/`-shm` after restore | FIXED; revert-checked |
| 6 | minor | `maintenance_window` | `last_built_commit` written before the restore; porcelain parse unquoted; 2 GB copy before dirty check | FIXED (write last, `-z`, dirty check first) |
| 7 | minor | `add_contributor.sh` | tabs unvalidated; user `*added*` clashes with logs; htpasswd under default umask; same nginx realm per user | FIXED; tests |
| 8 | nit | `justfile` | `git merge` may open an editor | FIXED (`--no-edit`) |
| 9 | minor | docs | corrupt file stops window; push overwrites `contributions`; htpasswd group | FIXED in README |
| 10 | minor | `contrib_reconcile.reconcile_all` | not atomic across files on a corrupt later file | DEFERRED: the window's rollback covers it; standalone CLI only |
| 11 | minor | `db_helpers` | `query_only` follows the config.ini role too | DEFERRED: matches the documented fallback |
| 12 | nit | `db_tests_manager` | duplicate exception lines appended | DEFERRED: harmless, deduped on load |
| 13 | claim | `merge_all` drops removed users' log entries | NOT A FINDING: the log is read first and only extended |

## Fixes Applied
Items 1-9 above. New tests: `test_add_contributor.py` (7), plus tests for `changed_columns`, retired keyboard, failed stop, WAL.

## Test Evidence
- `uv run pytest tests/ -q` (scope: whole project, slow tests deselected) → 2646 passed
- `just typecheck` (scope: whole repo, pyrefly) → 0 errors
- `uv run ruff check` + `ruff format --check` (scope: 18 files changed in the review round; all 43 files of the thread were clean at the 7.3 gate) → pass
- revert checks on `changed_columns`, failed stop, WAL removal, merged-lines log → each test fails without its fix
- live runs with the user: web run as "alice" (7.1) and desktop run as user 1 (7.2), recorded in `plan.md`

## Not Verified
- Flet and nginx under the `/<user>/` path prefix (needs a live server, contrib_4 Phase 4)
- the nginx worker's read access to the htpasswd file (documented, not checked)
- Reject on an addition live (unit test only); the real server sync end to end (only the local round-trip test)
- pi agent and Sonnet subagent did not run the full suite

## Verdict
PASSED
- Review date: 2026-10-30
- Reviewer: Sonnet subagent, pi agent "contributor sever review 2", CodeRabbit CLI; fixes and checks by the implementing Claude session
