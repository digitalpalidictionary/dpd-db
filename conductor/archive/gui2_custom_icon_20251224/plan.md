# Implementation Plan: Custom Application Icon for DPD GUI2

This plan follows the hybrid approach of setting the window icon programmatically in Flet and creating a Linux `.desktop` file for full system integration on Linux Mint.

## Phase 1: Asset Preparation
Goal: Ensure the application has a dedicated icon file in its own assets directory.

- [x] Task: Create the `gui2/assets/` directory if it doesn't exist.
- [x] Task: Copy `identity/logo/dpd-logo-512.png` to `gui2/assets/icon.png`.
- [x] Task: Conductor - User Manual Verification 'Asset Preparation' (Protocol in workflow.md)

## Phase 2: Programmatic Icon Implementation
Goal: Set the window icon in the Flet application code.

- [x] Task: Update `gui2/main.py` to set `page.window.icon` pointing to the new asset.
- [x] Task: Conductor - User Manual Verification 'Programmatic Icon Implementation' (Protocol in workflow.md)

## Phase 3: Linux System Integration
Goal: Create a `.desktop` file to ensure the icon is correctly displayed in the taskbar and Alt-Tab menu.

- [x] Task: Create `dpd-gui2.desktop` in the project root or a helper script to generate it.
- [x] Task: Verify the `Exec` path in the `.desktop` file correctly points to `scripts/cl/dpd-gui2`.
- [x] Task: Conductor - User Manual Verification 'Linux System Integration' (Protocol in workflow.md)

## Phase 4: Documentation & Cleanup
Goal: Ensure the changes are documented and the project state is clean.

- [x] Task: Update `gui2/README.md` to mention the new assets and how the icon is managed.
- [x] Task: Conductor - User Manual Verification 'Documentation & Cleanup' (Protocol in workflow.md)
