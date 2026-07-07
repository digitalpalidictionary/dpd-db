# Plan: Revert deconstructor parallel export (CI OOM)

## Tasks

- [x] 1. Restore serial export in `exporter/deconstructor/deconstructor_exporter.py`
      (file content back to `a8316ab6^`: serial `prepare_and_export_to_gd_mdict`,
      no `_export_worker`, no parallel-only imports)
      → verified: `git diff a8316ab6^ -- exporter/deconstructor/deconstructor_exporter.py` is empty
- [x] 2. Lint gate: ruff check passed, ruff format left file unchanged,
      pyright 0 errors
- [x] 3. Full `uv run pytest tests/`: 1229 passed, 16 deselected
