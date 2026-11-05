# Handoff (2026-11-02) — contrib_mem_wordfinder_lazy

Resume with `/kamma:2-do 20261102_contrib_mem_wordfinder_lazy`. Read `spec.md` and `plan.md` in this folder first. They are final. No code has been changed yet. The owner has not yet said "start the build"; get that one go-ahead (or take "build it" from the message that sent you here) and then run the plan.

## What the thread does (owner's decisions, do not change them)

- The word finder (`tools/wordfinder_manager.py`, about 160-172 MB per instance) is built **only when the user has Pass2Add** (tab 7 is in `self._visible` in `gui2/main.py`). One condition, nothing else. **No role check** (`is_headless_server()` is not used for this), no new setting. The owner corrected this twice: "it must be tied to one thing. pass2add access."
- Without Pass2Add: the warm-up does not touch `toolkit.wordfinder_manager` or `toolkit.wordfinder_popup`; Ctrl+F and Ctrl+W do nothing; the shortcut list drops the Ctrl+F and Ctrl+W rows (`gui2/main.py` lines about 401 and 437).
- For every role: `Pass1AddController` stops building its unused copy (`gui2/pass1_add_controller.py:51` and the import at line 24).
- Not lazy-on-first-use. Not a contributor-role switch. Do not add either. Do not add anything the spec lists under "What's not included".
- The folder name says "lazy" because the first draft was lazy. The spec says "off".

## Facts verified (do not re-derive; re-read a line before you edit it)

- Pass2Add is tab index 7. `App._visible` comes from `tab_selection()` (`gui2/main.py:48-54`): the desktop shows every tab, a contributor gets only the tabs in `gui2/contributor_tabs.py`, and `DPD_GUI2_TABS` cannot add Pass2Add.
- Nothing in `gui2/` or `tests/` reads `Pass1AddController.wordfinder_manager` (rg checked). The only real user of the word finder is the Ctrl+F popup (`gui2/main.py:308`).
- Ctrl+W (`gui2/main.py:311`) calls `wordfinder_popup.is_dialog_open()`, which would build the popup and the word finder. It must be skipped without Pass2Add.
- Tests to copy from: `tests/gui2/test_main.py` (`_server_app` helper, `test_server_warmup_builds_only_visible_tabs`, `test_server_shortcut_list_names_only_visible_tabs`) and `tests/gui2/test_wordfinder_popup.py`. The Pass1Add controller tests: `rg -n "Pass1AddController" tests`.
- Earlier numbers: warm 943.3 MB and one `mn` book 1,045.7 MB on the server (commit 247a8429). The word finder costs 172.1 MB isolated and 159.8 MB in the full build on the laptop.

## Repo state at handoff

- The branch is `main`. The last commit is `33a995bc` ("#215 contrib_mem_savings: review fixes, server results, finalized"); it was local only when written. Check `git status -sb` before you rely on it. The server must have it pulled before Phase 4.
- This thread's folder (`kamma/threads/20261102_contrib_mem_wordfinder_lazy/`) is new and untracked. Other threads are in `kamma/threads/`; another session may be editing the tree.
- The earlier thread `kamma/threads/20261102_contrib_mem_measure` is still open and not archived (its last task is the owner's). Do not touch it.

## Rules for you (from the owner's global and project rules)

- **No git command and no commit** unless the owner asks. Never `git stash`, `checkout --`, `restore`, `reset --hard`. When asked to commit: stage by explicit file list, message in the form `#215 area: change1, change2`, **no signature or Co-Authored-By line**, max 72 chars on line one.
- **Never write to GitHub issue #215.** Skip the GitHub step in finalize.
- Chat replies: plain English, no file paths or code names, short sentences, end with one next step. Say "Hopa!" before using a tool. Open plan mode with "Hmmm...". Paths and code names belong in files.
- **Do not make your own decisions** on the design. If something in the spec is wrong or unclear, say so and ask through the question tool. The owner has twice corrected invented design choices in this thread.
- Never read, print or edit `config.ini` or any `.env`. Never touch the live `dpd.db` (probe on a `.backup` copy).
- Touch a file = own its lint: `uv run ruff check --fix <file>`, `uv run ruff format <file>`, `uv run pyright --project /dev/null <file>` (for `gui2/` and `tests/`), then `just typecheck`, then the tests. Write each test first and watch it fail. Do a revert check per change. If `ruff format` rewrites unrelated lines, undo and re-apply the edit by hand.
- Order of work: build with tests, laptop measurement, **parallel reviews** (CodeRabbit and the `pi-review` skill with DeepSeek, no edits while they run), fix real findings, server check, results, `/kamma:4-finalize`, then commit when the owner asks. CodeRabbit: `--committed` cannot be combined with `--include-untracked`. Validate every finding against the code; a finding can be wrong (one was, last time: a NULL claim the live data disproved).
- When you finish a task, say it is ready to commit; do not wait for the end of the thread.

## Running the laptop probe (Phase 2)

- Copy the old probe as the plan says. Run from the repo root: `PYTHONPATH=. uv run kamma/threads/20261102_contrib_mem_wordfinder_lazy/artifacts/lever_probe.py ...`. Each child runs under a 1.5 GB cap, read-only on the database copy, no network.
- A database copy existed at `/tmp/claude-1000/-home-bodhirasa-MyFiles-3-Active-dpd-db/212a07c4-9a04-409b-9eee-e92c985ca66f/scratchpad/dpd_copy.db` (89,774 headwords). If it is gone, make a new one with `sqlite3 dpd.db ".backup <your scratchpad>/dpd_copy.db"` and check the headword count against the live file (both read-only).
- Tell the owner the cap and number of processes first. Do not poll a background job; the harness reports its end. Check `ps --sort=-rss -eo pid,rss,cmd | head -5` afterwards. Machine load is often high (about 15); that makes timing noisy, not memory.

## Server check (Phase 4) — how it worked last time

- Ask the owner for **one** yes before the restart (it drops unsaved input in alice's page). After that run the whole sequence yourself. The owner said: "stop asking me to babysit you."
- The server agent: the opencode agent titled "OC | dpd contributor" on host `epitaka`. Find its pane with `ssh -o BatchMode=yes epitaka '/root/.local/bin/herdr agent list'` (it was `w2:p1`; the pane `w1:p1` is a different agent). Read the skill `~/.agents/skills/herdr-remote/SKILL.md`. Read the pane first; send only when it is idle. Quote carefully (no single quotes or dollar signs in the message). It takes about a minute to answer; wait with a bounded loop, for example `timeout 240 bash -c 'until ssh -o BatchMode=yes epitaka "grep -q <label> ~/mem/readings_wordfinder.jsonl"; do sleep 8; done'`.
- Readings come from `cd ~/dpd-db && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ~/.local/bin/uv run --no-sync ~/mem/mem_probe.py --unit-readings dpd-gui@alice --label <label> >> ~/mem/readings_wordfinder.jsonl`, run by the server agent.
- Opening the page: it needs a login (401 without it). Use the owner's Chrome: `playwright-cli -s=chrome attach --extension=chrome` with the environment variable `PLAYWRIGHT_MCP_EXTENSION_TOKEN` (the owner gives the value in the conversation; never write it into a file or print it). Then `goto https://<server-ip>.sslip.io/alice/`. Flutter hides its text until you run `playwright-cli -s=chrome eval "document.querySelector('flt-semantics-placeholder').click()"`. Then `snapshot` shows the tabs. Install a MutationObserver on the body to catch the short "Database loaded" and "All tabs and tools ready" messages (they last 2 seconds).
- **Open exactly one page session.** Every open page builds its own copy of the app inside the same process. Two extra pages gave 2,059 MB instead of 943 MB last time. Put the Chrome tab on `about:blank` before a restart and after the run, then `playwright-cli -s=chrome detach`. Count "App initialized" lines in `journalctl -u dpd-gui@alice` (one Chrome page gave 2 lines last time).
- Run `mn` in Pass1Auto: the Book picker is the first button in the row; click it, click `mn`, then "AutoProcess Book". `mn` has no missing words, so the counter reads 0 / 0 and the message says "Finished processing mn". That is correct (the owner confirmed).
- If a tunnel is useful: only to `127.0.0.1:8551` on the server with a time limit; close it by its PID when done.

## Known leftovers, not for this thread

- Pre-existing test failures: `tests/tools/test_configger.py::...[uposatha_reset]`, and `tests/tools/test_tipitaka_db_deadline.py` under heavy load. List them, do not fix them.
- Not touched: `gui2/wordfinder_widget.py` (dead code), the detector rebuild worker, the "refresh DB" extra memory.
- `kamma/tech.md` gets one sentence at finalize: instances without Pass2Add do not build the word finder.
