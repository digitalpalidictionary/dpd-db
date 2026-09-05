## Thread
- **ID:** 20260905_anki_stale_root_fields
- **Objective:** Anki notes keep old root data when a headword stops being root-derived.

## Files Changed
- `exporter/anki/anki_updater.py` — `update_note_values()` now blanks the seven root fields when a headword has no `root_key`
- `tests/exporter/anki/test_anki_updater.py` — two regression tests: fields cleared with no root, still populated with a root

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `tests/exporter/anki/test_anki_updater.py:237` | root sign written as a `√` escape | harder to read than the literal `√` used elsewhere in the repo | replaced with literal `√` |

No blocking or major findings.

## Fixes Applied
- Replaced the unicode escapes with literal `√` characters in the new test.

## Test Evidence
- Failing-test-first proof: with the `else` branch temporarily removed, `test_update_note_values_clears_root_fields_when_root_removed` fails at the first cleared-field assertion → confirms the test catches the reported bug
- `uv run pytest tests/exporter/anki/` (scope: whole anki test module, 17 tests) → pass
- `uv run pytest tests/` (scope: whole project suite, 1815 tests, 12 slow deselected) → pass
- `uv run ruff check` + `ruff format --check` + `uv run pyright` (scope: the two changed files) → clean
- `just typecheck` (scope: repo-wide pyrefly) → 0 errors
- `coderabbit review --agent --dir exporter/anki --type uncommitted` (scope: `exporter/anki/anki_updater.py` only) → 0 findings

## Not Verified
- No live Anki collection was touched; the fix is proven only against the fake-note stubs, not a real `Collection` write
- CodeRabbit did not see the test file (outside the `--dir` scope)
- Slow-marked tests (12) were deselected, as in the default pipeline
- Independence reduced: reviewed by the implementing session, not a fresh agent

## Verdict
PASSED
- Review date: 2026-09-05
- Reviewer: Claude (implementing session)
