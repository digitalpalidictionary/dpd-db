# Specification: Grouped Headwords in Apple Dictionary Export

## 1. Overview
Currently, the Apple Dictionary export treats every database entry as a distinct dictionary entry (e.g., "dhamma 1.01", "dhamma 1.02"). This creates a cluttered user experience where multiple definitions of the same word are scattered.

This feature will refactor the export logic to group all headwords that share the same "clean lemma" (e.g., all variants of "dhamma") into a single, unified dictionary entry. This entry will list the individual definitions as sub-items, providing a cleaner and more organized interface.

## 2. Functional Requirements

### 2.1 Grouping Logic
- **Criteria:** Entries MUST be grouped strictly by their `lemma_clean` property (the headword text without numbers).
- **Scope:** This applies to ALL entries. Every resulting XML entry represents one unique `lemma_clean`.

### 2.2 XML Entry Structure
- **ID:** The main entry MUST have a unique ID derived from the `lemma_clean` (e.g., `dpd_group_dhamma`).
- **Title:** The entry title MUST be the `lemma_clean` (e.g., "dhamma").
- **Indexing:**
    - The entry MUST be indexed by the `lemma_clean`.
    - The entry MUST include a merged set of ALL inflections from ALL sub-entries contained within the group.
    - Searching for any inflection (e.g., "dhammassa") should open the main "dhamma" entry.

### 2.3 Visual Presentation (HTML/CSS)
- **Global Rule:** The `lemma_clean` text MUST NOT be repeated within the body of the entry (it is already in the header).
- **Header:** Displays the `lemma_clean` (e.g., "dhamma").
- **Content Layout:**
    - **Singletons (Group size = 1):**
        - Display: `pos`, `meaning`, `construction_summary`, `degree_of_completion`.
        - Do NOT display the numeric ID (e.g. "1").
    - **Groups (Group size > 1):**
        - Display as a list of sub-entries.
        - For each sub-entry, display: **`number`** (e.g., "1.01", "1.02"), `pos`, `meaning`, `construction_summary`, `degree_of_completion`.

## 3. Technical Implementation
- **File:** `exporter/apple_dictionary/apple_dictionary.py`
- **Data Loading:** The export script currently streams entries. This logic needs to be adjusted to buffer or query entries in a way that allows grouping before writing to XML.
    - *Constraint:* Memory efficiency is important. Sorting by `lemma_clean` in the database query will allow sequential processing of groups (chunking by group rather than arbitrary count) without loading the entire DB into memory.

## 4. Acceptance Criteria
- [ ] searching "dhamma" shows one result in the dictionary index.
- [ ] opening "dhamma" (a group) shows the header "dhamma" followed by "1.01 ...", "1.02 ...", etc.
- [ ] opening "gacchati" (a singleton) shows the header "gacchati" followed by its data, without a number or repeated headword.
- [ ] searching an inflection (e.g., "dhammānaṃ") leads to the main "dhamma" entry.
- [ ] The export process completes successfully.

## 5. Out of Scope
- Deep linking specific inflections to specific sub-entries (e.g., anchor links).
