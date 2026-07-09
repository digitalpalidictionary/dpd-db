# Spec: Revert deconstructor parallel export (CI OOM)

## Problem

Draft Release run 28826476411 (`build-linux`) died with "The runner has
received a shutdown signal" 28s into the `exporting deconstructor
dictionaries in parallel` stage introduced by commit `a8316ab6`. The
parallel export pickles two halves plus one full extra copy of the
~861k-entry `dict_data` to three worker processes while the parent keeps
the original (~3× memory), and runs three memory-hungry writers
(2× pyglossary GD+slob, writemdict) concurrently. On the 16GB GitHub
runner this exceeds available memory and the OOM killer takes down the
runner VM. The last green run (May 31, `d91aa456`) predates the commit.

## Fix

Revert only the parallelization in
`exporter/deconstructor/deconstructor_exporter.py` — restore the serial
`prepare_and_export_to_gd_mdict`, delete `_export_worker`, and drop the
imports that existed only to support it (`os`, `shutil`, `sys`,
`tempfile`, `ProcessPoolExecutor`/`as_completed`, `glossary_v2`).

The pyglossary cache-race fix and fd-level output capture in
`_export_worker` exist only to make concurrent exports safe, so they go
with it. The kamma archive files added in the same commit are untouched.
No later commit modified this file, so restoring the file to its
`a8316ab6^` content is an exact, scoped revert.

## Out of scope

- Keeping the parallel path behind a CI/memory gate (rejected: two code
  paths to maintain for a ~26s local win).
- Any other change from commit `a8316ab6` or the `#157` series.
