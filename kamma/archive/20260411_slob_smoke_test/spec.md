# Issue Reference
GitHub issue #31: Export to Aard2 Slob format

# Overview
Implement issue #31 in the existing project structures instead of a one-off workaround. This work now has three parts:
- prove Slob export works in isolation with a one-entry smoke test
- diagnose why Slob was failing locally
- wire the real GoldenDict exporter and GitHub release path so Slob stays off locally by default and turns on in the GitHub release configuration

# What it should do
- Keep the standalone Slob smoke-test exporter and dedicated GitHub workflow.
- Add `goldendict.make_slob` to the existing config defaults in `tools/configger.py`, with local default `no`.
- Use that existing config structure in `exporter/goldendict/main.py` so the real exporter passes `include_slob=g.make_slob`.
- Turn Slob on in `scripts/build/config_github_release.py` by setting `goldendict.make_slob = yes` for the release pipeline.
- Ensure the main GitHub release workflow installs the Linux ICU build dependencies before `uv sync --all-groups` so `PyICU` can be available in CI.
- Ensure the main GitHub release workflow uploads `dpd.slob` as a Linux artifact and attaches it to the draft GitHub release.
- Preserve local behavior so the normal local exporter path does not require Slob to run.

# Relevant repo context
- `tools/goldendict_exporter.py` already contains the Slob path:
  - `DictVariables.slob_path_name`
  - `write_to_slob(...)`
  - `export_to_goldendict_with_pyglossary(..., include_slob=False)`
- `exporter/tester/tester.py` is the closest existing example of a simple one-file exporter.
- The only existing issue #31 commit is `3f6ced99 #31 slob: add option to main exporter`, which only added a commented `include_slob=True` line in `exporter/goldendict/main.py`.
- The real release path is controlled by `scripts/build/config_github_release.py` and `.github/workflows/draft_release.yml`, so the GitHub-on behavior should be added there rather than by inventing a separate switch.
- Upstream dependency notes indicate Slob export depends on ICU collation support through `PyICU`.
- Upstream docs reviewed:
  - PyGlossary Aard2 Slob docs state read/write support requires `pyicu`
  - PyGlossary `pyicu.md` says Linux needs PyICU installed, and distro packages may be used
  - `itkach/slob` README states Slob depends on ICU and PyICU, with Ubuntu examples using `python3-icu`
- Local diagnosis showed:
  - ICU libraries were already present locally (`pkg-config --libs icu-i18n` succeeded)
  - the failing piece was the Python `icu` module, not the ICU system library
  - after adding `PyICU` to the `tools` dependency group and running `uv sync --all-groups`, the local Slob smoke test succeeded
- For GitHub Actions on Ubuntu, the workflow must install the system ICU build layer before `uv sync --all-groups` so `PyICU` can be installed reliably.

# Constraints
- Use the existing exporter helpers; do not introduce a new Slob implementation.
- Use the existing config structures instead of inventing a separate toggle system.
- Install the required Linux Slob dependencies in the workflows instead of assuming they are preinstalled.
- Do not modify `config.ini` or require manual config changes.
- Preserve local exporter behavior by keeping Slob off unless GitHub release config turns it on.
- Avoid requiring Slob support for normal local GoldenDict export runs.

# How we'll know it's done
- A workflow exists in `.github/workflows/` specifically for the Slob smoke test.
- That workflow installs the Linux dependencies needed for Slob export.
- The workflow runs the new Python script without needing the full database build.
- The script produces a `.slob` file in `exporter/share/`.
- The workflow uploads that `.slob` file as an artifact.
- The implementation uses the existing `tools/goldendict_exporter.py` path with `include_slob=True`.
- `tools/configger.py` defaults `goldendict.make_slob` to `no`.
- `scripts/build/config_github_release.py` turns `goldendict.make_slob` to `yes`.
- `exporter/goldendict/main.py` uses the config value to decide whether to write Slob.
- The local Slob smoke test runs successfully once the environment is synced with `PyICU` available.
- The draft release workflow includes `exporter/share/dpd.slob` in both the uploaded Linux artifacts and the release asset list.

# What's not included
- Solving every local environment variation beyond the identified ICU plus `PyICU` requirement
- Reworking the exporter architecture beyond the existing config and exporter flow
