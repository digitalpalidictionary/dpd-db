# Specification: EPD Integration into Kindle Export

## Overview
This track includes the English to Pāḷi Dictionary (EPD) as a distinct, searchable section within the existing DPD Kindle export. Currently, the Kindle export only contains Pāḷi to English entries. This enhancement allows users to look up English words to find their Pāḷi equivalents within the same dictionary file.

## Functional Requirements
- **EPD Section Integration:** Add a dedicated section for EPD at the end of the Pāḷi dictionary entries within the Kindle EPUB/MOBI.
- **Full Scope Coverage:** Include all English headwords available in the `Lookup.epd` table, regardless of the Pāḷi EBT filtering.
- **Alphabetical Organization:** Organize the EPD section alphabetically A-Z (English letters) to facilitate browsing and indexing. Files named `epd_0_a.xhtml`, `epd_1_b.xhtml`, etc.
- **Navigation & TOC:** 
    - Add an entry for "English to Pāḷi Dictionary" in the Kindle Table of Contents (TOC).
    - Use a distinct visual separator (page break and large header "English to Pāḷi Dictionary") between the Pāḷi and EPD sections.
- **Entry Formatting:** EPD entries display: English headword, followed by Pāḷi equivalents with POS and meaning. Format: `<b class='epd'>{lemma_clean}</b> {pos}. {meaning_plus_case}`

## Technical Requirements
- **Templates:** 
    - Create `ebook_epd_entry.html` for EPD entries with `<idx:entry name="English">` tags
    - Create `ebook_epd_letter.html` for EPD section headers with English alphabet
- **Path Configuration:** Add `ebook_epd_entry_templ_path` and `ebook_epd_letter_templ_path` to `tools/paths.py`
- **Exporter Logic:** Update `exporter/kindle/kindle_exporter.py`:
    - Create `render_epd_xhtml()` function to query EPD data from `Lookup` table where `Lookup.epd != ""`
    - Group EPD entries by first English letter (A-Z) using `epd_letter_dict`
    - Generate XHTML files: `epd_0_a.xhtml` through `epd_25_z.xhtml`
    - Update `ebook_content_opf.html` template to statically include 26 EPD files in `<manifest>` and `<spine>` after Pāḷi files
    - Add EPD section to Kindle TOC/nav.xhtml
- **Searchability:** EPD entries use `<idx:entry name="English">` with `<idx:orth value="{english_headword}">` for Kindle dictionary search

## Acceptance Criteria
- [ ] A single EPUB (and subsequently MOBI) is generated containing both DPD and EPD sections.
- [ ] The Kindle TOC contains a link to the "English to Pāḷi Dictionary" section.
- [ ] Searching for an English word in the Kindle dictionary correctly identifies and jumps to the EPD entry.
- [ ] The EPD section is visually distinct from the Pāḷi section.
- [ ] All English entries from the database are present in the export.

## Out of Scope
- Creating a separate `.mobi` file specifically for EPD.
- Modifying the Pāḷi entry scope or logic.
