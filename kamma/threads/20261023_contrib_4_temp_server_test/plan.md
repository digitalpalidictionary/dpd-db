# Plan: test gui2 on a borrowed server — no domain, a few weeks of access

**Thread:** 20261023_contrib_4_temp_server_test · **Spec:** `spec.md` (read first)
**GitHub issue:** #215 · **Rewritten:** 2026-10-31 for a smaller server agent

## READ THIS FIRST — rules for the SERVER AGENT

You are the SERVER AGENT. You run on the server. You are not Claude. Follow
these rules exactly. If a rule and a task seem to disagree, STOP and ask.

1. Do the tasks in order. Do one task at a time. Do not skip a task.
2. Each step says **WHO**: `MAINTAINER` or `AGENT`. Do only `AGENT` steps.
   For a `MAINTAINER` step, show him the command, then wait until he says it
   is done.
3. Copy each command exactly. Do not change it, shorten it, or "improve" it.
4. After each task, run its **CHECK**. Compare the output with **EXPECT**.
5. If the output does not match EXPECT, or any command prints an error:
   STOP. Write the command and its full output in `results.md`. Tell the
   maintainer. Do not try a fix of your own.
6. Write results ONLY to
   `~/dpd-contrib/handoff/20261023_contrib_4_temp_server_test/results.md`. Append to it.
   Never edit `spec.md`, `plan.md` or `handoff.md`.
7. Never edit any file inside `~/dpd-db`. Never edit code.
8. Never print, open, read, grep or edit `config.ini`, any `.env` file, or any
   htpasswd file. Only the maintainer types secrets.
9. Git in `~/dpd-db`: you may run only `clone`, `submodule update`, `pull`,
   `log`, `status`, `merge-base`. NEVER `commit`, `push`, `stash`, `reset`,
   `checkout`, `restore`, `clean`.
10. Never use `sudo` unless the task says so. Never install anything with
    `apt`, `pip` or `npm`.
11. Stop gui2 only with `~/stop_gui2.sh`. Never use `pkill`, `killall` or
    `kill -9`.
12. Never delete anything in `~/contrib_data`.
13. Ask the maintainer one question at a time.

## Values

The MAINTAINER fills these in `results.md` (section "Values") before the agent
starts. In MAINTAINER commands below, replace `<user>@<ip>` with them.

| Name | Value |
|---|---|
| SSH login | `<user>@<ip>` |
| Server IP | `<ip>` |

## Phase 0 — Before the agent starts — MAINTAINER only

- [ ] 0.1 **WHO: MAINTAINER, own machine.** Create the folder on the server
      and copy this thread folder over:
      `ssh <user>@<ip> 'mkdir -p ~/dpd-contrib/handoff'`
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && rsync --bwlimit=400 -r kamma/threads/20261023_contrib_4_temp_server_test <user>@<ip>:~/dpd-contrib/handoff/`
      If the server has no rsync, use:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && scp -l 3200 -r kamma/threads/20261023_contrib_4_temp_server_test <user>@<ip>:~/dpd-contrib/handoff/`
- [ ] 0.2 **WHO: MAINTAINER, server.** Create `results.md` with this content,
      and fill the Values table:
      ```
      # Results — contrib_4 temp server test

      ## Values
      | Name | Value |
      |---|---|
      | SSH login | |
      | Server IP | |
      ```
- [ ] 0.3 **WHO: MAINTAINER.** Install and log in the server agent. Start it in
      `~/dpd-contrib/handoff/20261023_contrib_4_temp_server_test`, in normal permission
      mode (not auto-approve). Its first prompt: "Read spec.md, then plan.md,
      then handoff.md in this folder. Do the first open task in plan.md."

## Phase 1 — Survey

- [ ] 1.1 **WHO: AGENT.** Run each command. Put every output in a table in
      `results.md` under "## 1.1 Survey".
      ```
      uname -a
      cat /etc/os-release
      free -m
      nproc
      df -h ~
      sudo -n true && echo SUDO_YES || echo SUDO_NO
      git --version
      curl --version | head -1
      command -v rsync setsid ss || true
      git ls-remote https://github.com/digitalpalidictionary/dpd-db HEAD
      curl -sSfI https://astral.sh/uv/install.sh | head -1
      curl -sSfI https://pypi.org/simple/ | head -1
      ```
      **EXPECT:** `git` and `curl` print a version. `git ls-remote` prints one
      line: a 40-character hash, then `HEAD`. Both `curl -sSfI` lines start
      with `HTTP/` and contain `200`. `setsid` and `ss` print a path.
      If `git` or `curl` is missing, or a network line fails: STOP.
- [ ] 1.2 **WHO: AGENT.** Decide from the survey. Write the decision in
      `results.md` under "## 1.2 Decision".
      - Take the `available` number from the `Mem:` line of `free -m`.
        - `available` ≥ 6000 → 2 instances (alice on 8551, bob on 8552).
        - 3000 to 5999 → 1 instance (alice on 8551).
        - under 3000 → 0 instances. Write "RAM too low", then STOP. This is a
          finding, not a failure.
      - Take the `Avail` number from `df -h ~`. Under 10G → STOP.
      - Write `sudo: yes` or `sudo: no`. Phase 4 runs only with `sudo: yes`.
      - Write whether `rsync` was found. The maintainer needs this for 2.3.

## Phase 2 — Setup and smoke test

- [ ] 2.1 **WHO: AGENT.** Install uv in the home folder:
      ```
      curl -LsSf https://astral.sh/uv/install.sh | sh
      ~/.local/bin/uv --version
      ```
      **EXPECT:** the last line starts with `uv `. If the installer put uv in
      another folder, STOP. All later commands use `~/.local/bin/uv`.
- [ ] 2.2 **WHO: AGENT.** Clone the repo and the two submodules. The
      submodules are large, so this can take a long time. Wait for it.
      ```
      cd ~ && git clone https://github.com/digitalpalidictionary/dpd-db
      cd ~/dpd-db && git submodule update --init resources/sc-data resources/dpd_submodules
      cd ~/dpd-db && ~/.local/bin/uv sync --all-groups
      cd ~/dpd-db && ~/.local/bin/uv run python -c "import flet, sqlalchemy; print('IMPORT_OK')"
      cd ~/dpd-db && git submodule status resources/sc-data resources/dpd_submodules
      ```
      **EXPECT:** the import line prints `IMPORT_OK`. Each `submodule status`
      line starts with a space, not `-` or `+`. Never run a bare
      `git submodule update --init` with no paths: it fetches every submodule.
      Never run `uv sync` without `--all-groups`.
- [ ] 2.3 **WHO: MAINTAINER, own machine.** Copy the db. First close gui2 and
      anything else that has `dpd.db` open. Then fold the WAL into the db:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && uv run python -c "import sqlite3; print(sqlite3.connect('dpd.db').execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone())"`
      It must print `(0, 0, 0)`. If the first number is 1, something still has
      the db open. Close it and run the line again. Then copy (about 1.5 h):
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && rsync --bwlimit=400 --partial --progress dpd.db <user>@<ip>:~/dpd-db/`
      If the server has no rsync (task 1.2):
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && scp -l 3200 dpd.db <user>@<ip>:~/dpd-db/`
      Then print the checksum, and give the hash to the agent:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && sha256sum dpd.db`
      Do not open gui2 locally until the agent confirms the match.
- [ ] 2.4 **WHO: AGENT.** Check the db:
      ```
      cd ~/dpd-db && sha256sum dpd.db
      cd ~/dpd-db && ~/.local/bin/uv run python -c "import sqlite3; print(sqlite3.connect('file:dpd.db?mode=ro', uri=True).execute('select count(*) from dpd_headwords').fetchone()[0])"
      ```
      **EXPECT:** the hash equals the maintainer's hash exactly. The count is a
      number above 80000. Write both in `results.md`.
- [ ] 2.5 **WHO: MAINTAINER, server.** Make `config.ini`. The agent does not
      do this step and does not open the file afterwards.
      `cd ~/dpd-db && cp scripts/server_contrib/config_server.template config.ini && nano config.ini`
      Replace the two `<FILL IN ...>` values under `[apis]` with the real keys.
      Save. Tell the agent "config done".
- [ ] 2.6 **WHO: AGENT.** Check that `config.ini` exists and that no
      placeholder is left. This counts lines only. It prints no content.
      ```
      cd ~/dpd-db && test -f config.ini && echo CONFIG_EXISTS
      cd ~/dpd-db && grep -c "FILL IN" config.ini || true
      cd ~/dpd-db && git status --porcelain --untracked-files=no
      ```
      **EXPECT:** `CONFIG_EXISTS`, then `0`, then no output at all.
- [ ] 2.7 **WHO: AGENT.** Write the two scripts. Copy each text exactly.
      ```
      cat > ~/start_gui2.sh <<'EOF'
      #!/usr/bin/env bash
      # usage: ~/start_gui2.sh <username> <port>
      set -euo pipefail
      user="$1"
      port="$2"
      mkdir -p "$HOME/contrib_data" "$HOME/logs"
      cd "$HOME/dpd-db"
      DPD_GUI2_USERNAME="$user" \
      DPD_GUI2_ROLE=contributor-server \
      DPD_GUI2_TABS="Bold Search,DB" \
      DPD_GUI2_DATA_DIR="$HOME/contrib_data" \
      FLET_FORCE_WEB_SERVER=true \
      FLET_SERVER_IP=127.0.0.1 \
      FLET_SERVER_PORT="$port" \
      setsid nohup "$HOME/.local/bin/uv" run python gui2/main.py \
        >> "$HOME/logs/gui2_$user.log" 2>&1 < /dev/null &
      echo $! > "$HOME/logs/gui2_$user.pid"
      echo "started $user on 127.0.0.1:$port pid $(cat "$HOME/logs/gui2_$user.pid")"
      EOF
      cat > ~/stop_gui2.sh <<'EOF'
      #!/usr/bin/env bash
      # usage: ~/stop_gui2.sh <username>
      set -uo pipefail
      pidfile="$HOME/logs/gui2_$1.pid"
      if [ ! -f "$pidfile" ]; then echo "no pid file for $1"; exit 1; fi
      pid="$(cat "$pidfile")"
      # setsid made pid the leader of its own group: this stops uv and its python child
      kill -TERM -- "-$pid" 2>/dev/null || echo "process group $pid was not running"
      sleep 5
      rm -f "$pidfile"
      ps -eo pid,cmd | grep "[g]ui2/main.py" || echo "NO_GUI2_RUNNING"
      EOF
      chmod +x ~/start_gui2.sh ~/stop_gui2.sh
      bash -n ~/start_gui2.sh && bash -n ~/stop_gui2.sh && echo SCRIPTS_OK
      ```
      **EXPECT:** `SCRIPTS_OK`.
- [ ] 2.8 **WHO: AGENT.** Start alice. Wait 60 seconds. Then check:
      ```
      ~/start_gui2.sh alice 8551
      ss -ltn | grep 855
      tail -n 30 ~/logs/gui2_alice.log
      ```
      **EXPECT:** `ss` shows `127.0.0.1:8551` and nothing else on 855x. If it
      shows `0.0.0.0:8551`, `*:8551` or `[::]:8551`: run
      `~/stop_gui2.sh alice` at once, then STOP. The log shows no
      `Traceback`. If it shows a `Traceback`, copy it to `results.md`, run
      `~/stop_gui2.sh alice`, then STOP.
      If task 1.2 chose 2 instances, also run `~/start_gui2.sh bob 8552` and
      check the same way.
- [ ] 2.9 **WHO: MAINTAINER, own machine.** Open the tunnel and keep it open:
      `ssh -N -L 8551:127.0.0.1:8551 <user>@<ip>`
      Open `http://localhost:8551` in the browser. The AGENT asks him these,
      one at a time, and records each answer:
      1. Does gui2 load and show "Database loaded."?
      2. Which tabs show? (expected: Pass1Auto, Pass1Add, Bold Search, DB)
      3. Add one test word in Pass1Add and save. Did the save succeed?
      4. How does the speed feel: fast, usable, or too slow?
- [ ] 2.10 **WHO: AGENT.** Check the save and measure memory:
      ```
      ls -l ~/contrib_data/
      ps -eo pid,rss,cmd | grep "[g]ui2/main.py"
      ```
      **EXPECT:** `additions_alice.json` exists. Write the RSS (KB) of the
      `python` line, the largest number, into `results.md`. Do not edit or
      delete the test entry. The maintainer handles it at wrap-up.
- [ ] 2.11 **WHO: AGENT.** Ask the maintainer: "Leave alice running, or stop
      it?" If stop: `~/stop_gui2.sh alice`. EXPECT `NO_GUI2_RUNNING`. Write the
      state in `results.md`.

## Phase 3 — Live checks of the finished sibling threads

- [ ] 3.1 **WHO: AGENT.** Check that the maintainer's latest work is on GitHub:
      ```
      cd ~/dpd-db && git pull --ff-only
      cd ~/dpd-db && git merge-base --is-ancestor 5497d80c HEAD && echo READY || echo NOT_READY
      ```
      **EXPECT:** `READY`. If `NOT_READY`: tell the maintainer "push main to
      GitHub, then tell me". Wait. Run both lines again. This wait is normal.
      If `git pull` prints an error: STOP.
- [ ] 3.2 **WHO: AGENT.** Update and restart:
      ```
      ~/stop_gui2.sh alice
      cd ~/dpd-db && git submodule update --init resources/sc-data resources/dpd_submodules
      cd ~/dpd-db && ~/.local/bin/uv sync --all-groups
      cd ~/dpd-db && git log -1 --oneline
      ~/start_gui2.sh alice 8551
      ```
      Wait 60 seconds. Run the CHECK of task 2.8 again. Write the
      `git log` line in `results.md`.
- [ ] 3.3 **WHO: AGENT.** Count the db rows before the checks:
      ```
      cd ~/dpd-db && ~/.local/bin/uv run python -c "import sqlite3; print(sqlite3.connect('file:dpd.db?mode=ro', uri=True).execute('select count(*) from dpd_headwords').fetchone()[0])"
      ```
      Write the number in `results.md` as "count before".
- [ ] 3.4 **WHO: MAINTAINER, browser** (tunnel from 2.9 open; ask him to
      reload the page). The AGENT asks one item at a time and records the
      answer, word for word:
      1. Only Pass1Auto, Pass1Add, Bold Search and DB show?
      2. Alt shortcuts to other tabs do nothing?
      3. In DB, "Save Changes" refuses?
      4. In Pass1Add, the preview opens (new tab, or the "Open preview" button)?
      5. Save says it saved?
      6. After a page reload, his own new word shows?
      7. Adding a spelling word and pressing Sandhi OK both work?
      8. Opening a second browser tab on the same address is refused?
      9. Any error message or red screen at any point? (copy the text)
- [ ] 3.5 **WHO: AGENT.** Check the server side of the checklist:
      ```
      ls -l ~/contrib_data/
      cd ~/dpd-db && ~/.local/bin/uv run python -c "import sqlite3; print(sqlite3.connect('file:dpd.db?mode=ro', uri=True).execute('select count(*) from dpd_headwords').fetchone()[0])"
      cd ~/dpd-db && git status --porcelain --untracked-files=no
      ```
      **EXPECT:** new or changed `*_alice*` files in `~/contrib_data/`. The
      count equals "count before". `git status` prints nothing. Record all
      three. A mismatch is a finding: record it and go on to 3.6.
- [ ] 3.6 **WHO: AGENT.** Memory. Run
      `ps -eo pid,rss,cmd | grep "[g]ui2/main.py"` now. Run it again after one
      hour with the page open and idle. Record both RSS numbers.

## Phase 4 — OPTIONAL public access (only if task 1.2 says `sudo: yes`)

The AGENT asks the maintainer first: "Run Phase 4?" If he says no, write
"Phase 4 skipped by maintainer" and go to Phase 5. Phase 4 changes system
files, so the maintainer watches every step. On ANY error: STOP.

- [ ] 4.1 **WHO: AGENT, with sudo, maintainer watching.** Read
      `~/dpd-db/scripts/server_contrib/README.md`,
      `nginx_contrib.conf.template` and `add_contributor.sh` in the same
      folder. Write in `results.md` the exact commands they need, with server
      name `<ip-with-dashes>.sslip.io` (for 1.2.3.4: `1-2-3-4.sslip.io`).
      Show the list to the maintainer. Run nothing until he says yes.
- [ ] 4.2 **WHO: AGENT, with sudo, after the yes.** Run the approved commands
      one at a time. The maintainer types the contributor password himself.
      Open only ports 80 and 443.
      **CHECK:** `sudo nginx -t` prints `syntax is ok` and `test is successful`.
- [ ] 4.3 **WHO: MAINTAINER, browser.** Open
      `https://<ip-with-dashes>.sslip.io/alice/`. The AGENT asks, one at a
      time, and records: asks for a password? rejects a wrong one? loads
      gui2 with the right one? stays connected for 5 minutes? preview opens
      under `/alice/preview/...`?
      If gui2 does not work behind `/alice/`, record exactly what fails. This
      answer decides contrib_1 Phase 3. If certbot fails, record its error and
      skip to Phase 5.

## Phase 5 — Wrap-up before access ends

- [ ] 5.1 **WHO: AGENT.** Stop every instance and check:
      ```
      ~/stop_gui2.sh alice
      ~/stop_gui2.sh bob || true
      ps -eo pid,cmd | grep "[g]ui2/main.py" || echo NO_GUI2_RUNNING
      ```
      **EXPECT:** `NO_GUI2_RUNNING`.
- [ ] 5.2 **WHO: MAINTAINER, own machine.** Copy the work and the results back
      into a new local folder, so nothing local is overwritten:
      `mkdir -p /home/bodhirasa/MyFiles/3_Active/dpd-db/kamma/threads/20261023_contrib_4_temp_server_test/artifacts/server_data`
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && rsync --bwlimit=400 -r <user>@<ip>:~/contrib_data/ <user>@<ip>:~/logs <user>@<ip>:~/dpd-contrib/handoff/20261023_contrib_4_temp_server_test/results.md kamma/threads/20261023_contrib_4_temp_server_test/artifacts/server_data/`
      Then check that `additions_alice.json` and `results.md` are there.
- [ ] 5.3 **WHO: AGENT, only after the maintainer says "copy done".** If
      Phase 4 ran: undo it with `sudo`, using the list from 4.1 in reverse
      (remove the nginx site, the htpasswd file, the certbot certificate,
      close ports 80 and 443). Show the list to the maintainer first.
- [ ] 5.4 **WHO: AGENT, only after "copy done".** Remove what this plan
      installed. Ask the maintainer to confirm each line before you run it:
      ```
      rm -rf ~/dpd-db ~/contrib_data ~/logs ~/start_gui2.sh ~/stop_gui2.sh
      ~/.local/bin/uv cache clean
      rm -rf ~/.local/share/uv ~/.local/bin/uv ~/.local/bin/uvx
      ```
      **EXPECT:** `ls ~` no longer shows `dpd-db`, `contrib_data` or `logs`.
- [ ] 5.5 **WHO: MAINTAINER.** Log out and remove the server agent and its
      config, then remove `~/dpd-contrib/handoff`. Write a short summary of the findings
      (RAM, latency, breakages, the prefix answer) into the local thread for
      contrib_1 Phase 3.
