# Implementation Plan - Integrate Play Button into GoldenDict Exporter

## Phase 0: Research & Documentation
- [x] Task: Document Exporter Architecture
- [x] Task: Conductor - User Manual Verification 'Document Exporter Architecture' (Protocol in workflow.md)

## Phase 1: Template and Logic Updates
- [x] Task: Update `exporter/goldendict/templates/dpd_button_box.html`
    -   Add the SVG play button HTML structure, mirroring the WebApp template.
    -   Use the variable `${play_button}` which will be passed from the python logic.
- [x] Task: Update `exporter/goldendict/export_dpd.py`
    -   In the button rendering logic (around line 580), generate the `play_button` HTML.
    -   Ensure `i.lemma_clean` is used for the `headword` argument in `playAudio`.
    -   Pass `play_button` to the `button_box_templ.render` call.
- [x] Task: Conductor - User Manual Verification 'Template and Logic Updates' (Protocol in workflow.md)

## Phase 2: JavaScript Implementation
- [x] Task: Update `exporter/goldendict/javascript/main.js`
- [x] Task: Conductor - User Manual Verification 'JavaScript Implementation' (Protocol in workflow.md)

## Phase 2.5: Audio Availability Check
- [x] Task: Create `get_audio_set` helper
- [x] Task: Integrate Audio Check into Exporter
- [x] Task: Conductor - User Manual Verification 'Audio Availability Check' (Protocol in workflow.md)

## Phase 3: Final Verification
- [x] Task: Build GoldenDict Export
- [x] Task: Conductor - User Manual Verification 'Final Verification' (Protocol in workflow.md)
