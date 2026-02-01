# Implementation Plan: EPD Integration into Kindle Export

## Phase 1: Templates and Path Configuration
- [ ] Task: Create EPD entry template.
    - [ ] Create `exporter/kindle/templates/ebook_epd_entry.html`:
        ```html
        <idx:entry name="English" scriptable="yes" spell="yes" id="${counter}">
            <idx:short>
                <idx:orth value="${english_headword}"><h4>${english_headword}</h4></idx:orth>
                ${pali_equivalents}
            </idx:short>
        </idx:entry>
        <hr class="dpd" />
        ```
- [ ] Task: Create EPD letter template.
    - [ ] Create `exporter/kindle/templates/ebook_epd_letter.html`:
        - Header: "English to Pāḷi Dictionary"
        - Section heading with English letter (A, B, C, etc.)
- [ ] Task: Update paths configuration.
    - [ ] Add to `tools/paths.py`:
        - `self.ebook_epd_entry_templ_path`
        - `self.ebook_epd_letter_templ_path`

## Phase 2: Update content.opf Template
- [ ] Task: Hardcode EPD files in content.opf.
    - [ ] Add 26 `<item>` entries to `<manifest>` in `ebook_content_opf.html`:
        - `epd_0_a.xhtml` through `epd_25_z.xhtml`
    - [ ] Add 26 `<itemref>` entries to `<spine>` after Pāḷi files:
        - `epd_0_a.xhtml` through `epd_25_z.xhtml`

## Phase 3: Exporter Logic - Data Processing
- [ ] Task: Implement EPD data fetching and rendering.
    - [ ] Create `render_epd_xhtml(pth, id_counter)` function in `kindle_exporter.py`:
        - Query `Lookup` table where `Lookup.epd != ""`
        - Create `epd_letter_dict` with English alphabet (A-Z)
        - For each entry, unpack EPD data: `list[tuple[str, str, str]]` = (lemma_clean, pos, meaning_plus_case)
        - Render each Pāḷi equivalent: `<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}`
        - Group by first letter of English headword
        - Save to `epd_0_a.xhtml` through `epd_25_z.xhtml`
        - Return updated `id_counter`

## Phase 4: Integration into EPUB Structure
- [ ] Task: Update main rendering orchestration.
    - [ ] Modify `main()` in `kindle_exporter.py`:
        - Call `render_dpd_xhtml(pth)` (rename existing `render_xhtml`)
        - Call `render_epd_xhtml(pth, id_counter)` after DPD completion
- [ ] Task: Update TOC generation.
    - [ ] Add "English to Pāḷi Dictionary" entry to `nav.xhtml` or TOC.ncx
    - [ ] Link to first EPD file `epd_0_a.xhtml`

## Phase 5: Verification and Checkpointing
- [ ] Task: Verify EPUB Structure.
    - [ ] Run the exporter and inspect `OEBPS/Text/` directory:
        - Confirm `epd_0_a.xhtml` through `epd_25_z.xhtml` exist
        - Verify files are listed in `content.opf` manifest and spine
- [ ] Task: User Manual Verification.
    - [ ] Conductor - User Manual Verification 'EPD Integration' (Protocol in workflow.md)
    - [ ] Test Kindle dictionary search for English words
    - [ ] Verify EPD section appears in Kindle TOC
