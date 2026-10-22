# Plan: ci_exporter_flags_mismatch

Issue: #272. The four projects: `fdg_dpd` = Dhamma Gift plugin, `bw2` = The
Buddha's Words, `sc-data` = SuttaCentral data, `tpr_downloads` = Tipitaka Pali
Reader downloads.

Revised 2026-10-22 after review (decisions in `spec.md` are
locked). Goal: fold the submodule-producing exporters and the push into
`draft_release.yml` behind a `push_submodules` dispatch switch, then delete
`submodules_update.yml`.

## Baseline
- [ ] `draft_release.yml` currently runs no exporters and pushes no submodules.
- [ ] `submodules_update.yml` exists, unused by the user, and will be deleted.

## Tasks
- [x] **1. Add dispatch inputs** to `draft_release.yml`:
  ```yaml
  on:
    workflow_dispatch:
      inputs:
        push_submodules:
          description: "Run exporters and push to fdg_dpd, bw2, sc-data, tpr_downloads"
          type: boolean
          required: false
          default: false
        push_dry_run:
          description: "With push_submodules: run git push --dry-run"
          type: boolean
          required: false
          default: false
  ```
  Reference in steps as `inputs.push_submodules` (not `github.event.inputs`).
- [x] **1b. Add one gate step** (id `submodule_gate`) after "Install dependencies":
  ```yaml
  - name: Check submodule gate
    id: submodule_gate
    if: inputs.push_submodules == true
    run: |
      if [ "${{ inputs.push_dry_run }}" = "true" ]; then
        echo "run=true" >> "$GITHUB_OUTPUT"
      else
        answer=$(uv run python -c "from tools.uposatha_day import UposathaManger; print(UposathaManger.uposatha_today())" | tail -n 1) || answer="crashed"
        # True -> run=true, False -> run=false, anything else -> ::error:: and exit 1
      fi
  ```
  The tool exits 0 on an uposatha day and 1 otherwise. The `if` form never fails
  the job. Tasks 2 to 4 use `if: steps.submodule_gate.outputs.run == 'true'`.
  When the switch is off, the gate step is skipped, its output is empty, and every
  later step is skipped. Same logic as the spec: switch on AND (uposatha OR dry run).
  Revised after review: the gate reads the printed answer of
  `UposathaManger.uposatha_today()`, not the exit code of the command-line form
  (a crash also exits 1). Any answer other than `True`/`False` gives an `::error::`
  and no output. The step has `continue-on-error: true`.
- [x] **2. Add the sync step** (id `sync_submodules`), guarded by the gate from
  task 1b, `continue-on-error: true`, BEFORE the exporters. For each of the four
  paths: `git fetch --depth 1 origin <branch> && git checkout -B <branch> origin/<branch>`.
  The branch is `main` for fdg_dpd, bw2 and sc-data, and **`master`** for
  tpr_downloads (see the spec table). Do NOT use `reset --hard` (it would restore
  sc-data's 70k `html_text` files).
- [x] **3. Add the exporter steps** (ids `tbw`, `sc`, `tpr`) after the db build and
  the existing exporters. Each: gate AND `steps.sync_submodules.outcome == 'success'`,
  `continue-on-error: true`.
  - `Run TBW Exporter` → `uv run python exporter/tbw/tbw_exporter.py`
  - `Run SuttaCentral Exporter` → `uv run python exporter/sutta_central/sutta_central_exporter.py`
  - `Run TPR Exporter` → `uv run python exporter/tpr/tpr_exporter.py`
- [x] **4. Add the collect step and upload** (ids `collect_submodules`; upload step
  after it), both gated, `continue-on-error: true`. Per leg, only if sync and that
  exporter succeeded: `git add` the stage path (`.` for fdg_dpd, bw2, tpr_downloads;
  `dictionaries/simple/en/pli2en_dpd.json` only for sc-data), refuse the leg on any
  `D` line, pack the staged files into `submodule-out/<name>.tar.gz`. Legs fail
  alone. Upload `submodule-out/` as artifact `submodule-output`
  (`if-no-files-found: ignore`). Add the job output `SUBMODULES_RUN`.
- [x] **5. Add the `push-submodules` job** (`needs: [build-linux, create-release]`,
  `if: needs.build-linux.outputs.SUBMODULES_RUN == 'true'`). Checkout without
  submodules, download the artifact, then per leg with a tarball: fresh `--depth 1`
  clone of the `.gitmodules` URL on the right branch (sc-data sparse, no
  `html_text`), unpack, `git add -- .`, commit, push (`--dry-run` when
  `push_dry_run`). Auth header from `GH_PAT`, masked. `continue-on-error: true`
  on the push step; each leg fails alone and exits 1 at the end.
- [x] **6. Validate** the workflow: YAML parses
  (`uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/draft_release.yml'))"`)
  and `actionlint` passes if installed. Re-read the final diff end to end.
  Done: YAML parses, `bash -n` passes on the new `run` blocks. `actionlint` is
  not installed here, so it was not run.
  Local shell test (2026-10-22, second round, for the collect step and push job):
  the real `run` blocks, extracted from the YAML, ran against throwaway repos with
  local fake upstreams (sc-data with deleted `html_text` files, tpr_downloads on
  `master`), the push job starting from an empty workspace. Results: all four legs
  pushed one commit each, the sc-data commit held only the one JSON file and
  upstream `html_text` stayed at 5 files; a dry run left all upstreams unchanged; a
  failed sc exporter skipped only sc-data; a deleted sc-data JSON failed only that
  leg in the collect step; an unreachable bw2 upstream failed only bw2, exit 1,
  others pushed; nothing written pushed nothing, exit 0.
  Not covered locally: the gate against the real uposatha tool, the dispatch
  switches, artifact upload and download, `GH_PAT` push auth, and job ordering.
- [x] **7. Proof run 1: switch off.** Dispatch Draft Release from the thread
  branch with the defaults. Confirm the release builds and none of the new steps
  run. Note: the run uses the branch's workflow file but main's code.
- [x] **8. Proof run 2: switch on, dry run.** Dispatch with `push_submodules: true`
  and `push_dry_run: true` (the dry-run bypass opens the gate on any day). Read the staged-file lists in the log. Confirm sc-data
  stages one file and zero deletions, and that tpr_downloads no-ops on a
  non-uposatha day. Never change a remote or touch an upstream repo in this
  thread. The dry run is the only proof before release day.
- [x] **9. Delete `submodules_update.yml`** once step 8 passes.
- [ ] **10. (open, outside this thread's finalize) Real test on release day, 2026-10-26.** That date is in the uposatha
  list, so the gate opens. The user dispatches after 00:00 UTC (the runner uses
  the UTC date) with `push_submodules: true` and `push_dry_run: false`. The user checks
  each upstream repo for the new commit. The thread stays open until then.

## Proof run results (2026-10-22, both on main at commit ce0683c0)
- **Run 1, switches off** (run 39776856545): green. Linux, macOS and release jobs
  succeeded, a draft release v0.4.20261022 was made. All seven new Linux steps and
  the push job were skipped.
- **Run 2, push_submodules and push_dry_run on** (run 39777176226): green. Gate,
  sync, three exporters, collect and upload all succeeded. Collect staged 3 files in
  fdg_dpd, 3 in bw2, exactly 1 in sc-data (`pli2en_dpd.json`, no `D` line), and
  nothing in tpr_downloads (not an uposatha day). The push job ran after the
  release, cloned fresh, and logged `main -> main` for fdg_dpd, bw2 and sc-data
  with `--dry-run`. A direct check of the four upstream repos afterwards showed
  their newest commits unchanged, so nothing was pushed.
- Side effect: each run made a draft release with the same tag. The user deletes
  the extra draft.
- Not proven by these runs: a real push with `GH_PAT` write access, and the TPR
  leg with real output. Both are covered only by the real run on 2026-10-26.
- Task 9 done: `submodules_update.yml` was deleted after run 2 passed.

## Notes / pitfalls
- The sync (task 2) must come before the exporters. A reset or checkout after
  them can overwrite their output.
- Every new step in `build-linux` has `continue-on-error: true`, so a submodule
  problem never fails the job the release depends on.
- `actions/checkout` fetches submodules shallow. The per-submodule fetch is what
  makes committing back possible. Do not simplify it away.
- `tpr_exporter.py` has its own uposatha gate. On a dry run held on another day
  its leg writes nothing. A no-op TPR leg is correct, not a failure.
- An earlier review said `checkout -B main origin/main` aborts in sc-data when
  upstream changed a deleted `html_text` file. A test in a throwaway repo (git
  2.43) did not abort. It restored only the files changed upstream, and the rest
  stayed deleted. So the build-job sync uses no sparse checkout. The push job does
  use one for sc-data, because it clones fresh and must not materialise 70k files.
  Single-file staging stays mandatory in the collect step, since the other deleted
  files still show as deletions there.
- The collect step writes `collect_done.txt` first. The push job treats a missing
  marker as an error, so a failed artifact upload or download is never silent.
- Reviews done 2026-10-22: a Sonnet subagent, CodeRabbit on the workflow (0
  findings; the run on the spec and plan was stopped by the user) and a GLM review.
  One GLM claim was wrong: the push job does not run when `build-macos` fails,
  because `create-release` needs it and is then skipped.
- Pitfall: the deletion guard applies to all four legs (see the spec, Accepted
  risks). Read an `::error::` about a deletion on a real run as the guard working.
- The exporter steps must come AFTER the db build completes. They read `dpd.db`.
- Keep the `github_release` profile unchanged (`tools/configger.py`).
- The submodule pointers in dpd-db are not bumped by CI.

## Not in this plan
- Any exporter code changes; `mobile_release.yml` changes.
