# Review: contrib same-word clash and book split

Reviewers: CodeRabbit (free plan, one run per folder: gui2, tests, tools, scripts, kamma) and pi on DeepSeek flash (thinking off), twice. The second pi run covered only the code changed after the first review. `/kamma:3-review` was not run. The verdict below rests on these reviews and on the user running `/kamma:4-finalize` on 2026-11-14.

## Files Changed

- `gui2/pass1_file_manager.py`, `gui2/pass1_add_controller.py`: `finished_words` and the skip in `get_next_item`.
- `gui2/books.py`, `gui2/pass1_context.py`: `story_range`, the new book keys (`tha-ap`, `thi-ap`, `mnd`, `cnd`, `ja-1` to `ja-5`) and their prompt names.
- `gui2/data/pass1_auto_*.json`: nine new part files, three combined files deleted (written once by `artifacts/split_drafts.py`).
- `tools/cst_sc_text_sets.py`: shared helpers and `make_cst_jataka_text_list`.
- `tools/docs_update_missing_words.py`, `docs/missing_words.md`, `docs/missing_words.pdf`: the Apadāna, Niddesa and Jātaka rows split; page rebuilt.
- `kamma/tech.md`, `scripts/server_contrib/README.md`: notes.
- Tests: `tests/gui2/test_books.py`, `test_pass1_add_controller.py`, `test_pass1_auto_controller.py`, `test_pass1_file_manager.py`, `tests/scripts/server_contrib/test_contrib_pull.py`, `tests/tools/test_cst_sc_text_sets.py` (new), `tests/tools/test_docs_update_missing_words.py`.

## Findings

CodeRabbit: one major (live steps said ignored old-key finished entries were harmless), six gui2 findings about the content of single draft entries.
pi first run: seven findings. pi second run: five findings.

## Fixes Applied

- Live steps and spec now say old-key finished entries are not carried over, with the measured exposure (two test users, 18 words under `ap`, none left in the new files).
- A test with two real contributors on one folder now crosses from a finished list into `get_next_item`. Removing the skip loop fails 3 of 13 controller tests.
- Four tests pin the exact output of `make_cst_text_list` after the refactor. Breaking the dedupe step fails 2 of them.
- Tech note wording corrected twice (best-effort check, 478 dropped fragments, Jātaka rows versus Pass1 books).
- Not real, with reasons in `plan.md`: pi first run findings 1 and 4, pi second run findings 1 and 3. Skipped: pi first run findings 2 and 6, pi second run finding 5.
- Not caused by this thread: the six CodeRabbit gui2 findings. All 1262 entries in the new files are identical to the old files.

## Test Evidence

- `uv run pytest tests/gui2 tests/tools tests/scripts -q`: 2220 passed, 7 deselected.
- `just typecheck`: 0 errors. ruff clean. pyright 0 errors on every touched file.
- Live server, read-only: all 8 contributor units use one data folder; the server checkout is clean on `main`; the window is started by cron at 00:30 and pulls `main` after its 30-minute notice.
- The split script was run with `--write` once, on 2026-11-14. Nine new files load with the expected counts.

## Verdict

PASSED
