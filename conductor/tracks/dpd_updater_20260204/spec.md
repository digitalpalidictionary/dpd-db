# DPD Updater/Installer Specification

## Overview
A standalone, cross-platform GUI application that automates checking for and installing updates to the Digital Pāḷi Dictionary (DPD) for GoldenDict users. The application will be distributed as platform-specific binaries (Windows .exe, macOS .app, Linux executable) built from a single Python codebase using PyInstaller or similar tool.

## Functional Requirements

### 1. First-Time Setup
- Display a welcome/setup wizard on first launch
- Prompt user to select their GoldenDict content/dictionaries folder
- Validate that the selected folder is a valid GoldenDict location
- Store the path in a configuration file (`~/.config/dpd-updater/config.json` on Linux/Mac, `%APPDATA%\dpd-updater\config.json` on Windows)
- Store the currently installed DPD version (if detectable, otherwise mark as "unknown")

### 2. Version Checking
- On startup, query the GitHub API for the latest DPD release: `api.github.com/repos/digitalpalidictionary/dpd-db/releases/latest`
- Parse the release version tag (e.g., `v2.5.1`) and compare to locally stored version
- Display current version and latest available version in the UI
- If versions differ, highlight that an update is available

### 3. Update Process
- Display a clear "Update Available" notification when newer version detected
- Show release notes from GitHub (first 500 chars) in the UI
- "Update Now" button initiates the update process:
  1. **Close GoldenDict**: Detect if GoldenDict is running and close it gracefully (with force kill as fallback after timeout)
  2. Download the GoldenDict asset from the latest release with progress indicator
  3. Backup existing DPD files to a timestamped folder before overwriting
  4. Extract and install to the configured GoldenDict folder
  5. **Reopen GoldenDict**: Launch GoldenDict after successful installation to trigger re-indexing
- Update the stored version number in config
- Display success/failure message

### 4. Configuration Management
- Allow user to change GoldenDict path via settings menu
- Option to check for updates on startup (boolean, default: true)
- Option to enable/disable automatic backup before updates (boolean, default: true)

### 5. Manual Check
- "Check for Updates" button to manually trigger version check
- Force re-check even if already up to date

## Non-Functional Requirements

### Platform Support
- **Windows:** Standalone .exe file (no Python installation required)
- **macOS:** Standalone .app bundle or .dmg with executable
- **Linux:** Standalone executable binary
- All platforms share the same Python codebase with platform-specific paths handled via `pathlib`

### Distribution
- Binaries built using PyInstaller or Nuitka from single Python source
- No external dependencies required by end users
- GitHub Actions workflow for automated building on release tags

### UI Requirements
- Simple, clean GUI using Flet (consistent with existing DPD GUI2)
- Dark/light theme support (respect system preference)
- Responsive layout that works on all desktop screen sizes
- Clear status indicators and error messages

### Security
- HTTPS only for all network requests
- Verify GitHub API SSL certificates
- No storage of credentials or sensitive data

## Acceptance Criteria

1. User can download and run the updater without having Python installed
2. First launch prompts for GoldenDict folder and remembers it
3. Subsequent launches auto-check for updates (if enabled)
4. When update available, user sees clear notification with version info
5. Clicking "Update" downloads, backs up, and installs latest DPD
6. GoldenDict detects the new dictionary after installation
7. Settings allow changing GoldenDict path and update preferences
8. Works identically on Windows 10/11, macOS 12+, and Ubuntu 22.04+

## Out of Scope

- Mobile platforms (Android/iOS) - GoldenDict mobile apps handle their own updates
- MDict, Kindle, Kobo, or other dictionary formats
- Automatic background updates (always requires user confirmation)
- Delta/patch updates (full download each time)
- Support for GoldenDict-ng vs classic GoldenDict differences
- Integration with package managers (apt, brew, choco, etc.)
- System tray mode with monthly auto-check (future enhancement)

## Technical Notes

- Use GitHub REST API v3 for release information
- GoldenDict dictionaries are typically `.zip` or folder-based
- Config storage locations:
  - Windows: `%APPDATA%\dpd-updater\`
  - macOS: `~/Library/Application Support/dpd-updater/`
  - Linux: `~/.config/dpd-updater/`
- Release assets naming convention: Look for `dpd-goldendict-*.zip` pattern
- **Release Schedule:** DPD updates are released monthly on Uposatha days (Buddhist observance days). See `tools/uposatha_day.py` for the specific dates. The updater should check whenever the user launches it - no need for background scheduling.
