# Implementation Plan: EPD Integration into Kindle Export

## Phase 1: Templates and Path Configuration
- [x] Task: Create EPD entry template.
    - [x] Create `exporter/kindle/templates/ebook_epd_entry.html`
- [x] Task: Create EPD letter template.
    - [x] Create `exporter/kindle/templates/ebook_epd_letter.html`
- [x] Task: Update paths configuration.
    - [ ] Add to `tools/paths.py`:
        - `self.ebook_epd_entry_templ_path`
        - `self.ebook_epd_letter_templ_path`

## Phase 2: Update content.opf Template
- [x] Task: Hardcode EPD files in content.opf.
    - [x] Add 26 `<item>` entries to `<manifest>` in `ebook_content_opf.html`
    - [x] Add 26 `<itemref>` entries to `<spine>` after Pāḷi files

## Phase 3: Exporter Logic - Data Processing
- [x] Task: Implement EPD data fetching and rendering.
    - [x] Create `render_epd_xhtml(pth, id_counter)` function in `kindle_exporter.py`
    - [x] Create `render_epd_entry()` function for single EPD entry rendering
    - [x] Create `render_epd_letter_templ()` function for letter grouping

## Phase 4: Integration into EPUB Structure
- [x] Task: Update main rendering orchestration.
    - [x] Rename `render_xhtml()` to `render_dpd_xhtml()`
    - [x] Modify `main()` to call both `render_dpd_xhtml()` and `render_epd_xhtml()`
- [x] Task: Update TOC generation.
    - [x] Add "English to Pāḷi Dictionary" entry to `nav.xhtml`
    - [x] Add all 26 letter links (A-Z) to the TOC

## Phase 5: Verification and Checkpointing
- [x] Task: Verify EPUB Structure.
    - [x] Write and run unit tests for EPD functionality (11 tests passing)
    - [x] Fix linting errors
    - [ ] Run the exporter and inspect `OEBPS/Text/` directory (manual)
- [ ] Task: User Manual Verification.
    - [ ] Conductor - User Manual Verification 'EPD Integration' (Protocol in workflow.md)
    - [ ] Test Kindle dictionary search for English words
    - [ ] Verify EPD section appears in Kindle TOC
