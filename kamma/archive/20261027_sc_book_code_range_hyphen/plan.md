# Plan: range code hyphen fix (issue #208)

**Thread:** 20261027_sc_book_code_range_hyphen · **Spec:** `spec.md` (read first)
**GitHub issue:** https://github.com/digitalpalidictionary/dpd-db/issues/208

## Architecture Decisions
- One-line regex change at the source. Use `re.sub`, not `re.match(...).group()`: pyright basic mode flags the Optional result.
- Tests go in the existing tests/db/test_sutta_info.py, next to the `s_4nt_link` and `dhamma_gift` tests.
- The `rstrip("-")` workaround and its comment in `s_4nt_link` are removed. The user approved this on 2026-10-27.
  The existing `SN39.1-15` test of `s_4nt_link` (tests/db/test_sutta_info.py) guards it.

## Phase 1 — Failing tests first
- [x] 1.1 In tests/db/test_sutta_info.py add:
      (a) a parametrized `sc_book_code` test: `AN2.1-10`, `AN1.1-10`, `AN2.11-20`, `SN12.1-10`, `SN39.1-15` all
      give the letters only; unchanged `AN3.1`, `SN1.1`, `MN1`, `DN1`, `SNP1.1`, `THAG1.1`, `ITI1`, `DHP1-20`,
      `DHP90-00`, `UD1.1`;
      (b) `tbw` and `tbw_legacy` for `AN2.1-10` with `book_code = "AN"`: exact URL, no `-` in the folder part;
      (c) `sc_vagga_link` for an SN39 saṃyutta row (dpd_code `SN39`, sc_code `SN39.1-15`, dpd_sutta set so
      `is_samyutta` is true).
      → verify: run `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && uv run pytest tests/db/test_sutta_info.py -q`.
      Expect only the range cases to fail, with `'AN-' == 'AN'`. Paste the failure output here.
      Baseline before the new tests: 21 passed. Result with the new tests (2026-10-27): `7 failed, 31 passed`.
      Failures: the 5 range cases of the `sc_book_code` test (`AN2.1-10`, `AN1.1-10`, `AN2.11-20`, `SN12.1-10`,
      `SN39.1-15`); `tbw` gave `https://thebuddhaswords.net/an-/an2.1-10.html` instead of `.../an/an2.1-10.html`;
      `sc_vagga_link` gave `None` instead of the SN39 pitaka URL (book code `SN-` misses the `sn` branch).
      The 10 unchanged-code cases pass before the fix.

## Phase 2 — Fix
- [x] 2.1 db/models.py line 834: change the regex to `re.sub(r"\d.*", "", self.sc_code)`.
      → verify: run the same pytest command. Expect all pass.
- [x] 2.2 In `s_4nt_link` (db/models.py ~927-928) delete the stale comment and replace
      `sc_book_code.rstrip("-").lower()` with `sc_book_code.lower()`.
      → verify: run the same pytest command. Expect all pass, including the `SN39.1-15` and `AN3.156-162` tests.

## Phase 3 — Verify
- [x] 3.1 Run `uv run ruff check` and `uv run ruff format --check` on db/models.py and tests/db/test_sutta_info.py,
      `uv run pyright db/models.py`, then `uv run pytest tests/db -q`.
      → verify: all exit 0. If ruff format wants a large diff, do not apply it. Report it.
      Result 2026-10-27: ruff check passed, ruff format --check clean on both files, pyright 0 errors, `uv run pytest tests/db -q` 255 passed.
- [x] 3.2 Re-run the all-rows probe (/tmp/probe208/probe.py) against the changed code. It must call the real
      properties, so remove the `sc_book_code` override for the new side.
      → verify: 215 / 215 / 215 / 4 / 0 changed rows against the old regex output.
      Result: the first probe showed 215 for `s_4nt_link` because its "old" side lacked the removed workaround (probe artefact).
      Redone against a real copy of the old models.py: `{'sc_book_code': 215, 'tbw': 215, 'tbw_legacy': 215, 'sc_vagga_link': 4, 's_4nt_link': 0}` over 5,115 rows.
- [x] 3.3 Guard proof: put the old regex back (keep 2.2), run the new tests, record how many fail, restore the
      fix in the same command.
      → verify: the fail count is above 0 and the failures are the range cases. After restore, all pass.
      Result: with the old regex and 2.2 kept, `8 failed, 30 passed`: the 7 new tests plus the existing `s_4nt_link` `SN39.1-15` test. All are assertion failures. After restore: `38 passed`.

## After the thread
- Run `/kamma:3-review` (CodeRabbit and a subagent, in parallel), then `/kamma:4-finalize`. No commit unless the user asks.
