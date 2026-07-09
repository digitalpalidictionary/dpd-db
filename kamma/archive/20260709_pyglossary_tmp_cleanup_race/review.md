## Thread
- **ID:** 20260709_pyglossary_tmp_cleanup_race
- **Objective:** Eliminate the spurious `no such file or directory: …/pyglossary/tmp` stderr error that fires when `export_to_goldendict_with_pyglossary` runs with `include_slob=True`.

## Files Changed
- `tools/goldendict_exporter.py` — added `_ = glos.tmpDataDir` in `create_glossary()` to force a per-glossary tmp dir before any `newDataEntry` call.
- `tests/tools/test_goldendict_exporter.py` — new regression test (4 tests) guarding the fix.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `tests/tools/test_goldendict_exporter.py` | Tests call `create_glossary()` which creates real `~/.cache/pyglossary/<uuid>_res` dirs that persist since `cleanup()` is never called. | Accumulates stray dirs over many test runs. | Optional: add a fixture that calls `glos.cleanup()` after each test. |
| 2 | nit | `tests/tools/test_goldendict_exporter.py::test_glossary_tmp_dir_is_not_shared_cache_dir_tmp` | Monkeypatches `XDG_CACHE_HOME`, but the assertion holds via the `_res` suffix regardless of whether pyglossary honors that env var. | The env-var setup is partly cosmetic; test still valid. | Optional: simplify by dropping the monkeypatch. |

No blocking or major findings.

## Fixes Applied
None — both findings are nits and may be skipped.

## Test Evidence
- `uv run ruff check tools/goldendict_exporter.py tests/tools/test_goldendict_exporter.py` → pass
- `uv run ruff format ...` → pass
- `uv run pyright tools/goldendict_exporter.py tests/tools/test_goldendict_exporter.py` → 0 errors
- `uv run pytest tests/tools/test_goldendict_exporter.py -v` → 4 passed
- `uv run pytest tests/` → 1249 passed, 16 deselected, 0 failures
- Manual: user ran export with `include_slob=True`, confirmed stderr clean of `no such file or directory`.

## Verdict
PASSED
- Review date: 2026-07-09
- Reviewer: pi agent (same session as implementation — independence reduced; compensated with source-level verification of pyglossary 5.4.1 internals)
