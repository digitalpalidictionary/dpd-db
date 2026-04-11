# Issue Reference
GitHub issue #31: Export to Aard2 Slob format

# Phase 1: Add a minimal one-entry Slob exporter
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

# Phase 3: Local verification and thread bookkeeping
- [x] Re-read the final implementation files and check that file paths, artifact paths, dictionary names, and dependency assumptions match between the script and workflow.
- [x] Check the upstream dependency notes already reviewed against the workflow commands so the package install step is justified and explicit.
- [x] Run targeted non-execution verification appropriate to this session by checking the changed files for consistency and obvious YAML or path mistakes.
- [x] Update the Kamma thread files so every completed task is marked accurately and any remaining limitation is recorded explicitly.
- [x] Verify Phase 3 automatically by confirming the spec, plan, and changed files all agree on the scope: isolated one-entry Slob workflow only, with Linux dependencies included.

## Remaining limitation
- The exporter script and GitHub workflow were not executed in this session, so live validation still depends on a manual GitHub Actions run.
