# Plan: dpdict server pulls the docs site once a day

Spec: `kamma/threads/20261110_dpdict_docs_daily_pull/spec.md`

## Architecture Decisions
- **Cron, not a systemd timer.** The server user already has a crontab and
  has no passwordless sudo and no lingering, so a user timer would not run
  after logout. Cron needs neither.
- **One line, no script file.** The whole job is one `git pull`. A script
  would add a file to deploy and keep level for no gain.
- **`--ff-only -q` with the log appended.** A normal run writes nothing. An
  error leaves the served files untouched and leaves one entry in the log.
- **Installed by hand over ssh, recorded in the README.** The crontab is not
  in the repo, the same as the two `@reboot` lines. The README is the record
  for a new server.
- **The hand-run update paths stay.** Step 1 of `update-dpd.sh` and the
  server's `docs-update` recipe keep their current behaviour.

## Facts the executor needs
- Log in with `ssh "$(just _dpdict-login)"` from the repo root. Never print
  or write the host address into a committed file.
- The server user is not root. Clock is UTC. OS is Debian 12.
- Never touch `~/dpd-db-sbs`, port 8081, or the two `@reboot` cron lines.
- The cron line, exactly:
  `0 1 * * * git -C "$HOME/digitalpalidictionary.github.io" pull --ff-only -q >> "$HOME/logs/docs-pull.log" 2>&1`
- Make no edit to the working tree of dpd-db other than the README and this
  thread's files.

## Model Strategy
| Phase | Tier | Suggested model | Reason |
|---|---|---|---|
| 1 — Install and prove on the server | Pro | Opus | Edits a live server's crontab; must read each result and stop on a surprise. |
| 2 — README and next-day check | Fast | Sonnet | One doc section and two read-only checks. |

## Phase 1 — Install and prove on the server — *Pro*

- [x] 1.1 Record the "before" state. On the server run `crontab -l`,
  `command -v git`, `git -C ~/digitalpalidictionary.github.io rev-parse --short HEAD`.
  From the laptop, request the Paliverse integrations page on
  `docs.dpdict.net` (take its URL from `mkdocs.yaml` nav and
  `docs/integrations/paliverse.md`) with `curl -s -o /dev/null -w '%{http_code}'`.
  Paste all four results into this plan.
  → verify: crontab shows exactly two `@reboot` lines; git is in `/usr/bin`
  or `/bin`; the page returns 404 (this proves the site serves the stale
  clone). If the page returns 200, stop and tell the user: the spec's
  assumption about what the docs address serves is wrong.
  RESULT 2026-11-10: crontab holds the two `@reboot` lines (plus the stock
  comment lines, which the spec did not mention); git is `/usr/bin/git`;
  clone is at `311d8f5` and has no `integrations/paliverse` folder; the page
  `docs.dpdict.net/integrations/paliverse/` returns 404, an old page
  (`.../integrations/tpr/`) returns 200, and the same new page on
  `digitalpalidictionary.github.io` returns 200. Assumption confirmed.

- [x] 1.2 Run the pull command once the way cron runs it. On the server:
  `env -i HOME="$HOME" PATH=/usr/bin:/bin /bin/sh -c 'git -C "$HOME/digitalpalidictionary.github.io" pull --ff-only -q >> "$HOME/logs/docs-pull.log" 2>&1'; echo "exit $?"`
  → verify: prints `exit 0`; `docs-pull.log` is empty or absent of errors;
  the clone's short commit equals
  `gh api repos/digitalpalidictionary/digitalpalidictionary.github.io/commits/main --jq '.sha[0:7]'`;
  the Paliverse page now returns 200.
  RESULT 2026-11-10: `exit 0`; log 0 bytes; clone `287ac59` equals GitHub's
  `287ac59`; working tree clean; page returns 200 (first request 18 s, then
  about 2 s; the first request after the files changed was slow, one sample).

- [x] 1.3 Add the cron line, only if it is not there yet. On the server:
  `crontab -l | grep -qF 'digitalpalidictionary.github.io" pull' || (crontab -l; echo '<the cron line>') | crontab -`
  → verify: `crontab -l` shows three lines: the two old `@reboot` lines,
  character for character as recorded in 1.1, and the new line. Run 1.3 a
  second time and confirm the count is still three.
  RESULT 2026-11-10: first run "installed", second run "already installed";
  3 non-comment lines (two `@reboot` as in 1.1, plus the new line). The
  before/after backup file was overwritten by the second run, so the
  comparison with 1.1 was by eye; the temp backup was removed from the server.

- [x] 1.4 Phase check.
  → verify: `ps -eo args | grep "[u]vicorn"` on the server still shows both
  webapps (8080 and 8081) running, as before the phase.
  RESULT 2026-11-10: both uvicorn webapps run (8080 and 8081); the main site
  returns 200; no stray file left on the server.

## Phase 2 — README and next-day check — *Fast*

- [x] 2.1 Add a "Docs site" section to `scripts/server_dpdict/README.md`,
  at the end of the file (after "Mistakes to avoid", which belongs to "Code-only update"). Content: the docs address serves the clone of
  the pages repo; a cron line pulls it daily at 01:00 UTC; the exact line;
  the install command from 1.3; the log is `~/logs/docs-pull.log` and is
  empty when all is well; for an immediate update run the server's
  `docs-update` recipe. Write `~` paths only, no user name, no address.
  → verify: `rg -n "/home/|[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" scripts/server_dpdict/README.md`
  returns nothing; read the section against the crontab line from 1.3 and
  confirm they match character for character.
  RESULT 2026-11-10: the scan hit only two old lines (33, 34: `0.0.0.0` and
  `127.0.0.1`), none in the new section; the install line in the README
  matches the cron line exactly.

- [ ] 2.2 Next-day check, after 01:00 UTC on the day after 1.3. This does
  not block review or finalize. Record the result here when done.
  → verify: on the server, `grep CRON /var/log/syslog` or
  `journalctl -t CRON --since today` (whichever the user can read) shows the
  01:00 run; `docs-pull.log` holds no error; the clone's commit equals
  GitHub's latest.

- [x] 2.3 Phase check. (The user's rules forbid the agent running git, so the
  git status half is left to the user at commit time.)
  → verify: `ls scripts/server_dpdict/` shows no stray file.
  RESULT 2026-11-10: folder holds `README.md` and `update-dpd.sh` only.
