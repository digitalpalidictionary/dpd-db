# Gate 1: stress-test the idea (2026-11-04)

## Backend and run record
- Backend: pi, provider azure, model deepseek-v4.1-flash, `--tools read --no-session`, run ONE AT A TIME.
- Smoke probe: passed (8 s, used the read tool once, returned the first line of brief.md).
- Four reviewers (the thread is small, so lenses were paired; security was added at the owner's request):
  R1 = Contrarian + Cost; R2 = UX + Migration; R3 = Observability + Tech debt; R4 = Security.
- R1 first attempt: text mode, hit the 900 s cap, no output. Counted as failed. Retried once in `--mode json`: finished in about 90 s, exit 0.
- R2 first attempt: no output and 0% CPU after 88 s. Stopped by process number. Retried once: finished in about 3 min, exit 0.
- R3 and R4: first attempt worked. Each finished in under 3 min.
- Lesson for later gates: use `--mode json` and look at the event file after 30 s; an empty file at 60 s means hung.
- R1 got only the request and the hypothesis (no facts). R2, R3, R4 got brief.md (claims to re-check).

## Raw findings (verbatim from each reviewer)

### R1: Contrarian + Cost
## Findings (problems first)

**1. Blocker — the whole feature already exists; this reinvents it.**
The server already runs a nightly window that reconciles against main's processed logs and pushes the remaining files to the `contributions` branch (`scripts/server_contrib/README.md`, "nightly maintenance window" + cron `0 1 * * *`). The laptop side is one existing recipe: `justfile` `contrib-merge` (fetch + merge + `merge_contrib_files.py`). The only genuinely new need is "run that recipe daily," which is a `systemd --user` timer around the existing command — no scp, no new filter, no scratch folder. git also gives atomic ref updates, deltas, and conflict detection for free.

**2. Blocker — the "processed-word filter" duplicates `contrib_reconcile.py` and, as scoped, is incomplete.**
The idea says "every word." Reconcile also drops *corrections* JSON and *flag lines*, using the union of `additions_added.json` and `corrections_added.json` (`scripts/server_contrib/contrib_reconcile.py:177-236`), plus reserved test ids via `reconcile_exception_lines`. A word-only filter brings back every rejected/processed correction and every merged flag line, daily. Fix: call the existing `uv run scripts/server_contrib/contrib_reconcile.py --project-root . --data-dir gui2/data` on the laptop instead of writing one.

**3. Blocker — log propagation is asymmetric on the scp route.**
Server reconcile only drops an entry after main holds its `(_source_key, _source_hash)` (`contrib_reconcile.py:195-201`). The git route gets the maintainer's logs to the server because "Backup & Quit commits `additions_added.json`... with the TSV backup" (README). Nothing pushes the laptop's logs to the server in the scp design, so the server's copy keeps re-delivering processed entries and the laptop filter becomes the *sole* guard. Correct, but only if it is the real reconcile — see #2. Use git and this asymmetry disappears.

**4. Major — a blind scp into `gui2/data` is invisible to a running editor.**
`AdditionsManager.load_additions()` runs once in `__init__` (`gui2/additions_manager.py:20-22`). If the copy lands while the editor is open, the new `additions_*.json` are not visible until a restart, and a later editor save can overwrite them. The guard is load-bearing for more than file-safety. Also scp of N files is not transactional: a flaky link can copy some files and not others, then `merge_contrib_files.py` runs on a mixed set (git fetch/`--force-with-lease` is per-ref atomic).

**5. Major — "skip if editor open" silently loses the whole day.**
A daily `OnCalendar` unit that fires, sees the editor open, and exits will not re-fire when the editor closes; next attempt is 08:00 tomorrow. The explicit `just contrib-merge` has no such silent miss. If kept, use `Persistent=true` plus a retry/lock, or write to a spool and drain on editor close.

**6. Major — new auth surface.**
The existing route never has the laptop SSH the server. The server deploy key is deliberately "for pushes only" (README); this adds a laptop→server key, pointing at a host that may not be `config.ini [dpdict_server]` (that is dpdict.net). Key placement/rotation and host discovery are unaddressed. Prefer the GitHub route.

**7. Nit — laptop-off / concurrency.**
08:00 timer needs `Persistent=true` and a single-flight lock; otherwise a suspended laptop misses the run, and two fires overlap.

Cost/quota: volume is trivial — per-contributor files are small, and git packs the same set more efficiently than N scp files. No peak-load or token concern. The real cost is duplicated logic and a non-atomic transfer, not bandwidth.

### R2: UX + Migration
## Findings (Goldfish review, read-only)

**BLOCKER 1 — "skip if editor is open" has no backing mechanism; a copy during an open editor is silently lost.**
`gui2/additions_manager.py:20` loads all `additions_*.json` once in `__init__`; `gui2/additions_manager.py:66-73` `_save_dict` rewrites the *entire in-memory dict* to disk. `gui2/main.py`'s `_session_lock`/`ALREADY_OPEN_MESSAGE` is in-process only — there is no pidfile or on-disk lock. Scenario: laptop resumes at 08:00 with gui2 already open (or `Persistent=true` fires at login); the job overwrites files on disk, then the editor's next save wipes every freshly pulled word. Fix: the editor must hold a real `fcntl` lock file that the job tests; abort loudly if held. Process-name grep is not enough.

**BLOCKER 2 — Two routes write the same git-tracked file.**
`justfile:contrib-merge` still runs `git fetch/merge origin/contributions` nightly. `additions_*.json` is **not** gitignored (`gui2/data/checked_*.csv`, `manual_corrections_*.tsv`, `variant_readings_*.tsv`, `spelling_mistakes_*.tsv` **are**, per `.gitignore`). Copying server `additions_<user>.json` over `gui2/data/additions_<user>.json` dirties the tree and races the branch, which will re-introduce entries the laptop already filtered/removed. Fix: retire the branch push, or land direct copies in an ignored dir (e.g. `gui2/data/contrib_incoming/`) that gui2 reads, never overwriting tracked files. (Brief claim 7 is partly wrong: the flag files are local-ignored, not tracked.)

**BLOCKER 3 — No rollback for shared-file merges.**
`scripts/server_contrib/merge_contrib_files.py:merge_all` appends in place to `user_dictionary.txt`, `checked.csv`, `manual_corrections.tsv`, `variant_readings.tsv`, `spelling_mistakes.tsv`, `db_tests_columns.tsv`, and rewrites `contrib_lines_merged.json`. The git route leaves a merge commit to reset; direct mutation leaves nothing. A bad run is irreversible. Fix: copy the six shared files aside (dated) before merging, or keep everything under git; document `just contrib-undo`.

**MAJOR 4 — Failure is invisible and non-actionable.**
A `systemd --user` timer that fails is only visible via `journalctl --user`. Non-interactive `ssh` gets no TTY, no `SSH_AUTH_SOCK`/keyring in the user-manager environment, and will hang/fail on first-connect host-key prompts. `merge_contrib_files.py:main` prints `pr.red("no contributor files found")` and returns 1 — indistinguishable from a real error. Fix: `BatchMode=yes`, explicit `IdentityFile`+`known_hosts` in the unit, and a status file / desktop notification the maintainer actually sees, naming the exact retry command.

**MAJOR 5 — First run resurrects old entries.**
`scripts/server_contrib/contrib_reconcile.py:reconcile_entries` drops a word only when `(_source_key, _source_hash)` exists in `additions_added.json`. Entries processed before that logging existed have no hash, so a plain copy brings them back. Compounding: under the direct route main is never pushed, so the server's own nightly reconcile (`contrib_reconcile.py`) never advances and the laptop filter is the only gate. Fix: dry-run against real data first; snapshot the already-processed baseline and log every filtered key.

**MAJOR 6 — Partial copy corrupts local JSON silently.**
`scripts/server_contrib/merge_contrib_files.py:merge_appended_lines` and the copy step have no atomicity on the destination; an interrupted rsync leaves a mixed file, and `gui2/additions_manager.py:38` silently `continue`s on `JSONDecodeError`, dropping a contributor's words with no message. Fix: rsync to scratch, validate JSON, then atomic replace; never swallow decode errors.

**NIT 7** — Reserved-id test exceptions, CRLF/header preservation, and per-kind merge functions carry real complexity against "keep it simple"; each is a failure mode the maintainer must learn. Consider shipping additions+corrections first, flags later.

**NIT 8** — Brief claim 6 (`[epitaka_server] ssh`) is unverifiable (secrets) and inconsistent with the `[dpdict_server]` user+host precedent in `justfile:_dpdict-login`. Confirm the section/option before coding.

Verified accurate: `DELIVERED_KINDS` (`tools/contrib_entry.py:12-21`), the nightly-window/reconcile design (`contrib_reconcile.py`), and `merge_all` not touching additions/corrections JSON.

### R3: Observability + Tech debt
## Findings

**Blocker — processed-state never reaches the server; the local filter duplicates server logic.** `add_contributor.sh`/`maintenance_window.py` show the server reconciles against main's `additions_added.json` (`contrib_reconcile.py:load_processed`, `reconcile_entries`). The maintainer processes words on the **laptop**, so the server file is never cleared without a git push — which the constraints forbid. The proposed laptop filter therefore re-implements `reconcile_entries` (key+`entry_hash`) in a second place (`gui2/additions_manager.py:save_processed_addition/_remove_key_from_file` vs `scripts/server_contrib/contrib_reconcile.py`). Two implementations of "already processed" **will drift**; an edited word gets a new hash and silently returns. Fix: import `tools.contrib_entry.entry_hash` and share one processed-log loader/function; accept that the server file only ever shrinks by local filter.

**Blocker — non-interactive ssh will hang or fail silently.** `[epitaka_server] ssh` has no reader; the only existing pattern is `justfile:_dpdict-login` (handles `None`, exits 1). A `systemd --user` timer has no agent/known_hosts in the same context. A passphrase key or unaccepted host key blocks the 08:00 run with no surface — the maintainer sees nothing. Fix: explicit `BatchMode=yes`, `StrictHostKeyChecking=accept-new`, and a recorded outcome.

**Major — no status surface for the skipped/no-op/failed cases.** `maintenance_window.py:_write_status` already writes a small `status.txt` (outcome, problems count, commit) precisely so a non-technical operator can read the result. The brief describes three silent paths: laptop off at 08:00 (`OnCalendar` without `Persistent=true`), editor open (skip), and ssh failure. All three are indistinguishable from success. Fix: mirror `_write_status`; a status file with `outcome: skipped|ok|failed`, contributor file counts, and problems. Without it, triage a month later is impossible.

**Major — torn flag files poison a permanent log.** `merge_contrib_files.py:merge_all` appends every handled line to `contrib_lines_merged.json`, and `contrib_reconcile.py:reconcile_lines` drops by exact match. The brief admits flag files' atomicity "was not checked" (`additions_manager.py` writes JSON swap, but `checked`/`manual_corrections` are appended by gui2 writers). Copying mid-write yields a truncated line; once logged it is permanently merged and the real line is suppressed forever. Fix: write-then-swap for every flag writer before relying on a daily copy, or hash-verify each file.

**Major — copying server files over git-tracked local files creates a permanent dirty tree.** `gui2/data/additions_alice.json`, `checked_alice.csv`, `manual_corrections_alice.tsv` are tracked (brief fact 7). The daily copy modifies tracked files with no git path to commit them, so `git status` is always dirty and the repo's automated "data update" habit (AGENTS.md) can sweep half-merged state. Fix: copy into an untracked staging dir and merge from there, or document the files as generated.

**Major — working-directory and path coupling.** `merge_contrib_files.py:main` defaults `data_dir=gui2/data` and `Gui2Paths()` resolves against cwd; `SharedFiles.default()` likewise. A systemd unit without `WorkingDirectory=<repo root>` fails (AGENTS.md: `ProjectPaths` uses cwd). Fix: require absolute `--data-dir`/repo root and fail loudly otherwise.

**Nit — silent collision on many contributors.** `additions_manager.py:load_additions` logs duplicate keys only with `pr.red`, non-persisted; with many contributors the losing entry vanishes with no durable record. Log collisions to the status file.

**Nit — skip-on-open detection is unspecified** and has no timeout; a stale lock would skip forever.

Priority: fix the ssh/status observability pair first, then unify the processed-log logic.

### R4: Security
**Blocker — test-exception injection into main's integrity suite.** `scripts/server_contrib/merge_contrib_files.py:191,200`. Only ids `>= CONTRIB_ID_BASE` (10,000,000) are dropped; any other digit is appended to the named test and saved. A hostile `db_test_exceptions_x.tsv` line `<real_test>\t<real id>` silences a db_tests check for an existing entry, unattended. Fix: merge only ids held by that contributor's own additions (mirror the `held_ids` cross-check at `scripts/server_contrib/contrib_reconcile.py:150-151`); reject all others; run db_tests after merge.

**Blocker — symlinks read/write outside scratch.** With `rsync -a`/`scp` defaults, a server-planted `additions_x.json -> /home/<user>/.ssh/id_rsa` (or `/etc/passwd`) is copied as a symlink, then `json.load`/`_lines` follows it: secrets leak into `user_dictionary.txt`/exports, and a write-back path can clobber the target. Fix: `rsync --no-links`, never `-L`/`--copy-links`; after copy require `not p.is_symlink()` and `stat.S_ISREG`; per-run scratch dir mode 0700.

**Blocker — SSH trust and key scope.** Requirement: `ssh/rsync -o StrictHostKeyChecking=yes -o UserKnownHostsFile=<pinned-file> -o BatchMode=yes -o IdentitiesOnly=yes -o ForwardAgent=no -o PermitLocalCommand=no`. Server `authorized_keys` entry with `from=`, `restrict`, and a forced `command="rsync --server --sender ..."` (read-only). `accept-new` — the usual unattended workaround when the address changes — silently trusts a rekeyed/hijacked server and redirects the pull to hostile data. The key is root-over-ssh: a compromised server can rewrite `authorized_keys`, so a dedicated restricted key limits reverse pivoting, and agent forwarding must be off.

**Blocker — server-chosen names and paths.** `tools/contrib_entry.py:delivered_files` globs by pattern with no registered-contributor check; a fake or duplicated user name spoofs attribution and can collide with another contributor's log key (`additions_1.json` masquerades as primary). Fix: validate every name with an anchored regex (`^[a-z_]+_[a-z][a-z0-9_]{0,31}\.(json|csv|tsv|txt)$`), keep only names for known contributors, and never interpolate a server-supplied name into a remote path or shell.

**Major — hostile lines overwrite shared dictionary data.** `merge_contrib_files.py:160-174` (`merge_two_column`) replaces an existing variant/spelling value in place for any contributed key; `merge_appended_lines`/`merge_user_dictionary` append arbitrary lines to `checked.csv`, `manual_corrections.tsv`, and `user_dictionary.txt`. A hostile server can silently rewrite the deconstructor, spellchecker and dictionary. Fix: per-line validation (allowed charset, column count, max length, reject C0 controls), and stage changes for review instead of auto-overwriting shared files.

**Major — huge/deep JSON DoS.** `gui2/additions_manager.py:load_additions` and `contrib_reconcile.py:load_json_dict` `json.load` the whole file with no cap. A multi-GB file or deeply nested JSON exhausts memory or raises `RecursionError`, aborting the unattended job and the editor. Fix: `stat` a size cap and entry/depth cap before parsing; quarantine oversized files.

**Major — dictionary fields unsanitised (stored XSS).** `additions_manager.load_additions` takes every field verbatim; `gui2/dpd_fields_functions.make_dpd_headword_from_dict` writes them to `DpdHeadword` and exports render to HTML. Fix: strip C0 controls, reject raw `<`/`&`, cap lengths, or prove exporter escaping.

**Major — scheduled-job integrity.** Run as the maintainer with an absolute `ExecStart` to a script no other local user can write; fix `PATH`/cwd; keep the key path/passphrase out of logs and `status.txt`; and never invoke `git` (the contributions branch still exists, claim 7 — a merge would import attacker-controlled tracked files).

## Disposition table

How checked: "code" = I read the cited lines; "cmd" = I ran a read-only command; "—" = judgement.

| ID | Finding | Sev | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| R1.1 | The feature exists: a timer around `just contrib-merge` | Blocker | Escalate | code: justfile:300 is manual, not nightly; kamma/archive/20261101_contrib_6 spec line 336 records the dirty-tree friction of that route | Owner decision Q1 |
| R1.2 | Reuse `contrib_reconcile.py`, do not write a filter | Blocker | Accept | code: `reconcile_all(project_root, data_dir)` and its CLI do exactly this, also for corrections, flag lines, exceptions | spec: design |
| R1.3 | Processed state never reaches the server on this route | Blocker | Accept as text, claim rejected | code: Backup & Quit commits the logs (README:157, global_tab_view.py:34); the server learns when main is pushed. Not forbidden by the owner's rule | spec: assumptions |
| R1.4 | Copy under an open editor is invisible and can be overwritten | Major | Accept | code: additions_manager.py:20-22 loads once | spec: skip rule, checked twice |
| R1.5 | "Skip if editor open" loses the day | Major | Accept | — | spec: retry window + once-a-day marker |
| R1.6 | New laptop-to-server auth | Major | Accept (see R4.3) | cmd: `[epitaka_server] ssh` equals the ssh alias's user@host; no code reads it | spec: security |
| R1.7 | Laptop off / overlap | Nit | Accept | — | spec: Persistent + lock |
| R1.cost | Cost and volume | — | No issue | cmd: alice's file is 13 KB | none |
| R2.1 | "Skip if open" has no backing mechanism | Blocker | Accept in part | code: no on-disk lock. Reject a new lock inside the editor (over-built) | spec: process check before and again before the final copy |
| R2.2 | Two routes write the same tracked files | Blocker | Escalate (same fork as R1.1) | cmd: `additions_*.json`, `corrections_*.json`, `db_test_exceptions_*.tsv` are not ignored; `checked_*`, `manual_corrections_*`, `variant_*`, `spelling_*`, `user_dictionary_*` are ignored (brief claim 7 was partly wrong: some are tracked only because they were force-added). Its "ignored folder the editor reads" fix is rejected (changes the editor) | Owner decision Q1 |
| R2.3 | No rollback for shared-file merges | Blocker | Reject | cmd: all 7 shared files are tracked in git, so `git diff` and a restore by file name undo a bad run | spec: "how to undo" note |
| R2.4 | Failure is invisible | Major | Accept | — | spec: status file + notification |
| R2.5 | First run resurrects old entries | Major | Accept as a dry run | cmd: 39 of 43 rows in `additions_added.json` and 525 of 525 in `corrections_added.json` have no hash. These are from earlier contributors whose files are not on the server. Its claim that the server never advances is rejected (main is pushed by Backup & Quit) | plan: dry run on real files |
| R2.6 | Partial copy corrupts local JSON | Major | Accept | code: additions_manager.py:38 swallows a bad file silently (existing) | spec: scratch, check, then swap |
| R2.7 | Shared-file merge is complex; ship additions first | Nit | Reject | — the merge script exists and is reused unchanged | none |
| R2.8 | `[epitaka_server] ssh` unverifiable | Nit | Accept, resolved | cmd: equals user@hostname of the ssh alias | spec: assumptions |
| R3.1 | Local filter duplicates server logic | Blocker | Accept | same as R1.2 | spec: design |
| R3.2 | Unattended ssh hangs or fails | Blocker | Accept; its fix `accept-new` rejected | see R4.3: pinned host key | spec: security |
| R3.3 | No status surface | Major | Accept | code: maintenance_window.py `_write_status` is the pattern | spec: status file |
| R3.4 | Torn flag files poison the permanent log | Major | Accept | code: `_read_lines` treats a last line with no newline as a line | spec: copy flag files only if they end with a newline |
| R3.5 | Copy dirties the tracked tree for ever | Major | Reject | code: Backup & Quit commits data (README:157); expected state, same as the old route | spec: note |
| R3.6 | Working folder and path coupling | Major | Accept | code: `Gui2Paths` uses the working folder; tonight's cron failure was a missing `uv` path | spec: unit sets folder and path |
| R3.7 | Duplicate keys across contributors | Nit | Reject | code: keys start with the user name (additions_manager.py:83) | none |
| R3.8 | Stale lock skips for ever | Nit | Reject | — there is no lock file | none |
| R4.1 | Hostile test-exception line silences a check | Blocker | Accept | code: merge_contrib_files.py:183-208 adds any non-reserved id for an existing test | spec: drop non-reserved ids from pulled exception files |
| R4.2 | Symlinks leak or clobber files | Blocker | Accept | rsync behaviour: `-a` keeps links | spec: `--no-links`, regular files only |
| R4.3 | SSH trust and key scope | Blocker | Accept; key scope escalated | cmd: `rrsync` is installed on the server; its authorized_keys has 1 key | spec: strict host key; Owner decision Q2 |
| R4.4 | Server-chosen names | Blocker | Accept in part | code: delivered_files globs without a name check. A registered-contributor list is rejected (over-built) | spec: anchored name pattern |
| R4.5 | Hostile lines overwrite shared data | Major | Accept in part | code: merge_two_column replaces values. Staging for review is rejected; shared files are tracked so `git diff` shows it | spec: line checks + printed summary |
| R4.6 | Huge or deep JSON | Major | Accept | code: `json.load` has no cap | spec: size cap, count cap |
| R4.7 | Dictionary fields are unsanitised (XSS) | Major | Reject for this thread | — existing flow: the maintainer reviews every word in the editor | spec: not included |
| R4.8 | Scheduled-job integrity | Major | Accept | — | spec: absolute paths, no git, no secrets in logs |
