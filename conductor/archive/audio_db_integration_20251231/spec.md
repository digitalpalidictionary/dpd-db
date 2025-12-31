# Specification: Audio Database Release Integration

## Overview
Integrate the building and uploading of the audio database into the standard DPD component generation workflow. The audio database will be built during every run (by default), but only uploaded to GitHub during the monthly Uposatha release or when manually enabled.

## Functional Requirements
1.  **Config Settings:**
    -   Update `tools/configger.py` to include `make_audio_db` and `upload_audio_db` in the `[exporter]` section.
    -   Default values: `make_audio_db = "yes"`, `upload_audio_db = "no"`.
2.  **Early Exit Logic:**
    -   Modify `audio/db_create.py` to check `make_audio_db` and return early if set to `"no"`.
    -   Modify `audio/db_release_upload.py` to check `upload_audio_db` and return early if set to `"no"`.
3.  **Uposatha Automation:**
    -   Update `scripts/build/config_uposatha_day.py` to set both `make_audio_db` and `upload_audio_db` to `"yes"` when it's an Uposatha day.
4.  **Pipeline Integration:**
    -   Add `audio/db_create.py` and `audio/db_release_upload.py` to the `COMMANDS` list in `scripts/bash/generate_components.py`.
    -   Placement should be after database-related updates but before the final "dealbreakers" check.

## Acceptance Criteria
- [ ] Running `generate_components.py` on a non-Uposatha day builds the audio database (creating the tarball) but does not upload it.
- [ ] Running `generate_components.py` on an Uposatha day both builds and uploads the audio database to GitHub.
- [ ] Setting `make_audio_db = "no"` in `config.ini` prevents the audio database build.
- [ ] Setting `upload_audio_db = "yes"` in `config.ini` forces an upload regardless of the date.
