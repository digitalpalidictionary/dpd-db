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
- [x] Task: Add collapse/expand toggle button to history-pane header
- [x] Task: Add collapse/expand toggle button to settings-pane header
- [x] Task: Add CSS for collapsed/expanded states (display: none/block)
- [x] Task: Add JavaScript for toggle functionality
- [x] Task: Add @media query for ≤576px to enable collapsible behavior
- [x] Task: Conductor - User Manual Verification 'Make History & Settings Collapsible' (Protocol in workflow.md)

## Phase 4.5: Clear Button Behavior Fix
- [x] Task: Clear button should not restore default text
- [x] Task: Clear button should show empty dpd pane
- [x] Task: Clear button should have no other side effects
- [x] Task: Conductor - User Manual Verification 'Clear Button Behavior Fix' (Protocol in workflow.md)

## Phase 5: Make Logo Click Clear Search
- [x] Task: Wrap logo image in anchor tag with onclick handler
- [x] Task: Add JavaScript to clear #search-box and #dpd-results on logo click
- [x] Task: Reset URL to clean path when logo clicked
- [x] Task: Make clear button use same clear function as logo click
- [x] Task: Conductor - User Manual Verification 'Make Logo Click Clear Search' (Protocol in workflow.md)

## Phase 6: Dictionary Entry Spacing
- [x] Task: Increase margin between dictionary entries for better readability

## Phase 7: Mobile Double-Tap Search
- [x] Task: Improve double-tap/double-click search functionality on mobile

## Phase 8: Final Testing & Verification
- [x] Task: Run all tests with `CI=true pytest`
- [x] Task: Verify layout on Pixel 9 (~412px viewport)
- [x] Task: Verify layout on iPhone Pro Max (~430px viewport)
- [x] Task: Run `uv run ruff check` for linting
- [x] Task: Run `uv run ruff format` for formatting
- [x] Task: Conductor - User Manual Verification 'Final Testing & Verification' (Protocol in workflow.md)
