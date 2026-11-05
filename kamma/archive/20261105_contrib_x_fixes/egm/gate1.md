# Gate 1: stress-test of the idea (2026-11-05)

Backend: pi, provider `deepseek`, model `deepseek-flash`, thinking off, tools read, grep, find, ls, no session. Six Goldfish, run one at a time (14:48 to 14:51). Raw reports: `raw/gate1_<lens>.md`.

Backend switch: the first smoke probe on `azure` / `deepseek-v4.1-flash` hung past the 180 s cap. It was replaced by the direct `deepseek` provider, which passed the probe (read one file), a second probe (grep tool) and all six runs. Azure was not used.

Finding ids: C contrarian, K cost, U ux, M migration, O observability, D debt.

## Facts checked against the code before deciding

- `dpd.db.prev` is made by `_capture_rollback` (`maintenance_window.py:273-288`, name built with `+ ".prev"`) on every run that passes the dirty check, and read back by `_restore_rollback`. The Goldfish that said it "does not appear" was wrong. The brief's note was right that it is the rollback copy.
- The worktree default is `<project-root>_contrib_worktree` beside the clone (`maintenance_window.py:456-457`). `contrib_push._ensure_worktree` (`contrib_push.py:51-56`) makes it with `git worktree add --detach` only when `.git` is missing, then reuses it every night.
- `contrib_pull.main` skips `maybe_notify` for any outcome starting `skipped` (`contrib_pull.py:596`). `maybe_notify` handles only `pulled with problems`, `failed` and `partial`. No existing notice covers "skipped: editor open". The skip is set at two sites: `run` (~526, before the pull) and `_pull` (~476, editor opened mid-pull).
- `gui2/user.py:24-29` sets `routed_username = self.username or "1"` at start and `is_not_primary()` reads it. `gui2/toolkit.py:52` uses `resolve_username() or "1"` at the same start-up moment. Both already agree. Spec item 9 (username) is stale.
- `mark_corpus_stale()` only sets a flag; the corpus reloads on the next `load_corpus()` (`database_manager.py:210-265`).
- `FilterTabView` reads `get_first_preset()`; with no preset file it uses the defaults passed in (`filter_tab_view.py:60-100`). The Save Changes button is built without `disabled` (`filter_component.py:174`); `read_only` is set on the view after it is built (`main.py:486-487`).
- `_make_logger` clears its handlers and writes to a per-tmp-path file; the flaky test runs one window in a fresh `tmp_path`. A theory that needs two runs in one log (C5, U8, O5, D5) does not fit that test.

## Dispositions (40 findings)

| Id | Severity | Decision | How checked | Where fixed |
| :--- | :--- | :--- | :--- | :--- |
| C1 | Blocker | Accept for the db copy; worktree part escalated (E1) | read `maintenance_window.py` | spec: Server cleanup |
| C2 | Major | Accept the placement (change in `main`); reject the question (owner decided "every time") | read `contrib_pull.py` | spec: Skip notice |
| C3 | Major | Reject folding #4 into #12; delete part accepted via D4 | read callers | spec: Helper server |
| C4 | Nit | Accept in part (see O1) | read `database_manager.py` | spec: Decon cache |
| C5 | Nit | Reject splitting out; owner chose to investigate | owner answer | spec: Flaky test |
| C6 | Nit | Accept for the username item; reject for the preset and Save button (owner decisions) | read `user.py`, `toolkit.py` | spec: Dropped |
| K1 | Blocker | Accept (same as C1) | read code | spec: Server cleanup |
| K2 | Blocker | Escalate (E1) | read `contrib_push.py` | spec: Server cleanup |
| K3 | Major | Reject: owner decided every editor-open skip | owner answer | spec: Skip notice |
| K4 | Major | Reject: the stale flag is lazy | read `database_manager.py` | none |
| K5 | Major | Reject the probe; accept a message check instead (O1) | read code | spec: Decon cache |
| K6 | Nit | Reject | read code | none |
| K7 | Nit | Reject: columns offered do not change | read `filter_tab_view.py` | none |
| U1 | Blocker | Reject: "editor open" is not a `pulled with problems` outcome, so no duplicate | read `maybe_notify` | none |
| U2 | Major | Accept: disable the Save button where `read_only` is set; keep the refusal in the handlers for the Ctrl+S key | read `filter_component.py`, `main.py` | spec: Save button |
| U3 | Major | Accept: a saved preset wins; change only the defaults used when none exists | read `filter_tab_view.py` | spec: Starter preset |
| U4 | Major | Accept: gate the key handler and the shortcuts popup on the same test | read `main.py` | spec: Alt keys |
| U5 | Nit | Accept: other errors still print | read code | spec: Decon cache |
| U6 | Nit | Accept: one line message on a failed copy | read `pass2_add_view.py` | spec: Clipboard |
| U7 | Nit | Accept: log what the cleanup deleted | read code | spec: Server cleanup |
| U8 | Nit | Reject: theory does not fit the test (see facts) | read the test | spec: Flaky test |
| M1 | Blocker | Accept for the db copy (as C1); worktree part escalated (E1) | read code | spec: Server cleanup |
| M2 | Major | Accept: keep the try, the print for other errors, and the rollback | read code | spec: Decon cache |
| M3 | Major | Reject: stored presets keep working; no column set changes | read `filter_presets_manager.py` | none |
| M4 | Major | Reject the feature flag: owner decided to remove | owner answer | none |
| M5 | Nit | Accept: username task dropped | read `user.py` | spec: Dropped |
| M6 | Nit | Reject: spec and plan follow | none | none |
| O1 | Blocker | Accept: hide the print only when the message says the database is read-only | read code | spec: Decon cache |
| O2 | Blocker | Accept: log before deleting; reject the refuse-if-unpushed check (the push runs earlier in the same window and the worktree is rebuilt from a commit) | read both scripts | spec: Server cleanup |
| O3 | Major | Reject (as K3) | owner answer | none |
| O4 | Major | Accept (as U6); reject the once-per-session log | read code | spec: Clipboard |
| O5 | Major | Reject: "production bug" is not shown; the test runs one window | read the test | spec: Flaky test |
| O6 | Nit | Reject: no change to those two files | read `user.py` | none |
| O7 | Nit | Reject: unrequested | none | none |
| D1 | Blocker | Accept (as C6, M5) | read `user.py` | spec: Dropped |
| D2 | Blocker | Accept the popup gate; reject a shared helper (one call site) | read `main.py` | spec: Alt keys |
| D3 | Major | Accept: delete the copy only when the outcome is not FAILED; reject "a SKIPPED run keeps the only copy" (the db did not change that night) | read `run_maintenance` | spec: Server cleanup |
| D4 | Major | Accept in part: delete the call, the print and the module with its tests; sweep for stale mentions | read callers | spec: Helper server |
| D5 | Nit | Reject (as C5) | read the test | spec: Flaky test |
| D6 | Nit | Accept: same notice at both skip sites | read `contrib_pull.py` | spec: Skip notice |

## Escalation

E1: delete the nightly worktree after a good run, or keep it? The owner chose "delete both" after being told it was a temporary checkout. The code shows it is reused each night, and a deleted one is rebuilt by `git worktree add` the next night. Asked of the owner below.

## Counts

Counted from the table above by the first word of each Decision cell: 40 findings, 22 accepted (3 of them in part), 17 rejected, 1 escalated (E1). Three rows (C1, K2, M1) carry the E1 worktree question.
