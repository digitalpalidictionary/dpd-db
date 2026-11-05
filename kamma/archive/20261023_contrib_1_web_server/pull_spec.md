# Spec: daily pull of contributor words from the server

Part 2 of thread `20261023_contrib_1_web_server` (merged from `20261104_contrib_pull`, 2026-11-04). Part 1 is `spec.md` in this folder (the server). Plan: Phases 4 to 8 of `plan.md`. GitHub issue: #215 (same contributor-server work).

## Overview

The contributor web server keeps each contributor's words and flag lines in per-contributor files in one folder. Today the maintainer gets them only by running `just contrib-merge` by hand. The maintainer wants them to arrive on the laptop **by themselves, every day, with no step after setup**, with no GitHub pull request and no git merge.

A small script, started by a systemd user timer at 08:00 (and retried every 30 minutes until it succeeds), copies the contributor files from the server into a scratch folder, checks them, drops what the maintainer already processed, copies the rest into `gui2/data`, and runs the existing merge step for the flag files. It does nothing while the editor (gui2) is open.

## Terms

- **Contributor file**: a file in the server folder `/var/lib/dpd/contrib_data` whose name matches one of the patterns in `tools/contrib_entry.py` `DELIVERED_KINDS`, with the user name in the name (`additions_alice.json`).
- **Processed word**: a contributor entry whose `(_source_key, _source_hash)` is in the local `gui2/data/additions_added.json` or `corrections_added.json`. The editor writes that log and removes the entry from the contributor's local file when the maintainer processes or rejects it (`gui2/additions_manager.py` `save_processed_addition`, `reject`).
- **Flag files**: user dictionary, sandhi checked, sandhi manual corrections, variant readings, spelling mistakes, db test exceptions.
- **Reserved id**: a db id at or above `CONTRIB_ID_BASE` (10,000,000). A contributor's new word has a reserved id until the maintainer adds it.

## What it should do

Each run, in this order. A failure before step 5 leaves `gui2/data` untouched.

State lives in `logs/contrib_pull_status.txt`, which every run reads first. A missing or unreadable status file counts as no earlier success; the run goes on and rewrites it. If step 7 cannot write the file, the run exits non-zero with the error on stderr (the systemd journal) and `last_success` stays unset. It carries `last_success: YYYY-MM-DD` forward unchanged on every run that is not a full success. The lock is `fcntl.flock` (standard library) on `logs/contrib_pull.lock`.

1. **Gate.** Stop quietly if (a) `last_success` is today, (b) the lock is held, or (c) the editor is running. A skipped run prints its reason and writes neither the status file nor the log, so the status keeps the last real result (changed 2026-11-04: the timer runs 30 times a day). The editor is a process with an argument that ends in `gui2/main.py` (matched on the argument list, never on the whole command line; the script's own process is excluded). It is checked again before step 5 and before step 6.
2. **List, then copy.** `rsync --list-only` (one level, no `-r`, so a hostile tree is never walked) from the server gives names and sizes without copying. The script checks each name and size (step 3) and then copies only the accepted names with a second `rsync` using `--files-from`, into a new scratch folder (`tempfile.mkdtemp`, mode 0700, deleted on every exit). Options: no links, no permission or owner copy, 60 s timeout. Read-only. The listing shows everything in the server folder (names and sizes only); the script picks the names that match a `DELIVERED_KINDS` pattern and copies only those. A name from which no user can be read is ignored and counted.
3. **Check every file, per contributor.** Files are grouped by the user name in the file name. If any file of a contributor fails, **all of that contributor's files are skipped today** (their local copies stay as they are) and the status names the contributor and the reason. Other contributors continue. A contributor's files belong together: their reserved-id exceptions are judged against their additions.
   - the name matches the glob of exactly one kind in `DELIVERED_KINDS` (so `checked_alice.json` fails: each kind has its one extension) and its user part matches `^[a-z][a-z0-9_]{0,31}$`, and the name does not contain `added`; the listing shows a regular file; at most 5 MB. More than 200 names in the listing fails the whole run (status `failed: too many files`);
   - `manual_corrections`: every line has exactly 2 non-empty tab-separated columns (the Go reader indexes the header by column, so a third column stops the build). `checked` and `user_dictionary`: no tab in any line (added 2026-11-04 after review);
   - JSON kinds: every entry's `id`, if present, is an integer or a digit string of at most 12 digits (a huge or odd string makes the reconcile step raise and stop the run for everyone; added 2026-11-04 after review); valid UTF-8 JSON (a parse error or `RecursionError` fails the file), top level is an object, every value is an object;
   - line kinds: valid UTF-8, no control characters except tab, CR and LF, each line at most 500 characters, tab-separated kinds have the right number of columns, the file is empty or ends with a newline (a copy taken mid-write is refused, not merged);
   - `db_test_exceptions_*`: each line is `<test name><TAB><digits>`.
4. **Drop what is already handled.** Run `contrib_reconcile.reconcile_all(project_root=<repo>, data_dir=<scratch>)`. It drops processed words, merged flag lines, and reserved-id exceptions that no word holds, and writes the scratch files in place. Then drop every `db_test_exceptions` line whose id is **not** reserved: a contributor can only have exceptions for their own new words, and the merge step would otherwise add any other id to a real test. The count of dropped lines goes in the status. After this, the exceptions the merge step sees are all reserved ids, which it skips by design, so in practice step 6 merges the other five flag kinds.
5. **Copy in.** Re-check the editor. For each remaining scratch file, write a temp file in `gui2/data` and rename it over the target (atomic per file). A crash part-way leaves some contributors' files new and some old; the next run repairs it, because `last_success` is set only in step 7 and every step can be repeated. A file that is absent from the server listing is left alone locally (the server writes an emptied file back, it never deletes one).
6. **Merge flag files.** Re-check the editor. If it is running now, stop here with status `partial` (not a success, so the next retry runs again; every step is repeatable because the merge logs each handled line). Otherwise call `merge_contrib_files.merge_all(gui2/data, SharedFiles.default(), contrib_lines_merged_path)`, the same call as `just contrib-merge`.
7. **Record.** Set `last_success` to today only now. Write `logs/contrib_pull_status.txt` (outcome, time, last success, per contributor: files pulled or skipped and why, entries kept, flag lines added, test lines dropped) and append one line to `logs/contrib_pull.log`. The last run of the day is the one that starts at or after 22:30 local time. If that run ends in `failed` or `partial`, send a desktop notice (`notify-send`) and say so in the status. A `pulled` run with a skipped contributor sends the notice at once, at any hour: it counts as the day's success, so no later run would report it (changed 2026-11-04 after review). A skip because the editor is open or because today is already done sends no notice.

Everything above runs without the maintainer. A new contributor needs no change: the file patterns pick up any name.

### Timer
User unit `dpd-contrib-pull.timer`: `OnCalendar` hours 08 to 22, at :00 and :30; `Persistent=true`. Service `Type=oneshot` with `WorkingDirectory` = the repo, an absolute `uv` path, an explicit `PATH` in the unit (the server's cron failed on its first night because `uv` was not on cron's path) and `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus` so `notify-send` works from a timer; if the notice fails, the status file still says so. Unit files are committed as templates in `scripts/server_contrib/`; the planner installs them on the maintainer's laptop.

### Login
- The ssh target is `config_read("epitaka_server", "ssh")` (already set, `user@host`, nothing in the repo reads it today). No new config line. If it is missing, the run fails with a message naming the section and option.
- The server folder is a constant, `/var/lib/dpd/contrib_data` (set by `add_contributor.sh`, never changes).
- Options (both rsync calls): `BatchMode=yes`, `StrictHostKeyChecking=accept-new` (trust a host on first contact, refuse a changed key), `IdentitiesOnly=yes`, `ForwardAgent=no`, a dedicated key file `~/.ssh/dpd_contrib_pull` (mode 600, outside the repo).
- **Restricted key.** A new ed25519 key, passphrase-less, that the server allows only as `restrict,command="/usr/bin/rrsync -ro /var/lib/dpd/contrib_data"`. It can read that one folder and nothing else. The planner creates it and appends one line to the server's `authorized_keys` after a backup. The maintainer's own login is not touched.

### Changes to existing code
- `scripts/server_contrib/merge_contrib_files.py` `write_merged_log` writes a temp file and renames it (as `contrib_reconcile._write_atomic` does). Today it truncates and rewrites in place, so a kill mid-write corrupts the log, and both this pull and the server's nightly window then fail on it.
- `justfile`: one comment line on `contrib-merge`; recipe `contrib-pull` that runs the script by hand (the same command the unit runs); recipe `contrib-pull-install` that fills the unit templates, installs them in the user's systemd folder and enables the timer (also used on a future laptop).
- `scripts/server_contrib/README.md`: a short section for the pull and a link to the runbook.
- New: `scripts/server_contrib/contrib_pull.py`, the two unit templates, `tests/scripts/server_contrib/test_contrib_pull.py`, the runbook.

### The old route
`just contrib-merge` stays in the justfile with a one-line comment that it is replaced and must not be run together with the pull. The server's nightly push to the `contributions` branch is **not** changed: it is a free off-server copy of the words, and stopping it would be another server edit with its own risk.

### Undo
The six shared files and `contrib_lines_merged.json` are tracked in git, so `git diff` shows what a run merged and a restore of a named file undoes it. The contributor files in `gui2/data` are copies of server state and can be pulled again.

## Second deliverable: a runbook for a new server

The owner's current server will close, and a new one must be set up. The owner wants instructions so exact that **a simple agent with no context can do it**. Nothing like this is kept today: the plan of the server thread records that "the runbook file itself was not kept up", `scripts/server_contrib/server_setup.sh` leaves out the one-time steps on purpose (swap, nginx and certificate, `add_contributor.sh`, the deploy key, `systemctl enable`), and those steps sit in `kamma/threads/20261101_contrib_6_e2e_server_test/plan.md` and `kamma/threads/20261023_contrib_1_web_server/plan.md`, in older form.

Deliverable: `scripts/server_contrib/NEW_SERVER_RUNBOOK.md`, linked from `scripts/server_contrib/README.md`.

Rules for the document:
- **Reader:** an agent that knows nothing of this project. No step depends on knowledge from a chat.
- **Every step** names WHO runs it (OWNER at the provider's web console or on the laptop, or AGENT over ssh), gives the exact command, then a `CHECK` command and an `EXPECT` line with the exact result. If the result differs, the agent stops and tells the owner; it does not improvise.
- **Executor rules at the top:** never print a secret file or an environment; run any command over 60 seconds with `setsid nohup ... &` and a bounded wait loop; never use `pkill`; one change, then its check; take a backup before editing any system file; say what failed with the exact error text.
- **Placeholders** (new server address, domain, user names) are defined once with how to obtain each. A value that exists on a machine is read from it, never typed as a placeholder.
- **Unproven steps** are marked `UNTESTED` in the document. The runbook is not rehearsed end to end on a fresh machine; every command is checked against the live server (read-only) or the script it calls, and the Gate 3 reviewer follows it as a naive agent.

Steps it must cover, in order, using what is known to work on the current server (2026-11-04):
1. Order the server, get root ssh with a key; record the address (OWNER).
2. Time zone (`timedatectl set-timezone Asia/Colombo`, the current server's zone; a fresh image is UTC and the 01:00 cron would fire at the wrong hour), keys-only ssh (a drop-in file that sorts first, because the cloud image's own file says `PasswordAuthentication yes`), firewall for 22, 80, 443 with a self-disarming safety timer, automatic security updates.
3. Packages, `uv`, swap, clone, three submodules, `server_setup.sh`.
4. `config.ini` (OWNER enters the API keys; the agent never reads or prints it), mode 600.
5. First database build through the maintenance window, detached, with a bounded wait.
6. The service unit with `FLET_WEB_APP_PATH=%i`; nginx site and per-user files (path prefix, no trailing slash on `proxy_pass`); the domain name (`<ip with dashes>.sslip.io` resolves by itself, so no DNS record is needed; with any other domain the A record must point at the server before certbot runs) and the certificate (port 80 stays open; check `certbot renew --dry-run` and the renewal timer); the status block and the maintainer's own login file that it uses (today `alice.htpasswd`).
7. Contributors: copy the folder `/var/lib/dpd/contrib_data`, the htpasswd files and the env settings from the old server **before it closes** (no password is asked again), or run `add_contributor.sh` for a new one; the htpasswd group is set by the script.
8. The deploy key for the nightly push (`git remote set-url --push` **and** `core.sshCommand`, per the README), and the cron job: the full line with `--data-dir`, `--status-file` and one `--instance dpd-gui@<user>` per contributor, **with its `PATH` line**.
9. The restricted read-only key for the laptop pull (one `authorized_keys` line with `rrsync -ro`).
10. Laptop side: the OWNER changes `[epitaka_server] ssh` in `config.ini` to the new `user@host` (nothing else; the first connection trusts the new host by itself), and runs one manual pull.
11. A full check from outside: each contributor's page loads at the new address; the status page says `rebuilt`; the first pull brings a test word.
12. Cutover and retirement of the old server: tell contributors the new address; stop the old server's cron first so two servers never push the `contributions` branch; keep a backup of the old data folder.

## Residual risks (accepted, on purpose)

- **The editor can start between a check and the rename in step 5.** The window is milliseconds long, the timer runs at hours when the editor is normally closed, and closing it needs a lock inside the editor, which the owner does not want. If it happens, the editor's next save can overwrite one pulled file; the server still holds the words and the next day's run brings them back.
- **A hostile first connection to a new server address.** With `accept-new` the first contact trusts whatever answers. The checks in steps 3 and 4 limit what it can deliver, the key never leaves the laptop, and flag-file changes show in `git diff` of tracked shared files. The same exposure exists if the real server is hacked.
- **A dirty git tree is the normal state**: the files in `gui2/data` change on every pull and are committed by the maintainer's usual data commit. No dirty-tree guard.

## Assumptions & uncertainties

Verified by reading code or running a command (2026-11-04):
- Folder contents on the server; `DELIVERED_KINDS`; `reconcile_all` signature and CLI; `merge_all` signature; the editor removes a processed key from the contributor file and logs `(key, hash)`; `[epitaka_server] ssh` has the shape `user@host` and equals the ssh alias's user and host; `rrsync` and `rsync` are installed on the server; `systemd --user` works on the laptop; the unattended login works without an agent (the laptop key has no passphrase); `notify-send` and `rsync` exist on the laptop; `logs/` is gitignored; `psutil` is a dependency.
- Git tracking: `additions_*.json`, `corrections_*.json`, `db_test_exceptions_*.tsv` are not ignored; `checked_*`, `manual_corrections_*`, `variant_readings_*`, `spelling_mistakes_*`, `user_dictionary_*` are ignored (some, for example `checked_alice.csv`, are tracked anyway because they were force-added).

Not verified, to be tested in the plan:
- How `rrsync -ro` wants the remote path (relative to its root). A test on the server settles it.
- That the first run on real files drops nothing it should keep and keeps nothing it should drop. 39 of 43 rows in `additions_added.json` and 525 of 525 in `corrections_added.json` have no hash; they belong to earlier contributors whose files are not on the server, so none is expected to match. The dry run proves it.
- That the editor process matches the exact argument `gui2/main.py` and nothing else. A substring match over the whole command line matched the planner's own commands. Match an argument that ends in `gui2/main.py` and exclude the script's own process.
- `systemd --user` timers run when the maintainer is not logged in only with lingering enabled. The laptop is on and the maintainer is logged in at 08:00, so this is not needed; if the laptop is off at 08:00, `Persistent=true` runs the job at the next start.

Goldfish findings accepted (full list in `egm_pull/gate1.md`):
- (Blocker) Do not write a new filter; reuse `reconcile_all`. Applied in step 4.
- (Blocker) A hostile exception line could silence a database check. Applied in step 4.
- (Blocker) Links could read or write outside the folders. Applied in steps 2 and 3.
- (Blocker) Unattended ssh needs a fixed option set and a visible outcome. Applied in "Login" and step 7.
- (Major) A day is lost if the editor is open at 08:00: fixed by the 30-minute retries and the once-a-day marker.
- (Major) A half-copied flag file must not be merged: step 3.
- (Major) The unit needs its own folder and path: "Timer".
- (Major) Size and count caps on files: step 3.
- Finding R4.1 to R4.4 and R4.6 are applied as listed in `egm_pull/gate1.md`.

Goldfish findings rejected, with reasons in `egm_pull/gate1.md`: a lock inside the editor, a registered-contributor list, staging shared-file changes for review, an ignored folder the editor reads, dictionary field sanitising (out of scope: the maintainer reviews every word in the editor), a copy of the shared files before every merge (git already tracks them).

Decisions made on the owner's rule "least maintenance, I want it to just happen" (provisional until the owner reads this):
- Route: copy straight from the server (the owner's agreed plan); not a timer around `just contrib-merge`; the server's push is left alone.
  Options considered: A timer around `just contrib-merge`; copy from the server and leave the push; copy from the server and stop the push.
- Key: a dedicated read-only key. Alternative: the maintainer's existing root login (fewer steps, but an unattended job would hold a full root key).
- Host key: `accept-new`. I had first rejected it as unsafe. It only trusts a host on first contact and refuses a changed key; a server address change would otherwise need a manual step, which the owner does not want. The checks in step 3 and 4 limit what a hostile first contact can deliver, and the key never leaves the laptop.

## Constraints

- Never edit `.env` or `.ini` files; the only setting used already exists.
- No git commands, no GitHub, no pull request in the script.
- Python rules of this repo: type hints, `Path`, `icecream` not `print`, no `sys.path` tricks, run from the repo root.
- Each file the work touches must pass `ruff check`, `ruff format` and `pyright` (and `just typecheck` before the end).
- No secrets in logs or the status file: never write the ssh target or the key path.

## How we'll know it's done

- A unit test run shows: a processed word in the server copy is absent from `gui2/data` after a run; an entry the contributor edited after review (new hash) stays; a hostile name, a symlink, an oversized file, broken JSON, a flag file with no final newline and a non-reserved exception id are each refused or dropped; one bad file leaves `gui2/data` byte-identical; running twice in one day does nothing the second time; an open editor skips the run.
- A dry run on the real server files prints what would change and changes nothing.
- A real run on the maintainer's laptop pulls alice's words, `gui2/data` has them, the editor shows them in its queue, and the status file says `pulled`.
- The restricted key can read the folder and nothing else: `ssh` with a command and a write attempt are refused.
- The timer is installed, `systemctl --user list-timers` shows the next run, and a run started by `systemd-run --user` with the unit's environment succeeds.
- The next morning at 08:00 a run happens with no step from the maintainer.
- `NEW_SERVER_RUNBOOK.md` exists, covers steps 1 to 12 above, and every step has WHO, command, CHECK and EXPECT. A fresh reviewer who follows it as a naive agent finds no step that needs a guess. Each command in it was checked against the live server (read-only) or the script it calls, and the steps that were not are marked `UNTESTED`.

## What's not included

- Changes to the server (its nightly push, reconcile, window) except one `authorized_keys` line.
- Actually building the new server. The runbook is the deliverable, not the new server.
- Changes to the editor.
- Sanitising dictionary fields against markup (existing flow; the maintainer reviews every word).
- A pull request, a git merge, or a change to `just contrib-merge` beyond one comment line.
- Lingering, a second laptop, or running when the laptop is off.

## Review record

Gate 1: 4 reviewers on azure deepseek-v4.1-flash, one at a time, 32 rows in `egm_pull/gate1.md`: 23 accepted, 6 rejected, 2 escalated (resolved on the owner's rule above), 1 no issue. Two first attempts hung and were retried once (recorded in `egm_pull/gate1.md`).
Gate 2: 2 reviewers on the same backend, 25 rows in `egm_pull/gate2.md`: 22 accepted, 3 rejected. The first read the first draft; the second read the corrected spec with the runbook section.
Gate 3: 1 reviewer on the same backend, 11 rows in `egm_pull/gate3.md`: 10 accepted, 1 rejected. All fixes are in `plan.md`.
