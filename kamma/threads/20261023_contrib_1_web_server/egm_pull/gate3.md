# Gate 3: implementation-readiness audit of plan.md (2026-11-04)

## Backend and run record
- Backend: pi, azure, deepseek-v4.1-flash, `--tools read --no-session`, `--mode json`. One reviewer.
- The first look at 30 s showed an empty file, the same sign as the earlier hangs. At 60 s it had 11 file reads and 800 KB, so it was not hung and was not stopped. It finished in about 3 min.
- Told not to open `egm/`. Read the plan and spec only.

## Raw findings (verbatim)

All checks done from the plan, spec, and referenced code (`merge_contrib_files.py`, `contrib_reconcile.py`, `contrib_entry.py`, `gui2/paths.py`, `gui2/database_manager.py`, `tools/configger.py`, `justfile`, `pyproject.toml`, `tests/.../test_merge_contrib_files.py`, `gui2/data/additions_alice.json`). Findings, worst first.

**BLOCKER — `run()` cannot be tested in isolation; tests write the real repo.**
plan.md §1.6 calls `merge_all(repo/"gui2"/"data", SharedFiles.default(), …)`. `SharedFiles.default()` (`scripts/server_contrib/merge_contrib_files.py`, staticmethod) builds from `Gui2Paths()` with no base dir and `DbTestManager()`, both cwd-relative — it ignores `repo`. Any §1.6 test with a temp repo will merge into the real `shared_data/user_dictionary.txt`, `shared_data/deconstructor/*`, and `db_tests/db_tests_columns.tsv`. `merge_test_exceptions` can mutate `db_tests/db_tests_columns.tsv` for real. Fix: add a `SharedFiles` parameter to `run`/`prepare` (default constructed from `repo` in `main`), never `SharedFiles.default()` inside the tested path.

**BLOCKER — the undo step orders a forbidden command.**
plan.md §2.5: "restore tracked shared files by name only"; §3.5 repeats "restore the named file from git". The only ways are `git checkout -- <path>` / `git restore`, explicitly banned in the Executor rules ("**Never** run … `git restore`, `git checkout --`"). §2.4 backs up only contributor files + `contrib_lines_merged.json`, not the six shared files, so the agent has no legal restore path. Fix: add the six shared files to the §2.4 backup and say "copy them back by name".

**MAJOR — test §1.5(a) cannot pass as written.**
It puts `{"_source_key": "alice_1", "_source_hash": entry_hash(entry)}` in `gui2/data/additions_added.json`. `load_processed` (`contrib_reconcile.py`) requires a JSON **list** and raises `RuntimeError("expected a JSON list …")` on a dict. Fix: write `[{...}]`.

**MAJOR — `main()` never specified to print the status.**
`run` returns a `Status` (§1.6) but the plan never says `main` prints it, yet §2.4 ("It prints what it would copy") and §3.3 verify depend on visible dry-run output. Add "`main` prints the status, including dry-run".

**MAJOR — §3.3 verify cannot succeed.**
`just contrib-pull-install` only enables the **timer** (`systemctl --user enable --now dpd-contrib-pull.timer`). The service has never run, and `systemd-run` creates a transient unit, not `dpd-contrib-pull.service`. So `systemctl --user status dpd-contrib-pull.service --no-pager` "shows the last result" is false. Fix: verify on the `run-*.service` transient unit instead.

**MAJOR — per-contributor attribution undefined for malformed names.**
§1.5 `select_names` returns `user -> reason`, and §3 says any bad name skips that contributor. But a name failing the user regex or containing `/` (spec step 3, and §1.4 "returned as-is and fails `kind_of`") has no derivable user. The plan does not say whether it is dropped silently or bucketed. Fix: state the fallback (e.g. skip non-attributable names, log the raw name).

**MAJOR — `REMOTE_SOURCE_SUFFIX` default contradicts the restricted key.**
§1.6 documents the default as `:/var/lib/dpd/contrib_data/`, a full remote path, while the key is `restrict,command="/usr/bin/rrsync -ro /var/lib/dpd/contrib_data"` (§2.2), whose paths are relative to that root. §2.3 discovers the working form, but the constant's stated default is wrong and only phase-2 fixes it. Say the default is a placeholder and 2.3 must replace it.

**NIT — `kind_of` rejects legitimate names.**
§1.3 refuses any name containing `added`, so a contributor named `additions_addedfoo.json` is dropped. Use the `_added` log exclusion (as `delivered_files` does) instead.

**NIT — symlink listing may not appear.**
§1.4 expects `rsync -r --list-only` to report a symlink's type; without `-l`, rsync may print "skipping non-regular file" and omit it, failing the test. §1.1 asks about link vs regular but not this. Settle in 1.0 or add `-l`.

**NIT — verify-line that cannot mechanically fail.**
§4.6 verify: "the list is written and every item is fixed" — self-referential. Make it "every listed item has a commit-ready change and none remains".

**NIT — listing filter not implemented.**
Spec step 2 says the listing asks only for `DELIVERED_KINDS` patterns, but §1.4's `list_source` runs bare `rsync -r --list-only`. Functionally masked by `select_names`, but the plan as runbook does not match the spec.

Named functions all exist with claimed signatures; the existing test file `tests/scripts/server_contrib/test_merge_contrib_files.py` exists; `db_test_exceptions_alice.tsv` is absent locally and §1.3 correctly provides a fallback.

## Disposition table

| ID | Finding | Sev | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| G3.1 | `run()` tests would write the real shared files | Blocker | Accept | code: merge_contrib_files.py:86-96 `SharedFiles.default()` uses `Gui2Paths()` and `DbTestManager()`, both cwd-relative | plan 1.6 (`shared` parameter, git-status check) |
| G3.2 | Undo orders a git restore the executor rules forbid | Blocker | Accept | plan read | plan 2.4, 2.5, 3.5 |
| G3.3 | Test 1.5(a) writes a dict where a list is required | Major | Accept | code: contrib_reconcile.py:100 "expected a JSON list" | plan 1.5 |
| G3.4 | `main` never prints the status | Major | Accept | plan read | plan 1.6 |
| G3.5 | 3.3 verify checks a unit that has not run | Major | Accept | systemd behaviour: `systemd-run` makes a transient unit | plan 3.3 |
| G3.6 | No rule for names with no readable user | Major | Accept | plan read | plan 1.5 (`ignored_names`) |
| G3.7 | `REMOTE_SOURCE_SUFFIX` default contradicts the restricted key | Major | Accept | plan read | plan 1.6 |
| G3.8 | `added` also rejects a user named `addedfoo` | Nit | Reject | code: add_contributor.sh already refuses any user name containing `added` | none |
| G3.9 | Symlink may not appear in `--list-only` | Nit | Accept | rsync behaviour | plan 1.4 |
| G3.10 | 4.6 verify cannot fail | Nit | Accept | — | plan 4.6 |
| G3.11 | Listing filter in spec does not match the plan | Nit | Accept | — | spec step 2 |
