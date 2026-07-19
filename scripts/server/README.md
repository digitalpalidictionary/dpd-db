# Contributor web server tooling

Server-side scripts for the hosted gui2 **contributor web server** (issue #215,
round 2 — the zero-install web version of gui2 for non-technical contributors).
Each contributor gets one gui2 web instance; their work writes to a shared
scratch `dpd.db` **and** to per-user JSON files that are the authoritative
record. A nightly maintenance window pushes those JSONs up, and — only when safe
— rebuilds the scratch db from `main`.

> **Not part of this system:** `update-dpd.sh` is the deploy script for the
> separate **dpdict.net webapp** server (downloads the release db, runs
> uvicorn). It is unrelated to the contributor server below.

See also: `config_server.md` (the lean rebuild — kept/dropped step rationale),
`spec.md`/`plan.md` in `kamma/threads/20260719_contributor_web_server/`.

## The nightly maintenance window

`maintenance_window.py` is the orchestrator. It composes the other scripts:

```
stop instances
  → contrib_push        (per-user JSONs → contributions branch)
  → pin origin/main     (fetch once, git rev-parse — one commit for the whole run)
  → absorption_check    (is every contributor JSON in main empty? i.e. all absorbed)
     ├─ NO  → SKIP the rebuild, keep serving yesterday's db (a NORMAL outcome)
     └─ YES → capture rollback (db + pre-pull HEAD + JSONs/snapshots)
              → pull the pinned commit + submodules
              → db_rebuild_from_tsv.py
              → generate_components_server.py   (LEAN gui2-only rebuild)
              → health check (headword/lookup row-count bounds)
              → contrib_reconcile               (drop absorbed keys, keep local edits)
              → re-apply WAL
              on ANY failure: restore EVERYTHING, log ERROR
  → start instances (always)
```

Every run logs to `logs/maintenance_YYYYMMDD.log`.

### Run it

Production (cron on the server):

```bash
uv run scripts/server/maintenance_window.py \
    --instance dpd-gui@alice --instance dpd-gui@bob
```

Local dry-run (no systemd, logic only — safe to run against a scratch copy):

```bash
uv run scripts/server/maintenance_window.py --no-systemd --no-push \
    --project-root /path/to/scratch/repo
```

Key flags: `--no-systemd` (log instead of `systemctl`), `--no-push` (skip the
git push), `--instance <unit>` (repeatable), `--db-path`, `--data-dir`,
`--snapshot-dir`, `--log-dir`, `--remote`, `--branch`.

## The pieces (each is a pure core + thin CLI; unit-tested in `tests/scripts/server/`)

| Script | Does | Run standalone |
|---|---|---|
| `contrib_push.py` | Stages ONLY `gui2/data/{additions,corrections}_*.json` by explicit path, commits on the `contributions` branch, pushes, and refreshes `last_pushed/` snapshots. No-op when nothing changed. | `uv run scripts/server/contrib_push.py` |
| `absorption_check.py` | The wipe invariant: exits 0 (rebuild allowed) only if every contributor work file in `origin/main` is empty/absent; exits 1 and lists blockers otherwise. `*_added` review files are ignored. | `uv run scripts/server/absorption_check.py` |
| `contrib_reconcile.py` | Snapshot key-level merge: `final = local − (last_pushed − main)`, but KEEPS a key the maintainer processed if it was re-edited locally since the push. Refreshes snapshots. | `uv run scripts/server/contrib_reconcile.py` |
| `maintenance_window.py` | Orchestrator (above). | see Run it |
| `generate_components_server.py` | LEAN rebuild — only the `generate_components.py` steps that populate tables/columns gui2 reads. No pytest. See `config_server.md`. | `uv run scripts/server/generate_components_server.py` |
| `config_server.template` | Server `config.ini` template — secrets are `<FILL IN>` placeholders; audio/anki/exporter output OFF; db_rebuild + deconstructor ON. Copy to `./config.ini` on the server; NEVER commit the result. | copy to `config.ini` |

## Snapshots (`last_pushed/`)

`contrib_push` writes a snapshot of each contributor file after pushing;
`contrib_reconcile` reads those snapshots to tell "processed upstream" from
"edited locally since the push". Default location `gui2/data/last_pushed/`
(override with `--snapshot-dir`). These are server-local state — do not commit
them.

## Common defaults

All scripts default to `--project-root .`, data dir `gui2/data`, snapshot dir
`<data>/last_pushed`, remote `origin`. The reconcile/absorption default ref is
`origin/main`; the maintenance window pins one `origin/main` commit up front and
uses it for both the absorption check and the reconcile so it never rebuilds a
moving target.
