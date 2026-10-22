# Spec: test gui2 on a borrowed server — no domain, a few weeks of access

**Thread:** 20261007_contrib_temp_server_test
**Date:** 2026-10-07
**GitHub issue:** [#215 — Contributor Onboarding](https://github.com/digitalpalidictionary/dpd-db/issues/215)
**Builds on:** `kamma/threads/20260719_contributor_web_server/` (its Phase 1–2
work is committed: per-user files, env-var username/role, server-mode gating,
`scripts/server_contrib/`).
**Waits on (for Phase 3 only):** `20261007_contrib_edits_json` and
`20261007_contrib_preview_before_save`. Phases 1–2 can start now.

## Overview

The maintainer has SSH access to a server for the next few weeks, with no
domain name and no website. Use it to prove gui2 web mode on a real remote
host before paying for the permanent VPS planned in 20260719 Phase 3.

The test runs in two steps:
1. Now: survey the server, set it up, and run the CURRENT main code over an
   SSH tunnel. This proves the 20260719 work remotely.
2. Later, after the two sibling threads are finished, committed and pushed by
   the maintainer: pull, restart, and run their live checks on the server.

## Decisions made (2026-10-07)

- **SSH tunnel, not a domain.** gui2 listens on 127.0.0.1 on the server only.
  The maintainer reaches it with `ssh -N -L 8551:127.0.0.1:8551 <user>@<ip>`
  and opens `http://localhost:8551`. No domain, TLS, password page or open
  port is needed.
- **Optional public access, only if sudo is available:** nginx on the bare IP
  with a free IP hostname (`<ip-with-dashes>.sslip.io` resolves to the IP),
  certbot TLS, basic auth and a path prefix `/alice/`. This tests the preview
  URL and websockets behind a prefix, and lets one remote contributor try it.
- **Claude Code runs on the server too**, installed in the user's home, for
  troubleshooting the setup there (install, uv sync, db copy, first start).
  The maintainer logs in himself. The thread folder is copied over, because it
  is not on GitHub until committed. Normal permission mode, not bypass. The
  maintainer's global `~/.claude/CLAUDE.md` is NOT on the server. The project
  `CLAUDE.md` comes with the clone.
- **The server is borrowed:** install nothing system-wide without sudo, leave
  nothing running at the end, and copy all contributor work back before access
  ends.

## Facts (verified 2026-10-07)

- `uv run flet run --help` shows `-p PORT`, `--host HOST`, `-w` (web) and
  `-a ASSETS_DIR`.
- `dpd.db` is 2,262,204,416 bytes locally.
- Required submodules: `resources/sc-data`, `resources/dpd_submodules`
  (`scripts/onboarding/contributor_setup.py::REQUIRED_SUBMODULES`).
  `resources/dpd_audio` and others are skipped.
- Server config template: `scripts/server_contrib/config_server.template`
  (notes in `config_server.md`). It needs the maintainer's AI keys. The
  generated `config.ini` is never committed.
- One gui2 web session ≈ 2.0–2.5 GB RSS; idle server ≈ 330 MB (measured
  2026-07-19 on the maintainer's machine).
- Env vars per instance: `DPD_GUI2_USERNAME`, `DPD_GUI2_ROLE=contributor-server`
  (`gui2/user.py`, `tools/server_mode.py`). In this role the local webapp
  helper, GoldenDict and the Ask AI window are off.

## What it should do

1. Survey: OS, RAM, CPU, disk, sudo or not, outbound GitHub access. Run 2
   instances (alice, bob) only if free RAM ≥ 6 GB, otherwise 1.
2. Setup in the user's home: clone the public repo with the two submodules,
   install uv, `uv sync --all-groups`, copy `dpd.db` up with
   `rsync --bwlimit=400` (about 1.5 h), and write `config.ini` from the
   template on the server.
3. Run each instance in `tmux` (or `nohup`), bound to localhost:
   `DPD_GUI2_USERNAME=alice DPD_GUI2_ROLE=contributor-server uv run flet run --web --host 127.0.0.1 -p 8551 gui2/main.py`.
4. Reach it by SSH tunnel and run a smoke test of the current code. Record
   RSS per session and the latency felt from the maintainer's location.
5. After the sibling threads land on main: `git pull`, `uv sync --all-groups`,
   restart, and run their live contributor checks over the tunnel.
6. Optional (sudo only): the nginx + sslip.io setup above.
7. Before access ends: copy `gui2/data/additions_*.json`, `corrections_*.json`
   and `user_dictionary_*.txt` back, then stop every process. Log Claude Code
   out on the server (`/logout`) and remove its install and `~/.claude`.

## Assumptions & uncertainties

- Server specs, OS, sudo and GitHub access are unknown until the survey.
- sslip.io + Let's Encrypt is unverified. Certbot rate limits on shared
  sslip.io names may block issue; if so, skip the optional step.
- Flet web behaviour over a real network (reconnect after sleep, slow links)
  is untested. Record what is seen. Fixes are out of scope.
- Whether `git pull` on the server can reach the new code depends on the
  maintainer committing and pushing threads 1 and 2. Phase 3 waits for that.
- If the server has under ~3 GB free RAM, even one instance may swap. Then
  record it and stop. This is a finding, not a failure.

## Constraints

- Never commit or copy secrets into the repo (API keys, htpasswd).
- Use `--limit-rate` / `--bwlimit` on every transfer (project rule: the total
  of concurrent transfers ≤ 400 KB/s).
- Kill processes by PID and re-list to confirm, never with `pkill -f`.
- No git commands on the maintainer's local repo. `git clone` / `git pull` on
  the server clone are part of this thread's setup.
- Every command handed to the user names its machine and directory.

## How we'll know it's done

1. A survey table and the 1-or-2-instance decision are recorded in the plan.
2. gui2 loads over the tunnel from the maintainer's machine, and a smoke-test
   save by "alice" writes `additions_alice.json` on the server.
3. After the sibling threads land: their contributor checks pass on the
   server over the tunnel (save → JSON only, db row unchanged, own edits
   shown, preview opens on the maintainer's machine).
4. RSS per session recorded.
5. Wrap-up done: files copied back, no gui2 process left on the server.

## What's not included

- systemd units, nightly sync, the maintenance window, the `contributions`
  branch (20260719 Phase 3).
- A permanent VPS or a real domain.
- Fixing anything found. Findings are recorded and become new work.
