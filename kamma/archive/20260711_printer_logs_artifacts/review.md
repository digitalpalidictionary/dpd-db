# Review

## Thread
- **ID:** 20260711_printer_logs_artifacts
- **Objective:** Stop makedict/printer leaving `typescript` and `dpd_operations.log` artifacts in the repo root; `logs/` HTML files remain the only record.

## Files Changed
- `justfile` — four makedict recipes DRYed into hidden `_logged-makedict`; `script` transcript → `/dev/null`
- `tools/printer.py` — dead TSV logging machinery removed (~90 lines); console output byte-identical
- `scripts/cl/dpd-makedict`, `scripts/cl/dpd-build-db` — same `/dev/null` fix (found in review)
- `.gitignore` — dropped `typescript` entry
- `AGENTS.md` — printer docs updated (CLAUDE.md symlinks to it)
- `tests/db/inflections/test_create_inflection_templates.py`, `tests/scripts/build/test_families_to_json.py` — stale printer-log comments removed; strengthened to assert import leaves cwd completely untouched
- Deleted: stale `typescript`, `dpd_operations.log`

## Findings
| # | Severity | Location | What | Fix |
|---|----------|----------|------|-----|
| 1 | major | `scripts/cl/dpd-makedict:14`, `scripts/cl/dpd-build-db:14` | Still produced `./typescript`, now un-ignored | `/dev/null` transcript added to both |
| 2 | minor | `justfile:30–47` | Linewise recipes fail-fast if a *leading config script* fails (build-failure → reset path preserved) | Documented in spec.md as accepted improvement |
| 3 | nit | two test files | Stale "printer still writes its log" comments | Removed; tests upgraded to full no-artifact guard |
| 4 | nit | `justfile:29` | `just _logged-makedict` body vs plain dependency | Accepted as-is for uniformity |

CodeRabbit (`--agent --type uncommitted`): 0 findings.

## Fixes Applied
- Findings 1–3 fixed as above; finding 4 accepted.

## Test Evidence
- `uv run pytest tests/` → 1471 passed, 16 deselected (pre-review)
- `uv run pytest` on the two strengthened test files → 13 passed (post-fix)
- `uv run ruff check` + `ruff format` + `pyright` → clean on all touched Python files
- `rg 'script -q'` sweep → all three invocations carry `/dev/null`
- Full test run (imports printer transitively) did NOT recreate `dpd_operations.log`

## Verdict
PASSED
- Review date: 2026-07-11
- Reviewer: independent zero-context subagent (findings) + CodeRabbit + main session (fixes)
- Residual: live `just makedict` terminal/HTML fidelity to be user-verified on next real build
