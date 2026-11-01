# Spec: contributor server, full end-to-end test from a fresh clone

**Thread:** 20261101_contrib_6_e2e_server_test
**Date:** 2026-11-01
**GitHub issue:** [#215 — Contributor Onboarding](https://github.com/digitalpalidictionary/dpd-db/issues/215). Never write to the issue.
**Builds on:** `kamma/threads/20261023_contrib_4_temp_server_test/` (read its `results.md`; it is the full log of the previous run on the same server).
**Feeds:** `kamma/threads/20261023_contrib_1_web_server/` Phase 3 and task 4.1 (the production server). This thread is the rehearsal of those steps on the borrowed server.

## Overview

The previous test (contrib_4) proved that gui2 runs on the borrowed server, over an
SSH tunnel and behind nginx with basic auth. It did not build anything on the
server: the maintainer copied `dpd.db` (3.6 hours over his link) and then copied
generated files one by one as each one crashed gui2. It never ran the nightly
maintenance window, never pushed the contributor files to GitHub, and never closed
the loop with the maintainer.

This thread runs the whole loop once, for real:

1. Build the server from a fresh clone, using only GitHub and commands that run on
   the server. No file is copied from the maintainer's laptop except `config.ini`.
2. A contributor (alice, played by the maintainer) adds real words and flags in the
   web gui2.
3. The maintenance window pushes alice's files to the `contributions` branch.
4. The maintainer merges that branch locally, processes the words in desktop gui2,
   commits and pushes `main`.
5. The next window drops what the maintainer processed, rebuilds the db from the new
   `main`, and the words are now real headwords in the server db.

Along the way it fixes the defects found while planning (section "What it should do",
part A), and it leaves behind one setup script so the next server build is one
command (the maintainer's request after contrib_4).

The maintainer's words after contrib_4 (2026-11-01):
1. "we need to not copy the db and build from scratch with init build once script."
2. "we need to have all the pass1auto files on the server, they were missing this time."
3. "the whole thing needs to be build seamlessly into a script or set of commands so it happens almost instantly the next time."

## Who does what

- **Maintainer (owner):** types every secret, runs every `sudo` step that touches
  nginx, GitHub settings or the deploy key, plays alice in the browser, and does the
  whole local half (merge, process, commit, push). Only he commits and pushes `main`.
- **Server agent:** a smaller model on the server, same rules as contrib_4 (plan
  "READ THIS FIRST"). It runs the `AGENT` steps and writes `results.md`.
- **Local agent (Claude, in the maintainer's repo):** writes the Phase 1 code fixes,
  and helps with the local half.

## Facts verified while planning (2026-11-01)

Read from the repo or the server, not assumed:

- **Server.** Ubuntu 24.04, 2 CPUs, 8 GB RAM, no swap, about 80 GB free, root login,
  sudo works. SSH alias on the maintainer's machine: `epitaka`
  (`root@187.126.118.33`). The box also hosts an unrelated project,
  `~/epitaka-translator`, which this thread must not touch. Go is not installed.
- **Left over from contrib_4 (kept on purpose):** the old clone `~/dpd-db` (with the
  copied db and a filled `config.ini`), `~/contrib_data/` (alice's test entries
  `testa 1` / `testa 2`), `~/start_gui2.sh` and `~/stop_gui2.sh`, nginx 1.24 with the
  site `dpd-contrib`, the Let's Encrypt certificate for `187-126-118-33.sslip.io`
  (expires 2027-01-29), `/etc/nginx/dpd/alice.conf`, `alice.htpasswd` (group
  `www-data`), the alice-only root asset shim `/etc/nginx/dpd/zz_root_asset_shim.conf`,
  `/etc/dpd/alice.env`, and the empty `/var/lib/dpd/contrib_data/`. No gui2 process
  runs. uv 0.13.6 is in `~/.local/bin`. `pkg-config` and `libicu-dev` are installed.
- **`/etc/dpd/alice.env`** was written by `add_contributor.sh`. It sets
  `DPD_GUI2_DATA_DIR=/var/lib/dpd/contrib_data`, port 8551 and the tabs
  "Bold Search,DB". It does **not** set `FLET_SERVER_IP`
  (`scripts/server_contrib/add_contributor.sh`, the `cat > "$env_file"` block).
  contrib_4 bound gui2 to 127.0.0.1 only because `~/start_gui2.sh` set it.
- **No systemd unit exists.** `add_contributor.sh` tells the operator to run
  `systemctl enable --now dpd-gui@<user>`, and `maintenance_window.py` stops and
  starts `--instance` units with `systemctl`, but no `dpd-gui@.service` file exists
  anywhere in the repo. With `--no-systemd` the window only logs "would stop", so a
  running gui2 keeps the db open while the rebuild deletes and recreates it.
- **Bold Search goes empty after a nightly rebuild.**
  `scripts/build/db_rebuild_from_tsv.py` deletes `dpd.db` and recreates it. The
  window then runs `scripts/server_contrib/generate_components_server.py`, which does
  not run `db/bold_definitions/update_bold_definitions_db.py`. Every other pipeline
  that rebuilds the db runs it (`scripts/bash/initial_build_db.py`,
  `.github/workflows/draft_release.yml`, `mobile_release.yml`). The Bold Search tab,
  one of alice's tabs, queries the `bold_definitions` table of `dpd.db`
  (`tools/bold_definitions_search.py`). The step reads
  `db/bold_definitions/bold_definitions.tsv`, which is untracked and made by
  `extract_bold_definitions.py` in the initial setup.
- **The window's submodule step fetches everything.** `_default_pull` and
  `_restore_rollback` in `maintenance_window.py` run
  `git submodule update --init --recursive` with no paths. The repo has 11
  submodules (`.gitmodules`), several of them large (`other-dictionaries`,
  `tpr_downloads`, `dpd_audio`, `tipitaka_translation_db`). Without `--init`, git
  updates only the submodules already initialised.
- **The server needs THREE submodules, not two.** `resources/sc-data` (1.0 GB) and
  `resources/dpd_submodules` (1.1 GB, holds CST and BJT), plus
  `resources/tipitaka.rte` (142 MB): the frequency setup reads the SYA corpus from it
  (`go_modules/tools/pth.go:107`), and the deconstructor reads the CST, BJT, SC and SYA
  word lists the frequency setup writes (`go_modules/deconstructor/importer/unmatched.go`).
  contrib_4 never hit this because the maintainer copied the finished frequency files.
  `scripts/onboarding/contributor_setup.py` lists only two (`REQUIRED_SUBMODULES`).
- **The initial setup** (`scripts/bash/initial_setup_run_once.py`) runs
  `tools/configger.py`, `cst4_xml_to_txt.py` (writes the CST text files Pass1Auto
  reads, `resources/dpd_submodules/cst/romn_txt/`), `transliterate_bjt.py`,
  `go run ./go_modules/frequency/setup` (writes `shared_data/frequency/*.json`, which
  gui2's wordfinder reads at start) and `extract_bold_definitions.py`.
  `tools/configger.py` as a script runs `config_initialize()`, which only adds
  options that are missing; it never overwrites a value (`tools/configger.py:213`).
- **`scripts/bash/initial_build_db.py` cannot run on the server:** it runs the full
  `generate_components.py`, which includes pytest and audio/anki steps that fail on a
  headless server (`scripts/server_contrib/config_server.md`).
- **The maintenance window can do the first build.** With no
  `logs/last_built_commit` file it always rebuilds: `db_rebuild_from_tsv` → lean
  generate → health check (≥ 50 000 headwords, ≥ 400 000 lookup rows) → WAL → put
  back the tracked files the build rewrote (`db/sanskrit/root_families_sanskrit.tsv`
  every run) → write `logs/last_built_commit`. A failed step rolls back. Each step has
  a one-hour timeout (`STEP_TIMEOUT = 3600`). Child output is not captured into the
  window's log; it goes to the terminal. `main()` prints the outcome and always exits 0.
  A push failure is logged and the window goes on.
- **Preview needs** `audio/db/dpd_audio_index.tsv` (gitignored). It is downloaded by
  `audio/index_release_download.py` from the public `dpd-audio` GitHub release; a
  token is optional (`tools/github_api.py`).
- **GitHub:** `main` has no branch protection and no rulesets. No `contributions`
  branch exists. The server clone's remote is https with no push credentials.
- **Go:** `go.mod` says `go 1.22.2` and has no `toolchain` line. Ubuntu 24.04's apt
  `golang-go` is expected to be 1.22.2 (not yet checked on the server). The
  deconstructor runs as `go run go_modules/deconstructor/main.go`, the same form the
  release workflows use.
- **Local side:** `just contrib-merge` fetches `origin/contributions`, merges it into
  local `main`, and runs `scripts/server_contrib/merge_contrib_files.py`, which folds
  alice's flag files into `shared_data/user_dictionary.txt`,
  `shared_data/deconstructor/checked.csv`, `manual_corrections.tsv`,
  `variant_readings.tsv` and the spelling file, and logs each line in
  `gui2/data/contrib_lines_merged.json`. Words are processed in desktop gui2:
  Pass2Add tab → the **Add** button (tooltip "additions") loads the next contributor
  addition; saving it logs it in `gui2/data/additions_added.json` and removes it from
  `gui2/data/additions_alice.json`. **Backup & Quit** (global tab) writes the TSV
  backup in `db/backup_tsv/`; it does not commit. The server rebuild reads those TSVs.
  The server's reconcile drops an entry only when `main` holds its `(key, hash)` in
  `additions_added.json` / `corrections_added.json`, or the line in
  `contrib_lines_merged.json`.
- **Local working tree today** has uncommitted changes from other threads in
  `shared_data/deconstructor/checked.csv` and `variant_readings.tsv` — two of the
  files the merge script writes.

## What it should do

### A. Code fixes, done locally first (small, each one found while planning)

1. **Bold definitions after every rebuild.** Add
   `db/bold_definitions/update_bold_definitions_db.py` to `COMMANDS` in
   `scripts/server_contrib/generate_components_server.py`, and list it as KEPT in
   `scripts/server_contrib/config_server.md`. It needs
   `db/bold_definitions/bold_definitions.tsv`, made once by the initial setup.
   Place it directly after `tools/version.py`, so it runs first after the db is
   recreated — the same place `initial_build_db.py` runs it (between the rebuild and
   the components). Known limit, on purpose: the TSV is made once from the CST
   submodule, so it goes stale if CST changes; re-run the initial setup then.
   Tests: add it to `ESSENTIAL` in
   `tests/scripts/server_contrib/test_generate_components_server.py`.
2. **Window updates only the submodules it has.** In `maintenance_window.py`, change
   both `git submodule update --init --recursive` calls (`_default_pull` and
   `_restore_rollback`) to `git submodule update --recursive` (no `--init`). No test
   pins this command today; add one that records the commands `_default_pull` runs
   and asserts no `--init`. Consequence, written into the README: if `main` ever
   needs a new submodule, the server operator inits it once by hand.
3. **Window exit code.** `maintenance_window.py` `main()` exits 1 when the outcome is
   `failed`, so a script or a person can see it without reading the log. New test.
   A push failure still does not fail the window (by design, contrib_5); it is caught
   by reading the log (`contrib_push FAILED`) and by checking the branch on GitHub.
4. **Bind address in the env file.** `add_contributor.sh` writes
   `FLET_SERVER_IP=127.0.0.1` into the env file, next to `FLET_SERVER_PORT`. The unit
   does not set it, so there is one source. Extend
   `tests/scripts/server_contrib/test_add_contributor.py` to assert the line.
5. **systemd unit template.** New file `scripts/server_contrib/dpd-gui@.service`.
   The setup script fills the `@...@` placeholders with `sed` and installs it as
   `/etc/systemd/system/dpd-gui@.service`, then runs `systemctl daemon-reload`. Text:
   ```ini
   [Unit]
   Description=DPD gui2 contributor instance for %i
   After=network-online.target
   StartLimitIntervalSec=300
   StartLimitBurst=5

   [Service]
   Type=simple
   User=@USER@
   Environment=HOME=@HOME@
   EnvironmentFile=/etc/dpd/%i.env
   WorkingDirectory=@CLONE@
   ExecStart=@UV@ run --no-sync python gui2/main.py
   Restart=on-failure
   RestartSec=10
   TimeoutStopSec=30

   [Install]
   WantedBy=multi-user.target
   ```
   `--no-sync`: a restart must not re-sync the venv (network, and a race with the
   window's own `uv run`). `StartLimitBurst`: a broken db gives five restarts in five
   minutes, then the unit stays failed and `systemctl status` shows why. The default
   kill mode stops the whole process group (uv and its python child).
6. **Setup script.** New file `scripts/server_contrib/server_setup.sh`. It does not
   list build steps itself; it calls the existing entry points. Usage:
   `server_setup.sh <clone dir>` (default `$HOME/dpd-db`). Each step prints its
   name, start time and duration, and the script stops on the first error
   (`set -euo pipefail`). Re-running it is safe; each step has a probe:

   | Step | Skipped when |
   |---|---|
   | apt install `pkg-config libicu-dev golang-go` | `dpkg -s` finds all three |
   | install uv | `$HOME/.local/bin/uv` exists |
   | clone | `<clone>/.git` exists and `git -C <clone> rev-parse HEAD` works |
   | `git submodule update --init -- resources/sc-data resources/dpd_submodules resources/tipitaka.rte` (full depth) | never skipped (cheap when done) |
   | `uv sync --all-groups` | never skipped (cheap when done) |
   | `config.ini` present | — if missing, print "copy config.ini into <clone>, then run this script again" and exit 1 |
   | `go version` is at least the `go` line of `go.mod` | — if not, print both and exit 1 |
   | `uv run scripts/bash/initial_setup_run_once.py` | `<clone>/logs/initial_setup_done` exists (written after success) |
   | `uv run audio/index_release_download.py` | `audio/db/dpd_audio_index.tsv` exists |
   | `mkdir -p /var/lib/dpd/contrib_data` | — |
   | install the unit (always rewritten) + `systemctl daemon-reload` | never skipped |
   | clean-tree gate: `git status --porcelain --untracked-files=no` must print nothing | — if it prints, show it and exit 1 |
   | first build: `uv run scripts/server_contrib/maintenance_window.py --no-systemd --no-push --data-dir /var/lib/dpd/contrib_data` | `<clone>/logs/last_built_commit` exists |

   Not in the script, on purpose (each is a one-time, per-host or secret step, and
   stays a command in the README and the plan): the swap file, nginx and the
   certificate, `add_contributor.sh` (it asks for a password), the deploy key, and
   `systemctl enable` of an instance.
   A failed first build: the window's rollback has no old db to put back, so a partial
   `dpd.db` may stay on disk. That is safe: no gui2 runs yet, and the re-run rebuilds
   from scratch (`db_rebuild_from_tsv` deletes the db first). If a step hit the
   one-hour timeout, `subprocess.run` killed only `uv`; its children (python, the Go
   build, the deconstructor) may still run. Check with `ps` and stop them before a
   re-run.
7. **Docs.** `scripts/server_contrib/README.md` gets a short "New server" section
   (the setup script and what it leaves out, the three submodules, the deploy key, the
   unit, the no-`--init` consequence). `config_server.md` lists the bold step as KEPT.

### B. The end-to-end run on the borrowed server

The server agent may run, in addition to the contrib_4 rules, exactly these
commands when a task gives them: `mv` of the old clone, `ssh-keygen` for the deploy
key, and the repo-local `git config` / `git remote set-url --push` lines the plan
writes out. All `sudo` steps that touch nginx, systemd units, swap or `/etc` are run
by the agent only when the task says so and the maintainer has said yes.

1. Record the pre-state: `ls -la /etc/nginx/sites-enabled /etc/nginx/dpd`,
   `ls /etc/letsencrypt/live`, `free -m`, `swapon --show`, and the processes of the
   other project (`ps -eo pid,user,etime,cmd` filtered to `epitaka`). The end state is
   compared with it.
2. Move the old clone aside (`~/dpd-db` → `~/dpd-db_contrib4`). Keep it until this
   thread passes. Undo: `mv` back.
3. Add a 4 GB swap file (`/swapfile`, `fallocate`, `mkswap`, `swapon`). No
   `/etc/fstab` line: it is gone after a reboot, on purpose.
4. Put the fixed scripts on the server: the Phase 1 commits are on GitHub, so the
   fresh clone has them.
   Run `server_setup.sh` under `nohup`, with all output to
   `~/logs/server_setup_<date>.log`. On the first run it clones, syncs and then stops
   at "copy config.ini". The maintainer copies it from the old clone
   (`cp ~/dpd-db_contrib4/config.ini ~/dpd-db/config.ini`, nobody opens it), then the
   script is run again and goes to the end. Record each step's time from the log.
5. Re-create alice with the fixed `add_contributor.sh`, so the fix is exercised: move
   the old `/etc/dpd/alice.env`, `/etc/nginx/dpd/alice.conf` and `alice.htpasswd` into
   `/root/contrib4_backup/`, run `add_contributor.sh alice 8551 "Bold Search,DB"`
   (the maintainer types a password), `chgrp www-data` the new htpasswd (README note),
   `nginx -t`, reload. The root asset shim stays; it points at the same htpasswd path.
   Then `systemctl enable --now dpd-gui@alice`. Check: `ss -ltn` shows 8551 on
   127.0.0.1 only; `journalctl -u dpd-gui@alice` has no `Traceback`; the page loads at
   `https://187-126-118-33.sslip.io/alice/`.
6. As alice, the maintainer adds 2 real words in Pass1Add (words he wants in the
   dictionary anyway), one sandhi split, one spelling word and one variant reading.
   He checks that Bold Search returns results, that Preview opens, and that Pass1Auto
   loads a book without a missing-file error.
7. Deploy key: the agent makes `~/.ssh/dpd_deploy` (ed25519, no passphrase) and shows
   the public key; the maintainer adds it to the repo as a deploy key with write
   access, and records its GitHub key id in `results.md`. The agent sets, repo-local:
   `git remote set-url --push origin git@github.com:digitalpalidictionary/dpd-db.git`,
   `git config core.sshCommand "ssh -i ~/.ssh/dpd_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"`,
   and a git identity for the `contrib: submit data` commits. Fetches and pulls stay
   on https; only pushes use the key, and only `contrib_push.py` pushes. Preflight:
   `ssh -i ~/.ssh/dpd_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -T git@github.com`
   prints "successfully authenticated".
8. Window #1: `uv run scripts/server_contrib/maintenance_window.py --instance dpd-gui@alice --data-dir /var/lib/dpd/contrib_data`,
   output teed to a log. Record `git rev-parse HEAD` and `origin/main` before it.
   Expect: outcome `skipped` if `main` has not moved since the first build, else
   `rebuilt` (a CI workflow, `static.yml`, pushes to `main` on its own, so either is a
   pass); the log has `contrib_push: pushed` and no `FAILED`; GitHub's
   `contributions` branch holds alice's files. Then **stop alice**
   (`systemctl stop dpd-gui@alice`) and keep her stopped until window #2, so no edit
   lands between the push and the reconcile (an edited entry has a new hash and would
   survive the reconcile).
9. Local half: the maintainer checks the branch (`git ls-remote origin contributions`),
   makes sure `checked.csv` and `variant_readings.tsv` have no other uncommitted
   changes, runs `just contrib-merge`, processes the two words with Pass2Add's **Add**
   button and saves each, runs Backup & Quit, commits, and pushes `main`.
10. Window #2, same command. Before it, save a copy of alice's files. Expect: outcome
    `rebuilt`; the entries reconcile dropped are exactly the processed ones (copy
    before minus files after); the two lemmas are in the server db
    (`select id, lemma_1 from dpd_headwords where lemma_1 in (...)`); the
    `bold_definitions` table has rows; alice's unit is `active` again; Bold Search
    returns results in the browser.
11. Copy `results.md`, the window logs and the setup log back into this thread's
    `artifacts/server/`. The maintainer deletes the deploy key on GitHub. The server
    stays as it is unless the maintainer says otherwise.

## Decisions made while the owner was away (provisional — confirm at plan task 0.1)

**Owner, 2026-11-01: all six confirmed as written, except decision 1 (the key stays
after the test) and decision 5 (every shared file the merge writes is clean before
Phase 6). Everything on the borrowed server is temporary; overwrite it freely.**

The owner was away while this was planned. Each choice below had more than one fair
answer. The planner picked one so the plan is complete; the owner confirms or changes
each one before the run starts.

1. **How the server pushes to GitHub.**
   - **Owner decision 2026-11-01: keep the key after the test** (he may use the
     server long term). It is not deleted at the end. Blocking pushes to `main` stays
     with contrib_1 task 3.2.
   - Picked: a deploy key with write access, made on the server. The clone uses it only for pushes
     (`git remote set-url --push`, `core.sshCommand` with `IdentitiesOnly`).
   - Other options: (b) SSH agent forwarding from the maintainer's laptop during each
     window run — no key is stored on the server, but anyone with root on the box can
     use the forwarded agent while he is connected, and cron cannot use it; (c) no
     push from the server — copy the files back with rsync and push from the laptop —
     safest, but it does not test the push at all.
   - Risk of the pick: a deploy key with write access can push to any branch,
     including `main`, because `main` has no protection. The key exists only for the
     test. A ruleset that blocks pushes to `main` would close this, but CI
     (`.github/workflows/static.yml`) pushes to `main` too, so the ruleset would need a
     bypass for GitHub Actions; that belongs to contrib_1 task 3.2, not here.
2. **Real words, not test words.** The cycle writes into `main` and the shared files
   for real, so alice's entries are real ones the maintainer wants. Test words would
   have to be rejected and cleaned out of the shared files afterwards.
3. **Old contributor files stay where they are.** `~/contrib_data/` (the `testa`
   entries) is not moved into `/var/lib/dpd/contrib_data/`. The new run starts with an
   empty data folder.
4. **Swap.** Add a 4 GB swap file and leave it in place (it is cheap, and it protects
   the other project). Remove it at the end only if the maintainer asks.
5. **The local dirty files.** Before `just contrib-merge`, the maintainer commits (or
   deliberately sets aside by his own method) the other threads' changes to
   `checked.csv` and `variant_readings.tsv`, so the merge's changes to those files are
   the only ones in them. The plan stops there if they are still dirty.
6. **gui2 runs as root on this box.** The box is a root-only login, the clone and uv
   live under `/root`, and the window (run by root) rewrites contributor files with
   mode 600 (`contrib_reconcile.py`, `tempfile.mkstemp`). A separate `dpd` user would
   need its own clone, uv and file ownership — that is contrib_1's production design.
   Risk: a web-facing process runs as root, behind nginx basic auth, for the length of
   the test.

## Assumptions & uncertainties

Gate 1 (idea review) ran on 2026-11-01. The GLM reviewers timed out twice (no
output), so three Sonnet reviewers covered the six lenses. Accepted findings, with
severity, are folded in above and listed here so they can be checked:

- **[Blocker, accepted]** The third submodule `tipitaka.rte` is required (verified).
- **[Blocker, accepted]** A setup script that re-lists build steps would be a third
  copy of the step list. The script calls the existing entry points, and the first
  build is the window itself.
- **[Blocker, accepted]** A first build outside the window would leave the tree dirty
  (`root_families_sanskrit.tsv`) and leave no `last_built_commit`, so window #1 would
  be refused or would rebuild again. Building through the window avoids both.
- **[Major, accepted]** The window's submodule step fetches all 11 submodules.
- **[Major, accepted]** The window log does not hold child output, and the window
  always exits 0. The run tees all output to a file, and the fix makes a failed window
  exit 1.
- **[Major, accepted]** A push failure is only a log line. Every window run checks the
  log for `contrib_push:` and for `FAILED`, and the maintainer checks the branch with
  `git ls-remote` before he merges.
- **[Major, accepted]** `--no-systemd` would let gui2 hold the db during a rebuild.
  Windows #1 and #2 use the real unit.
- **[Major, accepted]** The env file lacks `FLET_SERVER_IP`; the fix goes in
  `add_contributor.sh` (one source). alice is re-created with the fixed script (B.5).
- **[Major, accepted]** Reconcile can drop entries silently. Before window #2 the
  agent saves a copy of alice's files; after it, the dropped entries must equal the
  ones the maintainer processed.
- **[Major, accepted]** 8 GB without swap is tight while the deconstructor runs.
- **[Major, accepted]** The local merge touches files other threads have changed.
- **[Major, accepted]** The other project on the box: record pre-state, never touch
  its files, `nginx -t` before any reload.
- **[Nit, accepted]** Preflight checks in the setup script (`config.ini` present,
  `go version`).

Gate 2 (spec review, two Sonnet reviewers, 2026-11-01) — accepted and fixed above:

- **[Blocker]** The unit's Unix user was undecided → decision 6 (root on this box)
  and the full unit text in A.5.
- **[Blocker]** A failed first build has no db to roll back to, and a timeout leaves
  child processes running → stated in A.6 with what to do.
- **[Major]** The first build's flags were incomplete (`--data-dir` missing) → A.6.
- **[Major]** "Safe to re-run" was undefined; a script under `nohup` cannot ask for
  `config.ini` → the probe table and the exit-and-re-run rule in A.6.
- **[Major]** No clean-tree check before the first build; files written inside a
  submodule may count as dirty → the clean-tree gate in A.6.
- **[Major]** Window #1 may rebuild if CI moved `main` → criterion 3 accepts both.
- **[Major]** alice could edit between the push and the reconcile → she is stopped
  after window #1 (B.8).
- **[Major]** SSH host key and push setup → B.7 (`accept-new`, preflight).
- **[Major]** The deploy-key risk had an unweighed mitigation → decision 1.
- **[Major]** The rehearsal never ran the fixed `add_contributor.sh` → alice is
  re-created (B.5).
- **[Major]** The server agent's rules forbade steps the run needs → the allowed list
  at the top of part B.
- **[Major]** No test pinned the submodule command; the exit code needed a test → A.2,
  A.3.
- **[Nit]** Bold step position, swap without fstab, submodule depth → A.1, B.3, A.6.

Gate 2 finding rejected: "make a push failure its own exit code" — the window treats
a failed push as non-fatal by design (contrib_5); this run checks the log and the
branch instead.

Gate 3 (plan readiness audit, one Sonnet reviewer, 2026-11-01): 20 findings — 0
Blockers, 13 Majors, 1 marked Minor-to-Major, 6 Nits — all addressed in `plan.md`. The most important: after window #2 the
`contributions` branch is one commit ahead of `main` (it removes the merged flag lines),
not equal to it; the window and the build steps call a bare `uv`, so the setup script
puts `~/.local/bin` on `PATH`; the copied `config.ini` is checked for the three values
the build needs; long runs go to the background with a pid file.

Still uncertain, to be measured or seen in the run:

- How long each step takes on 2 CPUs. Local: the full build is about 11 minutes on
  22 cores. A single step over one hour hits the window's timeout and rolls back. If
  that happens, it is a finding, and the plan has a fallback (run the step by hand,
  timed).
- Peak RAM of the frequency setup and the deconstructor on this box.
- Whether `initial_setup_run_once.py` changes any tracked file. If it does, the window
  refuses (dirty tree) — the plan checks `git status` before the first build.
- Whether apt's `golang-go` is 1.22.2 on the server.
- Whether the processed words reach the server db with the same lemma (the server
  rebuilds from the TSVs the maintainer committed).
- contrib_x problem child 4: a contributor's addition id can equal a real db id. This
  run will show whether it matters in a real merge.
- The root asset shim makes `/alice/` work for one user only. The native flet fix
  (`root_path`) is not part of this thread.

Rejected Gate 1 findings (owner may overrule):

- "`go run go_modules/deconstructor/main.go` is the wrong form" — rejected: that
  folder has one `main.go` plus sub-packages, and the release workflows run the same
  command.
- "`configger.py` could overwrite the placed `config.ini`" — rejected:
  `config_initialize()` only adds missing options.
- "Drop `cst4_xml_to_txt` and `transliterate_bjt` from the server setup" — rejected:
  the maintainer asked for the init-once script, and Pass1Auto failed in contrib_4 for
  lack of the CST text files that `cst4_xml_to_txt` makes.
- "Shallow clone and shallow submodules" — rejected for now: the previous full clone
  worked, and the saving is not needed for this test.

## Constraints

- Never touch `~/epitaka-translator`, its nginx config, or its processes.
- The server agent follows the contrib_4 rules (no secrets read, no code edits on the
  server, no `git commit`/`push`/`stash`/`reset`/`checkout` by hand).
- Never commit `config.ini`, keys, or htpasswd files.
- Local repo rules apply to Phase 1: ruff check, ruff format, pyright (with
  `--project /dev/null` for `tests/`), the related pytest files, and `just typecheck`.
- Only the maintainer commits and pushes `main`. The server pushes only the
  `contributions` branch, and only through `contrib_push.py`.
- Every download uses a rate limit where the tool has one; the maintainer's link is
  slow.

## How we'll know it's done

1. The server was built from a fresh clone by `server_setup.sh` with no file copied
   from the laptop except `config.ini`; the setup log shows every step's time.
2. alice's page loads at `https://187-126-118-33.sslip.io/alice/`; Pass1Auto,
   Pass1Add, Bold Search (with results) and Preview all work.
3. Window #1 ends `skipped` (or `rebuilt` if `main` moved since the first build), its
   log has `contrib_push: pushed` and no `FAILED`, and GitHub's `contributions`
   branch holds alice's files.
4. The maintainer's local merge and processing put the two words into `main`, with
   their entries in `additions_added.json` and the flag lines in
   `contrib_lines_merged.json`.
5. Window #2 ends `rebuilt`; reconcile dropped exactly the processed entries; the two
   words are headwords in the server db; Bold Search still returns results.
6. gui2 never listened on anything but 127.0.0.1; the other project is unchanged.
7. Results, logs and timings are in this thread's `artifacts/`; the deploy key stays
   on GitHub (decision 1), and its id is in `results.md`.

## What's not included

- The native flet `root_path` fix and a second contributor behind nginx (contrib_1
  Phase 3).
- Branch protection on `main`, cron for the window, a status page (contrib_1 3.2, 3.6).
- The production server, its provider and its domain.
- The other contrib_x problem children (Alt shortcuts, second browser tab, Pass2).
- Removing the borrowed server's nginx, certificate or packages.
