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
- `bjt_sutta_code`: Internal coding system preserving original text format (e.g., `1. 1. 1.`, `1. 15. 14-16`)
- `bjt_web_code`: Web URL mapping (sequential numbering within vagga)
- `bjt_filename`: Source JSON file name
- `bjt_book_id`: Numeric book identifier
- `bjt_page_num`: Page number in source
- `bjt_page_offset`: Page offset in source
- `bjt_piṭaka`: Piṭaka level (e.g., `suttantapiṭake`)
- `bjt_nikāya`: Nikāya level (e.g., `aṅguttaranikāyo`)
- `bjt_book`: Book level (e.g., `theragāthāpāḷi`)
- `bjt_paṇṇāsa`: Paṇṇāsa level (when applicable, e.g., `1. ekakanipāto`)
- `bjt_vagga`: Vagga level (when applicable)
- `bjt_sutta`: Sutta name

### Coding System Logic
- **DN/MN**: `dn-{book}-{sutta}` or `mn-{book}-{sutta}`
- **SN**: `sn-{mahāvagga}-{saṃyutta}-{vagga}-{sutta}`
- **AN**: `an-{nipāta}-{paṇṇāsa}-{vagga}-{sutta}` (paṇṇāsa optional)
- **KN**: `kn-{book_abbr}-{nipāta}-{vagga}-{sutta}` (vagga often omitted for later nipātas)

### Web Code Generation Rules
- **Sequential Numbering**: Web codes increment by 1 within each vagga
- **Vagga Reset**: Counter resets to 1 at start of each new vagga
- **Range Handling**: For ranges (e.g., "1. 15. 14-16"), use previous + 1
- **Format**: `an-{nipāta}-{vagga}-{sequential_number}` for AN
- **Original Format**: `bjt_sutta_code` preserves exact text format with trailing period (e.g., "1. 1. 1.", "1. 15. 14-16.")

### Web Code Mapping Rules
- **AN**: Sequential numbering within each vagga, resets at vagga boundaries
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
- **AN**: Implemented book boundary detection, vagga-based web code reset, original format preservation
- **KN 8**: Fixed nipāta detection regex, implemented 2-digit web codes for nipātas 3+
- **KN 9**: Fixed nipāta fullstop removal, implemented web code mapping for nipātas > 9
- **Both**: Added Sumedhātherīgāthā special case handling

### Testing & Validation
- Run individual scripts: `python scripts/suttas/bjt/an.py`, `python scripts/suttas/bjt/kn8_thag.py`
- Verify output: Check TSV files for correct web_code mapping
- Key test cases:
  - **AN**: `1. 1. 1.` → `an-1-1-1`, `1. 2. 1.` → `an-1-2-1` (vagga reset)
  - **AN**: `1. 10. 21-30.` → `an-1-10-118`, `1. 10. 31.` → `an-1-10-119` (sequential)
  - **KN 8**: `kn-thag-16-1-1` → `kn-thag-15-1` (Aññākoṇḍaññattheragāthā)
  - **KN 8**: `kn-thag-3-1-1` → `kn-thag-3-1` (2-digit format)
  - **KN 9**: `kn-thig-1-2` → `kn-thig-16-1` (Sumedhātherīgāthā)

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
    - **Dual Sutta Code Patterns**: Two different patterns for locating sutta codes:
        - **Pattern 1** (an-1, an-2, an-3): Sutta codes in `heading` entries with `level: 1`
        - **Pattern 2** (an-4+): Sutta codes in `centered` entries with `level: 1`
    - **Book ID Mapping**: Specific book_id assignments based on filename:
        - an-1, an-2, an-3: book_id = 22
        - an-4: book_id = 23  
        - an-5: book_id = 24
        - an-6, an-7: book_id = 25
        - an-8, an-9: book_id = 26
        - an-10, an-11: book_id = 27
    - **Complex File Naming**: Some files have simple numbering (an-1, an-2) while others have complex numbering (an-3-2, an-4-3, etc.)
    - **Page Offset**: Always 0 in backup data

---

## 5. Khuddaka Nikāya (KN)
**Script Runner**: `process_kn.py` (Runs `kn1_khp.py` ... `kn19_mil.py`)

### KN 1: Khuddakapāṭha (KHP)
- **Structure**: Simple list of suttas.
- **Handling**: Identifies suttas starting with a number. No vagga divisions.
- **Idiosyncrasies**:
  - **Numbered Suttas**: Suttas are numbered 1-9 with simple headings like "1. saraṇagamanaṃ{1}"
  - **Footnote References**: Some sutta names contain footnote references in curly braces like "{1}" that need cleaning
  - **No Vagga Structure**: Unlike other KN books, KHP has no vagga divisions - just a simple list of suttas
  - **Mixed Entry Types**: Some numbered entries appear as "heading" type, others as different patterns

### KN 2: Dhammapada (DHP)
- **Structure**: Verses grouped into Vaggas. No individual "suttas".
- **Handling**: **Vaggas are treated as the main entry**. Vagga name -> `bjt_vagga`. `bjt_sutta` is empty.

### KN 3: Udāna (UD)
- **Structure**: `Vagga -> Sutta`.
- **Handling**: Standard extraction.
- **Idiosyncrasies**:
  - **Mixed Entry Types**: Sutta numbers appear in "centered" entries (like "1. 1.") not "heading" entries like other books
  - **Vagga Detection**: Vagga names appear in "heading" entries with level 2 (like "bodhivaggo paṭhamo")
  - **Sequential Processing**: Must process all entries on a page before moving to next page to properly detect vaggas before sutta numbers

### KN 4: Itivuttaka (ITI)
- **Structure**: `Nipāta -> Vagga -> Sutta`.
- **Handling**: Handles sections like `Catukkanipāto` which lack explicit Vaggas by using consecutive numbering logic (`4. 1. 1.`).
- **Idiosyncrasies**:
    - **Sutta Number Pattern**: Uses 3-part numbering `{nipāta_num}. {vagga_num}. {sutta_num}.` (e.g., "1. 1. 1.", "4. 1. 1.")
    - **Entry Type Detection**: Sutta numbers appear in `centered` entries with `level: 1`, not in `heading` entries like other books
    - **Web Code Exception**: For *Catukkanipāto*, `bjt_web_code` omits the vagga number (e.g., `kn-iti-4-11` instead of `kn-iti-4-1-11`)
    - **File Structure**: Single JSON file `kn-iti.json` contains all 4 nipātas
    - **Hierarchy Detection**: 
        - Nipāta headings: `level: 3` entries ending in "nipāto" (e.g., "ekakanipāto")
        - Vagga headings: `level: 2` entries ending in "vaggo" (e.g., "paṭhamo vaggo")
        - Sutta numbers: `level: 1` `centered` entries with pattern `^\d+\.\s*\d+\.\s*\d+\.$`

### KN 5: Sutta Nipāta (SNP)
- **Structure**: `Vagga -> Sutta`.
- **Handling**: Standard extraction.
- **Idiosyncrasies**:
    - **Multiple File Structure**: Split across 5 files (`kn-snp.json`, `kn-snp-2.json` through `kn-snp-5.json`) requiring custom natural sorting
    - **File Naming Pattern**: `kn-snp.json` (no number) for vagga 1, then `kn-snp-{vagga_num}.json` for vaggas 2-5
    - **Sutta Number Pattern**: Uses 2-part numbering `{vagga_num}. {sutta_num}.` (e.g., "1. 1.", "2. 1.", "5. 16.")
    - **Entry Type Detection**: Sutta numbers appear in `centered` entries with `level: 1`
    - **Vagga Headings**: `level: 3` entries with pattern `^\d+\.\s*\w+.*vaggo?$` (e.g., "1. uragavaggo", "2. cullavaggo")
    - **Natural Sorting Requirement**: Files must be processed in order (1, 2, 3, 4, 5) to maintain sutta code sequence in final TSV
    - **Web Code Format**: `kn-snp-{vagga_num}-{sequential_num}` with sequential numbering resetting for each vagga
    - **Duplicate Entries**: Some sutta numbers appear twice in JSON (both Pali and Sinhala sections), script handles this correctly

### KN 6: Vimānavatthu (VV) & KN 7: Petavatthu (PV)
- **Structure**: `Vagga -> Vatthu`.
- **Handling**: Extracts stories identified by `vimānaṃ` or `vatthuṃ`.
- **Idiosyncrasies**:
    - **Single File Structure**: All 7 vaggas contained in one JSON file (kn-vv.json), not split across multiple files
    - **Vimāna Numbering**: Each vimāna appears as individual `heading` entry with `level: 1` (e.g., "paṭhamapīṭhavimānaṃ", "dutiyapīṭhavimānaṃ")
    - **No Sequential Counters**: Unlike other books, vimānas are individually present in JSON, so no counter logic needed - each vimāna gets its own entry
    - **Vagga Detection**: `level: 2` entries with pattern `^\d+\.\s*\w+.*vaggo?$` (e.g., "1. pīṭhavaggo", "2. cittalatāvaggo")
    - **Vimāna Name Extraction**: All `heading` entries with `level: 1` are treated as vimāna names, regardless of preceding number entries
    - **Web Code Format**: `kn-vv-{vagga_num}-{vimāna_num}` where vimāna_num is sequential within each vagga
    - **Numbering Logic**: Vimāna numbers are determined by counting existing vimānas within each vagga (e.g., first vimāna in vagga 3 becomes "3.1", second becomes "3.2")
    - **Example Structure**: 
        - Vagga 1: "1. pīṭhavaggo" → vimānas 1.1 through 1.17
        - Vagga 2: "2. cittalatāvaggo" → vimānas 2.1 through 2.12
        - Vagga 3: "3. pāricchattakavaggo" → vimānas 3.1 through 3.12
        - Vagga 4: "4. mañjeṭṭhakavaggo" → vimānas 4.1 through 4.11
        - Vagga 5: "5. mahārathavaggo" → vimānas 5.1 through 5.10
        - Vagga 6: "6. pāyāsivaggo" → vimānas 6.1 through 6.10
        - Vagga 7: "7. sunikkhittavaggo" → vimānas 7.1 through 7.11

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

---


## SN Implementation Guide

### SN-Specific Challenges and Solutions

#### 1. Deeper Hierarchy Structure
SN has 6 levels: `Piṭaka -> Nikāya -> Mahāvagga -> Saṃyutta -> Vagga -> Sutta`

**Implementation Strategy:**
```python
# Add mahāvagga tracking to function signature
def extract_sutta_data(
    json_file: Path,
    current_piṭaka: str,
    current_nikaya: str,
    current_mahāvagga: str,  # NEW: Track mahāvagga
    current_saṃyutta: str,   # NEW: Track saṃyutta  
    current_book: str,         # Maps to saṃyutta
    current_vagga: str,
    last_web_sutta_num: int,
    current_vagga_for_web: str,
) -> tuple[List[Dict[str, Any]], int, str]:
```

#### 2. Field Mapping for SN
```python
record = {
    "bjt_sutta_code": sutta_code,
    "bjt_web_code": web_code,
    "bjt_filename": filename,
    "bjt_book_id": book_id,
    "bjt_page_num": page_num,
    "bjt_page_offset": 0,
    "bjt_piṭaka": current_piṭaka,
    "bjt_nikāya": current_nikaya,
    "bjt_mahāvagga": current_mahāvagga,  # NEW FIELD
    "bjt_book": current_saṃyutta,        # Maps to saṃyutta
    "bjt_vagga": current_vagga,
    "bjt_sutta": sutta_name,
}
```

#### 3. Hierarchy Detection Patterns for SN
```python
# Update hierarchy based on entry type and content
if entry_type == "centered":
    if "suttantapiṭake" in text.lower():
        current_piṭaka = text
    elif "saṃyuttanikāyo" in text.lower():
        current_nikaya = text
    elif "mahāvaggo" in text.lower() and level == 2:
        current_mahāvagga = text
    elif "saṃyuttaṃ" in text.lower() and level == 3:
        current_saṃyutta = text
    elif "vaggo" in text.lower() and level == 3:
        current_vagga = text
    elif level == 1 and re.match(r"^\d+\.\s*\d+\.\s*\d+\.\s*\d+", text):
        # SN pattern: 1. 1. 1. 1 (mahāvagga.saṃyutta.vagga.sutta)
```

#### 4. SN Sutta Code Pattern
SN uses 4-part numbering: `1. 1. 1. 1` (mahāvagga.saṃyutta.vagga.sutta)

```python
# Parse SN sutta code
sutta_parts = text.rstrip(".").split(".")
if len(sutta_parts) >= 4:
    try:
        mahāvagga_num = int(sutta_parts[0].strip())
        saṃyutta_num = int(sutta_parts[1].strip())
        vagga_num = int(sutta_parts[2].strip())
        sutta_num = int(sutta_parts[3].strip())
        
        # Web code: sn-{mahāvagga}-{saṃyutta}-{vagga}-{sutta}
        web_code = f"sn-{mahāvagga_num}-{saṃyutta_num}-{vagga_num}-{sutta_num}"
```

#### 5. SN File Structure and Book ID Mapping
SN files typically follow pattern: `sn-1-1.json`, `sn-1-2.json`, etc.

```python
# SN book ID mapping (example - needs verification)
book_id_map = {
    "sn-1-1": 1,  # Sagāthavaggo - Devatāsaṃyutta
    "sn-1-2": 1,  # Sagāthavaggo - Devaputtasaṃyutta
    # ... continue mapping
}
```

#### 6. SN Web Code Reset Logic
For SN, web codes should reset at each vagga level, not just book level:

```python
# Check if vagga changed and reset web counter if needed
if current_vagga != current_vagga_for_web:
    last_web_sutta_num = 0
    current_vagga_for_web = current_vagga

# Increment and generate web code
web_sutta_num = last_web_sutta_num + 1
web_code = f"sn-{mahāvagga_num}-{saṃyutta_num}-{vagga_num}-{web_sutta_num}"
last_web_sutta_num = web_sutta_num
```

### SN Implementation Checklist

#### Pre-Implementation Tasks:
1. **Examine SN JSON files**: 
   - List files in `resources/dpd_submodules/bjt/public/static/roman_json/sn-*.json`
   - Analyze file naming patterns
   - Check actual hierarchy structure in JSON

2. **Identify Entry Patterns**:
   - Find sutta code patterns (likely 4-part numbers)
   - Determine entry types (centered/heading)
   - Locate hierarchy markers (mahāvaggo, saṃyuttaṃ, vaggo)

3. **Map Book IDs**:
   - Create book_id mapping for SN files
   - Verify against existing data if available

#### Implementation Steps:
1. **Create `sn.py`** with AN as template
2. **Update function signature** to include mahāvagga and saṃyutta tracking
3. **Implement hierarchy detection** for SN-specific markers
4. **Parse 4-part sutta codes** (mahāvagga.saṃyutta.vagga.sutta)
5. **Generate web codes** with vagga-level reset
6. **Test with sample files** and verify output

#### Testing Strategy:
1. **Run on single file**: `python scripts/suttas/bjt/sn.py`
2. **Check output format**: Verify all required fields present
3. **Validate web codes**: Ensure sequential numbering within vaggas
4. **Cross-reference**: Compare with known SN sutta lists if available

### Common SN Pitfalls to Avoid:

1. **Incorrect Hierarchy Levels**: SN has deeper structure than AN
2. **Missing Mahāvagga Tracking**: Essential for correct sutta codes
3. **Wrong Field Mapping**: `bjt_book` maps to `saṃyutta`, not `mahāvagga`
4. **4-Part Number Parsing**: Different from AN's 3-part pattern
5. **File Naming Complexity**: SN may have complex file naming patterns

### SN Adaptation Template

```python
def find_sn_files(json_dir: Path) -> List[Path]:
    """Find all JSON files starting with 'sn-' in directory."""
    sn_files = list(json_dir.glob("sn-*.json"))
    return natural_sort(sn_files)

def get_sn_book_number(filename: str) -> str:
    """Extract base book info from SN filename like 'sn-1-1', 'sn-1-2'"""
    # Adapt for SN naming pattern
    parts = filename.replace('sn-', '').split('-')
    return f"{parts[0]}-{parts[1]}"  # e.g., "1-1"

# Main processing loop adapted for SN
for json_file in sn_files:
    filename = json_file.stem
    if all_data:
        last_record = all_data[-1]
        last_filename = last_record["bjt_filename"]
        
        # SN-specific boundary detection
        current_book_info = get_sn_book_number(filename)
        last_book_info = get_sn_book_number(last_filename)
        
        # Reset if moving to different saṃyutta
        if current_book_info != last_book_info:
            # Reset appropriate hierarchy levels
            pass
```

This comprehensive guide should enable a new agent to successfully implement SN processing by adapting proven AN methodology while accounting for SN's unique structural requirements.

---

## SN Implementation Guide

### SN-Specific Challenges and Solutions

#### 1. Deeper Hierarchy Structure
SN has 6 levels: `Piṭaka -> Nikāya -> Mahāvagga -> Saṃyutta -> Vagga -> Sutta`

**Implementation Strategy:**
```python
# Add mahāvagga tracking to function signature
def extract_sutta_data(
    json_file: Path,
    current_piṭaka: str,
    current_nikaya: str,
    current_mahāvagga: str,  # NEW: Track mahāvagga
    current_saṃyutta: str,   # NEW: Track saṃyutta  
    current_book: str,         # Maps to saṃyutta
    current_vagga: str,
    last_web_sutta_num: int,
    current_vagga_for_web: str,
) -> tuple[List[Dict[str, Any]], int, str]:
```

#### 2. Field Mapping for SN
```python
record = {
    "bjt_sutta_code": sutta_code,
    "bjt_web_code": web_code,
    "bjt_filename": filename,
    "bjt_book_id": book_id,
    "bjt_page_num": page_num,
    "bjt_page_offset": 0,
    "bjt_piṭaka": current_piṭaka,
    "bjt_nikāya": current_nikaya,
    "bjt_mahāvagga": current_mahāvagga,  # NEW FIELD
    "bjt_book": current_saṃyutta,        # Maps to saṃyutta
    "bjt_vagga": current_vagga,
    "bjt_sutta": sutta_name,
}
```

#### 3. Hierarchy Detection Patterns for SN
```python
# Update hierarchy based on entry type and content
if entry_type == "centered":
    if "suttantapiṭake" in text.lower():
        current_piṭaka = text
    elif "saṃyuttanikāyo" in text.lower():
        current_nikaya = text
    elif "mahāvaggo" in text.lower() and level == 2:
        current_mahāvagga = text
    elif "saṃyuttaṃ" in text.lower() and level == 3:
        current_saṃyutta = text
    elif "vaggo" in text.lower() and level == 3:
        current_vagga = text
    elif level == 1 and re.match(r"^\d+\.\s*\d+\.\s*\d+\.\s*\d+", text):
        # SN pattern: 1. 1. 1. 1 (mahāvagga.saṃyutta.vagga.sutta)
```

#### 4. SN Sutta Code Pattern
SN uses 4-part numbering: `1. 1. 1. 1` (mahāvagga.saṃyutta.vagga.sutta)

```python
# Parse SN sutta code
sutta_parts = text.rstrip(".").split(".")
if len(sutta_parts) >= 4:
    try:
        mahāvagga_num = int(sutta_parts[0].strip())
        saṃyutta_num = int(sutta_parts[1].strip())
        vagga_num = int(sutta_parts[2].strip())
        sutta_num = int(sutta_parts[3].strip())
        
        # Web code: sn-{mahāvagga}-{saṃyutta}-{vagga}-{sutta}
        web_code = f"sn-{mahāvagga_num}-{saṃyutta_num}-{vagga_num}-{sutta_num}"
```

#### 5. SN File Structure and Book ID Mapping
SN files typically follow pattern: `sn-1-1.json`, `sn-1-2.json`, etc.

```python
# SN book ID mapping (example - needs verification)
book_id_map = {
    "sn-1-1": 1,  # Sagāthavaggo - Devatāsaṃyutta
    "sn-1-2": 1,  # Sagāthavaggo - Devaputtasaṃyutta
    # ... continue mapping
}
```

#### 6. SN Web Code Reset Logic
For SN, web codes should reset at each vagga level, not just book level:

```python
# Check if vagga changed and reset web counter if needed
if current_vagga != current_vagga_for_web:
    last_web_sutta_num = 0
    current_vagga_for_web = current_vagga

# Increment and generate web code
web_sutta_num = last_web_sutta_num + 1
web_code = f"sn-{mahāvagga_num}-{saṃyutta_num}-{vagga_num}-{web_sutta_num}"
last_web_sutta_num = web_sutta_num
```

### SN Implementation Checklist

#### Pre-Implementation Tasks:
1. **Examine SN JSON files**: 
   - List files in `resources/dpd_submodules/bjt/public/static/roman_json/sn-*.json`
   - Analyze file naming patterns
   - Check actual hierarchy structure in JSON

2. **Identify Entry Patterns**:
   - Find sutta code patterns (likely 4-part numbers)
   - Determine entry types (centered/heading)
   - Locate hierarchy markers (mahāvaggo, saṃyuttaṃ, vaggo)

3. **Map Book IDs**:
   - Create book_id mapping for SN files
   - Verify against existing data if available

#### Implementation Steps:
1. **Create `sn.py`** with AN as template
2. **Update function signature** to include mahāvagga and saṃyutta tracking
3. **Implement hierarchy detection** for SN-specific markers
4. **Parse 4-part sutta codes** (mahāvagga.saṃyutta.vagga.sutta)
5. **Generate web codes** with vagga-level reset
6. **Test with sample files** and verify output

#### Testing Strategy:
1. **Run on single file**: `python scripts/suttas/bjt/sn.py`
2. **Check output format**: Verify all required fields present
3. **Validate web codes**: Ensure sequential numbering within vaggas
4. **Cross-reference**: Compare with known SN sutta lists if available

### Common SN Pitfalls to Avoid:

1. **Incorrect Hierarchy Levels**: SN has deeper structure than AN
2. **Missing Mahāvagga Tracking**: Essential for correct sutta codes
3. **Wrong Field Mapping**: `bjt_book` maps to `saṃyutta`, not `mahāvagga`
4. **4-Part Number Parsing**: Different from AN's 3-part pattern
5. **File Naming Complexity**: SN may have complex file naming patterns

### SN Adaptation Template

```python
def find_sn_files(json_dir: Path) -> List[Path]:
    """Find all JSON files starting with 'sn-' in directory."""
    sn_files = list(json_dir.glob("sn-*.json"))
    return natural_sort(sn_files)

def get_sn_book_number(filename: str) -> str:
    """Extract base book info from SN filename like 'sn-1-1', 'sn-1-2'"""
    # Adapt for SN naming pattern
    parts = filename.replace('sn-', '').split('-')
    return f"{parts[0]}-{parts[1]}"  # e.g., "1-1"

# Main processing loop adapted for SN
for json_file in sn_files:
    filename = json_file.stem
    if all_data:
        last_record = all_data[-1]
        last_filename = last_record["bjt_filename"]
        
        # SN-specific boundary detection
        current_book_info = get_sn_book_number(filename)
        last_book_info = get_sn_book_number(last_filename)
        
        # Reset if moving to different saṃyutta
        if current_book_info != last_book_info:
            # Reset appropriate hierarchy levels
            pass
```

This comprehensive guide should enable a new agent to successfully implement SN processing by adapting the proven AN methodology while accounting for SN's unique structural requirements.
