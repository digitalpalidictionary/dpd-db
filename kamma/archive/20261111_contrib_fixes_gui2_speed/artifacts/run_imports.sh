#!/bin/bash
# 6 runs per variant (1 warm-up + 5 measured), fresh process each.
cd "${DPD_DB_ROOT:-.}" || exit 1
for variant in start all; do
  for i in 1 2 3 4 5 6; do
    PYTHONPATH=. uv run python /tmp/dpd_20261111_scratch/time_imports.py "$variant"
  done
done
