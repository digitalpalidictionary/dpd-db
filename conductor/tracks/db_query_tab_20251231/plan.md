# Database Query Tab Implementation Plan

## Phase 1: Research and Planning

- [ ] Task: Research webapp structure and existing query patterns
  - [ ] Examine existing tab implementation in home.html
  - [ ] Study existing API routes in main.py
  - [ ] Review gui2/filter_tab_view.py for reference patterns
  - [ ] Document query building approach

- [ ] Task: Research JavaScript patterns for localStorage and presets
  - [ ] Research localStorage API best practices
  - [ ] Study existing settings management in webapp
  - [ ] Document preset storage structure

- [ ] Task: Design data structures for queries and presets
  - [ ] Define filter criteria data structure
  - [ ] Define preset data structure
  - [ ] Define API request/response formats

## Phase 2: Backend API Implementation

- [ ] Task: Write tests for query building - convert filters to regex
  - [ ] Test single filter with contains pattern
  - [ ] Test single filter with starts_with pattern
  - [ ] Test single filter with ends_with pattern
  - [ ] Test single filter with regex pattern
  - [ ] Test multiple filters with AND logic
  - [ ] Test multiple filters with OR logic (grouping)
  - [ ] Test mixed AND/OR logic
  - [ ] Test display column selection filtering

- [ ] Task: Implement database query building logic
  - [ ] Create new FastAPI route for database queries
  - [ ] Implement query builder with filter criteria parsing
  - [ ] Implement AND/OR logic with proper grouping
  - [ ] Convert search types to regex patterns
  - [ ] Add display column filtering
  - [ ] Add results limit enforcement (max 100)

- [ ] Task: Write tests to confirm query results match expected data
  - [ ] Test query returns correct records for contains
  - [ ] Test query returns correct records for starts_with
  - [ ] Test query returns correct records for ends_with
  - [ ] Test query returns correct records for regex
  - [ ] Test AND logic returns correct records
  - [ ] Test OR logic returns correct records
  - [ ] Test mixed AND/OR logic returns correct records
  - [ ] Test column filtering returns only selected columns

- [ ] Task: Implement API endpoint with result verification
  - [ ] Connect query builder to FastAPI route
  - [ ] Add error handling for invalid regex
  - [ ] Ensure proper JSON response format
  - [ ] Verify results match expected data structure

## Phase 3: Frontend Tab Integration

- [ ] Task: Implement new tab button and content area in home.html
  - [ ] Add "Database Query" tab button to tab navigation
  - [ ] Create query-tab content div with initial structure
  - [ ] Follow existing tab design patterns

- [ ] Task: Implement tab switching JavaScript
  - [ ] Add tab switching logic to home.js
  - [ ] Ensure tab state is properly managed

## Phase 4: Query Builder UI Components

- [ ] Task: Implement field dropdown with type-to-filter
  - [ ] Create field dropdown HTML component
  - [ ] Implement type-to-filter JavaScript logic
  - [ ] Populate dropdown from DpdHeadword model columns

- [ ] Task: Implement search type selector
  - [ ] Create search type dropdown HTML component
  - [ ] Set default to "contains"
  - [ ] Ensure all four options are available

- [ ] Task: Implement value input field
  - [ ] Create text input field component
  - [ ] Add appropriate placeholder text

- [ ] Task: Implement add/remove filter rows
  - [ ] Create "Add Filter" button
  - [ ] Create remove button for each filter row
  - [ ] Implement add/remove JavaScript logic
  - [ ] Ensure minimum one filter row always exists

- [ ] Task: Implement AND/OR logic selector
  - [ ] Create AND/OR dropdown for each filter row
  - [ ] Set default to "AND"
  - [ ] Implement visual grouping for OR separators

- [ ] Task: Implement display column selector
  - [ ] Create multi-select dropdown for columns
  - [ ] Set default columns: id, pos, grammar, lemma_1, meaning_1, meaning_lit, meaning_2, construction
  - [ ] Make it clear how to add more columns
  - [ ] Ensure at least one column is always selected

- [ ] Task: Implement results limit input
  - [ ] Create numeric input field
  - [ ] Add validation for max 100
  - [ ] Set appropriate default value

- [ ] Task: Implement Performance/Responsive mode toggle
  - [ ] Create toggle switch component
  - [ ] Set default to Performance mode
  - [ ] Implement mode persistence in localStorage

## Phase 5: Results Display and Export

- [ ] Task: Implement HTML table with scrolling
  - [ ] Create results table HTML structure
  - [ ] Implement horizontal scrolling CSS
  - [ ] Implement vertical scrolling CSS
  - [ ] Populate table with query results
  - [ ] Handle empty results case

- [ ] Task: Implement TSV export
  - [ ] Create "Export to TSV" button
  - [ ] Implement TSV generation from results
  - [ ] Trigger file download

- [ ] Task: Implement JSON export
  - [ ] Create "Export to JSON" button
  - [ ] Implement JSON generation from results
  - [ ] Trigger file download

## Phase 6: Preset Management

- [ ] Task: Implement preset saving
  - [ ] Create save preset button and input for preset name
  - [ ] Implement localStorage save logic
  - [ ] Collect all current filter settings

- [ ] Task: Implement preset loading
  - [ ] Create preset dropdown selector
  - [ ] Implement localStorage load logic
  - [ ] Restore all settings from preset

- [ ] Task: Implement preset deletion
  - [ ] Create delete preset button
  - [ ] Implement localStorage delete logic
  - [ ] Update preset dropdown

## Phase 7: Final Testing and Documentation

- [ ] Task: Run test suite for backend query logic
  - [ ] Execute query building tests
  - [ ] Execute result verification tests
  - [ ] Debug and fix any failing tests

- [ ] Task: Update documentation
  - [ ] Update exporter/webapp/README.md if needed

- [ ] Task: Conductor - User Manual Verification 'Final Testing and Documentation' (Protocol in workflow.md)
