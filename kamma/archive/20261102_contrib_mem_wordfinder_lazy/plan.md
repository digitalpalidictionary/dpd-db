# Plan: no word finder for contributor servers

**Thread:** 20261102_contrib_mem_wordfinder_lazy · **Spec:** `spec.md` in this folder (read it first; the owner decided "off", not "lazy")
**GitHub issue:** #215 · never write to the issue · commits reference `#215`
**Baseline (server, commit 247a8429):** 943.3 MB warm, 1,045.7 MB after one `mn` book (`kamma/archive/20261102_contrib_mem_savings/artifacts/results.md`).

## Architecture Decisions

- **Gate on Pass2Add access, nothing else (owner's rule).** One condition, `7 in self._visible` (Pass2Add is tab 7; `self._visible` is set by `tab_selection()`), switches the warm-up, the two keys and the shortcut rows. No role check. Every instance that has Pass2Add, the desktop included, keeps today's behaviour.
- **Remove the dead attribute for every role.** `Pass1AddController.wordfinder_manager` has no reader, so removing it changes no behaviour. It is the one change that is not role-gated.
- **Off, not lazy.** The owner decided that only a user with Pass2Add needs the word finder. No `ToolKit` change, no first-use build, no wait to measure.
- **Measure a whole build.** The earlier thread showed that per-step deltas disagree with whole-build totals, so the saving is the difference of two whole builds, three fresh processes each.
- **No `git` command in any task.** The owner commits and pushes; checks use `ls`, `rg` and the scripts.

## Who does each step

- `LOCAL AGENT` — the agent in `/home/bodhirasa/MyFiles/3_Active/dpd-db` on the laptop.
- `OWNER` — pushes (task 4.1) and says yes once to the server restart (task 4.3).
- `SERVER AGENT` — the opencode agent titled "OC | dpd contributor", host `epitaka` (list panes first: `ssh epitaka '/root/.local/bin/herdr agent list'`; ids can change). The local agent messages it through the `herdr-remote` skill (`~/.agents/skills/herdr-remote/SKILL.md`). Rules for the server agent: one step at a time, append results only to `~/mem/results_wordfinder.md`, never print `config.ini`, any `.env`, htpasswd files, or `/proc/<pid>/environ`, no `git` command except the one `git pull` in 4.2, restart `dpd-gui@alice` only on the owner's yes in this conversation, never `pkill`, `killall` or `kill -9`, never touch `~/epitaka-translator`.

---

## Phase 1 — Tests first, then the change — WHO: LOCAL AGENT

Run every command from `/home/bodhirasa/MyFiles/3_Active/dpd-db`. Other sessions share the tree: re-read a file before editing it.

- [x] 1.1 **Write the tests and watch them fail.** In `tests/gui2/test_main.py`, next to `test_server_warmup_builds_only_visible_tabs` (use `_server_app`):
      (a) on an app whose visible tabs lack Pass2Add (a contributor-server app from `_server_app`) the warm-up never touches `toolkit.wordfinder_manager` or `toolkit.wordfinder_popup`; with tab 7 in `app._visible` (the desktop app, and a server app whose `_visible` is set to include 7) it still touches both. The last case proves the gate is Pass2Add, not the role. Use a toolkit double that records access to those two names.
      (b) without Pass2Add a Ctrl+F event and a Ctrl+W event touch neither name; with Pass2Add (desktop app, and a server app with 7 in `_visible`) Ctrl+F opens the popup and Ctrl+W closes an open one.
      (c) without Pass2Add the shortcut list has no row for Ctrl+F or Ctrl+W (build on `test_server_shortcut_list_names_only_visible_tabs`); with Pass2Add both rows are there.
      Then in the Pass1Add controller tests (find them with `rg -n "Pass1AddController" tests`): (d) the controller can be built with a toolkit whose `wordfinder_manager` raises on access.
      → verify: `uv run pytest <those test files> -q`; the new tests fail for the stated reason (paste the failing test names and a one-line reason each into this task).
        Done. 4 failed, 62 passed. Failures and reasons: `test_server_warmup_skips_the_word_finder_without_pass2add` — the warm-up touched both `wordfinder_manager` and `wordfinder_popup` on a tab set without Pass2Add; `test_server_ctrl_f_and_w_do_not_touch_the_word_finder_without_pass2add` — Ctrl+F (then Ctrl+W) touched `wordfinder_popup` 3 times; `test_server_shortcut_list_drops_the_word_finder_rows_without_pass2add` — the list still names Ctrl+F and Ctrl+W; `test_controller_builds_without_touching_the_word_finder` — the constructor read `toolkit.wordfinder_manager`, which raised. The 6 guard tests (with Pass2Add: server modified and desktop) passed already and must keep passing.
- [x] 1.2 **Make the change.**
      - `gui2/main.py` `_warmup_in_background` (lines 566-582): when `7 not in self._visible`, skip `self.toolkit.wordfinder_manager` and `self.toolkit.wordfinder_popup`; keep the other lines unchanged.
      - `gui2/main.py` `on_keyboard` (lines 307-312): when `7 not in self._visible`, the Ctrl+F and Ctrl+W branches do nothing.
      - `gui2/main.py` `_shortcut_groups` (rows at lines 401 and 437): leave those two rows out when `7 not in self._visible`.
      - `gui2/pass1_add_controller.py`: delete line 51 and the `WordFinderManager` import at line 24 if nothing else in the file uses it.
      Comments only say why. Re-read each region just before editing it.
      → verify: `uv run pytest tests/gui2 -q` passes, and the tests of 1.1 pass.
- [x] 1.3 **Lint and type check, every touched file.** `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright --project /dev/null <file>` for files under `gui2/` and `tests/`, then `just typecheck`. After `ruff format`, check `git diff --stat` shows only intended lines.
      → verify: all clean; `uv run pytest tests/gui2 tests/tools -q` run once, with any failure that was there before listed as `PRE-EXISTING — NOT CAUSED BY THIS THREAD` (known: `tests/tools/test_configger.py::...[uposatha_reset]`, and `test_tipitaka_db_deadline.py` under heavy load).
- [x] 1.4 **Revert check.** For each of the three changes, undo that change in the one file by hand (keep a copy in the scratchpad, restore in the same command), run the matching tests, and count the failures.
        Done. Four reverts (the three gates plus the controller attribute), each in isolation: warm-up gate → `test_server_warmup_skips_the_word_finder_without_pass2add` failed; key gate → `test_server_ctrl_f_and_w_do_not_touch_the_word_finder_without_pass2add` failed; shortcut rows → `test_server_shortcut_list_drops_the_word_finder_rows_without_pass2add` failed; controller attribute → `test_controller_builds_without_touching_the_word_finder` failed. Each file restored by copy, `cmp` identical, full `tests/gui2` back to 630 passed.
      → verify: each undo makes at least one named test fail; the files are restored and `cmp` shows them identical to the copies.

## Phase 2 — Measure on the laptop — WHO: LOCAL AGENT

- [x] 2.1 **Copy the probe.** Copy `kamma/archive/20261102_contrib_mem_savings/artifacts/lever_probe.py` to `artifacts/lever_probe.py` in this thread. Change `DEFAULT_COLUMNS_MD` to the archived `columns.md` path. Add the variant `contributor_no_wordfinder` (same steps as `contributor_real`, without `wordfinder_today`). Keep its safety rules: contributor role set, `PRAGMA query_only`, 1.5 GB system cap, in-process watchdog, writes only in this folder and temp dirs.
      → verify: `uv run ruff check --fix`, `ruff format`, `uv run pyright <file>` clean; `PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_wordfinder_lazy/artifacts/lever_probe.py --selftest` prints `SELFTEST_OK`.
- [x] 2.2 **Run the whole-build probe.** Tell the owner the cap and the number of processes (2 variants × 3 runs plus a warm-up), then run it in the background with `timeout 1500`: `PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_wordfinder_lazy/artifacts/lever_probe.py --all --only contributor_real,contributor_no_wordfinder --db <SCRATCH>/dpd_copy.db --out kamma/threads/20261102_contrib_mem_wordfinder_lazy/artifacts/laptop.jsonl`. `<SCRATCH>/dpd_copy.db` is a `.backup` copy of `dpd.db`; if the earlier copy is gone, make a new one with `sqlite3 dpd.db ".backup <SCRATCH>/dpd_copy.db"` and check the headword counts match. Do not poll; the harness reports the end.
      → verify: every row `ok`; guard clean; no stray python (`ps --sort=-rss -eo pid,rss,cmd | head -5`); the saving (median `contributor_real` final RSS minus median `contributor_no_wordfinder` final RSS, with min and max) is written to `artifacts/results.md`.
        Done. 7 processes, all `ok`, `query_only=1`, guard_warnings empty, swap 0, no stray python. Saving **170.0 MB** (range 170.0–170.1): medians 909.1 vs 739.1. Written to `artifacts/results.md`.
- [x] 2.3 **Phase check.** `rg -l "lever_probe" gui2 tools` prints nothing.
        Done: printed nothing. Note: 3.1's reviews start while the probe still runs — the code diff is final, the probe only measures.
      → verify: output as stated.

## Phase 3 — Reviews and fixes — WHO: LOCAL AGENT

- [x] 3.1 **Parallel reviews, no edits while they run.** Tell the owner the diff goes to the DeepSeek API. Run CodeRabbit (`coderabbit review --agent --fresh --uncommitted --include-untracked --dir <changed dir>`, or `--committed --base-commit <sha>~1` if the work is already committed; the two flag sets cannot be combined) and the `pi-review` skill with DeepSeek at max reasoning, on the diff of the touched `gui2/` and `tests/` files, in the background at the same time. Do not give one reviewer the other's findings.
        Done. CodeRabbit (`--agent --fresh --uncommitted`, free CLI allowance): reviewed all 4 files, **0 findings**. DeepSeek (deepseek-v4-pro, thinking max, 11.4 KB diff): verdict "nothing blocking", 2 findings. Neither saw the other's output. Flag note: `--include-untracked` left off — the code diff has no new files (the thread folder is docs/artifacts, out of the plan's review scope), so plain `--uncommitted` covered exactly the 4 modified files.
      → verify: both reports are in hand; every finding is checked against the current code and marked real, not real, or noticed-not-touching in `plan.md`.
- [x] 3.2 **Fix the real findings,** with a failing test first where the finding is a behaviour bug. Rerun 1.3.
        Finding 1 (DeepSeek, minor, real): the Ctrl+F comment claimed Pass2Add is "the only tab with a use for the word finder", contradicting `_get_current_lemma` (tab 3 fills the lemma too). The behaviour itself — contributors lose Ctrl+F, lemma fill included — is the owner's recorded decision in spec.md, so the gate is unchanged; only the comment now states the deliberate loss. Comment-only: no behaviour bug, no new test. Finding 2 (DeepSeek, nit, no action by design): five guard tests stay green on a revert — their paired skip tests catch it, proven in 1.4. Rerun of 1.3: ruff clean, format clean, pyright on main.py 24 errors = exactly HEAD's 24 (all on untouched lines), 630 tests pass, `just typecheck` 0 errors.
      → verify: lint, type check and tests clean; a one-line note per finding in this plan.

## Phase 4 — Confirm on the server — WHO: OWNER, LOCAL AGENT, SERVER AGENT

- [~] 4.1 **WHO: OWNER.** Push the commit (the local agent suggests the message, no signature, and commits only when asked).
        Committed locally by the local agent on the owner's instruction ("/cm and commit only your files"): `267740fc`, exactly the 4 code files, hooks passed. Push pending (owner).
      → verify: the server agent's report in 4.2 shows the same commit hash as the laptop.
- [x] 4.2 **WHO: SERVER AGENT.** Via `herdr-remote`: read the pane first (the agent must be idle), then send: "Run `cd ~/dpd-db && git pull` once, then `git log -1 --format=%h` and `git status --porcelain`. Append the output under `## 4.2` to `~/mem/results_wordfinder.md`. No other git command."
        Done. Pane w2:p1 (OC | dpd contributor) was idle, message sent once, section appeared within the bounded wait: server log shows `267740fc` — same as the laptop — and a clean tree. Note: the file already held the earlier thread's sections (its ## 4.3, commit 247a8429); the new ## 4.2 sits below them as the plan intends.
      → verify: same commit as the laptop; clean tree.
- [x] 4.3 **WHO: LOCAL AGENT, owner's yes first.** — owner amended mid-step: the one-book reading runs book `cp`, with AutoProcess stopped after about 10 words (real processing flow, not the trivial `mn` run). Consequence recorded: the 1,045.7 MB baseline was an `mn` run, so the one-book comparison is approximate, not exact. Restart yes received 2026-11-02; the whole sequence runs without asking again. One yes from the owner in this conversation (a restart drops unsaved input in alice's page). Then run the whole sequence without asking again. First put the owner's Chrome tab on `about:blank` so no old session reconnects. The server agent restarts `dpd-gui@alice`, waits 15 s and takes the reading `plus15s_wf`, with `cd ~/dpd-db && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ~/.local/bin/uv run --no-sync ~/mem/mem_probe.py --unit-readings dpd-gui@alice --label <label> >> ~/mem/readings_wordfinder.jsonl`. Then the local agent opens the alice page once in the owner's Chrome (`playwright-cli attach --extension=chrome` with the token from `PLAYWRIGHT_MCP_EXTENSION_TOKEN`, never printed; `eval` a click on `flt-semantics-placeholder` to expose text; a MutationObserver records "Database loaded" and "All tabs and tools ready"), and the agent takes `warmup_done_wf`. Then the local agent runs `mn` in Pass1Auto (Book picker, then "AutoProcess Book"), and the agent takes `one_book_wf`. Then the local agent presses Ctrl+F and confirms nothing opens, opens the shortcut list and confirms there is no Ctrl+F or Ctrl+W row, and the agent takes `after_ctrlf_wf`. Then the local agent closes the page (`about:blank`) and detaches.
      → verify: five readings in `~/mem/readings_wordfinder.jsonl`; `journalctl -u dpd-gui@alice` shows the "App initialized" count you expect for one page (the earlier run showed 2 for one Chrome page; more than that means a stray session and the run is invalid: redo it); no reading lower than the one before it except through a restart.
        Done, with two deviations recorded. (1) The verify line says five readings but the task names four labels (plus15s_wf, warmup_done_wf, one_book_wf, after_ctrlf_wf) — corrected to four here; all four are in the file, monotonic 86.4 → 774.1 → 879.2 → 879.2, never lower. (2) The build logs no "App initialized" line, so the journal session-count check is impossible; single-session evidence instead: one alice tab existed, no already-open banner showed, and the readings' magnitudes are single-session (a stray session read ~2 GB last time). The two snackbar messages fired before the MutationObserver was installed (page open to observer ≈ 40 s); warm-up completion is evidenced by the journal's AI-manager init lines at 03:48:54 server time and by the rendered tabs. Book deviation: owner amended mid-run — `cp`, stopped after about ten words, in place of `mn` (see note at 4.3 head). Ctrl+F opened nothing; the shortcut list shows no Ctrl+F row (App group) and no Ctrl+W row (Popups group), live-verified before after_ctrlf_wf. after_ctrlf_wf equals one_book_wf to the decimal: the key built nothing.
- [x] 4.4 **WHO: SERVER AGENT.** Append a before and after table to `~/mem/results_wordfinder.md` under `## 4.3`, with 943.3 and 1,045.7 MB beside the new readings.
        Done. Table verified by reading the file: warmup_done_wf 774.1 vs 943.3 (−169.2), one_book_wf 879.2 vs 1,045.7 (−166.5, noted approximate), after_ctrlf_wf 879.2 equal to one_book_wf. The file held only a 135-byte stub before these appends; the earlier thread's data lives in results_savings.md/results.md, nothing clobbered.
      → verify: the section exists.
- [x] 4.5 **Copy back.** `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && mkdir -p kamma/threads/20261102_contrib_mem_wordfinder_lazy/artifacts/server && rsync --bwlimit=400 -r epitaka:mem/results_wordfinder.md epitaka:mem/readings_wordfinder.jsonl kamma/threads/20261102_contrib_mem_wordfinder_lazy/artifacts/server/` (the local agent runs it).
      → verify: `ls artifacts/server/` lists both files.

## Phase 5 — Results and finish — WHO: LOCAL AGENT

- [~] 5.1 **Write `artifacts/results.md`:** the laptop saving, the server before and after, the new projection for 3, 8 and 16 contributors (baseline 1,066 MB plus N times the per-instance figure, same formula as before), and what is left.
      → verify: every number is quoted from `laptop.jsonl` or `artifacts/server/`; the before values equal those in the earlier thread's `results.md`.
- [x] 5.2 **Done check.** Re-read "How we'll know it's done" in `spec.md`; mark items 1 to 6 met or not met in `results.md`, each pointing to the file that proves it.
        Done: the six lines with file paths are in `artifacts/results.md`, section "Done check"; every number quoted from `laptop.jsonl` or `artifacts/server/`, before values equal the earlier thread's `results.md`.
      → verify: six lines, each with a file path.
- [x] 5.3 **Finalize, then commit.** Run `/kamma:4-finalize` (skip the GitHub step: never comment on or close #215; `kamma/tech.md` gets one sentence that contributor servers do not build the word finder), then commit when the owner asks.
        Done. tech.md got the one sentence (instances without Pass2Add do not build the word finder, commit 267740fc); project.md needed nothing; the thread is archived at `kamma/archive/20261102_contrib_mem_wordfinder_lazy/` and removed from `kamma/threads/`; the GitHub step is skipped per the plan; four lessons appended to `kamma/lessons.md`, none promoted. Commit suggested below, runs when the owner asks.
      → verify: the thread is in `kamma/archive/`, `kamma/threads/20261102_contrib_mem_wordfinder_lazy` is gone, and `git status --porcelain` shows only this thread's files.
