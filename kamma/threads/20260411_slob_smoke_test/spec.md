# Issue Reference
GitHub issue #31: Export to Aard2 Slob format

# Overview
Add a minimal, isolated proof path for Slob export by creating a dedicated GitHub workflow and a single-purpose Python exporter script that produces a one-entry `.slob` dictionary using the repository's existing `tools.goldendict_exporter.export_to_goldendict_with_pyglossary(..., include_slob=True)` flow.

This remains a smoke test only. It does not switch the main DPD exporter or the monthly release workflow to Slob yet.

# What it should do
- Add one standalone Python exporter script that:
  - uses the existing `DictEntry`, `DictInfo`, `DictVariables`, and `export_to_goldendict_with_pyglossary` helpers from `tools/goldendict_exporter.py`
  - builds a one-entry test dictionary with simple HTML content
  - writes output into `exporter/share/`
  - enables `include_slob=True`
- Add one dedicated GitHub Actions workflow that:
  - checks out the repository
  - installs the Linux system dependencies required for Slob export
  - installs project dependencies with `uv sync --all-groups`
  - runs the one-entry exporter script
  - uploads the generated `.slob` file as a workflow artifact

# Relevant repo context
- `tools/goldendict_exporter.py` already contains the Slob path:
  - `DictVariables.slob_path_name`
  - `write_to_slob(...)`
  - `export_to_goldendict_with_pyglossary(..., include_slob=False)`
- `exporter/tester/tester.py` is the closest existing example of a simple one-file exporter.
- The only existing issue #31 commit is `3f6ced99 #31 slob: add option to main exporter`, which only added a commented `include_slob=True` line in `exporter/goldendict/main.py`.
- The main release workflow `.github/workflows/draft_release.yml` is intentionally not the place for this proof run because it builds the full database and all release assets.
- Upstream dependency notes indicate Slob export depends on ICU collation support through `PyICU`.
- Upstream docs reviewed:
  - PyGlossary Aard2 Slob docs state read/write support requires `pyicu`
  - PyGlossary `pyicu.md` says Linux needs PyICU installed, and distro packages may be used
  - `itkach/slob` README states Slob depends on ICU and PyICU, with Ubuntu examples using `python3-icu`
- For GitHub Actions on Ubuntu, the workflow should install the system ICU/PyICU layer explicitly before `uv sync --all-groups` so Python dependency resolution has the native support it needs.

# Constraints
- Use the existing exporter helpers; do not introduce a new Slob implementation.
- Keep the solution minimal: one Python file and one workflow.
- Install the required Linux Slob dependencies in the workflow instead of assuming they are preinstalled.
- Do not modify `config.ini` or require manual config changes.
- Do not wire Slob into the monthly release workflow yet.
- Do not depend on the full DPD database build for this proof of concept.
- Preserve current behavior of `exporter/goldendict/main.py` and `.github/workflows/draft_release.yml`.

# How we'll know it's done
- A workflow exists in `.github/workflows/` specifically for the Slob smoke test.
- That workflow installs the Linux dependencies needed for Slob export.
- The workflow runs the new Python script without needing the full database build.
- The script produces a `.slob` file in `exporter/share/`.
- The workflow uploads that `.slob` file as an artifact.
- The implementation uses the existing `tools/goldendict_exporter.py` path with `include_slob=True`.

# What's not included
- Full DPD Slob export
- Adding Slob generation to the monthly draft release workflow
- Publishing Slob files in GitHub releases
- Database-backed export content beyond a one-entry smoke test
- Generalized dependency refactors outside what is needed for this isolated proof
