# DPD Contributor Setup Guide

This guide walks you through setting up the Digital Pali Dictionary GUI on your computer.

## Prerequisites

1. **GitHub Account** - Create one at [github.com](https://github.com/join) if you don't have one. Ask the maintainer to grant you repository access.

2. **Git** - Install git for your operating system:
   - **Windows**: Download from [git-scm.com/download/win](https://git-scm.com/download/win). During installation, select "Git from the command line and also from 3rd-party software".
   - **macOS**: Run `xcode-select --install` in Terminal, or install via `brew install git`.
   - **Linux**: `sudo apt install git` (Ubuntu/Debian), `sudo dnf install git` (Fedora), or `sudo pacman -S git` (Arch).

3. **uv** - Install the Python package manager:
   - **Windows**: Open PowerShell and run:
     ```
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - **macOS/Linux**: Open a terminal and run:
     ```
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```

## Setup (3 commands)

Open a terminal and run these commands one at a time:

```bash
# 1. Clone the repository
git clone https://github.com/digitalpalidictionary/dpd-db.git

# 2. Enter the project directory
cd dpd-db

# 3. Run the setup script
uv run scripts/onboarding/contributor_setup.py
```

The setup script will:
- Initialize the required data files
- Download the latest dictionary database
- Ask for your contributor username
- Create a desktop shortcut to launch the GUI

## Launching the GUI

**Option 1**: Double-click the "DPD GUI" shortcut on your Desktop.

**Option 2**: Open a terminal in the `dpd-db` folder and run:
```bash
uv run scripts/onboarding/launch_gui.py
```

## Submitting Your Data

When you've made changes and want to submit your work:

1. Click the **"Submit Data"** button in the top-right corner of the GUI.
2. The system will automatically commit and push your changes.
3. A dialog will confirm whether the submission was successful.

If the push fails (e.g., someone else pushed changes), the system will automatically pull the latest code and retry.

## Updating Your Environment

To get the latest code and database:

**Option 1**: Click the **"Update"** button in the top-right corner of the GUI.

**Option 2**: Open a terminal in the `dpd-db` folder and run:
```bash
uv run scripts/onboarding/contributor_update.py
```

This will:
- Pull the latest code from GitHub
- Update any changed dependencies
- Check if a new database version is available

## Troubleshooting

### "git is not installed"
Follow the git installation instructions in the Prerequisites section above.

### "uv: command not found"
Close and reopen your terminal after installing uv. If it still doesn't work, reinstall uv using the commands in the Prerequisites section.

### GUI won't launch
1. Make sure you're in the `dpd-db` directory.
2. Try running `uv sync` first to ensure dependencies are up to date.
3. Try `uv run gui2/main.py` directly to see error messages.

### "Submit Data" fails
- Check your internet connection.
- Make sure you have push permissions on the repository (ask the maintainer).
- If you see "rejected", the system should auto-retry. If it still fails, run `uv run scripts/onboarding/contributor_update.py` first, then try submitting again.

### Desktop shortcut doesn't work
- **Linux**: Right-click the shortcut and select "Allow Launching" or "Trust and Launch".
- **macOS**: Right-click the shortcut and select "Open" (needed only the first time).
- **Windows**: If SmartScreen blocks it, click "More info" then "Run anyway".

### Python version issues
uv automatically manages Python versions. If you encounter Python-related errors, try:
```bash
uv python install 3.13
uv sync
```
