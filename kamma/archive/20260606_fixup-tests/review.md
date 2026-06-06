## Thread
- **ID:** 20260606_fixup-tests
- **Objective:** Get `tests/` reliably green and runnable as a gate at the start of `scripts/bash/generate_components.py`; keep total runtime under a minute.

## Files Changed
- `pyproject.toml` — added `[tool.pytest.ini_options]` with `addopts = "--import-mode=importlib"`; fixes the only collection error (duplicate `test_dpd_headword.py` basename in `webapp/` + `goldendict/` with no `__init__.py`). Plain `uv run pytest tests/` now collects.
- `tests/exporter/mobile/test_mobile_exporter.py` — added `bhs_source_path=tmp_path / "bhs.xml"` to `_make_paths()`. Stale mock: commit `c7e1a31e` added BHS (Edgerton) support referencing `g.pth.bhs_source_path`, but the SimpleNamespace mock was never updated → `AttributeError` in 6 tests. Pointing at a non-existent tmp file makes BHS skip, as before.
- `tests/exporter/goldendict/test_dpd_headword.py` — renamed `test_sc_sutta_and_title_hidden` → `test_sc_sutta_and_blurb_hidden_eng_title_shown`; flipped `assert "All-Embracing" not in html` → `in html`. The test over-asserted: both goldendict (`dpd_headword.jinja:333`) and webapp (`dpd_headword.html:345`) render `sc_eng_sutta` for vagga (`and not is_samyutta`), hiding only `sc_sutta` and `sc_blurb` for vagga. Templates are consistent; the test was wrong. No production code changed.
- `scripts/bash/generate_components.py` — added `"uv run pytest tests/"` as the first COMMANDS entry; `run_script` already exits non-zero on failure, so a red suite aborts the build before any data work. Group separators converted from blank lines to bare `#` lines so `ruff format` (pre-commit) preserves the grouping.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|

No findings.

## Fixes Applied
- None beyond the planned changes.

## Test Evidence
- `uv run pytest tests/ --co -q` → 474 collected, 0 collection errors (was: 1 collection error)
- `uv run pytest tests/` → 474 passed, ~53–59s (was: 7 failed, 467 passed)
- `uv run ruff check` / `ruff format --check` / `uv run pyright` on changed files → all pass

## Known tradeoffs (documented, accepted)
- Suite is import-bound: `--co` alone is ~46s of the ~53–59s; only ~13s is execution. Deleting individual tests won't help — cost is shared module-import overhead. ~59s accepted by user; no parallelism (pytest-xdist) added.
- 4 pre-existing warnings (Starlette TemplateResponse Deprecation, fork DeprecationWarning, SAWarning in gui2 duplicate-key test) — unrelated to this thread, not addressed.

## Verdict
PASSED
- Review date: 2026-06-06
- Reviewer: kamma (inline)
