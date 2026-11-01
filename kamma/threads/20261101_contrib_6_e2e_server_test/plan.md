# Plan: contributor server, full end-to-end test from a fresh clone

**Thread:** 20261101_contrib_6_e2e_server_test · **Spec:** `spec.md` in this folder (read it first)
**GitHub issue:** #215 · never write to the issue · commits reference `#215`

## Architecture Decisions

- **The first db build is the maintenance window itself.** No second build path: the
  window already rebuilds, checks health, restores the tracked files the build
  rewrites, and writes `logs/last_built_commit`. The setup script calls it with
  `--no-systemd --no-push`.
- **The setup script lists no build steps.** It installs packages, clones, inits the
  three submodules, and calls `initial_setup_run_once.py`, the audio index download and
  the window. The step lists stay in `initial_setup_run_once.py` and
  `generate_components_server.py`.
- **One-time and secret steps stay out of the script:** swap, nginx, certificate,
  `add_contributor.sh`, deploy key, `systemctl enable`. They are commands in this plan
  and in the README.
- **Bold definitions are refilled inside the lean generate list**, not in the window,
  so the first build and every nightly build share it.
- **`FLET_SERVER_IP` lives in the env file only** (written by `add_contributor.sh`), not
  in the unit.
- **gui2 runs as root on this borrowed box** (spec decision 6). The production user
  design belongs to contrib_1.
- **Push credentials: a temporary deploy key**, used only for pushes (spec decision 1).
- **No new abstractions.** Each fix is a few lines in an existing file, plus two new
  files (the unit template and the setup script).

## Who does each step

Each task says **WHO**:
- `LOCAL AGENT` — an agent in the maintainer's repo on his laptop
  (`/home/bodhirasa/MyFiles/3_Active/dpd-db`). It never commits or pushes.
- `MAINTAINER` — the human owner. Only he commits, pushes, types secrets, and uses the
  browser and GitHub settings.
- `AGENT` — the server agent on the borrowed server. It follows the rules below.

## READ THIS FIRST — rules for the SERVER AGENT

You are the SERVER AGENT. You run on the server. You are not Claude. Follow these
rules exactly. If a rule and a task seem to disagree, STOP and ask.

1. Do the tasks in order. Do one task at a time. Do not skip a task.
2. Do only `AGENT` steps. For a `MAINTAINER` step, show him the command, then wait
   until he says it is done.
3. Copy each command exactly. Do not change it, shorten it, or "improve" it.
4. After each task, run its **CHECK**. Compare the output with **EXPECT**.
5. If the output does not match EXPECT, or a command prints an error: STOP. Write the
   command and its full output in `results.md`. Tell the maintainer. Do not try a fix
   of your own.
6. Write results ONLY to
   `~/dpd-contrib/handoff/20261101_contrib_6_e2e_server_test/results.md`. Append to it.
   Logs and copies go only to `~/logs/`, as the tasks name them.
   Never edit `spec.md` or `plan.md`.
7. Never edit any file inside `~/dpd-db` or `~/dpd-db_contrib4` yourself. Never edit
   code. `server_setup.sh` and the maintenance window write inside `~/dpd-db`; running
   them is allowed.
8. Never print, open, read, grep or edit `config.ini`, any `.env` file, any htpasswd
   file, or any private key. Only the maintainer types secrets. You may print the
   PUBLIC key `~/.ssh/dpd_deploy.pub` (task 5.1).
9. Git in `~/dpd-db`: you may run only `log`, `status`, `rev-parse`, `ls-remote`,
   `show --stat`, `remote -v`, `submodule status`, and the `config` /
   `remote set-url --push` lines in task 5.3.
   NEVER `commit`, `push`, `stash`, `reset`, `checkout`, `restore`, `clean`, `pull` by
   hand. The setup script and the maintenance window run git themselves; that is
   allowed.
10. Use `sudo` only when the task says so AND the maintainer has said yes to that task.
    `server_setup.sh` uses `sudo` itself (apt, `/var/lib/dpd`, `/etc/systemd`); that is
    why tasks 3.4 and 3.6 need his yes.
11. Never touch `~/epitaka-translator`, its files, its processes, or any nginx file not
    named in a task.
12. Never delete anything in `~/contrib_data`, `/var/lib/dpd/contrib_data`,
    `~/dpd-db_contrib4` or `/root/contrib4_backup`.
13. Never use `pkill`, `killall` or `kill -9`. Stop gui2 only with `systemctl stop`.
14. Ask the maintainer one question at a time.
15. Long commands run in the background with a pid file. To wait, check the pid file
    every 10 minutes with the CHECK the task gives. Never loop forever.

---

## Phase 1 — Local code fixes — WHO: LOCAL AGENT

Read `spec.md` part A first. Run every command from the repo root
`/home/bodhirasa/MyFiles/3_Active/dpd-db`. Project rules: `CLAUDE.md` (pre-commit
gate, `--project /dev/null` for pyright on `tests/`). Other threads share this working
tree: touch only the files a task names.

- [x] 1.1 **Bold definitions after every rebuild.**
      - In `scripts/server_contrib/generate_components_server.py`, insert
        `"db/bold_definitions/update_bold_definitions_db.py",` into `COMMANDS` directly
        after `"tools/version.py",`. In the module docstring, add one line under
        "WHAT gui2 READS": `- bold_definitions (Bold Search tab; db_rebuild_from_tsv
        deletes the db, so this refills it every build)`.
      - In `tests/scripts/server_contrib/test_generate_components_server.py`, add
        `"db/bold_definitions/update_bold_definitions_db.py",` to `ESSENTIAL`.
      - In `scripts/server_contrib/config_server.md`, add `update_bold_definitions_db`
        to the **KEPT** list, with the reason: "Bold Search reads the
        `bold_definitions` table; the rebuild deletes the db. Needs
        `db/bold_definitions/bold_definitions.tsv` from the initial setup."
        In its "Prerequisites" paragraph, change the submodules to the three
        (`sc-data`, `dpd_submodules`, `tipitaka.rte`), and say the first setup also
        needs network for apt, uv, the Go modules and the audio index download.
      → verify: `uv run pytest tests/scripts/server_contrib/test_generate_components_server.py`
        passes. Then remove the new `COMMANDS` line, re-run: expect exactly 1 failure
        (`test_all_essential_steps_present`). Put the line back in the same command
        sequence and re-run: pass.
- [x] 1.2 **The window updates only initialised submodules.**
      - In `scripts/server_contrib/maintenance_window.py`, in `_default_pull` and in
        `_restore_rollback`, change `["git", "submodule", "update", "--init", "--recursive"]`
        to `["git", "submodule", "update", "--recursive"]`. Add a WHY comment above the
        one in `_default_pull`: `# No --init: the server inits only the submodules it
        needs (server_setup.sh); --init would fetch all eleven.`
      - In `tests/scripts/server_contrib/test_maintenance_window.py`, add:
        ```python
        def test_pull_and_rollback_never_init_new_submodules(
            tmp_path: Path, monkeypatch: pytest.MonkeyPatch
        ) -> None:
            from scripts.server_contrib import maintenance_window as mw

            seen: list[list[str]] = []
            monkeypatch.setattr(mw, "_run", lambda cmd, cwd: seen.append(cmd))
            setup = _setup(tmp_path)
            mw._default_pull(setup.config)
            assert ["git", "submodule", "update", "--recursive"] in seen
            assert not any("--init" in cmd for cmd in seen)

            calls: list[list[str]] = []

            def fake_run(cmd, **kwargs):
                calls.append(cmd)
                return subprocess.CompletedProcess(cmd, 0)

            monkeypatch.setattr(mw.subprocess, "run", fake_run)
            backup = tmp_path / "rollback_data"
            backup.mkdir()
            mw._restore_rollback(
                setup.config,
                mw.Rollback(db_backup=None, pre_commit="abc", data_backup=backup),
                mw._make_logger(setup.config.log_dir),
            )
            submodule_calls = [c for c in calls if c[:2] == ["git", "submodule"]]
            assert submodule_calls == [["git", "submodule", "update", "--recursive"]]
        ```
      → verify: `uv run pytest tests/scripts/server_contrib/test_maintenance_window.py`
        passes. Put `--init` back in one of the two calls: expect this test to fail. Undo:
        pass.
- [x] 1.3 **A failed window exits 1.**
      - In `maintenance_window.py` `main()`, after `print(outcome.value)`, add
        `if outcome is Outcome.FAILED:` / `sys.exit(1)` and `import sys` at the top.
      - In the same test file, add:
        ```python
        @pytest.mark.parametrize(
            ("outcome", "code"),
            [(Outcome.FAILED, 1), (Outcome.SKIPPED, None), (Outcome.REBUILT, None)],
        )
        def test_main_exits_1_only_when_the_window_failed(
            monkeypatch: pytest.MonkeyPatch, outcome: Outcome, code: int | None
        ) -> None:
            from scripts.server_contrib import maintenance_window as mw

            monkeypatch.setattr(mw, "run_maintenance", lambda config: outcome)
            monkeypatch.setattr("sys.argv", ["maintenance_window.py", "--no-systemd"])
            if code is None:
                mw.main()
            else:
                with pytest.raises(SystemExit) as exc:
                    mw.main()
                assert exc.value.code == code
        ```
      → verify: the test file passes. Remove the two new lines in `main()`: expect the
        `FAILED` case to fail. Undo: pass.
- [x] 1.4 **Bind address in the env file.**
      - In `scripts/server_contrib/add_contributor.sh`, in the `cat > "$env_file" <<ENV`
        block, add `FLET_SERVER_IP=127.0.0.1` on the line before
        `FLET_SERVER_PORT=$port`.
      - In `tests/scripts/server_contrib/test_add_contributor.py`, in
        `test_every_user_shares_one_flat_data_folder_the_sync_scripts_can_read`, add
        `assert alice["FLET_SERVER_IP"] == "127.0.0.1"`.
      → verify: `uv run pytest tests/scripts/server_contrib/test_add_contributor.py`
        passes (not skipped: `htpasswd` is installed at `/usr/bin/htpasswd`). Remove the
        script line: expect that test to fail with a `KeyError`. Undo: pass.
- [x] 1.5 **systemd unit template.** Create `scripts/server_contrib/dpd-gui@.service`
      with exactly the text in spec A.5, plus this comment as the first lines:
      ```
      # One gui2 web instance per contributor: systemctl enable --now dpd-gui@<user>
      # server_setup.sh fills the @...@ values and installs this file.
      # The per-user settings (port, tabs, data folder, bind address) come from
      # /etc/dpd/<user>.env, written by add_contributor.sh.
      ```
      → verify: `grep -c "@USER@\|@HOME@\|@CLONE@\|@UV@" scripts/server_contrib/dpd-gui@.service`
        prints `4`; `sed -e 's|@USER@|root|;s|@HOME@|/root|;s|@CLONE@|/root/dpd-db|;s|@UV@|/root/.local/bin/uv|' scripts/server_contrib/dpd-gui@.service | grep "@"`
        prints only the comment lines (no `@...@` left in `[Service]`). If
        `systemd-analyze` exists locally, write that sed output to the scratchpad as
        `dpd-gui@.service` and run `systemd-analyze verify` on it; report its output
        (warnings about a missing `/root/dpd-db` or env file are expected).
- [x] 1.6 **Setup script.** Create `scripts/server_contrib/server_setup.sh`, mode 755,
      matching spec A.6 (the probe table is the contract). Write it in the style of
      `add_contributor.sh`. Required shape:
      ```bash
      #!/usr/bin/env bash
      # Build a contributor web server from a fresh clone, or finish one.
      #
      #   server_setup.sh [clone dir]        default: $HOME/dpd-db
      #
      # Safe to re-run: each step is skipped when its result is already there.
      # Left out on purpose (see README "New server"): swap, nginx, certificate,
      # add_contributor.sh, the deploy key, systemctl enable.
      set -euo pipefail
      # The window and run_script call a bare `uv`; a nohup shell may lack it on PATH.
      export PATH="$HOME/.local/bin:$PATH"
      clone="${1:-$HOME/dpd-db}"
      repo_url="https://github.com/digitalpalidictionary/dpd-db"
      uv="$HOME/.local/bin/uv"
      data_dir="/var/lib/dpd/contrib_data"
      # tipitaka.rte: the frequency setup reads the SYA corpus from it.
      submodules=(resources/sc-data resources/dpd_submodules resources/tipitaka.rte)

      step() { echo; echo "=== $1 | start $(date '+%F %T')"; step_start=$SECONDS; }
      step_done() { echo "=== done in $((SECONDS - step_start)) s"; }
      ```
      Then one block per row of the spec table, in that order, each:
      `step "<name>"` → probe → command or `echo "skipped: <why>"` → `step_done`.
      A refusal prints its `refused: ...` line and exits 1 without calling `step_done`.
      Exact commands:
      - apt: `if ! dpkg -s pkg-config libicu-dev golang-go >/dev/null 2>&1; then sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y pkg-config libicu-dev golang-go; fi`
      - uv: `[[ -x "$uv" ]] || curl -LsSf https://astral.sh/uv/install.sh | sh`
      - clone: if `$clone/.git` exists and `git -C "$clone" rev-parse HEAD` works, skip;
        if `$clone` exists but is not a working clone, print
        `refused: $clone exists but is not a working clone; move it away` and exit 1;
        else `git clone "$repo_url" "$clone"`. Then `cd "$clone"` for every later step.
      - submodules: `git submodule update --init -- "${submodules[@]}"`
      - sync: `"$uv" sync --all-groups`
      - config: `[[ -f config.ini ]] || { echo "copy config.ini into $clone, then run this script again"; exit 1; }`
      - go: `want="$(awk '/^go /{print $2}' go.mod)"`, `have="$(go version | awk '{print $3}')"; have="${have#go}"`;
        if `want` is empty print `refused: no go line in go.mod` and exit 1;
        fail unless `[[ "$(printf '%s\n' "$want" "$have" | sort -V | head -1)" == "$want" ]]`,
        printing `refused: go $have is older than go.mod's $want`.
      - initial setup: skip if `logs/initial_setup_done` exists; else
        `"$uv" run scripts/bash/initial_setup_run_once.py && mkdir -p logs && touch logs/initial_setup_done`
      - audio index: skip if `audio/db/dpd_audio_index.tsv` exists; else
        `"$uv" run audio/index_release_download.py`
      - data dir: `sudo mkdir -p "$data_dir"`
      - unit: `sed -e "s|@USER@|$(id -un)|g" -e "s|@HOME@|$HOME|g" -e "s|@CLONE@|$clone|g" -e "s|@UV@|$uv|g" scripts/server_contrib/dpd-gui@.service | sudo tee /etc/systemd/system/dpd-gui@.service >/dev/null && sudo systemctl daemon-reload`
      - clean-tree gate: `dirty="$(git status --porcelain --untracked-files=no)"`; if not
        empty, print `refused: tracked files changed before the first build:` and
        `$dirty`, exit 1.
      - first build: skip if `logs/last_built_commit` exists; else
        `"$uv" run scripts/server_contrib/maintenance_window.py --no-systemd --no-push --data-dir "$data_dir"`
        (exits 1 on failure after task 1.3, so `set -e` stops the script).
      - last line: `echo "SETUP_DONE"`.
      Do NOT run the script locally (it installs packages and writes `/etc`).
      → verify: `bash -n scripts/server_contrib/server_setup.sh` prints nothing;
        `test -x scripts/server_contrib/server_setup.sh && echo EXEC_OK`; every row of
        the spec A.6 table has its own `step "..."` line
        (`grep -c '^step "' scripts/server_contrib/server_setup.sh` prints 13 — one per
        table row); `grep -n "submodule update" scripts/server_contrib/server_setup.sh`
        shows the three paths and no bare `--init` without paths;
        `grep -n 'export PATH' scripts/server_contrib/server_setup.sh` shows the line.
- [x] 1.7 **Docs.** In `scripts/server_contrib/README.md`, add a section
      `## New server` after the first paragraph, at most 25 lines:
      what `server_setup.sh` does (one line per step group), what it leaves out (the
      five one-time steps, each with its one command or a pointer to this plan), the
      three submodules and why `tipitaka.rte`, that the window no longer inits new
      submodules (init a new one once by hand), the unit (`systemctl enable --now
      dpd-gui@<user>`; logs via `journalctl -u dpd-gui@<user>`), and the deploy key
      (push-only via `remote set-url --push` + `core.sshCommand`; write access; delete
      it when the server goes away). Add `dpd-gui@.service` and `server_setup.sh` rows
      to "The pieces" table.
      → verify: `grep -n "## New server\|tipitaka.rte\|dpd-gui@\|server_setup.sh" scripts/server_contrib/README.md`
        shows each; the README still says nothing that the new code contradicts
        (read it once end to end).
- [x] 1.8 **Phase gate.**
      `uv run ruff check --fix scripts/server_contrib/generate_components_server.py scripts/server_contrib/maintenance_window.py tests/scripts/server_contrib/test_generate_components_server.py tests/scripts/server_contrib/test_maintenance_window.py tests/scripts/server_contrib/test_add_contributor.py`,
      then `uv run ruff format` on the same files, then
      `uv run pyright scripts/server_contrib/generate_components_server.py scripts/server_contrib/maintenance_window.py`
      and `uv run pyright --project /dev/null tests/scripts/server_contrib/test_maintenance_window.py tests/scripts/server_contrib/test_generate_components_server.py tests/scripts/server_contrib/test_add_contributor.py`,
      then `uv run pytest tests/scripts/server_contrib/`, then `just typecheck`.
      → verify: all clean; paste the pytest summary line here. Record any pre-existing
        error in a file you touched and fix it (CLAUDE.md "touch a file = own its lint").
- [ ] 1.9 **WHO: MAINTAINER.** Review and commit the Phase 1 files (only these:
      the five files above, `dpd-gui@.service`, `server_setup.sh`, `README.md`,
      `config_server.md`, and this thread folder), e.g.
      `#215 contrib server: setup script, unit, bold refill, no submodule init`, and
      push `main`.
      → verify: `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && git ls-remote origin main`
        shows the same hash as `git rev-parse HEAD`.

## Phase 2 — Hand-off to the server — WHO: MAINTAINER

- [ ] 2.1 Copy this thread folder to the server:
      `ssh epitaka 'mkdir -p ~/dpd-contrib/handoff'`
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && rsync --bwlimit=400 -r kamma/threads/20261101_contrib_6_e2e_server_test epitaka:~/dpd-contrib/handoff/`
      → verify: `ssh epitaka 'ls ~/dpd-contrib/handoff/20261101_contrib_6_e2e_server_test'`
        lists `spec.md` and `plan.md`.
- [ ] 2.2 On the server (`ssh epitaka`), create
      `~/dpd-contrib/handoff/20261101_contrib_6_e2e_server_test/results.md` with
      `# Results — contrib_6 end-to-end server test`, an empty `## Decisions` section,
      and `## Values`: SSH login `root@187.126.118.33`, server name
      `187-126-118-33.sslip.io`.
      → verify: the file exists with the three headings.
- [ ] 2.3 Read spec "Decisions made while the owner was away". Write each of the six
      under `## Decisions` in that file as "confirmed" or the change. A changed
      decision may change later tasks: tell the local agent before going on.
      → verify: six lines under `## Decisions`.
- [ ] 2.4 Start the server agent in that folder in normal permission mode. First
      prompt: "Read spec.md, then plan.md in this folder. Do the first open AGENT task
      in plan.md, starting at Phase 3."
      → verify: the agent writes `## 3.1` into `results.md`.

## Phase 3 — Pre-state and a fresh build

- [ ] 3.1 **WHO: AGENT.** Record the pre-state under `## 3.1 Pre-state`:
      ```
      ls -la /etc/nginx/sites-enabled /etc/nginx/dpd
      ls /etc/letsencrypt/live
      free -m
      swapon --show
      df -h ~
      ps -eo pid,user,etime,cmd | grep -i "[e]pitaka" || echo NO_EPITAKA_PROCESSES
      ps -eo pid,cmd | grep "[g]ui2/main.py" || echo NO_GUI2_RUNNING
      ss -ltn | grep -E ':855[0-9]\b' || echo NO_855X_LISTENERS
      ls ~/dpd-db/.git >/dev/null && cd ~/dpd-db && git log -1 --oneline
      ```
      **EXPECT:** `NO_GUI2_RUNNING`, `NO_855X_LISTENERS`; `/etc/nginx/dpd` lists
      `alice.conf`, `alice.htpasswd`, `zz_root_asset_shim.conf`; `swapon --show` prints
      nothing. If gui2 runs or 855x listens: STOP.
- [ ] 3.2 **WHO: AGENT.** Move the old clone aside:
      `test ! -e ~/dpd-db_contrib4 && mv ~/dpd-db ~/dpd-db_contrib4 && echo MOVED`
      **CHECK:** `ls -d ~/dpd-db ~/dpd-db_contrib4`
      **EXPECT:** `MOVED`; then `~/dpd-db` is missing and `~/dpd-db_contrib4` exists.
- [ ] 3.3 **WHO: AGENT, sudo, after the maintainer says yes.** Add swap:
      ```
      sudo fallocate -l 4G /swapfile
      sudo chmod 600 /swapfile
      sudo mkswap /swapfile
      sudo swapon /swapfile
      swapon --show
      ```
      **EXPECT:** `swapon --show` lists `/swapfile` with size `4G`. No `/etc/fstab`
      change (spec B.3).
- [ ] 3.4 **WHO: AGENT, sudo (the script installs apt packages), after the maintainer
      says yes.** Fetch the setup script from GitHub and start the first run in the
      background:
      ```
      mkdir -p ~/logs
      curl -fsSL https://raw.githubusercontent.com/digitalpalidictionary/dpd-db/main/scripts/server_contrib/server_setup.sh -o ~/server_setup.sh
      bash -n ~/server_setup.sh && echo SYNTAX_OK
      nohup bash -c 'bash ~/server_setup.sh; echo "exit=$?"' > ~/logs/server_setup_run1.log 2>&1 &
      echo $! > ~/logs/server_setup.pid
      ```
      This run clones and syncs (long: the submodules are about 2.3 GB), then stops at
      `config.ini`. Wait as in rule 15:
      `kill -0 "$(cat ~/logs/server_setup.pid)" 2>/dev/null && echo RUNNING || echo ENDED; tail -n 3 ~/logs/server_setup_run1.log`
      When `ENDED`:
      `tail -n 5 ~/logs/server_setup_run1.log; grep "^=== " ~/logs/server_setup_run1.log`
      **EXPECT:** `SYNTAX_OK`; the log ends with the two lines
      `copy config.ini into /root/dpd-db, then run this script again` and `exit=1`.
      Any other ending: STOP. Copy the `=== ` lines (step times) into `results.md`.
- [ ] 3.5 **WHO: MAINTAINER, server.** Copy the config, then check the three values the
      server build needs. He reads the counts; nobody prints the file:
      ```
      cp ~/dpd-db_contrib4/config.ini ~/dpd-db/config.ini
      grep -c '^db_rebuild = yes' ~/dpd-db/config.ini
      grep -c '^freq_maps = yes' ~/dpd-db/config.ini
      grep -c '^deconstructor = yes' ~/dpd-db/config.ini
      ```
      Each count must be `1` (values from `scripts/server_contrib/config_server.template`).
      If one is `0`, he sets that value himself and re-runs the counts.
      **CHECK (AGENT):** `test -f ~/dpd-db/config.ini && echo CONFIG_PRESENT`
      **EXPECT:** `CONFIG_PRESENT`, and the maintainer says the three counts were `1`.
- [ ] 3.6 **WHO: AGENT, sudo (the script writes `/var/lib/dpd` and the systemd unit),
      after the maintainer says yes.** Start the second run in the background, with a
      memory log:
      ```
      nohup vmstat -t 60 > ~/logs/vmstat_setup.log 2>&1 &
      echo $! > ~/logs/vmstat.pid
      nohup bash ~/server_setup.sh > ~/logs/server_setup_run2.log 2>&1 &
      echo $! > ~/logs/server_setup.pid
      ```
      Wait. Every 10 minutes run:
      `kill -0 "$(cat ~/logs/server_setup.pid)" 2>/dev/null && echo RUNNING || echo ENDED; tail -n 3 ~/logs/server_setup_run2.log`
      When it prints `ENDED`, stop the memory log:
      `kill "$(cat ~/logs/vmstat.pid)"`
      Then:
      ```
      tail -n 20 ~/logs/server_setup_run2.log
      grep "^=== " ~/logs/server_setup_run2.log
      awk 'NR>2' ~/logs/vmstat_setup.log | sort -k4 -n | head -3
      awk 'NR>2 && $3>0' ~/logs/vmstat_setup.log | head -1 || true
      ```
      (`vmstat` columns: the 3rd is swap used, the 4th is free memory, both in KB.)
      **EXPECT:** the last line of the log is `SETUP_DONE`. Copy the `=== ` lines (each
      step's time) and the three lowest-free-memory `vmstat` lines into `results.md`.
      If the log ends any other way: STOP and copy the last 60 lines. If a step hit the
      one-hour timeout (`TimeoutExpired` in the log), also run
      `ps -eo pid,etime,cmd | grep -E "[d]econstructor|[g]o-build|[f]requency" || echo NONE_LEFT`
      and copy it (spec A.6: children may still run).
      Do not give up early: the run can take several hours on 2 CPUs. After 8 hours
      still `RUNNING`, STOP and ask.
- [ ] 3.7 **WHO: AGENT.** Check the fresh build:
      ```
      cd ~/dpd-db
      git status --porcelain --untracked-files=no | head
      cat logs/last_built_commit; git rev-parse HEAD
      tail -n 15 logs/maintenance_*.log
      ~/.local/bin/uv run python -c "import sqlite3; c=sqlite3.connect('file:dpd.db?mode=ro', uri=True); print([c.execute(f'select count(*) from {t}').fetchone()[0] for t in ('dpd_headwords','lookup','bold_definitions')])"
      ls -l audio/db/dpd_audio_index.tsv shared_data/frequency/cst_file_freq.json db/bold_definitions/bold_definitions.tsv
      ls resources/dpd_submodules/cst/romn_txt | wc -l
      git submodule status
      go version; free -m; swapon --show
      ```
      **EXPECT:** `git status` prints nothing; the two hashes are equal; the window log
      ends `maintenance window end: rebuilt`; the counts are above
      `[50000, 400000, 0]`; the three files exist; `romn_txt` holds more than 200 files;
      `git submodule status` shows a space (initialised) only for `resources/sc-data`,
      `resources/dpd_submodules`, `resources/tipitaka.rte` and `-` for all the others.
      Any mismatch: STOP.
- [ ] 3.8 **WHO: AGENT. Phase check.** Write `## Phase 3 verdict` in `results.md`:
      setup PASS or FAIL, total time (sum of the step times), the slowest three steps,
      the lowest free memory seen, and whether swap was used (the second `awk` line in
      3.6 printed a line or not).
      → verify: the section exists and every number in it is copied from a log line
        quoted above it.

## Phase 4 — alice works in the browser

- [ ] 4.1 **WHO: AGENT, sudo, after the maintainer says yes.** Move the old alice files
      aside:
      ```
      sudo mkdir -p /root/contrib4_backup
      sudo mv /etc/dpd/alice.env /etc/nginx/dpd/alice.conf /etc/nginx/dpd/alice.htpasswd /root/contrib4_backup/
      sudo ls /root/contrib4_backup
      ```
      **EXPECT:** the three files are listed.
- [ ] 4.2 **WHO: MAINTAINER, server.** Re-create alice with the fixed script and type a
      password at its prompt:
      `sudo bash ~/dpd-db/scripts/server_contrib/add_contributor.sh alice 8551 "Bold Search,DB"`
      **EXPECT:** `Added alice.`
- [ ] 4.3 **WHO: AGENT, sudo, after the maintainer says yes.**
      ```
      sudo chgrp www-data /etc/nginx/dpd/alice.htpasswd
      sudo nginx -t
      sudo systemctl reload nginx
      sudo systemctl enable --now dpd-gui@alice
      ```
      (The env file is never read; the `ss` line below proves the bind address that
      task 1.4 put in it.) Wait 90 seconds, then:
      ```
      systemctl is-active dpd-gui@alice
      ss -ltn | grep -E ':855[0-9]\b'
      journalctl -u dpd-gui@alice --no-pager | grep -c Traceback
      journalctl -u dpd-gui@alice --no-pager | tail -n 15
      ```
      **EXPECT:** `syntax is ok` and `test is successful`; `active`; exactly one
      line `127.0.0.1:8551`; Traceback count `0`.
- [ ] 4.4 **WHO: MAINTAINER, browser.** Open `https://187-126-118-33.sslip.io/alice/`,
      sign in with the new password. The AGENT asks one at a time and records each
      answer under `## 4.4`:
      1. Does gui2 load and show "Database loaded."?
      2. Bold Search: search a common bold word — are there results?
      3. Pass1Auto: pick a book — does it load with no "No such file" error?
      4. Pass1Add: fill in the first real word, press **Add to DB** — does the
         "Preview before save" dialog show the preview (new tab or its "Open preview"
         button)? Then press Save in that dialog. Did it save?
      5. Add the second real word the same way.
      6. In Pass1Add's sandhi row, use each of these once, on real words:
         **Sandhi OK**, **Add to Sandhi**, **Add to Variants**, **Add to Spelling**.
         Did each one report success?
      7. Any error or red screen? Copy the text.
      **EXPECT:** yes to 1–6; "none" to 7. Any no: record it as a finding, then STOP and
      ask whether to go on.
- [ ] 4.5 **WHO: AGENT.** Check what alice wrote, and that gui2 changed no tracked file
      (the window refuses a dirty tree):
      ```
      ls -l /var/lib/dpd/contrib_data/
      ~/.local/bin/uv run python -c "import json; d=json.load(open('/var/lib/dpd/contrib_data/additions_alice.json')); print(len(d)); [print(k, v.get('lemma_1')) for k, v in d.items()]"
      cd ~/dpd-db && git status --porcelain --untracked-files=no
      ```
      **EXPECT:** `additions_alice.json` holds 2 entries with the two lemmas from 4.4;
      `checked_alice.csv` (Sandhi OK), `manual_corrections_alice.tsv` (Add to Sandhi),
      `variant_readings_alice.tsv` (Add to Variants) and
      `spelling_mistakes_alice.tsv` (Add to Spelling) exist; `git status` prints nothing.
      If `git status` prints anything: STOP (window #1 would refuse). Write the two
      lemmas into `results.md` under `## Values` as `word 1` and `word 2`.
- [ ] 4.6 **WHO: AGENT. Phase check.** `## Phase 4 verdict`: PASS if 4.3–4.5 met EXPECT.
      → verify: the verdict names each of 4.3, 4.4, 4.5 as met or not.

## Phase 5 — Deploy key and window #1

- [ ] 5.1 **WHO: AGENT.**
      ```
      test ! -e ~/.ssh/dpd_deploy && ssh-keygen -t ed25519 -N "" -C "dpd contrib6 temp server" -f ~/.ssh/dpd_deploy
      cat ~/.ssh/dpd_deploy.pub
      ```
      Show the public key line to the maintainer.
      **EXPECT:** one line starting `ssh-ed25519`.
- [ ] 5.2 **WHO: MAINTAINER, GitHub.** Add the public key as a deploy key on
      `digitalpalidictionary/dpd-db` with **Allow write access**, title
      `dpd contrib6 temp server`. From the laptop (the key is public; `/tmp` is fine):
      `ssh epitaka 'cat ~/.ssh/dpd_deploy.pub' > /tmp/dpd_deploy.pub && gh repo deploy-key add /tmp/dpd_deploy.pub --repo digitalpalidictionary/dpd-db --allow-write --title "dpd contrib6 temp server" && rm /tmp/dpd_deploy.pub`
      (or paste it in GitHub: Settings → Deploy keys → Add, tick "Allow write access").
      Then list it: `gh repo deploy-key list --repo digitalpalidictionary/dpd-db`.
      **EXPECT:** the key is listed with read-write. The maintainer tells the AGENT the
      id; the AGENT writes it into `results.md` under `## Values` as `deploy key id`.
- [ ] 5.3 **WHO: AGENT.**
      ```
      cd ~/dpd-db
      git remote set-url --push origin git@github.com:digitalpalidictionary/dpd-db.git
      git config core.sshCommand "ssh -i ~/.ssh/dpd_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
      git config user.name "dpd contrib server"
      git config user.email "dpd@4nt.org"
      git remote -v
      ssh -i ~/.ssh/dpd_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -T git@github.com; echo "ssh_exit=$?"
      ```
      **EXPECT:** `git remote -v` shows fetch on `https://github.com/...` and push on
      `git@github.com:...`; the ssh line prints `successfully authenticated` and
      `ssh_exit=1` (GitHub always exits 1 for `-T`). Anything else: STOP.
- [ ] 5.4 **WHO: AGENT.** Window #1:
      ```
      cd ~/dpd-db
      git rev-parse HEAD; git ls-remote origin main
      ~/.local/bin/uv run scripts/server_contrib/maintenance_window.py --instance dpd-gui@alice --data-dir /var/lib/dpd/contrib_data > ~/logs/window1.log 2>&1; echo "exit=$?"
      tail -n 3 ~/logs/window1.log
      tail -n 40 "logs/maintenance_$(date +%Y%m%d).log" | grep -E "start|contrib_push|FAILED|rebuild|end:"
      git ls-remote origin contributions
      systemctl is-active dpd-gui@alice
      ```
      The run is short if `main` has not moved, and hours if it has (then wait as in
      3.6, using `kill -0` on the window's pid: start it with `nohup ... &` and
      `echo $! > ~/logs/window1.pid` instead).
      **EXPECT:** `exit=0`; the last output line is `skipped` if the two hashes before
      the run were equal, else `rebuilt`; the log has `contrib_push: pushed` and no
      `FAILED`; `git ls-remote` prints one hash for `refs/heads/contributions`;
      `active`.
- [ ] 5.5 **WHO: AGENT.** Freeze alice until window #2 (spec B.8):
      `sudo systemctl stop dpd-gui@alice && systemctl is-active dpd-gui@alice`
      **EXPECT:** `inactive`. Tell the maintainer: "alice is stopped until window #2;
      the local half can start."
- [ ] 5.6 **WHO: AGENT. Phase check.** `## Phase 5 verdict`: PASS if 5.3–5.5 met
      EXPECT; include the window #1 outcome and the pushed hash.
      → verify: the verdict quotes the `contrib_push:` log line.

## Phase 6 — The maintainer adds alice's work locally

Run from `/home/bodhirasa/MyFiles/3_Active/dpd-db`. The LOCAL AGENT may run the
read-only checks; the MAINTAINER runs every git write and gui2.

- [ ] 6.0 **WHO: MAINTAINER.** Clear the files the merge writes of other threads'
      work (spec decision 5): commit, or set aside by your own method, the uncommitted
      changes in `shared_data/deconstructor/checked.csv`,
      `shared_data/deconstructor/variant_readings.tsv`,
      `shared_data/deconstructor/manual_corrections.tsv`,
      `shared_data/user_dictionary.txt` and the spelling file. Other dirty files
      (e.g. `tools/configger.py`) do not block the merge; leave them out of every
      commit in this phase.
      → verify (LOCAL AGENT):
        `git status --porcelain shared_data/ gui2/data/` prints nothing.
- [ ] 6.1 **WHO: LOCAL AGENT.** Check the branch the server pushed:
      ```
      git fetch origin contributions
      git log --oneline origin/main..origin/contributions
      git diff --stat origin/contributions~1 origin/contributions
      ```
      **EXPECT:** exactly one commit, `contrib: submit data <date>`; its diff touches
      only `gui2/data/*_alice.*` files. If not: stop and tell the maintainer.
- [ ] 6.2 **WHO: MAINTAINER.** `just contrib-merge`
      → verify (LOCAL AGENT): `git log -1 --oneline` is the merge; the files
        `gui2/data/additions_alice.json` etc. now exist on `main`; `git diff --stat`
        shows the merge script's changes to the shared files, and
        `gui2/data/contrib_lines_merged.json` lists the sandhi, spelling and variant lines.
- [ ] 6.3 **WHO: MAINTAINER, desktop gui2 (`just gui`).** In Pass2Add press **Add**
      (tooltip "additions"); the first of alice's words loads. Check it, then press
      **Add to DB**. Repeat for the second. Then the global tab → **Backup & Quit**.
      → verify (LOCAL AGENT):
        `uv run python -c "import json; print(json.load(open('gui2/data/additions_alice.json')))"`
        prints `{}`;
        `uv run python -c "import json; print(sum(1 for e in json.load(open('gui2/data/additions_added.json')) if e.get('_contributor') == 'alice'))"`
        prints `2` (the file is a JSON list, `gui2/additions_manager.py` `_append_to_log`);
        `git diff --stat db/backup_tsv/` shows the TSV backup changed;
        `sqlite3 dpd.db "select id, lemma_1 from dpd_headwords where lemma_1 in ('<word 1>','<word 2>')"`
        (lemmas from `results.md` Values) prints both.
- [ ] 6.4 **WHO: MAINTAINER.** Commit and push `main`. Stage by explicit file list:
      the files 6.2 and 6.3 changed (`gui2/data/*_alice.*`, `gui2/data/additions_added.json`,
      `gui2/data/contrib_lines_merged.json`, the shared files the merge changed,
      `db/backup_tsv/*`). Re-check `db_tests/db_tests_columns.tsv` is not in the list
      unless he meant it (CLAUDE.md).
      → verify: `git ls-remote origin main` equals `git rev-parse HEAD`; record the
        hash in the server's `results.md` (tell the server agent).
- [ ] 6.5 **WHO: LOCAL AGENT. Phase check.** Write a short `## Phase 6 (local)` note
      for the maintainer to paste into the server's `results.md`: the merge commit, the
      pushed hash, the two lemmas with their new db ids, and the entries in
      `additions_added.json`.
      → verify: every value is read from git or the db, not typed from memory.

## Phase 7 — Window #2 closes the loop — WHO: AGENT

- [ ] 7.1 Save alice's files before the window:
      ```
      mkdir -p ~/logs/before_window2
      cp -p /var/lib/dpd/contrib_data/* ~/logs/before_window2/
      ls -l ~/logs/before_window2
      ```
      **EXPECT:** the same files as in 4.5.
- [ ] 7.2 Window #2, in the background (it rebuilds, so it takes hours):
      ```
      cd ~/dpd-db
      nohup ~/.local/bin/uv run scripts/server_contrib/maintenance_window.py --instance dpd-gui@alice --data-dir /var/lib/dpd/contrib_data > ~/logs/window2.log 2>&1 &
      echo $! > ~/logs/window2.pid
      ```
      Wait as in 3.6 (`kill -0 "$(cat ~/logs/window2.pid)"`). When it ends:
      `tail -n 3 ~/logs/window2.log; tail -n 60 "logs/maintenance_$(date +%Y%m%d).log" | grep -E "start|reconciled|contrib_push|FAILED|rebuild|health|end:"; git rev-parse HEAD; git ls-remote origin main`
      (If the window started before midnight and ended after it, read the log of the
      start date too.)
      **EXPECT:** last output line `rebuilt`; `health check passed`; no `FAILED`;
      `git rev-parse HEAD` is the hash from 6.4, or a later `main` commit (CI may push).
- [ ] 7.3 Check the loop closed:
      ```
      for f in ~/logs/before_window2/*; do echo "== $(basename "$f")"; diff "$f" "/var/lib/dpd/contrib_data/$(basename "$f")" | head -20; done
      ~/.local/bin/uv run python -c "import json; print(json.load(open('/var/lib/dpd/contrib_data/additions_alice.json')))"
      ~/.local/bin/uv run python -c "import sqlite3; c=sqlite3.connect('file:dpd.db?mode=ro', uri=True); print(c.execute('select id, lemma_1 from dpd_headwords where lemma_1 in (?, ?)', ('<word 1>', '<word 2>')).fetchall()); print(c.execute('select count(*) from bold_definitions').fetchone())"
      git ls-remote origin contributions; git rev-parse HEAD
      systemctl is-active dpd-gui@alice
      ss -ltn | grep -E ':855[0-9]\b'
      ```
      (Fill `<word 1>` and `<word 2>` from `results.md` Values.)
      **EXPECT:** `additions_alice.json` is `{}`; the diff removes exactly the two
      processed entries and the merged flag lines (the header line of the variant and
      spelling files stays), nothing else; the db query lists both lemmas, with the ids
      from 6.5; the bold count is above 0; `contributions` does NOT equal `HEAD`: `main`
      keeps alice's flag files as the merge left them, the reconcile emptied them on the
      server, so the push makes one new `contrib: submit data` commit that removes the
      merged lines (`contrib_push.py` commits whenever the copied files differ);
      `active`; one line `127.0.0.1:8551`.
- [ ] 7.3b **WHO: LOCAL AGENT, laptop.** Read that push:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && git fetch origin contributions && git diff --stat origin/contributions~1 origin/contributions`
      **EXPECT:** only `gui2/data/*_alice.*` flag files change, by removing the lines
      merged in 6.2; `additions_alice.json` is not in the diff (already `{}` on both
      sides). This is the next night's normal "nothing new" state; merging it later is
      harmless. Record it in the server's `results.md` via the maintainer.
- [ ] 7.4 **WHO: MAINTAINER, browser.** At `https://187-126-118-33.sslip.io/alice/`
      (reload): Bold Search returns results; searching the DB tab for `<word 1>` shows
      it as a normal headword. The AGENT records both answers.
- [ ] 7.5 **Phase check.** `## Phase 7 verdict`: PASS if 7.2–7.4 and 7.3b met EXPECT.
      → verify: the verdict lists each EXPECT clause of 7.3 and 7.3b as met or not.

## Phase 8 — Wrap-up

- [ ] 8.1 **WHO: AGENT.** Compare with the pre-state: re-run the 3.1 commands; write
      the differences under `## 8.1 End state`. **EXPECT:** the only nginx changes are
      the re-created `alice.conf` / `alice.htpasswd`; the epitaka processes from 3.1
      are still there (same pids, unless they restart on their own); `/swapfile` on.
- [ ] 8.2 **WHO: AGENT.** Write `## Findings` in `results.md`: every STOP, every
      deviation, the step times, the memory peak, and anything for contrib_1 Phase 3
      or contrib_x. Then stop; the agent's work ends here.
- [ ] 8.3 **WHO: MAINTAINER, laptop.** Copy the results back:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && mkdir -p kamma/threads/20261101_contrib_6_e2e_server_test/artifacts/server && rsync --bwlimit=400 -r epitaka:dpd-contrib/handoff/20261101_contrib_6_e2e_server_test/results.md 'epitaka:logs/server_setup_run*.log' 'epitaka:logs/window*.log' epitaka:logs/vmstat_setup.log 'epitaka:dpd-db/logs/maintenance_*.log' epitaka:logs/before_window2 kamma/threads/20261101_contrib_6_e2e_server_test/artifacts/server/`
      (Remote paths are relative to root's home. The wildcards are expanded on the
      server; if this rsync refuses them, add `--old-args`.)
      → verify: `ls kamma/threads/20261101_contrib_6_e2e_server_test/artifacts/server/`
        lists `results.md` and the logs.
- [ ] 8.4 **WHO: MAINTAINER.** Delete the deploy key:
      `gh repo deploy-key delete <deploy key id> --repo digitalpalidictionary/dpd-db`
      → verify: `gh repo deploy-key list --repo digitalpalidictionary/dpd-db` no longer
        lists it.
- [ ] 8.5 **WHO: LOCAL AGENT.** Read `artifacts/server/results.md` and add a
      `## Outcome` section to this plan: PASS/FAIL per phase, the measured build time,
      and a list of follow-ups, each marked for contrib_1 or contrib_x. Add the measured
      first-build time and memory peak to `scripts/server_contrib/README.md` "New
      server" (one line). Do not edit contrib_1 or contrib_x files; list the edits for
      the maintainer instead.
      → verify: every number in `## Outcome` is quoted from `artifacts/server/`.
