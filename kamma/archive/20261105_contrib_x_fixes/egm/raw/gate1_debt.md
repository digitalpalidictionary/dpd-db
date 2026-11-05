Findings.

## Blocker

**1. Task 9 (shared username value) is already implemented and the brief describes it wrongly.**
`gui2/user.py:24-29` and `:77-78` already resolve one value: `routed_username = self.username or "1"`, and `is_not_primary()` reads `routed_username`, deliberately *not* live `self.username` (comment at `:25-28`). `gui2/toolkit.py:52` uses `resolve_username() or "1"`. So the "two values" the task wants unified are already unified, and the "fix" as worded (make `is_not_primary()` follow `toolkit.py`'s value) would *introduce* the bug the comment warns about: after the first-run dialog sets a username, `is_not_primary()` would flip to True mid-session while `Gui2Paths` still points at the primary user's files — a contributor would then write primary-user paths, and `gui2/pass2_add_view.py:986`, `save_router.py:41` would take the wrong branch. Fix: drop task 9 or restate it as "assert the caveat in a test"; do not touch `user.py:24-29`.

**2. Task 12 (web-only Alt shortcuts) hardens a fragile discriminator.**
`gui2/main.py:299` gates every Alt branch on `e.alt` alone. Adding `if self.page.web: return` splits behaviour on `page.web`, which is *already* the only web/desktop test (`gui2/preview.py:170`) — the brief lists it as an unverified assumption. Brittle state: a second call site of a property nothing else guarantees, so the desktop-only audio work (task 8) plus this gives two independent web checks, and Flet upgrades or a `--web` run of desktop code silently changes key behaviour with no test asserting the desktop side stays. Fix: one helper (e.g. `gui2/ui_utils.is_web(page)`), used by both, and a test that asserts Alt keys still fire when `page.web` is False. Also note `_shortcut_groups()` (`main.py:386`) is the Alt+? popup text and will keep advertising shortcuts the web build no longer has — choose either to hide them there too or accept a doc/code drift you will re-discover in two years.

## Major

**3. Task 8's "good run only" cleanup has no owner and no test surface for the failure mode.**
`maintenance_window.py` deletes nothing today; `_capture_rollback` writes `db.prev` (`:297`) and the worktree is created by `push_contributions`. "Delete after a good run only" must key off `outcome is Outcome.REBUILT`, not `not FAILED` — a `SKIPPED` run (unchanged `last_built`, `:399-401`) never rebuilt, so `dpd.db.prev` is the only copy made that night and nothing is newer than the db. Deleting it there removes the sole rollback copy for free. Fix: delete strictly inside the `outcome = Outcome.REBUILT` path, and add a test for the SKIPPED case; the current suite documents SKIPPED as success.

**4. Task 4 (delete the helper server) leaves a stale port contract in three places.**
`tools/fast_api_utils.py:17-18` keeps `DPD_API_PORT`/`8080`; `main.py:746-747` prints "FastAPI server started"; `exporter/wxt_extension/wxt.config.ts` targets `127.1.1.1:8080`. Removing only the call makes the printed line, the env var and the extension config into permanent lies, and a future maintainer re-adds the server to make the extension work. Fix: delete `start_dpd_server` wholly, and in the same task add a comment at the `wxt.config.ts` origin and in the justfile webapp recipe saying gui2 no longer starts a server there.

## Nit

**5. Flaky test (`test_maintenance_window.py:230`) — the cause is visible.**
`_write_status` (`:181-206`) finds the run start with `if line.endswith("INFO maintenance window start"): start = index` and keeps the *last* match, but `problems` filters after it. `run_maintenance` logs `maintenance window end: failed` in the `finally` (`:449`) *before* `_write_status`. Anything else appending a start line to the same dated log (a second window run in the same second, a retried test writing to a shared `log_dir`, or a previous run with a trailing `ERROR` on the start line) shifts `start` past the error and yields `problems: 0`. That matches the observed one-off. Fix: pass the run's own offset or a unique run id, rather than re-deriving it by string match from the file.

**6. Task 7's notice on the `_pull` skip (`contrib_pull.py:476`) is dead in practice.** `run()` already returns at `:526` for the same `editor_running()` check, so the inner one only fires when the editor appeared mid-pull — the "partial" case, where "editor open, nothing pulled" would be the wrong message. Confirm which skip gets the notice.
