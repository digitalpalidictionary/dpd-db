## Thread
- **ID:** 20260927_dependency_cleanup
- **Objective:** Remove unused and unmaintained Python dependencies, archive the MCP server, apply small version updates only, and configure deptry.

## Files Changed
- `pyproject.toml`, `uv.lock` — removed prompt-toolkit, google-auth-httplib2, fuzzywuzzy, gitpython, mcp; added thefuzz; flet pin 1.0.1; 21 small upgrades; new `[tool.deptry]` block.
- `tools/fuzzy_tools.py` — thefuzz import; `List` → `list`.
- `db/backup_tsv/backup_dpd_headwords_and_roots.py` — gitpython → `subprocess` path-limited commit.
- `tests/db/backup_tsv/test_backup_dpd_headwords_and_roots.py` — NEW. Path-limited commit and failure reporting.
- `tests/exporter/analysis/test_analysis_analyzer.py` — `mcp_config.db_path` → `ProjectPaths().dpd_db_path`.
- `exporter/analysis/ranking.py` — one narrow pyrefly suppression (pyrefly 1.3 limitation).
- `exporter/mcp/` → `archive/exporter/mcp/` (server, config, README); leftover ignored files deleted at user request.
- `.gitignore` — `exporter/mcp/output/*` removed.
- `docs/technical/project_folder_structure.md`, `exporter/analysis/README.md` — MCP marked archived; `archive/` listed.
- `justfile` — `deps` recipe.
- `kamma/threads/20260927_dependency_cleanup/artifacts/capture_outputs.py` — throwaway before/after harness.

## Findings
Sonnet subagent (spec audit + code review), CodeRabbit (via subagent), and a user-supplied independent review. 11 findings.

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | flet 1.0.0 → 1.0.1 | The only upgrade with no verification. The package diff shows runtime changes: control diffing (`object_patch.py`), `page.py`, `messaging/session.py`, `raw_image.py`. | gui2 is the daily editor, is excluded from pyrefly, and has no launch test. | Closed: user confirmed `just gui` works on Flet 1.0.1. |
| 2 | minor | plan 3.2 | Suppressed count 95 → 103, only 1 of 8 explained. | The count is a signal in this repo. | Traced: all from the pyrefly version; +2 ignore comments (ranking.py new, dv_catalogue_suttas.py:133 existing comment now hiding a new `bad-return`), +6 from the `tests/**` sub-config. Recorded. |
| 3 | minor | `justfile` deps / plan 4.3 | Recipe always exits 1; plan said no one-line fix while naming one. | A recipe that always fails trains people to ignore it. | `package_module_name_map` for python-levenshtein (9 → 7); recipe comment says it exits 1 while findings remain; plan corrected. |
| 4 | minor | `archive/exporter/mcp/README.md` | Run and Claude Desktop instructions point at the deleted path (CodeRabbit). | A reader following it hits a missing file. | Archived note added at the top. |
| 5 | minor | `conductor/product.md:21,24`, `conductor/tech-stack.md:19` | Still describe the MCP server as a live feature. | Changes what the project claims to be. | Fixed at finalize: MCP bullet and SDK line removed; AI-ready paragraph reworded. |
| 6 | nit | `tools/fuzzy_tools.py` | `typing.List` in a touched file. | AGENTS.md: modern forms only; ruff does not select UP. | `list[str]`. |
| 7 | nit | `docs/technical/project_folder_structure.md` | Did not say where the MCP server went; `archive/` not listed. | The move was undocumented. | `archive/` added to tree and details. |
| 8 | nit | backup test | `test_a_failed_commit_is_reported_not_raised` never asserted the report. | Name claimed more than the test checked. | Asserts `pathspec` in captured output; mutation-checked. |
| 9 | nit | `[tool.deptry.per_rule_ignores]` | Six entries (dev-group tools) are inert: deptry never checks dev packages. | Harmless; the spec asked for them. | Kept. |
| 10 | note | `archive/exporter/mcp/` + `archive/exporter/mcp_server/` | Two archived versions of one thing coexist. | Deliberate plan decision (don't mix versions). | On record; no change. |
| 11 | note | adjacent | A bare `uv sync` / `uv add` / `uv remove` strips the tools group. | Recorded for this thread; a future session may not see it. | Already in the auto-memory; candidate for AGENTS.md at finalize. |

## Fixes Applied
Findings 2, 3, 4, 6, 7, 8 fixed. 5 fixed at finalize. 9, 10 kept by decision. 1 closed by the user's gui2 launch.

## Test Evidence
- `ruff check`, `ruff format`, `pyright` (all 6 touched `.py` files) → clean, 0 errors.
- `uv run pytest tests` → 1915 passed, 12 deselected, 1 warning (pytest 9.1 deprecation in the apple dictionary test; follow-up).
- `just typecheck` → 0 errors (103 suppressed).
- `just deps` → 7 findings, all listed in plan 4.3.
- Backup test mutations: whole-index commit → both fail; generic error text → failure test fails; restored with `cmp` → 2 passed.
- Before/after capture (13 functions): identical except fuzzy suggestion order (6 of 30 terms, top match unchanged), accepted by the user.

## Verdict
PASSED — finding 1 closed by the user's gui2 launch on Flet 1.0.1.
