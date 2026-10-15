## Thread
- **ID:** 20261014_longest_compound_parts
- **Objective:** suggest a second construction line built from the longest existing compound parts (db tests: compound).

## Files Changed
- `db_tests/single/test_longest_compound_parts.py` — new interactive check (parse, index, match, fewest-parts split, accept/exception loop, GoldenDict open).
- `tests/db_tests/single/test_test_longest_compound_parts.py` — 13 unit tests on real-row fixtures.
- `tools/paths.py` — `longest_compound_parts_exceptions_path`.
- `justfile` — `test-compounds` recipe.
- `db_tests/single/test_longest_compound_parts.json` — exceptions written by the user's live runs (not edited by the agent).

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `match_run` | bracket-only part (`[r]`) at a run edge joined to a word: `catu + [r] + asīti` → `catu + asīti`; `anv + a + [d]` → `anva` | sandhi letter lost, no real gain | run may not start or end on a bracket-only part |
| 2 | major | `match_run` | joined-text match won even when the word holds another spelling: `ānāpānasati` for `ānāpānassatisamādhi` (16 rows) | line 2 used a spelling the word does not contain | joined text only if in word; else in-word construction match; then joined text |
| 3 | minor | `match_run` | sandhi fallback picked first in sort order (`viriyārambha` for `vīriyārambha…`) | wrong variant | prefer longest common start with the word, then sort order |
| 4 | minor | data | `uttaramāṇavavatthu` = `māṇava + vatthu`, `vokiṇṇasukhadukkha` order reversed (2 rows) | odd suggestions | editor marks exception / fixes data |
| 5 | minor | `main` accept | a word given line 2 in gui2 mid-run would get a third line; `A`/` a` silently skipped | data corruption risk | `refresh` + newline guard before write; strip/lower input |
| 6 | minor | tests | no tests for `is_candidate` or exception saving | gaps | tests added |
| 7 | nit | imports | `goldendict_tools` import out of order | style | reordered |

CodeRabbit (`--uncommitted --include-untracked --dir db_tests/single`): 0 findings.

## Fixes Applied
- Findings 1, 2, 3, 5, 6, 7 fixed. Finding 4 left to the editor (data, not code).

## Test Evidence
- `uv run pytest tests/db_tests/single/test_test_longest_compound_parts.py` (scope: all pure functions) → 13 passed.
- Undo checks: removing the edge-bracket guard fails 2 tests; removing the in-word condition on joined text fails 1; tie-break undo fails 1 (earlier).
- `ruff check`, `ruff format`, `pyright` on the script and test file (test via `--project /dev/null`) → clean. `just typecheck` (whole repo) → 0 errors.
- Live recount over all candidates (35,775) → 1,949 hits before exceptions; every reviewer-named row re-checked by name.

## Not Verified
- The interactive accept path (refresh, newline guard, commit) was read, not run — the agent does not run the db-writing script. The user's earlier live runs exercised accept and exception before the guard was added.
- Random sample of suggestions: 70 of ~1,950 (3.6%) read by the reviewer; suspicious classes read in full.
- 5 number words (`saṭṭhi 1.1`, `cattārīsā` etc.) still get wrong number suggestions; editor marks them as exceptions.

## Verdict
PASSED
- Review date: 2026-10-15
- Reviewer: independent Claude subagent + CodeRabbit; fixes by the implementing session
