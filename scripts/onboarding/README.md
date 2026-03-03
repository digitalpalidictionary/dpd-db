# DPD Contributor Setup Guide

This guide walks you through setting up the Digital Pali Dictionary GUI on your computer. No programming experience is needed — just follow the steps for your operating system.

## Step 1: Create a GitHub Account

If you don't already have one, go to [github.com/join](https://github.com/join) and create a free account. Then ask the maintainer to grant you access to the DPD repository.

## Step 2: Install Git and uv

You need two tools installed before you begin. Follow the instructions for your operating system below.

### Windows

1. **Install Git:** Download from [git-scm.com/download/win](https://git-scm.com/download/win) and run the installer. When it asks about "Adjusting your PATH", select **"Git from the command line and also from 3rd-party software"**. For all other options, the defaults are fine.

2. **Install uv:** Open **PowerShell** (press the Windows key, type `PowerShell`, and click **"Windows PowerShell"**). Copy and paste this command, then press Enter:
   ```
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   After it finishes, **close PowerShell** completely (you'll reopen it in the next step).

### macOS

1. **Install Git:** Open **Terminal** (press Cmd+Space, type `Terminal`, press Enter). Copy and paste this command, then press Enter:
   ```
   xcode-select --install
   ```
   A popup will appear asking you to install developer tools — click **Install** and wait for it to finish.

2. **Install uv:** In the same Terminal window, copy and paste this command and press Enter:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   After it finishes, **close Terminal** completely (you'll reopen it in the next step).

### Linux (Ubuntu/Debian)

1. **Install Git:** Open **Terminal** (press Ctrl+Alt+T or find "Terminal" in your applications). Copy and paste this command and press Enter:
   ```
   sudo apt install git
   ```
   Enter your password when asked (the characters won't appear as you type — that's normal).

2. **Install uv:** In the same Terminal window, copy and paste this command and press Enter:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   After it finishes, **close Terminal** completely (you'll reopen it in the next step).

## Step 3: Download and Set Up DPD

Now open a **fresh terminal window** (this is important so it picks up the tools you just installed):

- **Windows:** Press the Windows key, type `PowerShell`, click **"Windows PowerShell"**
- **macOS:** Press Cmd+Space, type `Terminal`, press Enter
- **Linux:** Press Ctrl+Alt+T

Then copy and paste the following commands **one at a time**, pressing Enter after each one. Wait for each command to finish before pasting the next.

**Command 1** — Go to your Documents folder:
```
cd Documents
```

**Command 2** — Download the DPD project (this may take a few minutes):
```
git clone https://github.com/digitalpalidictionary/dpd-db.git
```

**Command 3** — Go into the project folder:
```
cd dpd-db
```

**Command 4** — Run the setup (this will download the database and create a desktop shortcut):
```
uv run scripts/onboarding/contributor_setup.py
```

The setup script will ask for your contributor username — type it in and press Enter. When it finishes, you'll have a **"DPD GUI"** shortcut on your Desktop.

Your DPD project is now located in your **Documents/dpd-db** folder.

## Launching the GUI

Double-click the **"DPD GUI"** shortcut on your Desktop.

If the shortcut doesn't work the first time:
- **Windows:** If SmartScreen blocks it, click "More info" then "Run anyway".
- **macOS:** Right-click the shortcut and select "Open" (only needed the first time).
- **Linux:** Right-click the shortcut and select "Allow Launching" or "Trust and Launch".

## Submitting Your Data

When you've made changes and want to submit your work:

1. Click the **"Submit Data"** button in the top-right corner of the GUI.
2. A dialog will confirm whether the submission was successful.

That's it! The system handles everything behind the scenes. If something goes wrong, it will tell you in the dialog.

## Updating Your Environment

When the maintainer tells you an update is available:

Click the **"Update"** button in the top-right corner of the GUI.

This will download the latest code and database updates.

## Troubleshooting

### "git is not installed"
Go back to Step 2 above and follow the git installation instructions for your operating system.

### "uv: command not found"
Close your terminal completely and open a new one. If it still doesn't work, go back to Step 2 and reinstall uv.

### GUI won't launch
1. Make sure you completed all 4 commands in Step 3 without errors.
2. Try running the setup again (Command 4 from Step 3) — it's safe to run multiple times.

### "Submit Data" fails
- Check your internet connection.
- Make sure you have repository access (ask the maintainer).
- Click the **"Update"** button first, then try submitting again.

### Python version issues
uv automatically manages Python versions. If you see Python-related errors, open a terminal, go to the project folder, and run:
```
cd Documents/dpd-db
uv python install 3.13
uv sync
```
