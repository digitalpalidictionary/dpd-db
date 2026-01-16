# Mobile Layout Improvements - Implementation Plan

## Phase 1: Research & Setup
- [x] Task: Research current webapp mobile behavior on Pixel 9 (~412px viewport)
- [x] Task: Review existing @media (max-width: 750px) breakpoint in home.css
- [x] Task: Conductor - User Manual Verification 'Research & Setup' (Protocol in workflow.md)

## Phase 2: Add Autofocus to All Tab Inputs
- [x] Task: Add `autofocus` attributes to all four search boxes in home.html
- [x] Task: Conductor - User Manual Verification 'Add Autofocus to All Tab Inputs' (Protocol in workflow.md)

## Phase 3: Add Clear Button to DPD Search
- [x] Task: Add clear button element to home.html after search-button
- [x] Task: Add CSS to make search buttons wrap to new line on mobile
- [x] Task: Add JavaScript click handler to clear search-box value
- [x] Task: Conductor - User Manual Verification 'Add Clear Button to DPD Search' (Protocol in workflow.md)

## Phase 4: Make History & Settings Collapsible
- [ ] Task: Add collapse/expand toggle button to history-pane header
- [ ] Task: Add collapse/expand toggle button to settings-pane header
- [ ] Task: Add CSS for collapsed/expanded states (display: none/block)
- [ ] Task: Add JavaScript for toggle functionality
- [ ] Task: Add @media query for ≤576px to enable collapsible behavior
- [ ] Task: Conductor - User Manual Verification 'Make History & Settings Collapsible' (Protocol in workflow.md)

## Phase 5: Make Logo Click Clear Search
- [ ] Task: Wrap logo image in anchor tag with onclick handler
- [ ] Task: Add JavaScript to clear #search-box and #dpd-results on logo click
- [ ] Task: Conductor - User Manual Verification 'Make Logo Click Clear Search' (Protocol in workflow.md)

## Phase 6: Mobile Layout Consolidation
- [~] Task: Add @media query for ≤576px in home.css
- [ ] Task: Consolidate TT search row elements to 3 lines:
       - Line 1: Search box (full width)
       - Line 2: "in" + lang dropdown + "in" + book dropdown (single line)
       - Line 3: "only show results" + filter dropdown + filter box + clear button (single line)
- [ ] Task: Restructure Tipiṭaka Translations results to match CST Bold Definitions table layout (bd-table, bd-row, bd-th, bd-td pattern)
- [ ] Task: Conductor - User Manual Verification 'Mobile Layout Consolidation' (Protocol in workflow.md)

## Phase 7: Theme Transition Check
- [ ] Task: Evaluate current theme transition (body { transition: 1s })
- [ ] Task: Reduce or disable transition for popup mode if causing issues
- [ ] Task: Conductor - User Manual Verification 'Theme Transition Check' (Protocol in workflow.md)

## Phase 8: Dictionary Entry Spacing
- [ ] Task: Increase margin between dictionary entries for better readability

## Phase 9: Mobile Double-Tap Search
- [ ] Task: Improve double-tap/double-click search functionality on mobile

## Phase 10: Final Testing & Verification
- [ ] Task: Run all tests with `CI=true pytest`
- [ ] Task: Verify layout on Pixel 9 (~412px viewport)
- [ ] Task: Verify layout on iPhone Pro Max (~430px viewport)
- [ ] Task: Run `uv run ruff check` for linting
- [ ] Task: Run `uv run ruff format` for formatting
- [ ] Task: Conductor - User Manual Verification 'Final Testing & Verification' (Protocol in workflow.md)
