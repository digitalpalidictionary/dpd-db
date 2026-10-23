# Plan: test gui2 on a borrowed server — no domain, a few weeks of access

**Thread:** 20261023_contrib_4_temp_server_test · **Spec:** `spec.md` (read first)
**GitHub issue:** #215
**Phases 1–2 start now. Phase 3 waits** until `20261023_contrib_2_edits_json`
and `20261023_contrib_3_preview_before_save` are finished, committed and pushed by the
maintainer. Waiting there is normal, not a failure.

## Architecture Decisions
- **SSH tunnel** for access: no domain, no TLS, no open port. gui2 binds to
  127.0.0.1 on the server.
- **Everything in the user's home** on the server. No system-wide install
  without sudo.
- **tmux / nohup, not systemd**: this is a few-week test, and systemd units
  belong to 20260719 Phase 3.
- **Optional nginx + sslip.io** only if sudo exists. It is the one way to test
  a path prefix and a remote contributor without buying a domain.

## Phase 1 — Survey
- [ ] 1.1 Get the host, user and SSH details from the maintainer. Over SSH run
      `uname -a`, `cat /etc/os-release`, `free -h`, `nproc`, `df -h ~`,
      `sudo -n true && echo sudo`, `git ls-remote https://github.com/digitalpalidictionary/dpd-db HEAD`,
      and `command -v tmux go sqlite3`.
      → verify: a table here with every value. Decide 1 or 2 instances
      (free RAM ≥ 6 GB → 2). Note sudo yes/no for Phase 4.
- [ ] 1.2 Claude Code on the server, for troubleshooting the setup from there.
      Install it into the home dir with the official native installer (take the
      current command from the Claude Code docs; it needs no sudo), then run
      `claude --version`. The maintainer runs `claude` once inside a `tmux`
      session and logs in himself. It prints a login URL to open in his local
      browser. Copy this thread's folder over, because it is not on GitHub
      until committed:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && rsync --bwlimit=400 -r kamma/threads/20261023_contrib_4_temp_server_test <user>@<ip>:~/handoff/`.
      After 2.1 it moves to `~/dpd-db/kamma/threads/`. Start the server Claude
      in `~/dpd-db` so it reads the project `CLAUDE.md`. Its first prompt points
      at this spec and plan. Use the normal permission mode, not bypass,
      because the server is borrowed.
      → verify: `claude --version` prints a version. In the server session, the
      server Claude reads `~/handoff/20261023_contrib_4_temp_server_test/plan.md` and
      names the next open task. Record which tasks it then ran.

## Phase 2 — Setup and smoke test of the current code
- [ ] 2.1 On the server, in `~`:
      `git clone https://github.com/digitalpalidictionary/dpd-db`, then
      `git submodule update --init resources/sc-data resources/dpd_submodules`.
      Install uv into the home dir (the official installer), then
      `cd ~/dpd-db && uv sync --all-groups`.
      → verify: `cd ~/dpd-db && uv run python -c "import flet, sqlalchemy"` exits 0.
- [ ] 2.2 From the maintainer's machine:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && rsync --bwlimit=400 --partial --progress dpd.db <user>@<ip>:~/dpd-db/`.
      Write `~/dpd-db/config.ini` from `scripts/server_contrib/config_server.template`
      on the server, adding the AI keys over SSH. Never commit it, never paste
      keys into chat.
      → verify: `sqlite3 ~/dpd-db/dpd.db "select count(*) from dpd_headwords"`
      on the server equals the same query locally.
- [ ] 2.3 Start alice in tmux:
      `cd ~/dpd-db && DPD_GUI2_USERNAME=alice DPD_GUI2_ROLE=contributor-server uv run flet run --web --host 127.0.0.1 -p 8551 gui2/main.py`
      (and bob on 8552 if 1.1 allowed 2). From the maintainer's machine:
      `ssh -N -L 8551:127.0.0.1:8551 <user>@<ip>` and open `http://localhost:8551`.
      → verify: gui2 loads and "Database loaded." appears. A Pass1Add save as
      alice writes `~/dpd-db/gui2/data/additions_alice.json`. Record the RSS
      (`ps -o pid,rss,cmd -p <pid>`) after the db load, and the felt latency.
      Remove the test entry after.
- [ ] 2.4 Leave the instance running or stop it (by PID, then re-list) as the
      maintainer prefers while Phase 3 waits.
      → verify: the state is recorded here.

## Phase 3 — Live checks of the sibling threads (WAIT until both are on main)
- [ ] 3.1 On the server: stop the instances by PID, then
      `cd ~/dpd-db && git pull && uv sync --all-groups`, and restart as in 2.3.
      → verify: `git log -1 --oneline` on the server shows the maintainer's
      latest commit.
- [ ] 3.2 Over the tunnel, run the contributor checklist from
      `20261023_contrib_2_edits_json` plan 3.1 and `20261023_contrib_3_preview_before_save`
      plan 2.2: preview opens in the maintainer's browser (or via the link) →
      Save writes JSON only → the server db row is unchanged (sqlite count) →
      own edit shown on reload → Pass2 re-edit of own new word → Delete
      discards own entry only → spelling add goes to the per-user file. Remove
      the test entries after.
      → verify: every item logged here with the observed result.

## Phase 4 — OPTIONAL public access (only if 1.1 shows sudo)
- [ ] 4.1 nginx with server name `<ip-with-dashes>.sslip.io`, certbot TLS, basic
      auth for alice, location `/alice/` proxying to 127.0.0.1:8551 with
      websocket headers (`proxy_http_version 1.1`, Upgrade / Connection), as in
      the 20260719 spec point 3. Open ports 80/443 only for this.
      → verify: `https://<ip-with-dashes>.sslip.io/alice/` loads gui2 after the
      password, and the preview opens under `/alice/preview/...`. If skipped or
      certbot fails, record why here.

## Phase 5 — Wrap-up before access ends
- [ ] 5.1 From the maintainer's machine:
      `cd /home/bodhirasa/MyFiles/3_Active/dpd-db && rsync --bwlimit=400 '<user>@<ip>:~/dpd-db/gui2/data/{additions,corrections}_*.json' '<user>@<ip>:~/dpd-db/gui2/data/user_dictionary_*.txt' <scratchpad>/server_data/`
      (into a scratch folder, so nothing overwrites local files). Stop every
      gui2 process on the server by PID. Remove any nginx site and htpasswd
      added in Phase 4. In the server Claude run `/logout`, then remove its
      install and `~/.claude`.
      → verify: the files exist locally, `ps -ef | grep [f]let` on the server is
      empty, `command -v claude` on the server finds nothing, and the findings (RAM, latency, breakages) are summarised here for
      20260719 Phase 3.
