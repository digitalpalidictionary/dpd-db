## Thread
- **ID:** 20261016_agent_nouns_set
- **Objective:** Add the `agent nouns` family_set to finished masc agent nouns and a db_test that keeps it complete.

## Files Changed
- `scripts/fix/add_agent_nouns_set.py` — one-off script that adds the set without dropping existing sets (already run by the user: 676 rows).
- `tests/scripts/fix/test_add_agent_nouns_set.py` — unit tests for `add_set`.
- `db_tests/db_tests_columns.tsv` — new row "family_set: masc agent no agent nouns".

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `db_tests/db_tests_columns.tsv` ("source_1 -" row) | The working tree also holds exception 47140 (puḷuvaka, adj) and CRLF endings from a gui2 save at 05:47. | Not this thread's change. Staging the file commits it too. | Not this thread's to fix. The user decides whether to keep it. CRLF is normalised by `text=auto`. Follow-up: `save_tests` writes CRLF because `csv.DictWriter` uses `\r\n` by default. |
| 2 | nit | `scripts/fix/add_agent_nouns_set.py:34` | The guard matches the exact part. The test matches `\bagent nouns\b`. | Only differs for set names that don't exist. | None. The script has run once. |
| 3 | nit | `scripts/fix/add_agent_nouns_set.py:36` | Returns the input untouched (no whitespace clean-up) when the set is already present. | No live row has odd spacing. | None. |
| 4 | nit | `scripts/fix/add_agent_nouns_set.py:68` | `[amber]` is not a rich colour. | Copied from `sort_family_sets.py`. | None. |

## Fixes Applied
- None. The plan's Phase 2 result now notes the later gui2 change to the TSV.

## Test Evidence
- `uv run pytest tests/ -q` (scope: whole suite) → 2086 passed, 12 deselected.
- `uv run pytest tests/scripts/fix/ -q` (scope: fix scripts) → 49 passed. Two revert checks proved all 5 new tests guard behaviour.
- `just typecheck` (scope: whole repo, pyrefly) → 0 errors. pyright → 0 errors on both new files (filesAnalyzed 1 each). ruff check and format → clean.
- DbTestManager on the live db (scope: all headwords) → integrity OK. New test 676 before the run, 0 after. aka test 64 unchanged.
- Reviewer, read-only (scope: all 89,698 live rows against HEAD's backup TSVs) → no existing set lost. 676 rows changed only by gaining the set. Selection is identical to the test's (813 / 676; no NULLs, no whitespace-only meaning_1, no "agentive"-style grammar).
- CodeRabbit `--uncommitted --include-untracked` (scope: all dirty files) → 0 findings on this thread's files. Its 1 finding is in another thread's plan.

## Not Verified
- The HEAD backup dates from 2026-10-15 16:11. An edit made and reverted between then and the run is invisible.
- gui2 was not opened, and no exporter build was run, to see the set on the family-set page.

## Verdict
PASSED
- Review date: 2026-10-16
- Reviewer: independent general-purpose subagent + CodeRabbit, findings checked by the implementing session (Claude Opus 5.5)
