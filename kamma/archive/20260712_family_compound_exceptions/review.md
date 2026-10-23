## Thread
- **ID:** 20260712_family_compound_exceptions
- **Objective:** Give the three `db_tests/gui/add_family_compound_*` editors a working Exception button that saves to the shared test rows.

## Files Changed
- `db_tests/gui/add_family_compound_neg.py` — Exception button; reads row `family_compound empty neg`; hardcoded `neg_exceptions` deleted.
- `db_tests/gui/add_family_compound_taddhita.py` — Exception button; reads its row through `DbTestManager`; hand TSV read and `json` import removed.
- `db_tests/gui/add_family_compound_su_dur.py` — Exception button; reads the union of the `su dur nir` and `sa` rows (fixes the ignored `sa` row); routes writes by `construction`; dead `lemma_clean` check removed.
- `justfile` — new recipe `db-tests-gui`.
- `kamma/threads/20260712_family_compound_exceptions/spec.md`, `plan.md` — written.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `should_process` in all three | `int(i.id)` is redundant (id is an integer in all 89,740 rows) | None, matches `add_antonyms.py` | None |
| 2 | nit | `add_exception` in all three | `load_tests()` has no try/except if gui2 is mid-write | Very unlikely; same as `add_antonyms.py` | None |
| 3 | nit | `self.exceptions` in all three | Stale after the reload | Harmless, the item is already queued past | None |

Independent agent review: no blocking or major findings. Earlier herdr review of the spec: accurate, reload-before-save added.

## Fixes Applied
- Reload of the test file before every save, added after the spec review.

## Test Evidence
- `uv run ruff check`, `ruff format`, `pyright` (scope: the three scripts) → pass, 0 errors
- `just typecheck` (scope: whole repo, pyrefly) → 0 errors
- `uv run pytest tests/db_tests` (scope: 64 tests in that folder) → pass
- Read-only probe of the four live rows (scope: all four) → 17, 32, 3, 3 ids, all `int`
- Real GUI click, taddhita tool (scope: one id) → row gained 19999, nothing removed
- Real `add_exception` of neg and su/dur code on a copy of the TSV (scope: one id each for neg, `su dur nir` row, `sa` row) → each id landed in the right row; real file untouched
- Read-only probe of `dpd.db` (scope: 5 su/dur candidates) → all route correctly to a row

## Not Verified
- No real GUI click on the neg and su/dur buttons. Their save code ran only on a copy.
- CodeRabbit not run. Permission not yet given.
- CRLF round trip of the TSV not tested. Check the TSV diff before commit.
- `db_tests/db_tests_columns.tsv` also holds changes from other work (antonym, source_2, neg "na", trans rows). Not this thread's.

## Verdict
PASSED
- Review date: 2026-10-23
- Reviewer: Claude (independent subagent plus main-session checks)
