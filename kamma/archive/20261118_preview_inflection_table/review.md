# Review: preview builds its button content

**Verdict: PASSED**

Reviewed 2026-11-18 by two independent reviewers run in parallel on the uncommitted change:
DeepSeek flash through pi (thinking off, one request, 41 KB) and CodeRabbit once per code
folder. The owner also ran the real gui2 and saw the inflection table; the audio and frequency
checks were not reported back. No separate `/kamma:3-review` run: the owner asked for this
review by name and then asked to finalize.

## Files Changed
- `db/inflections/generate_inflection_tables.py` (extracted `make_inflection_table`)
- `gui2/preview.py` (inflection table, frequency note, embedded audio)
- `tests/gui2/test_preview.py`
- `tests/tools/test_all_tipitaka_words.py` (new)
- `tools/all_tipitaka_words.py` (reads the SuttaCentral list)

## Findings
Fixed: frequency note shown for saved words with no matches (DeepSeek 6, real); `Container`
accepted a plain string (CodeRabbit); autouse fixture failed without the word lists
(CodeRabbit, major); audio tests needed the audio db (CodeRabbit); voice checks too weak
(CodeRabbit); word-list test not hermetic (CodeRabbit, unverified, accepted).

Rejected with reasons (see `plan.md`, review round): DeepSeek 1 and 2 (preview writes only to a
private copy, never the session or the saved word), 3 (build makes the same table), 4
(decode undoes encode), 5 (shared audio helper, milliseconds), 7 (already in the spec).

## Fixes Applied
All fixed findings above, each with a test that failed first or a revert check.

## Test Evidence
- `uv run pytest tests/gui2 tests/db tests/tools tests/audio tests/exporter`: 2707 passed,
  2 failed. The 2 are PRE-EXISTING abbreviation tests that import nothing this thread touched.
- `tests/gui2/test_preview.py`: 31 passed. `tests/tools/test_all_tipitaka_words.py`: 1 passed,
  fails when the SuttaCentral read is reverted.
- Equivalence: 500 of 500 sampled rebuilt tables equal the stored ones (before the word-list fix).
- `just typecheck`: 0 errors. ruff and pyright clean on every touched file.
