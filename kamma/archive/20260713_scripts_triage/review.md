# Review: scripts/ triage & refresh

**Thread:** 20260713_scripts_triage
**Date:** 2026-10-23
**Verdict:** PASSED

## Files Changed (this session, 2026-10-23)

- `scripts/bash/*.py` (5 files): `COMMANDS: list[str]`, steps moved into `main()` under a `__main__` guard. `initial_build_db.py` now takes the db path from `ProjectPaths`.
- `scripts/onboarding/contributor_setup.py`: two why-comments on the literal `"dpd.db"` strings. The other four onboarding scripts were left untouched (legacy, per thread `20260719_contributor_web_server`).
- `scripts/suttas/**` (67 `.py` files): module and function docstrings, modern type hints, `id` → `current_id` in the CST extractors, `natural_sort.py` pyright fix, `yellow_title` in `cst/main.py` and `sc/main.py.py`. In the 12 `dpd/` scripts `file_path.open("w")` became `file_path.write_text("")`. Unused `pth` removed from `sc/suttas.py`.
- `scripts/info/*`, `scripts/tutorial/*`, `scripts/export/*`, `scripts/patch/patch_dpd.py`, `scripts/project_management/project_health_check.py`: docstrings, hints, `-> None`.
- `scripts/find/variants_process.py`: `_freq_total` rewritten as a plain loop (pyright).
- `scripts/README.md`, `docs/technical/project_folder_structure.md`: folder lists match the disk.
- `tests/scripts/suttas/bjt/test_helpers.py`: new, 8 cases from real BJT headings.
- Deleted: `scripts/verse/` (git-ignored shells only), 24 orphan `.pyc` files.

Earlier sessions (Phases 1 to 4.1) are recorded row by row in `plan.md`; not re-reviewed here.

## Findings

- CodeRabbit (`--fresh`): `scripts/` 82 files, 0 findings. `tests/scripts` 1 file, 0 findings.
- DeepSeek pi review (deepseek-v4-pro, max thinking): 3 findings.
  1. `paranum` reset to `None` — rejected. The old compiled `kn2` shows the original did the same.
  2. Stale `pb` read before its loop in 17 CST files — real, pre-existing. A fix was applied, then REVERTED at the user's request ("leave this as it was"). Left unfixed on purpose.
  3. New test guards an unchanged function — accepted (characterization test).

## Fixes Applied

- Unclosed `open("w")` in 12 `dpd/` scripts, unused `pth` in `sc/suttas.py`, pyright error in `variants_process.py`.

## Left Unfixed (decided by the user)

- `sc/suttas.py` `re.match("[0-9-]", sutta)` tests only the first character; the comment says "only numbers and -".
- Stale `pb` check in 17 CST files (above).
- Suspected, harmless: `nipata` read before assignment in `sc/suttas.py`; module-level `db_session` in `dpd/*`; bare `uv sync` in `contributor_setup.py`.

## Test Evidence

- `uv run ruff check scripts/`: all checks passed.
- `uv run ruff format --check scripts/ tests/scripts`: 173 files already formatted.
- `uv run pyright scripts/`: 0 errors, 0 warnings.
- `uv run pytest tests/scripts`: 183 passed.
- Test guard: removing the curly-brace line from `clean_string` fails 4 of the 8 cases; restored.
- Every justfile, CI and `tools/paths.py` path under `scripts/` exists. `scripts/prepare_sources.py` runs inside the `other-dictionaries` submodule.

## Incident

At 10:31:55 on 2026-10-23 every file in `scripts/` got the same modification time and one read returned the pre-refresh text of `sc/suttas.py`. The disk content was correct afterwards. A full audit found no lost edit.
