# Specification: Sortable and Optimized Grammar Dictionary

## Overview
Enhance the DPD Grammar dictionary by making tables sortable, optimizing the HTML structure for better compatibility with dictionary viewers (GoldenDict, MDict), and improving export performance through caching.

## Functional Requirements
- **Sortable Tables:** Grammar tables must be sortable by clicking on headers.
  - Columns to sort: `pos` (col 1), `grammar` (cols 2, 3, 4), and `word` (col 6).
  - Sorting cycle: Ascending -> Descending -> Reset (original order).
  - Visual indicator: Unicode arrows (⇅, ▲, ▼) in headers.
- **Pāḷi Sort Order:** Sorting of `pos` and `word` columns must respect the Pāḷi alphabetical order (including handling of characters like `ā`, `kh`, `ṅ`, etc.).
- **Dynamic Column Visibility:** Hide columns 2, 3, and 4 if they are empty for a given entry.
- **Static "of" Column:** Column 5 ("of") remains static and non-sortable.
- **Platform Independence:** JavaScript must be lightweight and work on GoldenDict-ng (Desktop) and MDict (Android/iOS).

## Technical Requirements
- **HTML Structure:**
  - Preserve `<head>` and `<body>` tags for full compatibility with dictionary viewers (required for CSS/JS linking).
  - Use the `load_js` pattern in the header to ensure reliable JavaScript execution across different platforms (GoldenDict-ng, MDict).
- **JavaScript (sorter.js):**
  - Implement Pāḷi-aware sorting using a mapping technique similar to `tools/pali_sort_key.py`.
  - Handle the Reset state by storing the initial row order.
  - Ensure compatibility with various WebView versions used in dictionary apps.
- **Performance Optimization:**
  - Implement caching for generated HTML tables in `exporter/grammar_dict/grammar_dict.py` to avoid redundant processing of identical grammatical data.
- **Exporter Integration:**
  - Ensure `sorter.js` and relevant CSS are correctly packaged into the final dictionary files (zip/mdd).

## Acceptance Criteria
- [ ] Tables in GoldenDict-ng and MDict are sortable.
- [ ] Pāḷi words and POS tags sort in correct Pāḷi order.
- [ ] Clicking a header cycles through Ascending, Descending, and original order.
- [ ] Empty grammar columns are not displayed.
- [ ] The "of" column does not trigger sorting.
- [ ] Export process is significantly faster due to caching.
- [ ] Dictionary entries contain only the necessary `<div>` and `<table>` structure.

## Out of Scope
- Sorting for other dictionaries (EPD, Abbreviations) in this track.
