# Spec: dpdict server pulls the docs site once a day

## Overview
The docs site is built by GitHub on every docs change and pushed to the
`digitalpalidictionary.github.io` repo. The dpdict server serves its own
clone of that repo, and nothing updates the clone automatically. This thread
adds one daily cron line on the server that pulls the clone.

## Current behaviour (verified 2026-11-10)
- `.github/workflows/static.yml` builds the site on any push to `main` that
  touches `docs/**` or `mkdocs.yaml`, and pushes the result to the
  `digitalpalidictionary.github.io` repo. (Read the workflow.)
- The server holds a clone at `~/digitalpalidictionary.github.io`, remote
  over https, clean working tree, 144 MB. (Read over ssh.)
- The clone only moves when someone runs `~/update-dpd.sh` (step 1) or the
  `docs-update` recipe in the server's own `~/justfile`. (Read both.)
- The clone was at the 2026-10-26 build. GitHub's latest build was
  2026-11-10. (Compared the two commits.)
- The server user's crontab holds two `@reboot` lines and nothing else
  (apart from the stock comment lines).
  There are no user timers. The user has no passwordless sudo. Server clock
  is UTC, OS is Debian 12. (Read over ssh.)

## What it should do
1. Add one line to the server user's crontab:
   `0 1 * * * git -C "$HOME/digitalpalidictionary.github.io" pull --ff-only -q >> "$HOME/logs/docs-pull.log" 2>&1`
   - 01:00 UTC, once a day. The owner chose once a day: docs changes are rare.
   - `--ff-only`: never merges, so a surprise local change stops the pull
     with an error and leaves the served files as they are.
   - `-q`: a normal run writes nothing. Only errors reach the log.
2. Add a short "Docs site" section to `scripts/server_dpdict/README.md`:
   what the cron line is, how to install it on a new server, where the log is.
3. Keep step 1 of `update-dpd.sh` and the server's `docs-update` recipe as
   they are. They still work for an immediate update by hand.

## Assumptions & uncertainties
- ASSUMED: `docs.dpdict.net` serves `~/digitalpalidictionary.github.io`
  directly. The only evidence is a comment in the server's justfile. The
  web server config was not readable. The plan checks this with a real page.
- ASSUMED: `~/logs` on the server is a fine place for the log. The folder
  exists.
- Cron errors are silent unless someone reads the log. Accepted: the worst
  case is the current behaviour (a stale copy).

## Constraints
- Never touch the second site (`~/dpd-db-sbs`, port 8081) or its cron line.
- Keep the two existing `@reboot` cron lines unchanged.
- No home path with a user name and no server address in committed files.

## How we'll know it's done
- `crontab -l` on the server shows three lines: the two old ones and the new one.
- After one manual run of the same command, the clone's commit equals
  GitHub's latest commit, and a page that exists only in a recent build
  (the Paliverse integrations page) loads from `docs.dpdict.net`.
- On the day after, the clone is still level with GitHub and the log holds
  no error.

## What's not included
- No instant update from GitHub, no webhook, no new secrets.
- No change to the GitHub workflow.
- No change to the server's own `~/justfile` (it is not in this repo).
- No failure alert.
