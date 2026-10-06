# exporter/epitaka/

## Purpose & Rationale
The `epitaka/` directory refreshes the DPD data inside the ePitaka app on this machine. The app reads DPD from its own `dpd-dictionary.db`, which its maintainer builds privately and ships rarely. This exporter rebuilds that file from the live `dpd.db` in the same format, so the local app has today's data. Local only, not for public release.

## Architectural Logic
1.  **Rendering:** `epitaka_exporter.py` builds each headword's and root's `meaning_html` with plain f-strings, matching the upstream file byte for byte on the same data. Root family tables come from `FamilyRoot.html`.
2.  **Mapping:** Every `lookup` row is copied; root keys are mapped to root ids, which follow the last headword id.
3.  **Search table:** ePitaka's own `tool/build_dpd_norm.dart` prebuilds the app's diacritic-folded search table, so the app does not build it at launch.
4.  **Install:** If ePitaka is running it is closed, the file is copied into the app's folder through SQLite's backup, and the app is reopened through its desktop entry. If the app does not close within 30 s, the install is skipped.

## Relationships & Data Flow
- **Source:** Consumes `DpdHeadword`, `DpdRoot`, `FamilyRoot` and `Lookup` data from **db/**.
- **Config:** `[exporter] make_epitaka`, `[epitaka] db_path` (the app's `dpd-dictionary.db`), `[epitaka] repo_path` (the ePitaka repo, for the Dart tool).
- **Artifacts:** `output/dpd-dictionary.db`, plus `output/baseline_dpd-dictionary.db`, the saved upstream file. Install refuses to run without the baseline.

## Interface
- **Export:** `cd ~/MyFiles/3_Active/dpd-db && just export-epitaka`
