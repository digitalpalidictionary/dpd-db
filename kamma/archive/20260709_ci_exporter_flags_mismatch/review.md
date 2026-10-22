# Review: ci_exporter_flags_mismatch

Verdict: **PASSED** (2026-10-22), with the open items below.

Note: the formal `/kamma:3-review` command was not run. This record sums up the
review round done in the working session, at the user's request.

## Files changed
- `.github/workflows/draft_release.yml` (new inputs, gate, sync, three exporters, collect and upload steps, new `push-submodules` job)
- `.github/workflows/submodules_update.yml` (deleted)
- `kamma/threads/20260709_ci_exporter_flags_mismatch/spec.md`
- `kamma/threads/20260709_ci_exporter_flags_mismatch/plan.md`

## Reviewers
- Sonnet subagent (read-only, tested run blocks in scratch repos): no severe bug.
- CodeRabbit on the workflow folder: 0 findings. The run on the spec and plan was stopped by the user.
- GLM review (pasted by the user): approved, no code changes asked.

## Findings and fixes
- A missing artifact looked like success. Fixed: the collect step writes `collect_done.txt`, the push step fails if it is missing.
- A crash of the uposatha tool read as "not an uposatha day". Fixed: the gate reads the printed answer, anything but True/False gives an `::error::`.
- The gate step and the push job checkout lacked `continue-on-error`. Fixed.
- Spec said every leg fails alone, but the sync loop does not. Fixed in the spec: a sync failure stops all legs on purpose.
- Stale plan note about sparse checkout. Fixed.
- Own findings during build: tpr_downloads uses `master`, not `main`; `git add .` in sc-data would push about 70k deletions; a reset after the exporters would wipe their output. All fixed before the first run.
- Wrong review claims, checked and rejected: that `checkout -B` aborts in sc-data (tested, it does not); that `uposatha_today()` changes the counter (it does not); that the push job runs when the macOS job fails (it does not).
- Accepted risks, recorded in the spec: a stale tarball can overwrite a newer upstream edit; the deletion guard covers all four repos.

## Test evidence
- Local: the real `run` blocks, extracted from the YAML, against throwaway repos with fake upstreams. Dry run, real push, failed exporter, deleted file, unreachable upstream, nothing written, gate (stub tool) and missing artifact all behaved as intended.
- GitHub run 39776856545 (switches off, commit ce0683c0): green, all new steps and the push job skipped, draft release made.
- GitHub run 39777176226 (both switches on): green. Collect staged 3 files in fdg_dpd, 3 in bw2, 1 in sc-data (no deletion), none in tpr_downloads. The push job ran after the release and logged dry-run pushes. The four upstream repos were checked afterwards: no new commits.

## Open items (not proven by these runs)
- A real push with `GH_PAT` write access to the four upstreams.
- The TPR leg with real output (needs an uposatha day).
- Both are covered by the real run on 2026-10-26. If it fails, reference this thread.
- Each proof run left a draft release with the same tag; the user deletes the extra.
