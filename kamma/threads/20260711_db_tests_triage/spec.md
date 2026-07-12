# Spec: db_tests triage & refresh

**GitHub issue:** #157 (project cleanup umbrella)
**Thread:** 20260711_db_tests_triage

## Overview

`db_tests/`, `db_tests/single/` and `db_tests_gui/` hold ~39 Python scripts (~9,600 lines) of manual data-integrity tooling for `dpd.db`. Their condition was unknown. A full audit (2026-07-11) found: ruff fully clean, 5 pyright errors in 2 files, 12 orphaned scripts, a non-functional Flet prototype, 2 orphaned data files, ~16 FIXME markers, and zero pytest collection (pytest's `testpaths = ["tests"]` never touches these directories).

This thread is a **one-by-one triage**: the user runs each file, observes whether it works and is still useful, and issues a verdict. The spec makes **no per-file decisions** — every file is unique; decisions happen only at execution time, file by file.

## What it should do

1. **Preserve the evidence first.** All last-run dates (from `__pycache__` mtimes) and git dates are recorded in `plan.md` per file. This matters because running a file again destroys its date evidence. (Already captured — see plan dossiers.)
2. **Triage loop, one file per task.** For each file:
   - The **user runs it** (never the agent, per global rules) and reports what happened.
   - Verdict is chosen from the menu: **keep as-is · freshen · improve · archive · delete** (or any bespoke combination — files are unique).
   - Agent implements the verdict and records it in the plan row.
3. **The only constant — every file that survives gets freshened:** module/function docstrings, modern type hints (`dict[str, str]`, `| None`), `uv run ruff check --fix` + `ruff format` + `pyright` clean, and minor obvious fixes. This applies regardless of verdict (except archive/delete).
4. **Pytest coverage** for surviving files where it makes sense, following the existing pattern (`tests/db_tests/test_db_tests_manager.py`, `tests/db_tests/single/test_add_phonetic_variants.py`) — decided per file during triage, aimed at importable pure logic, not interactive loops.
5. **Cross-cutting cleanup** resolved as owner files get triaged: orphaned data files, stale `__pycache__` entries for deleted modules, the `archive/db_tests/old_tests_DELETE.py` live import, the `difefrence` filename typo, README updates.

## Key audit facts (2026-07-11 snapshot)

- **Lint:** `ruff check db_tests db_tests_gui` → all clean. `pyright` → 5 errors: `db_tests/single/test_root_family_vs_construction_prefixes.py:146` (2, `re.sub` on `str | None`), `db_tests_gui/main.py:110,118` (3, flet attribute access).
- **Live consumers:** `db_tests/db_tests_manager.py` is a shared library imported by `gui2/toolkit.py`, `gui2/test_manager.py`, `gui2/tests_tab_controller.py`, `gui2/tests_tab_view.py` — its API must not break. `db_tests/db_tests_relationships.py` is wired as `just db-test`. Five `single/add_*` scripts are justfile recipes.
- **pytest:** collects only `tests/`; the ~15 `single/test_*.py` files are NOT pytest tests despite their names (they are standalone interactive scripts). Their `-pytest-8.3.5.pyc` cache files show someone ran pytest over them directly in early 2026.
- **Date evidence caveats:** a `.pyc` mtime = last time the module was *imported* under that Python version. Running a script directly (`python file.py`) writes **no** `.pyc` for that file — so a missing `.pyc` does not prove disuse (e.g. `db_tests_relationships.py` has no `.pyc` but is actively used via `just db-test`). Conversely a `.pyc` can appear because a sibling imported the module.

## Assumptions & uncertainties

- Assumed verdicts cannot be predicted in advance — even "obvious" orphans ran as manual one-offs in Jan–Mar 2026 per pycache, so orphaned ≠ unused.
- Assumed "archive" means moving to `archive/` (repo convention: `archive/db_tests/` already exists), preserving history.
- Uncertain whether `db_tests_gui/main.py` and friends should even be run for triage (Flet app, writes to DB via its add_* functions) — user decides at that row.
- Uncertain how many surviving files warrant pytest coverage; decided per file.
- Many scripts **write to the live `dpd.db`** (marked in dossiers). The user runs them knowingly; agent never runs them.

## Constraints

- Agent never runs the triaged files — the user does.
- Model: Sonnet 5 suffices for Phases 1–3 (mechanical edits). At Phase 4 (latent bugs in `db_tests_relationships.py`, `DbTestManager` API work), switch to a stronger model (Opus 4.8) when necessary.
- No git commands unless explicitly asked; user commits at the end. Checkpoints are report-only.
- `DbTestManager` public API (used by gui2) must remain compatible.
- Touch a file = own its lint: every edited file must pass `ruff check`, `ruff format`, `pyright` before the task is done.
- `db_tests_columns.tsv` is live data (regenerated/edited via gui2) — not part of this refactor.

## How we'll know it's done

- Every row in the plan has a recorded verdict and its implementation is complete.
- All surviving files: docstrings, modern type hints, ruff + pyright clean.
- No orphaned data files, no stale imports from `archive/`, no dead prototypes left undecided.
- `uv run pytest tests/` passes, including any newly added tests.
- READMEs in the three directories match the post-triage reality; `docs/technical/project_folder_structure.md` still accurate.

## What's not included

- No changes to gui2's Tests tab beyond keeping imports working.
- No redesign of the column-rule TSV test system.
- No new GUI development; at most, retiring/archiving existing Flet code.
- No automation of the interactive scripts' human-in-the-loop workflows.

## Scope exception (2026-07-12)

The `test_bahubbihis.py` row surfaced a near-duplicate outside the plan's three directories: `scripts/find/bahubbīhi_finder.py`, a 2026-02-26 partial rewrite of the same tool sharing the same `test_bahubbihis.json` data file. Per explicit user instruction, that file was folded into this row (consolidated into the db_tests copy, duplicate deleted, result moved to `fixme/`) even though `scripts/find/` is outside this thread's normal scope. This is a one-off, not a standing invitation to sweep `scripts/find/` — future rows stay inside `db_tests/`, `db_tests/single/`, `db_tests/gui/` (renamed from `db_tests_gui/`, see Phase 3 note in `plan.md`) unless a row surfaces another explicit duplicate the user asks to fold in.
