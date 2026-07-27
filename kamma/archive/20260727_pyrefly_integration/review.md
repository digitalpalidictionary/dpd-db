## Thread
- **ID:** 20260727_pyrefly_integration
- **Objective:** Adopt `pyrefly` as a repo-wide type-check gate (`just typecheck` + CI) and clear the 46 findings it surfaced in production code, leaving the ruff+pyright pre-commit hook untouched.

## Files Changed
- `pyproject.toml` — `pyrefly` in `dev` group; new `[tool.pyrefly]` config
- `justfile` — new `typecheck` recipe
- `.github/workflows/typecheck.yml` — repo-wide gate on push to `main` + all PRs
- `AGENTS.md` — new "Repo-wide type check" section; whole-tree git command ban
- `tools/` ×6 — `utils.py`, `sinhala_tools.py`, `ai_manager.py`, `ai_gemini_manager.py`, `phonetic_change_manager.py`, `bjt_source_sutta_example.py`
- `db/` ×5 — `models.py`, `families/root_info.py`, `bold_definitions/…`, `inflections/…`, `lookup/…`
- `exporter/` ×6 — `webapp/toolkit.py` (−189 lines), `webapp/main.py`, `goldendict/export_dpd.py`, `pdf/pdf_exporter.py`, `tpr/tpr_exporter.py`, `analysis/analyzer.py`
- `db_tests/` ×5, `scripts/` ×4, `audio/` ×2 — type fixes
- `tools/docs_update_bibliography.py` — `_clean()` helper (user-requested test rewrite)
- **Deleted:** `tools/ipa.py`, `tools/ipa.tsv`, `tests/tools/test_ipa.py`, `tests/tools/test_docs_update_bibliography_fixtures.json`
- **New tests:** `tests/test_typecheck_gate.py` (7), `tests/tools/test_ai_gemini_manager.py` (15), plus 4 in `test_utils.py`, 9 in `test_docs_update_bibliography.py`

## Findings
Two independent reviewers: CodeRabbit CLI, and a fresh-context Sonnet subagent. **No blocking, no major.**

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `scripts/build/families_to_json.py:59` | `Mapping[str, object]` annotation admits `UserDict`/`mappingproxy`, which `json.dumps` rejects | Signature promised more than the body delivered | FIXED — `json.dumps(dict(data), …)`; verified the `TypeError` in the interpreter first |
| 2 | minor | `pyproject.toml:117` | `search-path = ["scripts/suttas/bjt"]` inert once `scripts/suttas/**` was excluded | Dead config implying the tree is still partly checked | FIXED — line removed; typecheck still 0 |
| 3 | minor | `db/models.py:1290` | Commented-out `convert_uni_to_ipa` lines referencing the module this thread deleted | Orphaned by this thread's own deletion | FIXED — removed (the concurrent-thread reason for not touching it no longer applied) |
| 4 | minor | `db_tests/db_tests_columns.tsv` | Modified in tree, unexplained by this diff | Would sweep another session's db_tests exception approvals into this commit | NOT FIXED — deliberately excluded from staging |
| 5 | nit | `exporter/tpr/tpr_exporter.py:325` | `else:` redundant after the `if` now returns | Cosmetic | NOT FIXED — dedenting ~60 lines for a nit is not worth the diff noise |
| 6 | nit | `tools/docs_update_bibliography.py` | `_clean()` collapses all internal whitespace, broader than the newline bug | No observable change on current data | ACCEPTED — documented |

## Fixes Applied
- Findings 1, 2, 3 fixed during review; each re-verified with `just typecheck` + `pytest`.
- One self-inflicted error caught and reverted: an attempted dedent of finding 5 wrapped the block in a meaningless `contextlib.ExitStack()`. `tpr_exporter.py` is back to its intended 3-line diff.

## Test Evidence
- `just typecheck` → **0 errors, exit 0** (from a 46-finding baseline)
- `uv run pytest tests/` → **1737 passed, 17 deselected, 0 failed**
- `uv run ruff check` + `ruff format` + `pyright` on all changed `.py` → clean
- Gate teeth proven: deliberate `def f(x: int) -> str: return x` → exit 1; reverted → exit 0
- `toolkit.py` deletion: 12 live `dpd.db` queries, output **byte-identical** before/after
- `ai_gemini_manager` guards proven non-tautological: reverting the fix fails exactly 2 of 15
- Reviewer independently reproduced every quantitative claim and hand-traced the `toolkit.py`
  control flow, confirming the trailing `raise RuntimeError` is genuinely unreachable

## Residual Risk
- `ai_gemini_manager` and `toolkit.py` retry paths are not exercised by automated tests (both need a live API failure / locked database).
- `docs/bibliography.md` is stale on `main` — missing Malalasekera + Levman rows and a category rename. Regenerate with `just docs-update`. Pre-existing, not introduced here.

## Verdict
PASSED
- Review date: 2026-07-27
- Reviewer: CodeRabbit CLI + independent Sonnet subagent (fresh context), findings applied by the implementing agent
