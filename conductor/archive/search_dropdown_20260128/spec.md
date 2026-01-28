# Specification: Diacritic-Insensitive Pāḷi Search Dropdown

**Overview**
Implement a diacritic-insensitive search dropdown in the DPD Webapp. The dropdown will provide suggestions for Pāḷi Headwords, Roots, and Root Families.

**Functional Requirements**
1. **Data Sources:**
   - **Headwords:** `lemma_clean` from `dpd_headwords`.
   - **Roots:** `root_no_sign` (clean version of roots like `bhū`) from `dpd_roots`.
   - **Root Families:** `root_family_clean` from `family_root`.
2. **Background Data Loading:** On app startup, fetch a static `search_index.json`. This file contains a mapping of ASCII-normalized keys to arrays of actual Pāḷi terms.
3. **Trigger:** Show the dropdown after 2 characters are entered in the main search box.
4. **Matching Logic:**
   - Normalize user input to ASCII (strip diacritics).
   - Perform prefix matching against the ASCII keys in the index.
5. **UI/UX:**
   - Display a floating dropdown list below the search input.
   - Show only the clean Pāḷi word/root/family.
   - Initial visible limit of 10 matches, but allow scrolling/arrowing down for more.
   - Support keyboard navigation (Arrow keys to navigate, Enter to select).
   - Selecting an item populates the search box and triggers `performSearch()`.
6. **Persistence:** Leverage browser caching for the static JSON file.

**Acceptance Criteria**
- Typing "bhū" or "bhu" shows "bhū" (as a root) in the dropdown.
- Typing "rupa" shows "rūpa" (as a headword).
- Root families like "bhū family" appear correctly.
- The UI remains responsive during background loading.
