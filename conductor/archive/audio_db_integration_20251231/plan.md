# Plan: Audio Database Release Integration

This plan integrates the building and uploading of the audio database into the standard DPD component generation workflow.

## Phase 1: Configuration and Model Updates
- [x] Task: Update `tools/configger.py` to include `make_audio_db` and `upload_audio_db` in the `[exporter]` section with default values.
- [x] Task: Update `scripts/build/config_uposatha_day.py` to enable both flags on Uposatha days.
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Script Logic Updates
- [x] Task: Implement early exit logic in `audio/db_create.py` based on `config_test("exporter", "make_audio_db", "no")`.
- [x] Task: Implement early exit logic in `audio/db_release_upload.py` based on `config_test("exporter", "upload_audio_db", "no")`.
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Pipeline Integration
- [x] Task: Add the audio scripts to the `COMMANDS` list in `scripts/bash/generate_components.py`.
- [x] Task: Verify the full build process by running `scripts/bash/generate_components.py` (simulating or checking config states).
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
