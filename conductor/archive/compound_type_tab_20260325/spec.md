# Spec: Compound Type Manager Tab (CT)

## Overview
Add a new "CT" (Compound Type Manager) tab as the last tab in gui2. It provides a UI for managing compound type rules stored in `tools/compound_type_manager.tsv` and searching the `dpd_headwords` database for matching entries.

## Functional Requirements

### Layout
1. **Row 1:** Four fields — `word` (text), `pos` (dropdown), `position` (dropdown), `type` (auto-fill text field)
2. **Row 2:** One field — `exceptions` (text field, expands horizontally and vertically to fit content, since some words have many exceptions)
3. **Row 3:** Buttons — `Add`, `Search`, `Clear`, `Delete`
4. **Data display:** Below buttons, a results table (same pattern as DB/filter tab) showing columns: #, lemma_1, meaning_1, compound_type, compound_construction. Each row includes an "e" button that adds that headword to the exceptions field.

### Field Behavior
- `pos` and `position` are standard searchable dropdowns populated from existing TSV values
- `type` is an auto-fill text field that suggests existing values from the TSV but allows free typing of new values
- `word` is a text field; when typing, check for pre-existing rules with that word and pre-fill all fields if found
- `exceptions` is a plain text field (comma-separated headword list), multiline, expands vertically

### Add
- Validates that required fields are filled
- Appends the new rule to `compound_type_manager.tsv`
- After adding, automatically triggers a Search to show matching database entries

### Search
- Queries `dpd_headwords` where the `construction` column matches the `word` using position-based regex (same logic as `CompoundTypeManager._check_rule_logic`):
  - first: `^word `
  - middle: ` word `
  - last: ` word\b`
  - any: `\bword\b`
- Filters by `pos` if not "any"
- Displays matching headwords in the data table

### Edit
- When selecting an existing rule (e.g., via pre-fill when typing a word), allow modifying fields and saving back to the TSV

### Delete
- Allow deleting an existing rule from the TSV

### Clear
- Resets all fields and clears the data display

### Exception Quick-Add
- Each row in the search results data table has an "e" button
- Clicking "e" appends that row's lemma_1 to the `exceptions` field (comma-separated)

## Non-Functional Requirements
- Follow existing gui2 tab code styling — no reinventing the wheel
- Use existing DpdDropdown, DpdTextField patterns from `dpd_fields_classes.py`
- Keep implementation simple and minimal

## Acceptance Criteria
- [ ] CT tab appears as the last tab in gui2
- [ ] Dropdowns for pos and position are populated from TSV data
- [ ] Type field auto-fills from existing values but allows new entries
- [ ] Typing in word field pre-fills other fields if matching rule exists
- [ ] Add writes a new rule to TSV and triggers search
- [ ] Search finds matching dpd_headwords using position-based regex on construction
- [ ] Edit updates an existing rule in the TSV
- [ ] Delete removes a rule from the TSV
- [ ] Clear resets all fields and results
- [ ] Data table displays #, lemma_1, meaning_1, compound_type, compound_construction
- [ ] Each result row has an "e" button to quick-add the headword to exceptions
- [ ] Exceptions field expands vertically to accommodate many entries

## Out of Scope
- Batch operations on multiple rules
- Undo/redo functionality
- Advanced filtering of search results
