## Findings

**1. Blocker — fix #3 silences the only signal that a cache write is failing, with no replacement.**
`gui2/database_manager.py:386-397` prints `decon cache refresh failed: {exc}` then rolls back. Making this "quiet" on read-only DBs removes the one trace of a real write failure (lock held by the build, concurrent self-heal race). After the fix, a broken cache degrades silently to the 1.4–2.2 s live scan on every launch and no one knows why. Worse, the branch is chosen by *exception type*, so a read-only error and a lock-timeout error look alike unless the fix inspects the message or `PRAGMA query_only`.
Fix: count and expose the miss (`self.decon_cache_refresh_failures`, surfaced once in the DB-tab status line or a `print` on the first occurrence per session), and gate the silence on an explicit read-only check, not on `except Exception`.

**2. Blocker — the two hidden-destructive fixes (8) have no verification trail.**
`scripts/server_contrib/maintenance_window.py:288` creates `dpd.db.prev`; `_restore_rollback` (306) *copies* it but never removes it. The new cleanup deletes `dpd.db.prev` and `_contrib_worktree/` after a good run. Nothing in the window records *which* path it deleted or its size, and `_contrib_worktree` may hold an unpushed contributions branch (see `_default_push` at :117). Today the briefing admits "not read in code this session" — that is the state the decrement runs against.
Fix: the cleanup step must `log.info(f"deleted {path} ({size} bytes, mtime …)")` *before* deleting, must refuse when `git -C worktree status --porcelain` is non-empty or the branch has commits not on the remote, and the task needs a test that asserts the skip path leaves both paths intact. Also note the deletion must not run when `Outcome.SKIPPED`/rebuild was skipped (`last_built` branch at :427) — "good run" is ambiguous there.

**3. Major — fix #7 sends a notice nobody can retract or deduplicate.**
`contrib_pull.py:563-573`: the docstring says a skip "is announced at once", yet `run()` returns early on skip (:527-529) without calling `maybe_notify` — `main` calls it only for non-skipped outcomes (:601). So the *claimed* current behaviour is already inconsistent with the code. If the fix adds a skip notice, `editor_running()` uses a `psutil` scan for `gui2/main.py` (:80-87) and can be true for a long-lived editor (or true spuriously from a stale cmdline), producing a `notify-send` every scheduled run of the day. Nothing rate-limits it: the `already done today` guard is skipped precisely on the editor-open path.
Fix: write the skip reason into `contrib_pull.log` and add a `skip_notice_last_sent` date to the status file so at most one skip notice is sent per day; make the test assert the second skip in the same day sends nothing.

**4. Major — clipboard fix (#1) turns a visible failure into an invisible one.**
`gui2/pass2_add_view.py:1066` and `:1344` are `await`ed mid-save. Wrapping them in `try/except` means the maintainer's own copy of `lemma_1` silently fails; the follow-on step (`_x_manager.remaining_count()` at :1346, the "X words remaining" message) still runs, so the UI looks correct while the very input the workflow depends on (paste into X) is stale. Contributors will report "the copy stopped working" with no log line.
Fix: on failure, show a one-line message ("copied nothing — clipboard unavailable") rather than swallowing, and log once per session. Do not swallow `asyncio.CancelledError` — use `except Exception`.

**5. Major — the flaky test (item 13) is a symptom of an observability gap, and fixing the test alone hides it.**
`_write_status` (`maintenance_window.py:190-195`) re-reads the day's log and anchors on the *last* `INFO maintenance window start`. Two overlapping runs, or a run whose log rotated, makes `problems` count wrong — exactly `problems: 0, expected 1`. The status file is the maintainer's only browser-visible surface (`:93`), so a wrong count is a real production bug, not test noise.
Fix: pass the run's `start` marker in memory (a `run_id` in the log line) instead of searching the file; add a test with two interleaved runs.

**6. Nit — fix #9 keeps two sources of truth.**
`gui2/toolkit.py:52` (`resolve_username() or "1"`) and `gui2/user.py:29` (`self.username or "1"`) will be "made to agree" but stay duplicated; a future edit to one re-breaks routing silently, and the mismatch will show as data saved under the wrong user with no error.
Fix: export one `routed_username()` from `user.py` and call it in both places.

**7. Nit — no diagnostic path for "notice spam" or shortcut regressions.**
`gui2/main.py:746-748` prints elapsed time and no server identity; `_TAB_JUMP_KEYS` (:254) is the only mapping, so a bug in fix #12 (`page.web` gate) has no log line to confirm which mode a client took. Add one `print(f"mode: web={page.web}, tabs={...}")` at startup.
