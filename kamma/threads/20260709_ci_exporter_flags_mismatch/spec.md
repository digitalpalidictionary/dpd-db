# Spec: ci_exporter_flags_mismatch (placeholder — to be filled in)

## GitHub issue
(none yet)

## Overview
The `github_release` config profile (`tools/configger.py`) switches on three exporters — `make_tbw`, `make_sutta_central`, `make_tpr` — but the GitHub workflows only partially match what those flags promise. Audit and reconcile the flags, the workflows, and the submodule push loop so each flag is either genuinely consumed in CI or removed from the profile.

## Current state (from the 2026-07-09 build audit)
- The same profile is applied by BOTH `draft_release.yml` and `submodules_update.yml` (via `scripts/build/config_github_release.py` → `config_apply_profile("github_release")`).
- `make_tbw` — **genuinely used**: `submodules_update.yml` runs `exporter/tbw/tbw_exporter.py` and pushes its output to the `resources/fdg_dpd` (dictPlugin) and `resources/bw2` (BW2) submodules. Keep.
- `make_sutta_central` — **half-wired**: `exporter/sutta_central/sutta_central_exporter.py` writes `pli2en_dpd.json` into `resources/sc-data/dictionaries/simple/en/`, and `submodules_update.yml`'s push loop includes `resources/sc-data` — but **no workflow ever runs the exporter**, so the sc-data leg of the loop always commits nothing ("No changes to commit"). Decide: (a) add a "Run SuttaCentral Exporter" step to `submodules_update.yml` before the push loop, or (b) sc-data updates are manual by intention → remove the flag from the profile and drop sc-data from the push loop.
- `make_tpr` — **unused in CI**: no workflow runs `exporter/tpr/tpr_exporter.py` or touches `resources/tpr_downloads`. TPR updates happen only in local `makedict-all` builds, which use a different profile. Decide: remove from the `github_release` profile, or wire up a CI step.
- `draft_release.yml` itself runs none of the three exporters; it only inherits the flags because it shares the profile.

## Open decisions (user to fill in)
1. sc-data: auto-update in CI (add exporter step) vs manual (remove flag + push-loop entry) vs leave as-is?
2. make_tpr: remove from profile vs add CI step?
3. Should `draft_release.yml` and `submodules_update.yml` keep sharing one profile, or should each apply only the flags it consumes (e.g. split `github_release` into two profiles)?

## Constraints
- `submodules_update.yml` pushes to third-party upstream repos (dictPlugin, BW2, sc-data) — test any change against forks or with push disabled first.
- Remember: `workflow_dispatch` workflows only run from the default branch — prove changes in isolation first (see kamma lessons).

## How we'll know it's done
- Every flag set by the `github_release` profile is consumed by at least one CI step, or has been removed.
- The submodule push loop only lists submodules that a preceding CI step actually writes to.
- One clean run of `submodules_update.yml` shows no "No changes to commit" legs caused by never-run exporters.

## What's not included
- No changes to the exporters themselves; wiring/config only.
