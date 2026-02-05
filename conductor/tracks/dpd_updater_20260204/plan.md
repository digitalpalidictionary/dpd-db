# Implementation Plan: DPD Updater/Installer

## Phase 1: Project Structure and Foundation

### 1.1 Create Updater Module Structure
- [x] Task: Create `exporter/updater/` directory
- [x] Task: Create `exporter/updater/__init__.py`
- [x] Task: Create `exporter/updater/README.md` with module overview
- [x] Task: Create `exporter/updater/main.py` - entry point for GUI application
- [x] Task: Add dependencies to `pyproject.toml` (requests, packaging, flet)

### 1.2 Configuration Management
- [x] Task: Create `exporter/updater/config.py` - handles config file I/O
- [x] Task: Implement cross-platform config path detection (Windows/Mac/Linux)
- [x] Task: Implement config schema with validation
- [x] Task: **Write Tests:** Create `tests/test_updater_config.py` with tests for config read/write, path detection, schema validation
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Core Functionality - GitHub Integration

### 2.1 GitHub API Client
- [x] Task: Create `exporter/updater/github_client.py` - GitHub API wrapper
- [x] Task: Implement `get_latest_release()` method
- [x] Task: Implement version comparison using `packaging.version`
- [x] Task: Implement asset URL extraction for GoldenDict releases
- [x] Task: **Write Tests:** Create `tests/test_updater_github.py` with mocked API responses, version comparison tests
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

### 2.2 Download and Install Logic
- [x] Task: Create `exporter/updater/installer.py` - download and installation logic
- [x] Task: Implement download with progress callback
- [x] Task: Implement backup of existing DPD files (timestamped)
- [x] Task: Implement extraction and installation to GoldenDict folder
- [x] Task: **Write Tests:** Create `tests/test_updater_installer.py` with mocked downloads, backup verification, installation tests
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

### 2.3 GoldenDict Process Management
- [x] Task: Create `exporter/updater/system_manager.py` - GoldenDict process control
- [x] Task: Implement `is_running()` to detect if GoldenDict is active
- [x] Task: Implement `close()` to gracefully terminate GoldenDict (with force kill fallback)
- [x] Task: Implement `reopen()` to restart GoldenDict after update
- [x] Task: **Write Tests:** Create `tests/test_updater_system.py` with mocked process tests
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

### 2.4 Installation Detection and Scanning
- [x] Task: Create `exporter/updater/utils.py` - DPD detection utilities
- [x] Task: Implement `detect_installed_version()` to scan GoldenDict folder
- [x] Task: Implement `verify_dpd_installation()` to validate DPD files
- [x] Task: Implement `scan_for_changes()` to detect folder changes on startup
- [x] Task: Integrate scanning into main app startup flow
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: User Interface

### 3.1 First-Time Setup Wizard
- [x] Task: Create `exporter/updater/ui_setup.py` - setup wizard UI
- [x] Task: Implement folder picker dialog (cross-platform)
- [x] Task: Implement GoldenDict folder validation
- [x] Task: Implement "Remember this location" checkbox
- [x] Task: **Write Tests:** Config validation tests covered in test_updater_config.py

### 3.2 Main Application UI
- [x] Task: Create `exporter/updater/ui_main.py` - main application window
- [x] Task: Implement current version display
- [x] Task: Implement "Check for Updates" button
- [x] Task: Implement update available notification with version info
- [x] Task: Implement progress indicator during download/install
- [x] Task: Implement settings menu (change path, toggle auto-check)
- [x] Task: **Write Tests:** UI functionality tested manually (Flet UI testing requires integration tests)
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Build and Distribution

### 4.1 PyInstaller Build Scripts
- [x] Task: Create `exporter/updater/build.py` - PyInstaller build automation
- [x] Task: Implement Windows build (.exe with icon)
- [x] Task: Implement macOS build (.app bundle)
- [x] Task: Implement Linux build (executable binary)
- [ ] Task: **Note:** PyInstaller cannot cross-compile. To get all 3 executables:
  - Build on Windows → get Windows .exe
  - Build on macOS → get macOS .app
  - Build on Linux → get Linux binary
  - OR use GitHub Actions (Phase 4.2) for automated multi-platform builds

### 4.2 GitHub Actions Workflow
- [ ] Task: Create `.github/workflows/build-updater.yml`
- [ ] Task: Configure matrix builds for Windows, macOS, Linux
- [ ] Task: Configure artifact upload on release tags
- [ ] Task: Test manual workflow trigger
- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)

## Phase 5: Documentation and Release

### 5.1 User Documentation
- [ ] Task: Create `docs/updater/installation.md` - installation guide
- [ ] Task: Create `docs/updater/usage.md` - user guide
- [ ] Task: Update main `README.md` with updater section

### 5.2 Developer Documentation
- [ ] Task: Update `exporter/README.md` with updater module info
- [ ] Task: Create `exporter/updater/DEVELOPMENT.md` - build instructions
- [x] Task: Final code review and linting (`uv run ruff check --fix && uv run ruff format`)
- [ ] Task: Conductor - User Manual Verification 'Phase 5' (Protocol in workflow.md)

## Implementation Notes

- Use Flet for UI (consistent with DPD GUI2)
- Use `pathlib.Path` for all file operations (cross-platform)
- Use `platform` module for OS detection
- GitHub API rate limit: 60 requests/hour for unauthenticated requests (sufficient for this use case)
- GoldenDict release asset naming: Look for `dpd-goldendict-*.zip` pattern
