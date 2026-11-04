# Gate 2: review of spec.md (2026-11-04)

## Backend and run record
- Backend: pi, azure, deepseek-v4.1-flash, `--tools read --no-session`, `--mode json`, one at a time. No retries needed; each finished in under 4 min (checked at 30 s, as the owner asked).
- G2.1 = comprehension reviewer (naive reader). It read the FIRST draft of the spec.
- G2.2 = design critic (includes security and the runbook scope). It read the spec AFTER the G2.1 fixes and after the runbook section was added at the owner's request.
- Both were told not to open `egm/`.

## Raw findings (verbatim)

### G2.1 Comprehension
## Restatement (my words, ~6 lines)
A systemd user timer runs a script twice-hourly (08:00–22:00) on the maintainer's laptop. Each run rsyncs contributor files from `/var/lib/dpd/contrib_data` over a restricted read-only SSH key into a 0700 scratch folder, validates each file strictly, reconciles (drops already-processed words/lines and non-reserved test exceptions), atomically copies survivors into `gui2/data`, merges flag files into shared files, and logs status. It skips if it already succeeded today, another run holds a lock, or the editor is open. Failures abort before `gui2/data` is touched, retry every 30 min, and notify on the day's last retry.

## Findings

**Blocker — undefined lock and "succeeded today" state.** `spec.md:22`, `spec.md:38`. No lock file/library/path is named (filelock is a dependency, unused here), and step 1(a) reads a "succeeded today" marker the spec never says lives in the status file nor that a failed run preserves the prior last-success date. A fresh implementer cannot build the gate; a naive one resets the date on failure and re-runs all day. Fix: name the lock file/lib and state the status file is read at start with last-success carried forward.

**Blocker — the `db_test_exceptions` merge never happens.** `spec.md:32` drops every non-reserved exception line; `merge_contrib_files.py` `merge_test_exceptions` skips reserved ids and its `handled` list never logs them. After step 4 only reserved lines remain, so step 6 (`spec.md:36`) merges zero exceptions — contradicting "runs the existing merge step". Fix: drop the db_test_exceptions job from step 6 and say so, or keep non-reserved lines that name a real test.

**Major — editor re-check misses step 6.** `spec.md:34` re-checks before step 5, but step 6 writes `shared_data/*`. An editor starting in between races the merge. Fix: re-check (or hold the lock) through step 6.

**Major — one bad file blocks every contributor.** `spec.md:26` fails the whole run on any invalid file, and `spec.md:20` stops steps 2–4. One contributor's corrupt or mid-write file stops all pulls all day, re-notifying at 22:30. Fix: quarantine/skip the bad file and report per-file status.

**Major — rsync `--max-size` defeats step 3's size check.** `spec.md:24` vs `spec.md:26`. rsync silently omits a >5 MB file, so step 3's "at most 5 MB / fails" can never fire and a large legit file is silently never pulled. Fix: `--list-only` sizes first or compare against a manifest.

**Major — the "editor running" heuristic is unreliable.** Assumptions (`spec.md` final section) match only a process arg ending `gui2/main.py`, while the spec explicitly rejected an editor-side lock. A packaged/desktop or `flet run` gui2 is missed and writes race. Fix: a single lock file both sides honour.

**Major — "last retry of the day" is unknowable.** `spec.md:38`. The script gets no signal it is the final 22:30 run. Fix: pass an env/flag from the unit, or compare time.

**Major — deleted server files never removed locally.** `spec.md:34` only writes; a server-deleted contributor file's unprocessed entries stay in the editor forever. Fix: track pulled names, delete local files absent from a successful run.

**Nit — "seven shared files."** Undo section; `SharedFiles` (`merge_contrib_files.py`) has six fields and Terms lists six. Fix: say six.

**Nit — `notify-send` under systemd `--user` lacks `DISPLAY`/`DBUS_SESSION_BUS_ADDRESS`.** Assumption only checks the binary exists. Fix: set `Environment=` or fall back to the log.

**Nit — scratch path and failure cleanup undefined.** `spec.md:24`. Fix: name it and state deletion on every exit.

**Unverifiable, read-only:** the `[epitaka_server] ssh` claim (`config.ini` off-limits) and that it equals the SSH alias user/host.

Checked references hold: `DELIVERED_KINDS`, `reconcile_all(project_root, data_dir)`, `merge_all(data_dir, shared, log_path)`, `SharedFiles.default()`, `CONTRIB_ID_BASE=10_000_000`, `save_processed_addition`/`reject`, `add_contributor.sh` regex, `psutil`, `logs/` ignored, `just contrib-merge` call — all match.

### G2.2 Design critic
## Design critique — `kamma/threads/20261104_contrib_pull/spec.md`

**1. Blocker — no dirty-tree guard before overwriting tracked `gui2/data` files.** Spec step 5 replaces tracked files (`additions_*.json`, `corrections_*.json`, `db_test_exceptions_*.tsv`, and force-added `checked_alice.csv` — spec "Assumptions"). The server's own window refuses a dirty tree (`maintenance_window.py` flow, README "The nightly maintenance window"); the laptop pull has no such check. A concurrent `just contrib-merge` (`justfile` contrib-merge) or an uncommitted local edit is silently overwritten. Fix: refuse when a target file is dirty in git, or write to a side path for the maintainer to merge.

**2. Blocker — `contrib_lines_merged.json` written non-atomically.** `merge_contrib_files.py:write_merged_log` opens the tracked log and `json.dump`s directly; a crash or kill mid-write corrupts it. The next `contrib_reconcile.load_merged_lines` raises, failing both the pull and the server's nightly window until hand-fixed. Fix: temp + `os.replace`, as `contrib_reconcile._write_atomic` already does.

**3. Major — editor TOCTOU, no shared lock.** Checks happen at step 1, before 5, before 6, but nothing stops the editor starting after a check. `additions_manager._save_dict` rewrites the file from in-memory `additions_dict`, so a pulled word is lost when the editor next saves. The owner rejected an editor lock, so this race is unhandled. Fix: re-check under the editor's own lock, or newer-mtime-wins.

**4. Major — `accept-new` makes auto-merged flag lines attacker-controlled.** On first-contact MITM the host serves arbitrary lines; step 6 `merge_all` folds them into tracked `shared_data/` files with no human review (only additions are reviewed in the editor). Fix: pin the host key at setup, or stage flag lines for review.

**5. Major — kind↔extension mismatch undefined.** Step 3's regex allows any kind with any extension (`\.(json|csv|tsv|txt)$`), so `checked_alice.json` passes the name and is then parsed by the wrong branch. Fix: bind each kind to its one extension from `DELIVERED_KINDS` (`tools/contrib_entry.py`).

**6. Major — step 5 is atomic per file, not per run.** A crash after 2 of 5 renames leaves `gui2/data` mixed old/new, contradicting "a failure before step 5 leaves `gui2/data` untouched" (which is silent on failures *during* 5). Fix: stage in a temp dir and swap, or record per-file progress.

**7. Major — "at most 200 names in the listing" has no defined outcome** (step 3): fail all, or skip some? Implementer must invent. Similarly step 1/7 are silent on a corrupt/missing `logs/contrib_pull_status.txt` and on a step-7 write failure.

**8. Nit — passphrase-less key file path/permissions unspecified** (spec Login: "outside the repo", no `600`, no path).

## Runbook scope — `scripts/server_contrib/NEW_SERVER_RUNBOOK.md`

Incomplete for a fresh machine + contributor move:

- **Timezone.** README: cron "01:00 IST on a host in IST". A fresh image is UTC; step 8 would fire at the wrong local time. Missing `timedatectl set-timezone Asia/Kolkata` + CHECK.
- **Maintainer `/status` htpasswd.** Step 6's status block needs `/etc/nginx/dpd/<maintainer>.htpasswd`; `add_contributor.sh` refuses existing files and is contributor-shaped, so no step creates it.
- **DNS A record** before certbot HTTP-01 (step 6 issues the cert but never points the domain).
- **Deploy key incomplete.** README requires `git remote set-url --push` **and** `core.sshCommand`; step 8 names only "the deploy key".
- **Cron line incomplete.** README's working line carries `--data-dir`, `--status-file` and one repeatable `--instance` per contributor; step 8 mentions only PATH.
- **Certbot renewal timer** unmentioned.

## Disposition table

| ID | Finding | Sev | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| G2.1.1 | Lock and "succeeded today" state undefined | Blocker | Accept | spec read | spec: state, lock (`fcntl.flock`) |
| G2.1.2 | Exception merge never happens | Blocker | Accept as text | code: merge_contrib_files.py:183-208 skips reserved ids | spec step 4 |
| G2.1.3 | Editor re-check misses step 6 | Major | Accept | spec read | spec steps 1, 6 |
| G2.1.4 | One bad file blocks every contributor | Major | Accept (per contributor) | reasoning: a contributor's files depend on each other | spec step 3 |
| G2.1.5 | rsync `--max-size` hides oversize files | Major | Accept | rsync behaviour | spec step 2 (list first) |
| G2.1.6 | Editor heuristic unreliable; add a lock | Major | Reject the lock | owner rule: no editor change | spec: residual risks |
| G2.1.7 | "Last run of the day" unknowable | Major | Accept | — | spec step 7 (22:30 local) |
| G2.1.8 | Server-deleted files never removed locally | Major | Reject | code: contrib_reconcile.py:22 "An emptied file is written back, never deleted" | none |
| G2.1.9 | "Seven" shared files should be six | Nit | Accept | code: `SharedFiles` has 6 fields | spec: Undo |
| G2.1.10 | notify-send lacks DBUS under systemd | Nit | Accept | — | spec: Timer |
| G2.1.11 | Scratch path and cleanup undefined | Nit | Accept | — | spec step 2 |
| G2.2.1 | No dirty-tree guard | Blocker | Reject | reasoning: dirty is the normal state; removals are in the processed log so reconcile keeps them | spec: residual risks |
| G2.2.2 | `write_merged_log` not atomic | Blocker | Accept | code: merge_contrib_files.py:117-125 truncates in place | spec: Changes to existing code |
| G2.2.3 | Editor start between check and rename | Major | Accept as residual risk | — | spec: residual risks |
| G2.2.4 | `accept-new` plus auto-merged flag lines | Major | Accept in part | line checks added; host pin rejected (owner wants no manual step) | spec step 3, residual risks |
| G2.2.5 | Kind and extension mismatch | Major | Accept | tools/contrib_entry.py patterns | spec step 3 |
| G2.2.6 | Step 5 atomic per file, not per run | Major | Accept as text | reasoning: next run repairs | spec step 5 |
| G2.2.7 | 200-name outcome, bad status file, step 7 write failure | Major | Accept | — | spec steps 3, 7 |
| G2.2.8 | Key file path and mode | Nit | Accept | — | spec: Login |
| G2.2.9 | Runbook: time zone | Major | Accept | cmd: server zone is Asia/Colombo | spec: runbook 2 |
| G2.2.10 | Runbook: maintainer status login | Major | Accept | code: server site file uses alice.htpasswd for /status | spec: runbook 6 |
| G2.2.11 | Runbook: DNS before certbot | Major | Accept | sslip.io resolves by itself | spec: runbook 6 |
| G2.2.12 | Runbook: deploy key incomplete | Major | Accept | code: README:37-38 | spec: runbook 8 |
| G2.2.13 | Runbook: cron line incomplete | Major | Accept | code: README cron line | spec: runbook 8 |
| G2.2.14 | Runbook: certbot renewal timer | Nit | Accept | cmd: timer exists on the server | spec: runbook 6 |
