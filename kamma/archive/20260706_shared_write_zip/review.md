# Review

## Thread
- **ID:** 20260706_shared_write_zip
- **Objective:** Optimize the shared write+zip stage in
  tools/goldendict_exporter.py (idzip compression level 9→6), benefiting all
  exporters. GitHub issue #157 (reference only, do not close).

## Files Changed
- `tools/goldendict_exporter.py` — new `IDZIP_COMPRESSION_LEVEL = 6`
  constant + `_idzip_compress()` helper (set/restore idzip's module global
  in try/finally); `zip_dictfile`/`zip_synfile` refactored to call it,
  signatures unchanged. Only source change in the thread.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | note | `AGENTS.md:256` | Uncommitted benchmarking-lesson addition in working tree, not authored by this thread's implementation | Could get committed accidentally with the thread | Confirm ownership at finalize; commit deliberately or leave to its owning session |
| 2 | nit | `tools/goldendict_exporter.py:295` | Generic exception handler prints "not found" wording for any error (pre-existing, carried over unchanged) | Slightly misleading log on non-FNF failures | Future cleanup, not this thread (behavior preservation was the goal) |

No blocking, major, or minor defects.

## Fixes Applied
- None required.

## Test Evidence
- `uv run ruff check` + `ruff format --check` + `pyright` on touched file → all clean
- `uv run pytest tests/tools/ -q` → 254 passed
- `uv run pytest tests/` → 1204 passed, 9 failed — all in
  `tests/exporter/analysis/`, confirmed pre-existing via clean-tree rerun
- Parity: decompressed .dict/.syn content byte-identical to level-9 output
  (855,761,583 / 408,418,009 bytes), same input through real code path
- Timing: full-scale write+zip 90.0s → 35.94s (2.50x); zip stage 3.36x,
  matching Phase 1 prediction (3.37x); sizes +1.0% dict / +2.9% syn
- Live run: user's `just export-grammar` passed through both changed
  functions cleanly (zip .dict 3.6→2.9s, zip syn 1.7→0.47s); GoldenDict
  display confirmation pending as the last open plan task
- Reviewer verified idzip source (level read at call time), process-pool
  safety (separate OS processes, no leak/race), and error-path preservation

## Verdict
PASSED
- Review date: 2026-07-06
- Reviewer: independent fresh-context subagent (implementation was by this
  session; review delegated per workflow independence rule)
