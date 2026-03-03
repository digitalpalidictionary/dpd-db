# Spec: Contributor Setup & Data Submission

**GitHub Issue:** #215
**Commit Convention:** `#215 <type>: <description>` (e.g., `#215 feat: add setup script`, `#215 fix: correct Windows path`)
**Working Directory:** `scripts/onboarding/` — all scripts, tests, and docs live here.

## Overview

Make DPD's GUI (gui2) easily installable and usable by non-technical contributors (5–10 people) on Windows, Mac, and Linux. Contributors use the full GUI functionality to input and edit dictionary data, then submit their work back via git commit and push (contributors are granted repo permissions by the maintainer).

## Target Users

Non-technical Pāḷi scholars and Dhamma practitioners who are willing to:
- Create a GitHub account
- Open a terminal once to run 3 copy-paste commands
- Use the Flet GUI for all data entry and editing work
- Click "Submit Data" in the GUI to commit and push their work

They do NOT know what git commits, branches, or PRs are, and should never need to. The submission process abstracts git operations behind a single button.

## Folder Structure

```
scripts/onboarding/
├── README.md                    # Contributor setup guide (FR-5)
├── contributor_setup.py         # Setup script (FR-1)
├── launch_gui.py                # GUI launch wrapper (FR-2)
├── data_submission.py           # Git commit & push logic (FR-3)
├── contributor_update.py        # Update script (FR-4)
└── tests/
    ├── test_contributor_setup.py
    ├── test_launch_gui.py
    ├── test_data_submission.py
    └── test_contributor_update.py
```

The only files outside this folder are GUI integration changes in `gui2/` (adding the "Submit Data" button).

## Functional Requirements

### FR-1: Contributor Setup Script (`scripts/onboarding/contributor_setup.py`)

A single Python script run via `uv run` that automates the full environment setup:

1. **Verify prerequisites:** Check that `git` is installed; print a friendly message with OS-specific install instructions if not.
2. **Init selective submodules:** Initialize only the submodules required for GUI operation (`sc-data`, `dpd_submodules`, and any others needed). Skip large export-only submodules (`dpd_audio`, `other-dictionaries`, `tpr_downloads`, `bw2`, `fdg_dpd`, `tipitaka_translation_db`).
3. **Download pre-built database:** Fetch the latest `dpd.db` from the most recent GitHub Release and place it in the correct project location.
4. **Configure contributor identity:** Prompt for a username (used by the existing `UsernameManager` secondary-user system) and store it in the project config.
5. **Create desktop shortcut:** Generate a platform-appropriate shortcut (`.desktop` on Linux, `.command`/alias on Mac, `.lnk`/`.bat` on Windows) that launches the GUI.
6. **Print success message:** Confirm setup is complete with instructions on how to launch the GUI.

### FR-2: GUI Launch Wrapper (`scripts/onboarding/launch_gui.py`)

A simple launcher script that:
1. Ensures dependencies are up to date (`uv sync` — quick no-op if already current).
2. Starts the Flet GUI (`gui2/main.py`).
3. Is invoked by the desktop shortcut.

### FR-3: Data Submission via Git (`scripts/onboarding/data_submission.py`)

A "Submit Data" button/action accessible from the GUI that:
1. Stages all contributor data files (`shared_data/additions.tsv`, `shared_data/corrections.tsv`, and any other modified data files).
2. Creates a git commit with an auto-generated message (e.g., `contrib(username): submit data 2026-03-03`).
3. Pushes the commit to the remote repository (contributors are granted push permissions by the maintainer).
4. Displays a success/failure message to the contributor.
5. Handles common errors gracefully (no internet, push rejected due to upstream changes — auto-pull and retry).

### FR-4: Contributor Update Script (`scripts/onboarding/contributor_update.py`)

A script contributors can run (or triggered via a GUI button) to update their environment:
1. `git pull` the latest code.
2. `uv sync` to update dependencies.
3. Download the latest `dpd.db` from GitHub Releases (if a newer version is available).
4. Print a summary of what was updated.

### FR-5: Contributor Guide Documentation (`scripts/onboarding/README.md`)

A clear guide covering:
1. Prerequisites (GitHub account, git installation per OS).
2. The 3 copy-paste setup commands.
3. How to launch the GUI.
4. Overview of GUI functionality.
5. How to submit data (click "Submit Data" button).
6. How to update their environment.
7. Troubleshooting section for common issues.

## Non-Functional Requirements

- **Cross-platform:** Must work on Windows 10+, macOS 12+, and Ubuntu 22.04+ / common Linux distros.
- **Minimal terminal use:** Contributors should only need the terminal for initial setup and updates. Day-to-day work is entirely in the GUI.
- **Idempotent setup:** Running the setup script multiple times should be safe and not corrupt existing data or contributor work.
- **Friendly error messages:** All scripts should catch common errors (no internet, git not found, disk full) and print human-readable guidance.
- **Full GUI support:** All GUI tabs and functionality should work for contributors, not just a subset.
- **Self-contained:** All onboarding code, tests, and docs live in `scripts/onboarding/`. Only GUI integration touches `gui2/`.

## Acceptance Criteria

- [ ] A new contributor on a clean Windows/Mac/Linux machine can go from zero to a running GUI using only the 3 documented commands.
- [ ] The GUI launches via desktop shortcut without needing a terminal.
- [ ] All GUI tabs function correctly for secondary users.
- [ ] "Submit Data" commits and pushes contributor data to the remote repository.
- [ ] The update script successfully pulls new code and database.
- [ ] The contributor guide is complete and tested on all 3 platforms.

## Testing Strategy

- Automated tests cover core logic (git detection, git commit/push, path handling, download logic).
- All tests live in `scripts/onboarding/tests/`.
- User verification is minimized — only a final end-to-end test on a borrowed Windows machine.
- Linux testing is done during development on the primary machine.
- macOS testing deferred unless a Mac is available.

## Out of Scope

- Building standalone binary executables (PyInstaller/Nuitka).
- PR-based submission workflow (contributors push directly, no PR review process).
- Running the full database build pipeline on contributor machines.
- Exporter functionality — contributors only need the GUI for data entry.
- Supporting more than ~10 concurrent contributors.
