# exporter/epitaka/

## Purpose & Rationale
The `epitaka/` directory puts the current DPD data into the ePitaka app on this machine. The app reads DPD from `dpd-mobile.db`, the same file the mobile exporter builds. This script copies that file into the app's folder. Local only, not for public release.

## Architectural Logic
1.  **Source:** `exporter/share/dpd-mobile.db`, built by `exporter/mobile/mobile_exporter.py`. In the full export it runs after the mobile exporter, so each export installs a fresh copy.
2.  **Install:** If ePitaka is running it is closed, the file is copied into the app's folder through SQLite's backup (the app's file is in WAL mode, so a plain file copy is unsafe), and the app is reopened through its desktop entry. If the app does not close within 30 s, the install is skipped.

## Relationships & Data Flow
- **Config:** `[exporter] make_epitaka`, `[epitaka] db_path` (the app's `dpd-mobile.db`; the script refuses any other file name).
- **No database access:** the script never opens `dpd.db`.

## Interface
- **Install:** `cd ~/MyFiles/3_Active/dpd-db && just export-epitaka`
