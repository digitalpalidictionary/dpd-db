# Plan: Contributor Setup & Data Submission

**GitHub Issue:** #215
**Commit format:** `#215 <type>: <description>`
**Working directory:** `scripts/onboarding/`

## Phase 1: Contributor Setup Script

- [x] Task 1.1: Research cross-platform prerequisites detection
  - [x] Sub-task: Research reliable methods to detect `git` installation on Windows, Mac, Linux
  - [x] Sub-task: Research `uv` capabilities for auto-installing Python 3.13
  - [x] Sub-task: Identify which submodules are required vs optional for full GUI operation

- [x] Task 1.2: Write tests for contributor setup script
  - [x] Sub-task: Test git detection logic (present/missing) — `scripts/onboarding/tests/test_contributor_setup.py`
  - [x] Sub-task: Test selective submodule initialization logic
  - [x] Sub-task: Test database download from GitHub Releases
  - [x] Sub-task: Test contributor username configuration
  - [x] Sub-task: Test idempotent re-runs (safe to run multiple times)

- [x] Task 1.3: Implement contributor setup script (`scripts/onboarding/contributor_setup.py`)
  - [x] Sub-task: Implement prerequisite checks (git detection with OS-specific install guidance)
  - [x] Sub-task: Implement selective submodule initialization
  - [x] Sub-task: Implement database download from latest GitHub Release
  - [x] Sub-task: Implement contributor username prompt and config storage
  - [x] Sub-task: Implement friendly progress messages and error handling

- [x] Task 1.4: Implement desktop shortcut creation
  - [x] Sub-task: Research and implement `.desktop` file creation for Linux
  - [x] Sub-task: Research and implement `.command` or alias creation for macOS
  - [x] Sub-task: Research and implement `.lnk` or `.bat` creation for Windows
  - [x] Sub-task: Test shortcut creation on available platforms

## Phase 2: GUI Launch Wrapper

- [x] Task 2.1: Write tests for launch wrapper — `scripts/onboarding/tests/test_launch_gui.py`
  - [x] Sub-task: Test dependency sync check logic
  - [x] Sub-task: Test GUI launch invocation

- [x] Task 2.2: Implement GUI launch wrapper (`scripts/onboarding/launch_gui.py`)
  - [x] Sub-task: Implement `uv sync` quick-check before launch
  - [x] Sub-task: Implement Flet GUI launch
  - [x] Sub-task: Ensure the desktop shortcut invokes this wrapper

## Phase 3: Data Submission via Git

- [ ] Task 3.1: Write tests for data submission — `scripts/onboarding/tests/test_data_submission.py`
  - [ ] Sub-task: Test git add stages only contributor data files
  - [ ] Sub-task: Test commit message generation (username, timestamp)
  - [ ] Sub-task: Test git push logic and error handling
  - [ ] Sub-task: Test auto-pull and retry when push is rejected (upstream changes)

- [ ] Task 3.2: Implement data submission logic (`scripts/onboarding/data_submission.py`)
  - [ ] Sub-task: Implement git add for contributor data files (additions.tsv, corrections.tsv, etc.)
  - [ ] Sub-task: Implement auto-generated commit message with username and date
  - [ ] Sub-task: Implement git push with error handling
  - [ ] Sub-task: Implement pull-and-retry logic for push rejection

- [ ] Task 3.3: Integrate submission into GUI
  - [ ] Sub-task: Add "Submit Data" button to the GUI (in `gui2/`)
  - [ ] Sub-task: Wire button to `scripts/onboarding/data_submission.py` logic
  - [ ] Sub-task: Display success/failure dialog to contributor

## Phase 4: Contributor Update Script

- [ ] Task 4.1: Write tests for update script — `scripts/onboarding/tests/test_contributor_update.py`
  - [ ] Sub-task: Test git pull logic and error handling
  - [ ] Sub-task: Test database version comparison (current vs latest release)
  - [ ] Sub-task: Test database download when newer version is available

- [ ] Task 4.2: Implement contributor update script (`scripts/onboarding/contributor_update.py`)
  - [ ] Sub-task: Implement `git pull` with error handling (dirty working tree, network errors)
  - [ ] Sub-task: Implement `uv sync` for dependency updates
  - [ ] Sub-task: Implement database version check against GitHub Releases
  - [ ] Sub-task: Implement conditional database download
  - [ ] Sub-task: Implement update summary output

- [ ] Task 4.3: Optionally integrate update into GUI
  - [ ] Sub-task: Add "Check for Updates" button to GUI (in `gui2/`)
  - [ ] Sub-task: Wire button to update script

## Phase 5: Documentation

- [ ] Task 5.1: Write contributor guide (`scripts/onboarding/README.md`)
  - [ ] Sub-task: Document prerequisites (GitHub account, git installation per OS)
  - [ ] Sub-task: Document the 3 copy-paste setup commands
  - [ ] Sub-task: Document how to launch the GUI
  - [ ] Sub-task: Document how to submit data (Submit Data button)
  - [ ] Sub-task: Document how to update the environment
  - [ ] Sub-task: Add troubleshooting section for common issues

- [ ] Task 5.2: Update `scripts/README.md` to reference the onboarding folder

## Phase 6: Final Verification (User Required)

- [ ] Task 6.1: End-to-end test on a borrowed Windows machine
  - [ ] Sub-task: Fresh install from the 3 copy-paste commands
  - [ ] Sub-task: Verify GUI launches via desktop shortcut
  - [ ] Sub-task: Verify all GUI tabs function
  - [ ] Sub-task: Verify "Submit Data" commits and pushes to remote
  - [ ] Sub-task: Verify update script works
  - [ ] Sub-task: Fix any Windows-specific issues discovered
