# Plan: Sync Sutta Info to GoldenDict

## Phase 1: Analysis & Template Mapping
- [x] Task: Compare `dpd_headword.html` and `dpd_sutta_info.html` to identify all missing/mismatched fields.
- [x] Task: Create a field mapping document for Jinja2 to Mako conversion.
- [x] Task: Conductor - User Manual Verification 'Analysis & Template Mapping' (Protocol in workflow.md)

## Phase 2: Implement BJT Section and SC Express Fix
- [x] Task: Create Render Test: Write a Python script to render `dpd_sutta_info.html` and verify the presence of BJT fields.
- [x] Task: Implement BJT Section: Port and convert BJT data from Webapp to GoldenDict template.
- [x] Task: Fix SC Express Label: Update the label from "SC Voice" to "SC Express" and verify link logic.
- [x] Task: Conductor - User Manual Verification 'Implement BJT Section and SC Express Fix' (Protocol in workflow.md)

## Phase 3: Full Synchronization & Cleanup
- [x] Task: Sync Remaining Fields: Ensure all other sections (CST, SC, DV) match the Webapp source of truth.
- [x] Task: Verify Template Logic: Ensure string methods (like `.replace()`) and conditionals work correctly in Mako.
- [x] Task: Conductor - User Manual Verification 'Full Synchronization & Cleanup' (Protocol in workflow.md)
