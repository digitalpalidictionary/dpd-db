## GitHub Issue
#239

## Architecture Decisions
- Check `p.exitcode` inline after each `p.join()` rather than collecting and checking
  later — fail fast on first bad exit.
- Raise `RuntimeError` (not `SystemExit`) so callers can catch it if needed.

## Phase 1 — Fix exit-code check

- [x] In `exporter/goldendict/export_dpd.py`, after `p.join()` (line 275), add a check:
  if `p.exitcode != 0`, raise `RuntimeError` with the exit code.
  → verify: read the modified lines and confirm the check is there.

- [x] Add a test in `tests/exporter/goldendict/test_export_dpd.py` that starts a Process
  with a target that raises an exception, joins it, and verifies the exit code is non-zero
  (mirrors what the production code now checks).
  → verify: `uv run pytest tests/exporter/goldendict/test_export_dpd.py -v` → 1 passed
