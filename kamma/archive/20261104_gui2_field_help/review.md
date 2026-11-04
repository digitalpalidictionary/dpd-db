## Thread
- **ID:** 20261104_gui2_field_help
- **Objective:** show a hover help text on the name of every one of the 50 fields in the gui2 editor form (Pass 1 and Pass 2).

## Files Changed
- `gui2/field_help.py` (new) — loader with module-level cache, `validate_field_help`, `get_field_help`.
- `gui2/field_help.json` (new) — 50 help texts, in `FieldConfig` order.
- `gui2/dpd_fields.py` — one import and a 7-line tooltip block in `_create_field_row`. Nothing else.
- `tests/gui2/test_field_help.py` (new) — 20 tests.
- `gui2/README.md` — one bullet naming the help file.

## Findings
Reviewed by a fresh read-only subagent (zero context, given spec, plan and file list). 10 findings, all minor or nit. Checked each against the live db and docs before acting.

| # | Severity | Location | What | Decision |
|---|----------|----------|------|----------|
| 1 | minor | `field_help.json` lemma_1 | example `kamma 1` vs guide's `1.1` scheme | Part right. The db has both forms (19,974 `word N`, 2,722 `word N.N`). Text now gives both. |
| 2 | minor | `comment` | "Contributors must write one" overstates `comment_change` (only shows an error for non-primary users) | Fixed. |
| 3 | minor | `stem` | `!` and `*` wording differed from `dpd_headwords_table.md` | Fixed to the table's meaning. |
| 4 | minor | `derivative` | guide format `kita (ta)` | Rejected: the dropdown holds only kita, kicca, taddhita. |
| 5 | minor | `derived_from` | text narrowed to verb forms | Fixed. |
| 6 | minor | several | claims "not verifiable" (semicolons, `family_word`, `origin`, `family_set`) | Rejected: `meaning_1` has `;` in 44,788 rows vs `, ` in 693; `family_word` wording is the table's "if not a root"; `origin` and `family_set` examples are real db values. |
| 7 | minor | tests | no test proved the file is read once | Fixed: added test. |
| 8-10 | nit | tests, loader log | import order, private import, log does not name the bad key | Skipped (not worth it; ruff clean). |
| 11 | major (CodeRabbit) | `field_help.py:7` | `HELP_PATH` is relative to the working directory; fails if gui2 starts elsewhere | Rejected: project rule is that gui2 runs from the project root (`flet run` is already banned for the same reason) and the spec chose this. |
| 12 | minor (DeepSeek v4-pro, max reasoning) | `field_help.json` phonetic | examples `thy > cch`, `ā > a` are not in the rules file | Rejected: the live db has `ā > a` in 85 rows and `thy > cch` in 14. The rules file is a different table. |
| 13 | minor (DeepSeek) | `field_help.json` origin | example `ncped` is flagged by a Tests-tab check (`origin: contains dps or ncped or cpd`, `db_tests/db_tests_columns.tsv:352`) | Fixed: example now `pass1 or pass2`. |

## Fixes Applied
- Rewrote five texts (`lemma_1`, `comment`, `stem`, `derived_from`, `origin`).
- Added `test_get_field_help_reads_the_file_only_once`.

## Test Evidence
- `uv run pytest tests/gui2/test_field_help.py` (scope: the new test file, 20 tests) → pass.
- Revert check for the cache test (replaced the cache with a stand-in that keeps `cache_clear`) → 1 test failed, the new one; 19 passed. File restored and diffed.
- Earlier revert check for the tooltip line (`if False:`) → 1 failed, 17 passed at that time.
- `uv run pytest tests/gui2` (scope: all gui2 tests) → 650 passed.
- `ruff check`, `ruff format --check`, `pyright --project /dev/null` on the three touched Python files; plain `pyright` on `dpd_fields.py` → clean.
- `just typecheck` (whole repo) → 0 errors, run before the review fixes. The fixes only touched a JSON file and a test.
- Live check in the owner's Chrome, web gui2: 13 of 13 hovers show the right tooltip (Pass 2: 9, Pass 1: 4), name selection still works.
- `coderabbit review --agent --uncommitted --include-untracked --fresh` (scope: only this thread's 5 files, copied into a throwaway repo in the scratchpad, because the real tree holds other threads' contributor data) → 1 finding, rejected (row 11). It had no remote, so it ran on the free allowance and saw no other repo files.
- `pi` review, DeepSeek `deepseek-v4-pro`, `--thinking max`, read-only (scope: diff and new files of this thread; it could read other repo files) → verdict Approve, 2 minor findings (rows 12, 13). It re-checked all 50 texts and the Flet API.
- Full `uv run pytest tests/` before the review fixes → 2858 passed, 2 failed (pre-existing, timing tests under load 13, no gui2 files: `test_tipitaka_db_deadline`, `test_maintenance_window`).

## Not Verified
- The four texts rewritten in review were not re-checked on screen. They are plain text changes under the same loader.
- Full suite not re-run after the review fixes.
- The "logged once" behaviour of a failed load is not asserted by a test.
- CodeRabbit saw only the five files in a copy, not the full repo.
- The `origin` text change was checked by `pytest tests/gui2/test_field_help.py` (20 passed) only.
- Keyboard-only use: no tooltip shows on focus. Accepted in the spec.
- The 50 texts are not yet skimmed by the owner, who plans to hand edit them.
- 90 strict-mode pyright errors in `gui2/dpd_fields.py` are pre-existing and not on this thread's lines.

## Verdict
PASSED
- Review date: 2026-11-04
- Reviewer: independent subagent (read-only), findings checked and fixes applied by the implementing session

## Post-review change (2026-11-04, owner request)
- The rule that rejected a newline in a help text was removed from `gui2/field_help.py`. `test_newline_is_reported` became `test_newline_is_allowed`.
- 30 texts in `gui2/field_help.json` were reworded: behaviour lines (key press, button, error, symbol) sit on their own line, and key words are in CAPITALS. Quote marks and bold were tried and dropped (a Flet tooltip takes plain text only; quotes are hard to write in JSON).
- Checked: `uv run pytest tests/gui2/test_field_help.py` (20 passed), ruff and pyright clean. The new look was not checked live by the implementer; the owner restarts gui2 and checks it by eye over the next few days.
