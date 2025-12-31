# Database Query Tab Feature Specification

## Overview
Add a new tab at the end of the existing three tabs (DPD, CST Bold Definitions, Tipiṭaka Translations) in the webapp (`exporter/webapp`) that provides database search query functionality with tabulated results.

## Functional Requirements

### Tab Integration
- Add a fourth tab button labeled "Database Query" after existing three tabs in the webapp interface
- The tab should follow same visual design and interaction patterns as existing tabs

### Query Builder Interface
- Field selector dropdown: Shows all DpdHeadword model columns with type-to-filter functionality
- Search type selector dropdown: "Contains" (default), "Starts with", "Ends with", "Regex"
- Value input field: Text input for the search value
- Ability to add multiple filter criteria visually with add/remove buttons
- Logic selector between filter rows: "AND" (default) or "OR"
  - OR operator starts a new logical group: AND AND AND OR AND = (filter1 AND filter2 AND filter3) OR (filter4 AND filter5)
- Display column selector: Multi-select dropdown to choose which fields to display in results
- Results limit input: Numeric input field, maximum value of 100

### Preset Management
- Ability to save query presets (filter criteria, display columns, limit, logic) to localStorage
- Load existing presets from a dropdown selector
- Delete saved presets
- Presets persist across sessions like other settings

### Data Fetching
- Default display columns: id, pos, grammar, lemma_1, meaning_1, meaning_lit, meaning_2, construction
- Clear and obvious UI for adding more display columns
- Toggle between "Performance Mode" (fetch only selected columns) and "Responsive Mode" (fetch all fields initially)
- Use existing SQLAlchemy models for query building
- Convert search types to appropriate regex patterns using SQLAlchemy's `regexp_match`

### Results Display
- Display results in an HTML table with both horizontal and vertical scrolling
- Table must handle large datasets (up to 100 results with many columns)
- Results table should be responsive and clearly formatted
- Column headers should match selected display fields

### Export Functionality
- "Export to TSV" button to download current results as tab-separated values file
- "Export to JSON" button to download current results as JSON file
- Both exports should include all displayed columns and their data
- JSON export should be array of objects with column names as keys

## Non-Functional Requirements
- Follow existing webapp code patterns and conventions
- Reuse existing database query methods where possible
- Maintain consistent styling with the webapp (use CSS from `identity/css/`)
- Handle edge cases: no results, invalid regex, limit exceeded
- Presets stored in localStorage (consistent with existing settings)

## Acceptance Criteria
1. New "Database Query" tab appears at the end of existing tabs
2. User can add/remove multiple filter criteria
3. Field selector dropdown filters fields as user types
4. All four search types (contains, starts_with, ends_with, regex) work correctly
5. AND/OR logic between filters works correctly (OR creates new logical groups)
6. Display column selector allows selecting which columns to show
7. Results limit prevents queries from returning more than 100 rows
8. Results display in a scrollable table with selected columns
9. Performance/Responsive mode toggle works correctly
10. Default columns are selected on initial load
11. Presets can be saved, loaded, and deleted
12. Presets persist across sessions (localStorage)
13. Export to TSV button downloads results correctly
14. Export to JSON button downloads results correctly
15. Existing tabs and functionality remain unaffected

## Out of Scope
- Editing functionality in the results table
- Advanced export formats (CSV, Excel, etc.)
- Search on other models besides DpdHeadword
