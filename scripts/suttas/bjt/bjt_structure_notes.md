# BJT Structure & Extraction Notes

This document details the structural idiosyncrasies of each BJT book (DN, MN, SN, AN, KN) and how the scripts handle them to produce a consistent TSV format.

## Project Overview

### What is BJT?
- **BJT** = Burmese Buddhist Text (Burmese Tipiṭaka)
- Contains the complete Pāli Canon in Burmese script and romanized versions
- Source files located in: `resources/dpd_submodules/bjt/public/static/roman_json/`
- Files follow naming pattern: `dn*.json`, `mn*.json`, `sn*.json`, `an*.json`, `kn*.json`

### Project Structure
```
scripts/suttas/bjt/
├── process_kn.py          # Main runner for all KN books
├── dn.py                  # Dīgha Nikāya extractor
├── mn.py                  # Majjhima Nikāya extractor  
├── sn.py                  # Saṃyutta Nikāya extractor
├── an.py                  # Aṅguttara Nikāya extractor
├── kn*.py                 # Individual KN book extractors
├── bjt_structure_notes.md # This documentation file
└── [supporting files]
```

### Output Format
All scripts produce TSV files with consistent schema:
- `bjt_sutta_code`: Internal coding system (e.g., `dn-1-1`, `kn-thag-16-1-1`)
- `bjt_web_code`: Web URL mapping (often simplified version of sutta_code)
- `bjt_filename`: Source JSON file name
- `bjt_book_id`: Numeric book identifier
- `bjt_page_num`: Page number in source
- `bjt_page_offset`: Page offset in source
- `bjt_piṭaka`: Piṭaka level (e.g., `suttantapiṭake`)
- `bjt_nikāya`: Nikāya level (e.g., `khuddakanikāyo`)
- `bjt_book`: Book level (e.g., `theragāthāpāḷi`)
- `bjt_minor_section`: Minor section (e.g., `1. ekakanipāto`)
- `bjt_vagga`: Vagga level (when applicable)
- `bjt_sutta`: Sutta name

### Coding System Logic
- **DN/MN**: `dn-{book}-{sutta}` or `mn-{book}-{sutta}`
- **SN**: `sn-{mahāvagga}-{saṃyutta}-{vagga}-{sutta}`
- **AN**: `an-{nipāta}-{paṇṇāsa}-{vagga}-{sutta}` (paṇṇāsa optional)
- **KN**: `kn-{book_abbr}-{nipāta}-{vagga}-{sutta}` (vagga often omitted for later nipātas)

### Web Code Mapping Rules
- **KN 8 (Theragāthā)**: Nipātas 3+ have 2-digit web codes (no vagga)
- **KN 8**: Nipātas > 14 map to web nipātas starting from 15
- **KN 9 (Therīgāthā)**: Nipātas > 9 map to web nipātas starting from 10
- **Special Cases**: Sumedhātherīgāthā = `kn-thig-16-1`

### Common Challenges & Solutions
1. **Regex Issues**: Source text may have periods, brackets, or special characters
   - Solution: Use flexible patterns like `r"nipāt"` instead of `r"nipāto?$"`
   
2. **Missing Numbered Headings**: Some entries lack numbered headings
   - Solution: Special case handling with fallback logic
   
3. **Hierarchy Variations**: Different books have different structural depths
   - Solution: Book-specific extraction logic
   
4. **Web Code Complexity**: Web URLs don't always match internal coding
   - Solution: Separate web_code generation with mapping logic

### Recent Fixes (as of Dec 2025)
- **KN 8**: Fixed nipāta detection regex, implemented 2-digit web codes for nipātas 3+
- **KN 9**: Fixed nipāta fullstop removal, implemented web code mapping for nipātas > 9
- **Both**: Added Sumedhātherīgāthā special case handling

### Testing & Validation
- Run individual scripts: `python scripts/suttas/bjt/kn8_thag.py`
- Verify output: Check TSV files for correct web_code mapping
- Key test cases:
  - `kn-thag-16-1-1` → `kn-thag-15-1` (Aññākoṇḍaññattheragāthā)
  - `kn-thag-3-1-1` → `kn-thag-3-1` (2-digit format)
  - `kn-thig-1-2` → `kn-thig-16-1` (Sumedhātherīgāthā)

### File Locations
- **Source JSON**: `resources/dpd_submodules/bjt/public/static/roman_json/`
- **Scripts**: `scripts/suttas/bjt/`
- **Output TSV**: `scripts/suttas/bjt/*.tsv`
- **Consolidated**: `scripts/suttas/bjt/kn.tsv` (from process_kn.py)

### Dependencies
- Python 3.13+
- Standard library only (csv, json, re, pathlib)
- Rich library for colored output
- ProjectPaths from `tools.paths`

### Maintenance Notes
- Always test with `python scripts/suttas/bjt/kn8_thag.py` after changes
- Check for new nipātas in source JSON files
- Web code mappings may need updates for new content
- Regex patterns are sensitive to source text formatting changes

## General Approach
- **Pipelines**: Dedicated scripts for each Nikāya (`dn.py`, `mn.py`, `sn.py`, `an.py`) and individual KN books (`kn*_*.py`).
- **Columns**: All output records strictly follow the schema: `bjt_sutta_code`, `bjt_web_code`, `bjt_filename`, `bjt_book_id`, `bjt_page_num`, `bjt_page_offset`, `bjt_piṭaka`, `bjt_nikāya`, `bjt_book`, `[hierarchy columns]`, `bjt_vagga`, `bjt_sutta`.
- **Web Code**: A `bjt_web_code` column duplicates the `bjt_sutta_code` initially, intended for manual mapping to web URLs where they differ.

## Extraction Scripts Updates

### KN 8: Theragāthā (kn8_thag.py) & KN 9: Therīgāthā (kn9_thig.py)
**Recent fixes implemented:**

#### KN 8: Theragāthā
1. **Fullstop Removal**: Fixed regex to remove trailing fullstops from nipāta headings (e.g., `"1. ekakanipāto."` → `"1. ekakanipāto"`)
2. **No Vaggas from Tikanipāto**: Updated web code generation to handle nipātas 3+ which have no vagga divisions:
   - Web codes only have 2 digits: `kn-thag-3-1-1` → `kn-thag-3-1`
   - Applies to all nipātas from 3 (Tikanipāto) onwards
3. **Web Code Mapping**: Updated web code generation to map nipātas > 14 (cuddasanipāto) to continuous web nipāta numbering starting from 15:
   - `kn-thag-16-1-1` → `kn-thag-15-1`
   - `kn-thag-20-1-1` → `kn-thag-16-1`

#### KN 9: Therīgāthā
1. **Fullstop Removal**: Fixed regex to remove trailing fullstops from nipāta headings (e.g., `"1. ekakanipāto."` → `"1. ekakanipāto"`)
2. **Web Code Mapping**: Updated web code generation to map nipātas > 9 (navakanipāta) to continuous web nipāta numbering starting from 10
3. **Sumedhātherīgāthā Handling**: Added special case handling for the final entry Sumedhātherīgāthā which lacks a numbered heading:
   - Automatically assigns `kn-thig-1-2` as sutta code
   - Automatically assigns `kn-thig-16` as web code
   - Correctly places it in the "mahānipāto" section

#### KN 10: Apadāna
1. **Two-Section Structure**: Fixed handling of separate Therāapadāna (section 1) and Therīapadāna (section 2)
2. **Regex Pattern**: Updated to handle both formats: `"1. sāriputtattherāpadānaṃ"` and `"1 sumedhāpadānaṃ"`
3. **Web Code Format**: Implemented correct `kn-ap-{section}-{vagga}-{sutta}` format
4. **Incremental Counting**: Fixed counters to reset for each vagga within a section
5. **Section Detection**: Added automatic detection based on book title ("therīapadāna" → section 2)

---

## 1. Dīgha Nikāya (DN)
- **Script**: `dn.py`
- **Structure**: `Piṭaka -> Nikāya -> Vagga -> Sutta`
- **Mapping**:
    - `bjt_book`: Mapped to `vaggo` (e.g., *Sīlakkhandhavaggo*).
    - `bjt_vagga`: **Empty**. (In DN, the 'book' level acts as the vagga).
- **Idiosyncrasies**: Simple structure. 3 main books (silakkhandha, mahavagga, pathika) distinct by filename/vagga heading.

## 2. Majjhima Nikāya (MN)
- **Script**: `mn.py`
- **Structure**: `Piṭaka -> Nikāya -> Paṇṇāsa -> Vagga -> Sutta`
- **Mapping**:
    - `bjt_book`: Mapped to `paṇṇāsa` (e.g., *Mūlapaṇṇāsako*).
    - `bjt_vagga`: Mapped to `vaggo`.
- **Idiosyncrasies**: Groups of 50 suttas (Paṇṇāsa).

## 3. Saṃyutta Nikāya (SN)
- **Script**: `sn.py`
- **Structure**: `Piṭaka -> Nikāya -> Mahāvagga -> Saṃyutta -> Vagga -> Sutta`
- **Mapping**:
    - `bjt_mahāvagga`: Mapped to `mahāvagga` (The 5 large divisions, e.g., *Sagāthavaggo*).
    - `bjt_book`: Mapped to `saṃyutta` (The connected discourses, e.g., *Devatāsaṃyuttaṃ*).
    - `bjt_vagga`: Mapped to `vaggo` (Sub-groups within a Saṃyutta).
- **Idiosyncrasies**: Deep hierarchy. Sutta codes include outer vagga number (e.g., `sn-1-1-1-1`).

## 4. Aṅguttara Nikāya (AN)
- **Script**: `an.py`
- **Structure**: `Piṭaka -> Nikāya -> Nipāta -> Paṇṇāsa -> Vagga -> Sutta`
- **Mapping**:
    - `bjt_book`: Mapped to `nipāta` (e.g., *Ekaka Nipāto*).
    - `bjt_paṇṇāsa`: Mapped to `paṇṇāsa` (Only present in larger Nipātas).
    - `bjt_vagga`: Mapped to `vaggo`.
- **Idiosyncrasies**:
    - **Peyyāla Ranges**: Some entries are ranges (e.g., `11. 3. 9-48.`).
    - **Numbered Suttas**: Suttas in the first few books (AN 1) often lack names and are just numbers (`1. 1. 1.`).
    - **Variable Hierarchy**: Smaller Nipātas skip the `Paṇṇāsa` level.

---

## 5. Khuddaka Nikāya (KN)
**Script Runner**: `process_kn.py` (Runs `kn1_khp.py` ... `kn19_mil.py`)

### KN 1: Khuddakapāṭha (KHP)
- **Structure**: Simple list of suttas.
- **Handling**: Identifies suttas starting with a number. No vagga divisions.

### KN 2: Dhammapada (DHP)
- **Structure**: Verses grouped into Vaggas. No individual "suttas".
- **Handling**: **Vaggas are treated as the main entry**. Vagga name -> `bjt_vagga`. `bjt_sutta` is empty.

### KN 3: Udāna (UD)
- **Structure**: `Vagga -> Sutta`.
- **Handling**: Standard extraction.

### KN 4: Itivuttaka (ITI)
- **Structure**: `Nipāta -> Vagga -> Sutta`.
- **Handling**: Handles sections like `Catukkanipāto` which lack explicit Vaggas by using consecutive numbering logic (`4. 1. 1.`).
- **Web Code Exception**: For *Catukkanipāto*, `bjt_web_code` omits the vagga number (e.g., `kn-iti-4-11` instead of `kn-iti-4-1-11`).

### KN 5: Sutta Nipāta (SNP)
- **Structure**: `Vagga -> Sutta`.
- **Handling**: Standard extraction.

### KN 6: Vimānavatthu (VV) & KN 7: Petavatthu (PV)
- **Structure**: `Vagga -> Vatthu`.
- **Handling**: Extracts stories identified by `vimānaṃ` or `vatthuṃ`.

### KN 8: Theragāthā (THAG) & KN 9: Therīgāthā (THIG)
- **Structure**: `Nipāta -> Vagga -> Gāthā`.
- **Handling**: Regex `therī?gāthā` handles spelling variations.
- **Idiosyncrasies**:
    - **Fullstop Removal**: Nipāta headings like `"1. ekakanipāto."` have the trailing fullstop removed to become `"1. ekakanipāto"`.
    - **No Vaggas from Tikanipāto**: From nipāta 3 (Tikanipāto) onwards, there are no vagga divisions. Web codes for these nipātas only have 2 digits: `kn-{book_abbr}-{nipata}-{sutta_num}`. For example, `kn-thag-3-1-1` maps to `kn-thag-3-1`.
    - **Web Code Exception**: For nipātas beyond 14 (cuddasanipāto), the `bjt_web_code` uses a continuous web nipāta numbering starting from 15. The web code structure simplifies to 2 digits for nipātas 3+, typically to `kn-{book_abbr}-{web_nipata}-{sutta_num}`, where `sutta_num` is a running counter within that web nipāta. For example, `kn-thag-16-1-1` maps to `kn-thag-15-1`.
    - **Special Case - Sumedhātherīgāthā**: The final entry Sumedhātherīgāthā appears in the "mahānipāto" section without a numbered heading. It's assigned:
        - **Sutta code**: `kn-thig-1-2` (second entry in mahānipāto)
        - **Web code**: `kn-thig-16` (mahānipāto maps to web nipāta 16)

### KN 10: Apadāna (AP)
- **Structure**: `Vagga -> Apadāna` (split into Therā and Therī sections).
- **Handling**: Extracts entries matching `^\d+\.?\s+.+(ā|)padāna` pattern.
- **Idiosyncrasies**:
    - **Two Sections**: Therāapadāna (section 1) and Therīapadāna (section 2)
    - **Web Code Format**: `kn-ap-{section}-{vagga}-{sutta}` where:
        - Section: 1 for therā, 2 for therī
        - Vagga: Vagga number within section
        - Sutta: Incremental count within each vagga
    - **Numbering Variations**: 
        - Therā entries: `"1. sāriputtattherāpadānaṃ"` (with period)
        - Therī entries: `"1 sumedhāpadānaṃ"` (without period)
    - **Incremental Counting**: Each vagga starts counting from 1, resets for new vagga
    - **Example**: `kn-ap-1-56-4` = Therā section, vagga 56, 4th sutta (kimbilattherāpadānaṃ)

### KN 11: Buddhavamsa (BV)
- **Structure**: Chronicles identified by `kaṇḍo` or `kathā`. No standard "vagga".
- **Handling**: Extracts headings ending in `kaṇḍo` or `kathā`.

### KN 12: Cariyāpiṭaka (CP)
- **Structure**: `Vagga -> Cariyā`.
- **Handling**: `vaggo` usually identified by `pāramitā`.

### KN 13: Jātaka (JAT)
- **Structure**: `Nipāta -> Vagga -> Jātaka`.
- **Handling**: Captures `nipāto`, `vaggo`, and stories ending in `jātakaṃ`.

### KN 14: Mahāniddesa (MN) & KN 15: Cūḷaniddesa (NC)
- **Structure**: Commentary style.
- **Handling**: Keyword `niddeso` identifies the main sections.

### KN 16: Paṭisambhidāmagga (PS)
- **Structure**: `Vagga -> Kathā`.
- **Handling**: Identifies `vaggo`, `kathā`, and `paṇṇāsa`.

### KN 17: Nettippakaraṇa (NETT)
- **Structure**: Treatise. `Vāra` instead of Vagga.
- **Handling**: `vāro` -> Vagga. Suttas: `hāro`, `nayo`, `viññatti`, `gāthā`, `vibhaṅgo`, `sampāto`.

### KN 18: Peṭakopadesa (PETK)
- **Structure**: Treatise, less structured headings.
- **Handling**: Relies on numbered headings.

### KN 19: Milindapañha (MIL)
- **Structure**: Questions (`Pañha`).
- **Handling**: Searches for `pañho` or numbered questions. (Often missing in BJT source).
