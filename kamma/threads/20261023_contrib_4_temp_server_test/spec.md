# Spec: test gui2 on a borrowed server — no domain, a few weeks of access

**Thread:** 20261023_contrib_4_temp_server_test
**Date:** 2026-10-07 · **Rewritten:** 2026-10-31 for a server agent that is a smaller model
**GitHub issue:** [#215 — Contributor Onboarding](https://github.com/digitalpalidictionary/dpd-db/issues/215)
**Builds on:** `contrib_1_web_server` Phases 1–2, `contrib_2_edits_json`,
`contrib_5_hardening`, `contrib_3_preview_before_save` (all committed).

## Who does what

There are two actors. Every step in `plan.md` names one of them.

- **MAINTAINER** — the human. Works on his own machine and in his browser.
  He gives the host details, types every secret, opens the tunnelled page and
  clicks through the checks.
- **SERVER AGENT** — a coding agent on the server. It is a smaller model (for
  example GLM flash), NOT Claude. It has no access to the maintainer's machine
  and no access to the maintainer's global rules. It follows `plan.md` word for
  word, one task at a time, and writes every result to `results.md`.

## Overview

The maintainer has SSH access to a borrowed server for a few weeks, with no
domain name. Use it to prove gui2 web mode on a real remote host before paying
for the permanent VPS (contrib_1 Phase 3).

1. Survey the server, install what is needed in the user's home, and run
   gui2 over an SSH tunnel.
2. Run the contributor checks of the finished sibling threads over the tunnel.
3. Optional, only with sudo: public access through nginx on a free hostname.
4. Copy all contributor work back and leave the server clean.

## Decisions (2026-10-07, updated 2026-10-31)

- **SSH tunnel, not a domain.** gui2 listens on 127.0.0.1 only. The
  maintainer runs `ssh -N -L 8551:127.0.0.1:8551 <user>@<ip>` and opens
  `http://localhost:8551`.
- **The bind address is set explicitly** with `FLET_SERVER_IP=127.0.0.1`.
  Flet reads this variable (`flet/app.py`, `env_host = os.getenv("FLET_SERVER_IP")`).
  Without it the bind address is unverified.
- **gui2 runs in the background, not in a terminal multiplexer.** The
  maintainer uses herdr locally, and there is no tmux. `~/start_gui2.sh` starts
  gui2 with `setsid nohup`, so it survives the SSH session ending.
  `~/stop_gui2.sh` stops it. Both texts are in `plan.md` task 2.4. The agent
  never types the long env-var line by hand.
- **The thread folder lives OUTSIDE the clone**, at
  `~/handoff/20261023_contrib_4_temp_server_test/`. Inside the clone it would
  make tracked files dirty, and `git pull` would then refuse.
- **The agent writes results only to `results.md`** in that folder. It never
  edits `spec.md` or `plan.md`.
- **One shared data folder**, `~/contrib_data`, the same shape as production
  (`scripts/server_contrib/README.md`: file names carry the user).
- **The db is copied after a WAL checkpoint.** `dpd.db` runs in WAL mode, so
  recent writes sit in `dpd.db-wal`. Copying `dpd.db` alone can miss them.
  The copy is checked by sha256 on both sides.
- **The borrowed server stays clean:** nothing system-wide without sudo,
  nothing left running at the end, all contributor files copied back.

## Facts (verified 2026-10-31 unless dated)

- Python: `requires-python = ">=3.13,<3.14"` (`pyproject.toml`). uv downloads
  a matching Python itself. No system Python is needed.
- Required submodules: `resources/sc-data`, `resources/dpd_submodules`
  (`scripts/onboarding/contributor_setup.py::REQUIRED_SUBMODULES`). Both are
  public on GitHub. Every other submodule is skipped.
- `dpd.db` is about 2.26 GB. At 400 KB/s the copy takes about 1.5 h.
- Env vars read by gui2: `DPD_GUI2_USERNAME`, `DPD_GUI2_ROLE`,
  `DPD_GUI2_TABS` (`gui2/contributor_tabs.py`), `DPD_GUI2_DATA_DIR`
  (`gui2/paths.py`). Flet reads `FLET_FORCE_WEB_SERVER`, `FLET_SERVER_IP`,
  `FLET_SERVER_PORT`.
- Do not use `flet run`. It starts the app in `gui2/.flet/storage/data` and
  every data path breaks.
- Server config template: `scripts/server_contrib/config_server.template`.
  It has two API key lines under `[apis]`. Only the maintainer fills them.
- Go is needed only for the nightly rebuild (`config_server.md`). This test
  runs no rebuild, so Go is not installed.
- `pyperclip` is imported by gui2. On a server without a clipboard tool, a
  copy button may raise an error. Record it if seen. Do not install anything.
- Commit `5497d80c` (contrib_3) was on the maintainer's local `main` only on
  2026-10-30. Phase 3 checks for it on the server before it starts.
- One gui2 web session ≈ 2.0–2.5 GB RSS (measured 2026-07-19, local machine).

## What it should do

1. Survey OS, free RAM, CPU, disk, sudo, and outbound access. Decide 0, 1 or 2
   instances from the RAM rule in `plan.md`.
2. Install uv, clone the repo with the two submodules, `uv sync --all-groups`,
   receive `dpd.db`, and get `config.ini` from the template.
3. Run gui2 in the background through `~/start_gui2.sh`, on 127.0.0.1 only.
4. Smoke test over the tunnel. Record RSS and felt latency.
5. After commit `5497d80c` is on GitHub: pull, sync, restart, and run the
   contributor checklist.
6. Optional (sudo only): nginx + sslip.io + certbot + basic auth.
7. Wrap-up: copy `~/contrib_data` and `results.md` back, stop every process,
   remove what was installed.

## Assumptions & uncertainties

- Server specs, OS, sudo and outbound access are unknown until the survey.
- sslip.io + Let's Encrypt is unverified. Certbot rate limits may block it.
  Then Phase 4 is skipped and the reason recorded.
- Flet over a real network (reconnect after sleep, slow links) is untested.
  Record what is seen. Fixes are out of scope.
- gui2 may need a gitignored file that a fresh clone lacks. If it crashes at
  start, the agent records the traceback and stops. It does not create files.
- The disk need (≥ 10 GB free) is an estimate: db 2.3 GB, plus submodules,
  plus the venv.

## Constraints

- Secrets (API keys, passwords) are typed by the maintainer only. The agent
  never prints, reads, greps or edits `config.ini`, `.env` or htpasswd files.
- Every transfer from the maintainer's machine uses `--bwlimit=400` (rsync) or
  `-l 3200` (scp, Kbit/s). Total of concurrent transfers ≤ 400 KB/s.
- Stop processes with `~/stop_gui2.sh` or by PID, then re-list. Never
  `pkill -f` or `killall`.
- On the server clone: only `git clone`, `git submodule update`, `git pull`,
  `git log`, `git status`, `git merge-base`. Never commit, push, stash, reset,
  checkout or restore.
- The agent never edits code or tracked files in `~/dpd-db`.
- Every command for the maintainer names its machine and directory.

## How we'll know it's done

1. `results.md` has the survey table and the instance decision.
2. gui2 loads over the tunnel, and a save by "alice" writes
   `~/contrib_data/additions_alice.json` on the server.
3. Every item of the Phase 3 checklist is logged with its observed result.
4. RSS after load and after one hour idle are recorded.
5. Wrap-up: files copied back, no gui2 process on the server, installs removed.

## What's not included

- systemd units, nightly sync, the maintenance window, the `contributions`
  branch (contrib_1 Phase 3).
- A permanent VPS or a real domain.
- Fixing anything found. Findings are recorded and become new work.
