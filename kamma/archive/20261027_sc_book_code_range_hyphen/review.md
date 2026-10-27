## Thread
- **ID:** 20261027_sc_book_code_range_hyphen
- **Objective:** `SuttaInfo.sc_book_code` must return only the letters of a range code (`AN2.1-10` → `AN`, not `AN-`). GitHub issue #208.

## Files Changed
- `db/models.py` — `sc_book_code` regex is now `re.sub(r"\d.*", "", self.sc_code)`; the `rstrip("-")` workaround and its comment in `s_4nt_link` are removed (scope widened by the user, 2026-10-27).
- `tests/db/test_sutta_info.py` — three tests added: `sc_book_code` (15 cases), `tbw`/`tbw_legacy` for `AN2.1-10`, `sc_vagga_link` for SN39.
- `kamma/threads/20261027_sc_book_code_range_hyphen/` — spec.md, plan.md, review.md.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `tests/db/test_sutta_info.py:210` (CodeRabbit) | The test asserts `.../an/an2.1-10.html`. CodeRabbit says the site has no range pages and the real page is `.../an/an2.1.html`. | A range link may still 404 after this fix. Own check 2026-10-27: `an2.1-10.html` gives 404, `an2.1.html` gives 509 (limit error), so the claim is plausible but not proven. | SKIPPED. The suggested fix needs a code change that maps a range to its first sutta page. That is a new feature outside the issue and spec. The test asserts what the code now produces. Follow-up thread if the user wants it. |
| 2 | nit | `db/models.py:878`, `:904` (subagent) | `if sc_book_code == "iti"` never matches, because the book code is `ITI`. | ITI rows get `.../iti/iti1.html`, not `.../it/it.html`. Verified: identical output on old and new code. | NOT TOUCHING. Pre-existing and unrelated. Separate thread if wanted. |

## Fixes Applied
- None. No blocking or major findings.

## Test Evidence
- `uv run pytest tests/db/test_sutta_info.py -q` (scope: one file) → 38 passed
- `uv run pytest -q` (scope: whole suite, 12 slow tests deselected by repo config) → 2524 passed
- `uv run ruff check` and `ruff format --check` (scope: the 2 touched files) → clean
- `uv run pyright db/models.py` (scope: the one file) → 0 errors
- Old-vs-new probe over all 5,115 `sutta_info` rows with an `sc_code` → 215 `sc_book_code`, 215 `tbw`, 215 `tbw_legacy`, 4 `sc_vagga_link`, 0 `s_4nt_link` changed (matches spec)
- Regex over all 4,680 distinct `sc_code` values (subagent) → every non-empty result is letters only
- Guard proof, old regex put back with the workaround removed → 8 failed (7 new + existing `s_4nt_link` `SN39.1-15`), restored → 38 passed
- Independent subagent review (read-only, no git) → no findings in scope
- CodeRabbit `review --agent --uncommitted --include-untracked --fresh` → 1 finding (#1). It also listed unrelated dirty files in the tree (resources/, shared_data/); none are this thread's.

## Not Verified
- Whether thebuddhaswords.net hosts range pages, and whether any corrected link resolves. The site returned 509 on existing pages.
- The 4 new `sc_vagga_link` URLs were checked as strings, not opened.
- The subagent did not run pyright or the revert proof. I ran both.

## Verdict
PASSED
- Review date: 2026-10-27
- Reviewer: Coder agent (Opus/Sonnet session) plus an independent subagent and CodeRabbit CLI
