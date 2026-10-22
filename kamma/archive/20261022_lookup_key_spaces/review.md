## Thread
- **ID:** 20261022_lookup_key_spaces
- **Objective:** Remove outer spaces from lookup keys and the one empty key (GitHub issue #270), so exact lookup finds their content.

## Files Changed
- `db/variants/variants_modules.py` — `key_cleaner` trims outer spaces (39 variant keys).
- `tools/sutta_codes.py` — skip an empty or whitespace-only `sc_code` (the empty key).
- `go_modules/deconstructor/importer/manualCorrections.go` — trim `compound`; loop body moved to `matchItemsFromRows`.
- `go_modules/deconstructor/importer/unmatched.go` — trim `compound` in the second reader, new helper `manualCorrectionWordsFromRows` (found in review).
- `go_modules/deconstructor/importer/manualCorrections_test.go` — new Go tests for both readers.
- `tests/db/variants/test_variants_modules.py`, `tests/db/variants/test_variants_modules_fixtures.json` — trim tests; `mixed` case now `"dukkha"`.
- `tests/tools/test_sutta_codes.py` — blank `sc_code` tests; old pyright error in the `aksharamukha` stub fixed.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `go_modules/deconstructor/importer/unmatched.go` (`makeManualCorrections`) | Second reader of the manual corrections file did not trim `compound` | The trimmed word stayed in the algorithm input and a worker result overwrote the curated split for `vinivijjhanaṭṭhenāti` | Trim in the reader, test first. Fixed. |
| 2 | minor | `tools/sutta_codes.py:40` | Whitespace-only `sc_code` passed the guard | Would make a spaced lookup key | `sc_code.strip()` in the guard, tests added. Fixed. |
| 3 | nit | `db/variants/variants_modules.py:22` | Docstring does not mention trimming | Reader may miss it | Skipped: existing comments stay as they are. |

Source: DeepSeek v4 pro (pi, max reasoning) found all three. CodeRabbit (free allowance) reported 2 findings, both in other threads' files (`tests/tools/test_search_battery.py`, committed under #268; `kamma/threads/20261007_temp_server_test/plan.md`, untracked). Scope checked with `git log` and `git status`. Nothing on this thread's files.

## Fixes Applied
- Findings 1 and 2, each with a test that failed first (output recorded in `plan.md`, Phase 2b).
- First twin check in Phase 3 was too weak (it tested only that a column was non-empty). Corrected in `plan.md`; content now compared.

## Test Evidence
- `uv run pytest tests/db/variants tests/tools/test_sutta_codes.py tests/db/suttas -q` (scope: 3 related areas) → 108 passed
- `go test -count=1 ./go_modules/deconstructor/...` (scope: all 4 deconstructor packages) → pass
- `go vet ./go_modules/...` (scope: all Go modules) → clean
- `uv run pytest tests/ -q` (scope: full suite, run before the review fixes) → 2339 passed; 1 timing test from another thread failed once at load 36 and passes alone
- `just typecheck` (scope: whole repo) → 0 errors; ruff and pyright clean on touched files
- Revert proof: key cleaner 8 fail, sutta builder 1 fail, first Go reader 1 fail; second Go reader fails before the fix
- Live database after rebuild + `just decon` re-run: spaced keys 0, empty keys 0, 1,283,190 → 1,283,176 rows, headwords changed on 0 rows, no change outside the 42 keys; `vinivijjhanaṭṭhenāti` holds the curated split

## Not Verified
- Full test suite was not re-run after the two review fixes; the 108 related tests, Go tests and typecheck were.
- The rebuild ran on the live database (scripts have no path option). The variant, sutta and inflection steps were not re-run after the review fixes, since those fixes only affect the Go step and a blank code that does not exist in the data today.
- The user has not yet tested lookups of `ūsakhaṇḍaṃ` and `kadāhaṃ dhanuggahe` in the webapp or mobile database.
- No guard exists against future spaced keys (out of scope, per spec).

## Verdict
PASSED
- Review date: 2026-10-22
- Reviewer: independent agent review (DeepSeek v4 pro via pi) plus CodeRabbit, validated by the implementing agent
