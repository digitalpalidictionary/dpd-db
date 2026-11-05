# Gate 3: readiness audit of the plan (2026-11-05)

Backend: pi, provider `deepseek`, model `deepseek-flash`, thinking off, tools read, grep, find, ls, no session. Five Goldfish, run one at a time (15:09 to 15:14), one per part of the plan: A lines 38-340 (phase 0, tasks 1 to 3), B lines 340-642 (tasks 4 to 8), C lines 642-1049 (tasks 9 to 11), D lines 1049-1320 (tasks 12 and 13), E lines 1320-end (phases 5 and 6). Each also read the executor rules (lines 1-37). One whole-plan review was not used: the plan is 66 KB. Raw reports: `raw/gate3_A.md` to `raw/gate3_E.md`. No backend switch, no failure.

The question each Goldfish got: can a less capable model do each task without a design decision the plan left open; does every "Find" snippet exist once in the real file; does every test fail before and pass after for the stated reason; is every command right. Items a reviewer marked correct or fine are not counted as findings.

Finding ids: A to E, as above.

## Facts checked before deciding

- `gui2/preview.py` does not import `gui2.main`, so a function-level import in `run_app` makes no cycle. `gui2/main.py` loads its views lazily (inside `App.__init__`), so a top-level import of `gui2.preview` would pull jinja and the webapp classes into every import of `gui2.main`. Decision: import inside `run_app`; the test patches `gui2.preview.PREVIEW_DIR`.
- `just typecheck` runs pyrefly (`justfile`), not pyright.
- The existing pull test (`test_contrib_pull.py` ~1006-1010) calls `monkeypatch.chdir`, patches `SharedFiles.default`, and `config_read`; the new `_run_main` now does the same.
- `ensure_translation_db.main()` returns 1 when the file is missing; `sys.exit(1)` gives exit code 1; `_run` uses `subprocess.run(check=True)`, which raises `CalledProcessError` on a non-zero exit. So the window logs a failure. Reviewer D4 (says it would not raise) is wrong.
- Task 11 and task 12 do not edit the builders dict at `main.py:188`; only task 10 does. Reviewer C1 is wrong.
- `graphify-out/` held one snapshot on 2026-11-05 (reviewer E2).

## Dispositions (47 findings)

| Id | Severity | Decision | How checked | Where fixed |
| :--- | :--- | :--- | :--- | :--- |
| A1 | Blocker | Accept: the exact failing assert is named | read the test and `get_all_decon_no_headwords` | plan 3.1 |
| A2 | Major | Accept in part: the expected message text is written in; the STOP stays for a real difference | read SQLAlchemy behaviour in the spec check | plan 3.1 |
| A3 | Major | Accept: the import moves inside `run_app`; no cycle exists | rg imports of `gui2.preview` | plan 2.1, 2.2 |
| A4 | Major | Accept: step A makes the test fail on a `run_app` without `mkdir` first | read the plan | plan 2.2 |
| A5 | Major | Accept: two tests for the X-button messages added; site 1 stays checked by reading | read `_click_x_button` | plan 1.1, 1.5 |
| A6 | Major | Reject: both snippets exist once at the stated indent (reviewer confirms) | rg `Clipboard` | none |
| A7 | Nit | Reject: insertion point is unambiguous | read | none |
| A8 | Nit | Reject: confirms the plan is right | read `clear_all_fields` | none |
| A9 | Major | Accept: 0.2 says pyrefly | read `justfile` | plan 0.2 |
| A10 | Nit | Reject: a new file keeps the read-only session visible; the existing fixture has a different shape | read both | none |
| B1 | Blocker | Accept: a line says no hit is expected in `exporter/` or the `justfile` and what to do if one appears | rg sweep | plan 4.1 |
| B2 | Major | Reject: the reviewer found the test works; no `pth` is needed | read the fixture | none |
| B3 | Nit | Reject: both paths give `dpd.db.prev` | read | none |
| B4 | Blocker | Accept: `_run_main` now changes folder, patches `SharedFiles.default`, and takes `tmp_path` | read the existing pull test | plan 7.1 |
| B5 | Blocker | Accept: the plan names which tests must fail and which are guards that already pass | read | plan 7.1 |
| B6 | Major | Accept: the dead `invalidate_relationship_detector` line is removed from the test | read `rename_pattern_in_headwords` | plan 5.1 |
| B7 | Major | Accept: the weak assertion is replaced by an exact bytes check | read | plan 8.1 |
| B8 | Major | Reject: no new type error; the helper already exists | read | none |
| B9 | Nit | Reject: line numbers are right | read | none |
| B10 | Nit | Accept: the line numbers of the neighbouring test are corrected | read | plan 5.1 |
| B11 | Nit | Reject: `archive/` is excluded by the glob on purpose | read | none |
| B12 | Nit | Reject: `Path` is imported | read | none |
| B13 | Nit | Accept: a note says the INFO line stays out of the status file | read `_write_status` | plan 8.1 |
| B14 | Nit | Reject: the double run matches an existing test | read | none |
| C1 | Blocker | Reject: tasks 11 and 12 do not edit the builders dict | read both tasks | none |
| C2 | Blocker | Accept: the plan says to keep the call without a `page` argument | read `_reset_to_default_clicked` | plan 10.2 |
| C3 | Major | Accept: the order of failures between steps 10.1, 10.2 and 10.3 is written out | read | plan 10.1 |
| C4 | Major | Accept: a note on what the toolkit stand-in answers | read `FilterComponent.__init__` | plan 10.1 |
| C5 | Major | Reject: the test is correct for both values of `web` | read | none |
| C9 | Nit | Reject: the snippet is found exactly once | read | none |
| C11 | Nit | Accept: the exact resulting line is given | read `_app_on_tab` | plan 11.1 |
| C12 | Nit | Accept: the plan says to reuse the existing helpers | read | plan 11.2 |
| D1 | Blocker | Accept in part: each README row is now its own find and replace; reject the "false doc" claim (`Pass1Auto` is not in `BASE_TABS`) | read `contributor_tabs.py`, README | plan 12.3 |
| D2 | Major | Accept: the plan says why the constructor needs the field and how overrides work | read `_steps` | plan 13.3 |
| D3 | Major | Accept in part: `problems: 1` added to the assert; reject the rest (fresh setup, one log) | read `Setup` | plan 13.3 |
| D4 | Major | Reject: exit code 1 raises with `check=True`; a note explains it | read `_run` | plan 13.4 |
| D5 | Major | Reject: the reviewer says no fix is needed | read | none |
| D7 | Nit | Reject: the `rg` is the last step of 13.6 | read | none |
| D8 | Nit | Reject: acceptable as is | read | none |
| E1 | Blocker | Accept in part: the loops now print a final line, run the whole folder, and point to the failing run's temp folder; the phase stays | read the test and `_write_status` | plan 14.1 to 14.3 |
| E2 | Blocker | Accept: prune only with two or more snapshots; stop if `graphify` is missing | `ls graphify-out` | plan 15.3 |
| E3 | Major | Accept: a subset-of-names check | read | plan 15.1 |
| E4 | Major | Accept: STOP if a path does not exist | read | plan 15.2 |
| E5 | Major | Accept: marked as owner-only text | read | plan 15.5 |
| E6 | Nit | Accept: the loops print `ALL n RUNS PASSED` | read | plan 14.1 |
| E7 | Nit | Reject: cosmetic | none | none |
| E8 | Nit | Reject: the duplicates are deliberate and now conditional on tasks 8 and 13 | read | plan 15.5 |

## Counts

Counted from the table by the first word of each Decision cell: 47 findings, 27 accepted (4 of them in part), 20 rejected, 0 escalated.
