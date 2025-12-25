# Specification: Custom Application Icon for DPD GUI2

## Overview
This track aims to replace the default Flet (Linux cog) icon with the custom DPD logo for the `gui2` application on Linux Mint. This will ensure that the application displays a professional and recognizable icon in the window title bar, the taskbar, and when switching applications via Alt-Tab.

## Functional Requirements
- **Programmatic Icon Setting:** Update `gui2/main.py` to set the window icon using `page.window.icon`.
- **Linux Integration:** Create a `.desktop` entry file template to ensure the Linux Mint window manager correctly associates the DPD logo with the running process.
- **Icon Format Conversion:** If necessary, convert the SVG logo to a high-resolution PNG format suitable for the `.desktop` file and Flet's `window.icon` property.

## Technical Details
- **Icon Source:** `identity/logo/dpd-logo-dark.svg` (or available PNGs like `dpd-logo-512.png`)
- **Icon Destination:** A standard location within the project (e.g., `gui2/assets/icon.png`) or an absolute path in the `.desktop` file.
- **Launch Script:** `scripts/cl/dpd-gui2`
- **Flet Property:** `page.window.icon`

## Acceptance Criteria
- When the `gui2` application is running on Linux Mint, the DPD logo is visible in the window title bar.
- When pressing Alt-Tab, the DPD logo (instead of the default cog) is displayed for the `gui2` application.
- The `.desktop` file correctly launches the application using the established `scripts/cl/dpd-gui2` path.

## Out of Scope
- Creating installers or packages (e.g., .deb files).
- Modifying icons for other operating systems (Windows/macOS) unless they happen to work via the programmatic change.
