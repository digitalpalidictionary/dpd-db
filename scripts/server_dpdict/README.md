# dpdict.net webapp server

The server runs the main webapp on port 8080 from `~/dpd-db`. A second site
(port 8081, from `~/dpd-db-sbs`) runs on the same machine. Never touch it here.

## Full update (code, databases, audio)

Run `just dpdict-push` on the laptop to copy `update-dpd.sh` to the server.
Then run `~/update-dpd.sh` on the server. It pulls the code, replaces the
databases, restarts the webapp and cleans up after itself.

## Code-only update (no rebuild)

Use this when only code changed. Skip it and do the full update if any of
these changed since the server's commit: `db/models.py`, `pyproject.toml`,
`uv.lock`, `.gitmodules`.

Check what changed first. On the laptop:

    git diff --stat <server commit> origin/main -- db/models.py pyproject.toml uv.lock .gitmodules

Then, on the server:

1. Pull. The server has local files git ignores, so use a fast-forward pull
   with no submodules: `git pull --ff-only --no-recurse-submodules`.
2. Add uv to the path. A plain ssh session does not have it:
   `export PATH=$HOME/.local/bin:$PATH`.
3. Check the new code compiles. Run `uv run python -m py_compile` on the
   changed webapp files. Do not restart if this fails.
4. Find the old process numbers: `ps -eo pid,args | grep "[u]vicorn exporter.webapp.main:app"`.
5. Stop it with `kill <pids>`. Run this as a separate command from step 4.
6. Start it. It must survive the end of the ssh session:
   `setsid nohup uv run uvicorn exporter.webapp.main:app --host 0.0.0.0 --port 8080 > logs/<timestamp>.uvicorn.log 2>&1 < /dev/null &`
7. Wait until `curl http://127.0.0.1:8080/` on the server returns 200. The
   site is offline from step 5 until then. Last time that took about 15 seconds.

## Mistakes to avoid

- Never use `pkill -f` or a `ps | grep | kill` in the same ssh command that
  also contains the start line. The pattern text is then inside the remote
  shell's own command line, so the shell matches itself and kills itself.
  On 2026-11-08 this stopped the old site and never started the new one.
  The site was offline for about a minute until the start was run again.
- Never run `uv` over ssh without the path in step 2.
- The full update script is not needed for code-only changes. It downloads
  both the main database and the audio database.

## Docs site

`docs.dpdict.net` serves the clone of the pages repo at
`~/digitalpalidictionary.github.io`. GitHub builds the site on every docs
change and pushes it to that repo. A cron line on the server pulls the clone
once a day at 01:00 UTC. The crontab is not in this repo, so install the line
by hand on a new server. Make the log folder first, because cron cannot
create it: `mkdir -p ~/logs`. Then run:

    crontab -l | grep -qF 'digitalpalidictionary.github.io" pull' || (crontab -l; echo '0 1 * * * git -C "$HOME/digitalpalidictionary.github.io" pull --ff-only -q >> "$HOME/logs/docs-pull.log" 2>&1') | crontab -

A normal run writes nothing. `~/logs/docs-pull.log` holds only errors. The pull
uses `--ff-only`, so a local change in the clone stops it and leaves the
served files as they were. For an immediate update, run the `docs-update`
recipe from the server's own `~/justfile`.
