## Overview
GitHub issue #239: When a worker process in the DPD exporter crashes, the main process
continues silently, producing incomplete output.

## GitHub Issue
#239

## What it should do
After joining each worker process, check its exit code. If any process exited with a
non-zero code, raise an error immediately so the parent process and any calling bash
script also fail.

## Assumptions & uncertainties
- Only one file is affected: `exporter/goldendict/export_dpd.py` (confirmed: the only
  place `p.join()` is used in the exporter).
- Option 1 (check exit codes) is the right approach — minimal, non-invasive, correct.
- The `_parse_batch_top_level` worker already prints its own traceback on crash, so no
  additional error message from the worker is needed — just propagate failure upward.

## Constraints
- No refactoring of the batching/pool logic (Option 2 is out of scope).
- No Manager.list() boilerplate (Option 3 is out of scope).

## How we'll know it's done
- After the join loop, if any `p.exitcode != 0`, a `RuntimeError` is raised.
- A test simulates a crashing worker and confirms the exit code behaviour.

## What's not included
- Pool-based refactor.
- Error collection across all batches.
