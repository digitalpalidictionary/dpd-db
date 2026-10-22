# Spec: ci_exporter_flags_mismatch

## GitHub issue
#272 (https://github.com/digitalpalidictionary/dpd-db/issues/272)

## Overview
The `github_release` config profile (`tools/configger.py`) switches on three
exporters — `make_tbw`, `make_sutta_central`, `make_tpr` — but `draft_release.yml`
runs none of them, and the standalone `submodules_update.yml` (which runs only TBW)
is never used. Fold all submodule-producing exporters and the submodule push into
`draft_release.yml` as a final, optional stage, then delete `submodules_update.yml`.

## Decisions (user)
1. **Fold into draft_release.** One build produces the db *and* the submodule
   outputs; no second full CI build. `submodules_update.yml` is deleted.
2. **Four submodules to update** (the ones the user currently pushes manually).
   The upstream is the `url` in `.gitmodules`; the workflow reads it from the
   checkout and does not repeat it.
   | Submodule path | Upstream (`.gitmodules`) | Branch | Produced by | What gets staged |
   |---|---|---|---|---|
   | `resources/fdg_dpd` (Dhamma Gift plugin) | dhammagift/dictPlugin | `main` | `exporter/tbw/tbw_exporter.py` | everything (`.`) |
   | `resources/bw2` (The Buddha's Words) | thebuddhaswords/BW2 | `main` | `exporter/tbw/tbw_exporter.py` | everything (`.`) |
   | `resources/sc-data` (SuttaCentral data) | digitalpalidictionary/sc-data | `main` | `exporter/sutta_central/sutta_central_exporter.py` | **only** `dictionaries/simple/en/pli2en_dpd.json` |
   | `resources/tpr_downloads` (Tipitaka Pali Reader downloads) | bksubhuti/tpr_downloads | **`master`** | `exporter/tpr/tpr_exporter.py` | everything (`.`) |
   `tbw_exporter.py` is one script with one on/off flag (`make_tbw`). It writes both
   the Buddha's Words and the Dhamma Gift files, so those two legs share one
   exporter step and cannot be switched on separately.
   Default branches read with `gh api repos/<repo> --jq .default_branch` on 2026-10-22.
   Fetching or pushing `main` for `tpr_downloads` would fail.
3. **A switch is required.** When testing, the user often does NOT want submodule
   pushes. Since `draft_release.yml` is `workflow_dispatch`-only, add a dispatch
   boolean input `push_submodules` (default **false**). When false, the exporter
   steps AND the push steps are skipped (`if:` guards) — a test release never
   touches upstream repos.
4. **Uposatha gate (user, 2026-10-22).** All four submodule updates run only on an
   uposatha day. A workflow step asks `tools/uposatha_day.py` whether today is an
   uposatha day (see Implementation shape, step 0) and stores the result as a
   step output. Every new step needs `push_submodules` true AND (uposatha OR
   `push_dry_run` true). The dry-run bypass lets the proof run happen on any day.
   A real push on a non-uposatha day is not possible.

## Current state (from the 2026-07-09 build audit, re-verified 2026-10-22)
- `draft_release.yml` already checks out `main` with `submodules: recursive`,
  `fetch-depth: 1` and the `GH_PAT` token. `actions/checkout` also writes that
  token into each submodule's git config, so pushing from a submodule works.
- `draft_release.yml` runs none of the three exporters today.
- `submodules_update.yml` runs only the TBW exporter, its push loop includes
  `sc-data` (always a "No changes to commit" leg), has no `tpr_downloads` entry,
  and does its own full db rebuild. The user never uses it.
- **Old workflow order matters.** It reset every submodule to `origin/main`
  BEFORE the build and exporter, then did a plain `git pull` before pushing. The
  reset must stay before the exporters. A reset after them wipes their output.
- **sc-data trap.** `draft_release.yml` runs `rm -rf resources/sc-data/html_text/*`
  to save disk. The sc-data repo tracks 70,438 files under `html_text` (of
  112,287 in all). `git add .` there would stage and push about 70k deletions.
  Only the one exporter output file may be staged in sc-data. Do not run
  `git reset --hard` there either: it would restore the 70k files and use the
  disk the delete was meant to save.
- **The TPR exporter has its own uposatha gate.** `tpr_exporter.py` exits early
  unless today is an uposatha day (`UposathaManger.uposatha_today()`) or
  `[tpr] make_beta` is `yes`. The profile does not set `make_beta` (default `no`).
  With the workflow gate (decision 4), a real push always runs on an uposatha day,
  so the TPR leg writes files. A dry run on another day makes the TPR leg a no-op,
  and the push loop must skip it cleanly.
- **The check uses the runner's date.** `date.today()` on a GitHub runner is the
  UTC date. If the user dispatches early on the local morning of an uposatha day,
  UTC can still show the day before, and the gate stays closed. Dispatch after
  00:00 UTC. The existing uposatha steps in this workflow have the same limit.
- SuttaCentral exporter writes
  `resources/sc-data/dictionaries/simple/en/pli2en_dpd.json`
  (`sc_pli2en_dpd_json` in `tools/paths.py`).
- TPR exporter writes `release_zips/dpd.zip`, `dpd_beta.zip` and updates
  `download_source_files/download_list.json` / `download_list_2.json`.
- `draft_release.yml` hardcodes `ref: 'main'` and the upstream repo in checkout.
  A dispatch run from another branch uses that branch's workflow file but main's
  code. Workflow edits are testable this way. Exporter or script edits are not.

## Implementation shape
In `draft_release.yml`. Steps 0 to 3 are in `build-linux`. Step 4 is a new job.

0. **Gate step** (id `submodule_gate`) — new step after "Install dependencies",
   skipped when `push_submodules` is off. It writes `run=true` when `push_dry_run`
   is on, or the uposatha check prints `True`, else `run=false`. The check is
   `UposathaManger.uposatha_today()` run with `python -c` and its printed answer is
   read, because the command-line form of `tools/uposatha_day.py` exits 1 both for
   "not an uposatha" and for a crash. Any answer other than `True` or `False` writes
   an `::error::` line and no output, which skips all submodule steps. The step has
   `continue-on-error: true`. `build-linux` exposes the result as the job output
   `SUBMODULES_RUN`.
1. **Sync submodules** (id `sync_submodules`) — guarded by the gate, BEFORE the
   exporters. For each of the four paths: `git fetch --depth 1 origin <branch>`,
   then `git checkout -B <branch> origin/<branch>`. No `reset --hard`.
2. **Exporters** (ids `tbw`, `sc`, `tpr`) — after the db build, guarded by the
   gate and by the sync outcome being `success`: `Run TBW Exporter`,
   `Run SuttaCentral Exporter`, `Run TPR Exporter`.
3. **Collect** (id `collect_submodules`) — after the exporters. Per leg, if the
   sync and that leg's exporter succeeded: stage the paths in the table above,
   refuse the leg if anything staged is a deletion (a tarball cannot carry one),
   and pack the staged files into `submodule-out/<name>.tar.gz`. The step first
   writes `submodule-out/collect_done.txt`, so the artifact exists even when no
   leg has anything to push. A following step uploads `submodule-out/` as the
   artifact `submodule-output`.
4. **Push job** `push-submodules` — `needs: [build-linux, create-release]`, runs only
   when `SUBMODULES_RUN` is `true`, so only after the release exists. It checks out
   dpd-db without submodules, downloads the artifact, and for each leg that has a
   tarball: clones the submodule fresh (`--depth 1`, branch from the table, sc-data
   with a sparse checkout that leaves out `html_text`), unpacks the tarball, stages,
   commits `DPD lookup: update <date>`, and pushes `<branch>:<branch>`
   (`--dry-run` when `push_dry_run`). Auth uses the same header `actions/checkout`
   uses, built from `GH_PAT`, and masked. Submodule URLs come from `.gitmodules`.
   A leg with no tarball or nothing changed is skipped. If `collect_done.txt` is
   missing (upload or download failed), the push step fails with an `::error::`
   instead of reporting "nothing to push".

**A submodule problem must never fail the release.** Every new step in
`build-linux` has `continue-on-error: true`, because the macOS and release jobs
wait for `build-linux`. In the push job the checkout and the push step have it
too. Each failing leg writes an `::error::` or `::warning::` line, so the run page
shows it. In the exporter, collect and push stages each leg fails alone. The sync
is the one exception: it is a single loop, and a failure there skips every
exporter and pushes nothing, because the likely causes (network, token, branch
name) hit all four legs. If `build-macos` fails, `create-release` is skipped, and
so is the push job: nothing is pushed without a release.

Then delete `.github/workflows/submodules_update.yml`.

## Decision: push after the release (user, 2026-10-22)
The push is a separate final job that runs only after the release is created, so a
failed Mac or release job never leaves the submodules pushed without a release.
The exporter output moves between jobs as a tarball artifact. The earlier plan
(push as the last step of the Linux job) is dropped.

## Accepted risks
- **Stale tarball.** The collected files are whole-file copies built from the
  sync-time base. If someone edits the same file upstream between the build and the
  push job (hours), the push job's copy replaces that edit. This matters most for
  `download_list.json` in the third-party tpr_downloads repo. No force push is used,
  so history stays intact and the edit can be recovered from it.
- **Deletion guard covers all four repos.** The collect step refuses any leg that
  staged a deletion, not only sc-data. If an exporter ever legitimately removes a
  stale file (old zips in `tpr_downloads/release_zips` are the likeliest case), that
  leg fails with an `::error::` on every run. The fix then is a list of allowed
  deletions or a delete list in the tarball. The sc-data guard is never weakened.
- **The gate uses the runner's UTC date** (see Current state).

## Constraints
- The push targets include third-party upstreams (dhammagift, thebuddhaswords,
  bksubhuti). The first proof run must not push to them.
- `workflow_dispatch` inputs and runs: the workflow file must exist on the default
  branch, but a run can use the file from another branch.
- `mobile_release.yml` also applies the `github_release` profile but runs no
  submodule exporters. Acceptable: the `push_submodules` input, not the profile,
  decides execution. Do not split the profile.
- The `github_release` profile flags stay as-is.
- The submodule pointers in the dpd-db repo are NOT updated by this workflow
  (same as the old workflow and the user's manual routine). The user bumps them
  when they commit.

## Decision: proof method (user, 2026-10-22)
Add a second dispatch input `push_dry_run` (default false) that runs
`git push --dry-run`. No forks, and no change to any remote or upstream repo
before the real run. The dry run proves staging and commit. It does not prove the
PAT has write rights on the real upstreams.
The real test is the release on 2026-10-26 (release day). That run is the first
real push. The user runs it with `push_submodules: true` and checks each upstream.

## How we'll know it's done
- A dispatch run with `push_submodules: false` (the default) builds and
  publishes the draft release and runs none of the new steps, on any day.
- A dispatch run with `push_submodules: true` and the dry-run option shows, in
  the log, the exact files staged per submodule. In sc-data that is exactly one
  file and zero deletions.
- A real run with `push_submodules: true` on an uposatha day commits real changes
  to all four submodules, or cleanly no-ops a leg with nothing to commit.
- A run with `push_submodules: true` and `push_dry_run: false` on a non-uposatha
  day runs none of the new steps and no push job.
- Forcing a failure in any new step (for example a bad branch name in the sync
  step) leaves the release published and the run green.
- `submodules_update.yml` no longer exists.
- With the switch on, every exporter flag in the `github_release` profile is
  consumed by the draft release workflow.

## What's not included
- No changes to the exporters themselves; workflow wiring only.
- No changes to `mobile_release.yml` beyond what it already inherits.
- No update of the submodule pointers in the dpd-db repo.
