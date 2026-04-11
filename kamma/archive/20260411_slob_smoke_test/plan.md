# Issue Reference
GitHub issue #31: Export to Aard2 Slob format

# Phase 1: Prove Slob export in isolation
- [x] Review `tools/goldendict_exporter.py` and `exporter/tester/tester.py` while implementing to mirror the existing exporter API and output conventions.
- [x] Create a new standalone exporter script for the Slob proof of concept.
- [x] In that script, import `DictEntry`, `DictInfo`, `DictVariables`, and `export_to_goldendict_with_pyglossary` from `tools/goldendict_exporter.py`.
- [x] Build a one-entry in-memory dictionary payload with simple HTML content and no database dependency.
- [x] Configure `DictVariables` so output lands in `exporter/share/` and uses a distinct dictionary name such as `dpd-slob-test`.
- [x] Call `export_to_goldendict_with_pyglossary(..., include_slob=True)` so the existing Slob writer path is exercised.
- [x] Keep the script self-contained and minimal, without touching `exporter/goldendict/main.py`.
- [x] Verify Phase 1 automatically by re-reading the new script and confirming it uses the existing exporter helper path and writes to `exporter/share/`.

# Phase 2: Add a dedicated GitHub workflow with Slob dependencies
- [x] Create a new workflow file under `.github/workflows/` for the Slob smoke test.
- [x] Configure the workflow to trigger manually with `workflow_dispatch`.
- [x] Add checkout, Python setup, and `uv` install steps consistent with existing workflows.
- [x] Add a Linux dependency installation step for the Slob toolchain before dependency sync.
- [x] Base that dependency step on the upstream Slob/PyGlossary requirements for ICU and PyICU on Ubuntu.
- [x] Install project dependencies with `uv sync --all-groups`.
- [x] Add a step that runs the new one-entry exporter script.
- [x] Add a diagnostic step that lists the expected generated files in `exporter/share/` so failures are easier to inspect.
- [x] Add an artifact upload step that uploads the generated `.slob` file from `exporter/share/`.
- [x] Keep the workflow isolated from `.github/workflows/draft_release.yml`.
- [x] Verify Phase 2 automatically by re-reading the workflow and confirming the Linux dependency step, script step, and `.slob` artifact path are all present and consistent.

# Phase 3: Diagnose local failure path
- [x] Check whether ICU system libraries are already available locally.
- [x] Check whether the Python `icu` module is available locally.
- [x] Confirm the original local failure is caused by missing `PyICU` in the active environment rather than missing ICU libraries.
- [x] Add `PyICU` to the existing `tools` dependency group in `pyproject.toml`.
- [x] Sync the local environment with all dependency groups.
- [x] Run the local Slob smoke test successfully.
- [x] Verify Phase 3 automatically by confirming local `icu` import works and the local smoke test writes a `.slob` file.

# Phase 4: Wire Slob into the real exporter path using existing config
- [x] Add a `goldendict.make_slob` default of `no` in `tools/configger.py`.
- [x] Update `scripts/build/config_github_release.py` to set `goldendict.make_slob` to `yes`.
- [x] Update `exporter/goldendict/main.py` to read the existing config structure and pass `include_slob=g.make_slob`.
- [x] Keep local behavior off by default without requiring a local `config.ini` edit.
- [x] Update `.github/workflows/draft_release.yml` so ICU build dependencies are installed before `uv sync --all-groups`.
- [x] Add `exporter/share/dpd.slob` to the Linux artifact upload and draft release asset lists in `.github/workflows/draft_release.yml`.
- [x] Remove the now-redundant manual `PyICU` install step from the smoke-test workflow because `uv sync --all-groups` should install it from project dependencies.
- [x] Verify Phase 4 automatically by re-reading the config, exporter, and workflow files for consistency.

# Phase 5: Verification and thread bookkeeping
- [x] Re-read the final implementation files and check that config defaults, GitHub release config, release workflow, and smoke-test workflow all agree on the same Slob behavior.
- [x] Confirm the smoke-test workflow result and local smoke-test result are both recorded in the thread files.
- [x] Update the thread review after the full issue scope is finished, not just the smoke-test slice.
- [x] Verify Phase 5 automatically by confirming the thread files now match the expanded issue scope.

## Verification results
- Manual GitHub Actions validation succeeded: the smoke-test workflow installed ICU and `PyICU`, generated `exporter/share/dpd-slob-test.slob`, and uploaded the `dpd-slob-smoke-test` artifact.
- Local validation succeeded after adding `PyICU` to the `tools` dependency group and running `uv sync --all-groups`; `uv run --all-groups python exporter/tester/slob_test.py` generated the local Slob smoke-test output successfully.
- Local real-exporter validation succeeded after placing `make_slob = yes` under `[goldendict]`; the exporter wrote `exporter/share/dpd.slob`.
