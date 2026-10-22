# PLAN — Lookup keys with outer spaces, and one empty key
GitHub issue: https://github.com/digitalpalidictionary/dpd-db/issues/270 (read-only; do not comment or close)
Spec: `kamma/threads/20261022_lookup_key_spaces/spec.md`

## Architecture Decisions
- Fix each source, not the shared sync function. The sync function is proven and used by many writers.
- The four variant extractors share one dict. Trimming in `key_cleaner` merges spaced and trimmed twins with no merge code.
- The existing stale-row clearing removes the old rows on the next build. No one-off SQL on `dpd.db`.
- Trim in the Go reader instead of editing the data file. The same reader already trims `split`.

## Phase 1 — Failing tests first
Baseline before any edit: `uv run pytest tests/db/variants tests/tools/test_sutta_codes.py tests/db/suttas` gave 98 passed. `go test ./go_modules/deconstructor/importer/` passed.

- [x] Write a test in `tests/db/variants/test_variants_modules.py` that `key_cleaner` trims leading and trailing spaces (for example `" word "` gives `"word"`) and keeps inner spaces.
  → verify: run `uv run pytest tests/db/variants/test_variants_modules.py`, expect the new test to fail. Paste the failure output below this task.
  Failure (before the fix): `test_key_cleaner_trims_outer_spaces` fails 5 of 6 cases, for example `AssertionError: assert 'ord ' == 'word'` and `assert 'ūsa khaṇḍaṃ ' == 'ūsa khaṇḍaṃ'`. (The `" word"` case shows as `' ord'` in the diff marker, the value is `' word'`.)
- [x] Write a test in `tests/tools/test_sutta_codes.py` that `make_list_of_sutta_codes` returns no empty string when `sc_code` is `""`.
  → verify: run `uv run pytest tests/tools/test_sutta_codes.py`, expect the new test to fail. Paste the failure output below this task.
  Failure (before the fix): `AssertionError: assert ['', 'SN46.36'] == ['SN46.36']`.
- [x] Write a Go test in `go_modules/deconstructor/importer/` that `makeMatchItems` returns a trimmed `Word` for a corrections line with a trailing space. Use a temp TSV or a small helper so the test does not read the real file.
  → verify: run `go test ./go_modules/deconstructor/importer/`, expect the new test to fail. Paste the failure output below this task.
  Change from the plan: the reader body moved into a helper `matchItemsFromRows` with no change in behaviour (same pattern as `cstAbbreviationsFromRows` in `unmatched.go`). The test calls the helper.
  Failure (before the fix): `item 0: expected word "ūsakhaṇḍaṃ", got "ūsakhaṇḍaṃ "` and `item 1: expected word "akkharappabhedānaṃ", got " akkharappabhedānaṃ"`.
- [x] Note: the existing `mixed` case in `tests/db/variants/test_variants_modules_fixtures.json` expects `"dukkha  "` (two trailing spaces). That is the bug itself. The fix changes it to `"dukkha"`. This is a deliberate change, not a weakened check.

## Phase 2 — The fixes
- [x] In `db/variants/variants_modules.py`, make `key_cleaner` return the trimmed key.
  → verify: run `uv run pytest tests/db/variants/`, expect all pass. Add a check that `"x "` and `"x"` from two extractors give one key in the dict.
  Result: 33 pass in `test_variants_modules.py`. A twin test covers the merge. The `mixed` fixture changed to `"dukkha"`.
- [x] In `tools/sutta_codes.py`, skip an empty `sc_code` (guard before the `add` and before the range and prefix code that reads it).
  → verify: run `uv run pytest tests/tools/test_sutta_codes.py tests/db/suttas/`, expect all pass.
- [x] In `go_modules/deconstructor/importer/manualCorrections.go`, set `mi.Word = strings.TrimSpace(d["compound"])`.
  → verify: run `go test ./go_modules/deconstructor/importer/` and `go vet ./go_modules/...`, expect pass.
- [x] Lint every touched file: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright <file>`. For files under `tests/` use `uv run pyright --project /dev/null <file>`.
  → verify: all three report no errors on each touched file. Then run `just typecheck`, expect pass.
- [x] Phase check: run the related tests together.
  → verify: `uv run pytest tests/db/variants tests/tools/test_sutta_codes.py tests/db/suttas`, expect all pass.

Lint note: `tests/tools/test_sutta_codes.py` had an old pyright error (the `aksharamukha` stub). Fixed with `types.ModuleType` plus `setattr`. Same behaviour. `just typecheck`: 0 errors. 106 tests pass.

## Phase 2b — Fixes from review (DeepSeek pro review, 2026-10-22)
- [x] Second Go reader (`makeManualCorrections` in `unmatched.go`) did not trim `compound`. Test `TestManualCorrectionWordsAreTrimmed` written first.
  → verify: before the fix `go test ./go_modules/deconstructor/importer/` failed with `manual match item word "vinivijjhanaṭṭhenāti" is not excluded from the input` and the same for `ūsakhaṇḍaṃ`. After the fix it passes. The reader body moved into `manualCorrectionWordsFromRows`.
- [x] Whitespace-only `sc_code` passed the guard. Test cases `" "` and `"\t "` added; before the fix they failed (`[' ', 'SN46.36'] == ['SN46.36']`). The guard now uses `su.sc_code.strip()`. The data has 0 null and 0 untrimmed `sc_code` values.
  → verify: `uv run pytest tests/db/variants tests/tools/test_sutta_codes.py tests/db/suttas` gives 108 passed. `go test ./go_modules/deconstructor/...` passes. `just typecheck` gives 0 errors. ruff and pyright are clean.
- [x] Re-ran `just decon` on the live database.
  → verify: `vinivijjhanaṭṭhenāti` now holds `["vinivijjhana + aṭṭhena + iti"]`, the curated split. Spaced keys 0, empty keys 0.
- Skipped: nit, `key_cleaner` docstring does not mention trimming. Existing comments stay as they are.

## Phase 3 — Proof on real data
- [x] Revert each fix by hand, one at a time, in a scratch copy of the file, and run its test.
  → verify: report how many tests fail for each revert. The failure must be the asserted behaviour, not a compile error. Restore the fix in the same command.
  Result: key cleaner reverted gives 8 failed, 25 passed (all assertion failures). Sutta code builder reverted gives 1 failed (`['', 'SN46.36'] == ['SN46.36']`). Go reader reverted gives 1 failed (`got "ūsakhaṇḍaṃ "`). All three restored and green.
- [x] Copy `dpd.db` to the scratchpad. Run the variant sync, the sutta-to-lookup sync and the deconstructor sync against the copy 
  Change from the plan: the scripts have no path option, so they ran on the live `dpd.db` after a backup (`.backup` to the scratchpad). The user allowed it and the config edit. `make_variants` was set to `yes` for the run and put back to `no`. Steps run: variants, `just decon`, inflections_to_headwords, suttas_to_lookup. Exit 0..
  → verify: on the rebuilt database, `SELECT count(*) FROM lookup WHERE lookup_key != trim(lookup_key)` returns 0 and `WHERE lookup_key = ''` returns 0.
- [x] On the copy, check the 13 old trimmed twins and the 29 other rows.
  → verify: each of the 13 twins still has its headwords and grammar and now holds the variant or deconstruction content. The 29 others exist under trimmed keys. Print the lists and read them.
  Result: of the 42, 13 had a twin and 29 did not. Headwords and grammar of the 13 twins: 0 changed. All 13 twins hold the content of their spaced row (CORRECTION: this first check was too weak for `vinivijjhanaṭṭhenāti`. Its twin already had a non-empty deconstruction, so the check passed while the curated split was lost. Review found the cause. See Phase 2b. After the fix and a re-run the curated split is present.). All 29 others now exist under trimmed keys with their content. No new key appeared other than those 29.
- [x] Compare the copy against the live database for unrelated rows.
  → verify: row count differs only by the removed or merged spaced rows and the empty row. Print the diff counts.
  Result: 1,283,190 rows before, 1,283,176 after (13 merged + 1 empty row deleted). Headwords changed on 0 rows. Variant changed on 11 rows and deconstructor on 1 row, all among the 13 twins. Zero changed rows outside the 42 trimmed keys.


After the rebuild: `lookup_key != trim(lookup_key)` returns 0 and `lookup_key = ''` returns 0.

## Smoke gate (full suite)
- `uv run pytest tests/ -q`: 2339 passed, 13 deselected, after one run stopped at a failure.
- PRE-EXISTING — NOT CAUSED BY THIS THREAD: `tests/tools/test_tipitaka_db_deadline.py::test_four_ordinary_searches_at_once_do_not_time_each_other_out` failed once while the machine load average was 36. The file is untracked and belongs to thread `20261021_webapp_search_limits`. Run alone, all 10 of its tests pass.
- NOTICED — NOT TOUCHING: `go_modules/deconstructor/importer/importer.go` has unused `pl` and `pf` vars (editor hint).
