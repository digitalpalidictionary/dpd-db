I have enough. Findings below.

## Blockers

**1. Phase 5 as written proves nothing — the flaky test cannot fail for the flaky reason, and the plan's diagnosis step is unreachable.**
`tests/scripts/server_contrib/test_maintenance_window.py:230-240` asserts only `problems: 1`, `"boom"`. The `rebuild` stub raises `RuntimeError("boom")`, which is caught at `maintenance_window.py:428` → one `log.error` line. No second ERROR/WARNING line can exist in a fresh `tmp_path` run (`use_systemd=False` at `test…py:118`, so the `no --instance` warning at `maintenance_window.py:380` never fires; `_systemctl` is a no-op). So 30+10 runs cannot reproduce, and task 14.2 (`-vv` shows the status and log text in the assertion message) is false: the asserts don't print either file. Under executor rule 7 the model must then take the "not reproduced" branch — but the spec's own history says a failure happened once in a full run, i.e. under suite conditions the plan never exercises (pytest tmp dirs are unique, so the only cross-test input is the shared `logs/`? no — `log_dir` is per `tmp_path`; the plausible cause is the log containing a second `src/…/maintenance_*.log`? `log_text()` at `test…py:141-144` takes `glob()[0]`). Fix: make 14.1 record the actual status and log text on failure (`-vv` is not enough), and require three runs of the *whole file in one session* plus one `pytest tests/ -q` run of that test so the plan explores the real condition that failed; otherwise delete phase 5 (it is unexecutable by a literal model).

**2. Task 15.3 `graphify-out/` prune keeps nothing / deletes the newest snapshot on a first run.**
`graphify-out/` currently holds exactly one dated snapshot, `2026-11-04/`. `ls -d graphify-out/20* | sort | head -n -1` yields the empty string on a single-snapshot tree, and `xargs rm -rf` with no arguments is harmless but the verify line "both commands end without error" passes while the *newest* stale snapshot is never removed — and if `graphify update .` writes no new dated dir (AGENTS.md:178 says every update writes one), the only snapshot is pruned. Also `graphify` is not in the justfile, so `uv run` is not used and the model cannot confirm the binary exists; `AGENTS.md:178` says prune "right after it finishes" and warns the update can exceed timeouts (`kamma/lessons.md:227`) — rule 12 says no retry loops, so a timed-out update leaves the prune step ambiguous. Fix: state the exact expected snapshot count, and guard with `[ "$(ls -d graphify-out/20* | wc -l)" -ge 2 ]`.

## Majors

**3. Task 15.1 is not self-checkable by a literal model.** "Compare with task 0.1" / 0.2 requires re-reading an earlier note and diffing multi-line pytest output; the verify line gives no measurable test. Fix: "new failures ⊆ the names written in 0.1" as an explicit set comparison.

**4. Task 15.2's file list is inconsistent with the tasks it closes.** It lints `scripts/server_contrib/ensure_translation_db.py` (created in 13.2 — fine), but omits files tasks 8 and 13 edit (`scripts/server_contrib/server_setup.sh` is bash, OK; however `scripts/server_contrib/maintenance_window.py`, `contrib_push.py` and `.gitignore`/`server_setup.sh` edits are not linted — fine) while listing `gui2/pass1_add_controller.py`, whose only change (task 6) is a line deletion. More importantly the list is a single 21-path line; if any task was skipped or renamed the model must decide whether to drop paths — a design decision the plan doesn't authorise. Fix: state "lint exactly these; if a path does not exist, STOP."

**5. Task 15.5 gives commands the executor cannot run and an unpinned server path.** "`cd <server clone>`" is a placeholder, and rule 2/12 plus the "no network, no ssh" spirit mean the model cannot verify anything here. Also `setsid nohup … &` contradicts rule 12 ("any background loop needs `timeout`"). Fix: label 15.5 explicitly as owner-only text to be copied into the report, with no execution implied, and drop the `timeout` rule conflict by noting the background command is the owner's.

## Nits

**6. Phase 5 task 14.1 uses `timeout 1500` with `tail -25` on a loop that stops at first failure** — on success the output is 30 lines of dots and the final `tail` truncates it, so "write the exact commands and the result" can only record the last lines; say what to record (the run count line).

**7. Phase 6 numbering skips 15.x to 15.5 with no 15.6 wrap-up while earlier phases end with a tidy step** — cosmetic; a literal model may look for a missing task.

**8. 15.5 asserts live behaviours that phase 5/6 cannot produce** (e.g. "the next nightly window deletes the old database copy") — these are owner checks from tasks 8/14, duplicated here; fine, but note they assume tasks 8 and 13 are `[x]`.
