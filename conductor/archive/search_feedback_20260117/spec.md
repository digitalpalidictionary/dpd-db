# Specification: Visual Search Feedback for DPD Webapp

## Overview
Currently, when a user initiates a search in the DPD Webapp—either by clicking a search button or double-clicking a word—there is no visual feedback indicating that a search is in progress. This track aims to add a subtle button spinner that replaces the button text while a search is being performed, improving the user experience by providing clear activity feedback.

## Functional Requirements
- **Spinner Style:** Implement a simple, understated CSS-based spinner animation.
- **Triggers:** The feedback must be shown for ALL search initiations:
    - Clicking the specific tab's search button.
    - Double-clicking any word on the page (which auto-triggers a search).
    - Pressing "Enter" in a search box.
- **Feedback Mechanism:** When any search starts, the currently active tab's primary search button text should be replaced by the spinner.
- **State Management:**
    - The button should be disabled during the search to prevent redundant requests.
    - Once results are received (or an error occurs), the spinner must be removed, the original text restored, and the button re-enabled.
- **Scope:** This applies to the primary search buttons in all tabs:
    - `#search-button` (DPD tab)
    - `#bd-search-button` (CST Bold Definitions tab)
    - `#tt-search-button` (Tipiṭaka Translations tab)

## Non-Functional Requirements
- **CSS Location:** Styles must be added to `exporter/webapp/static/home.css`. Do NOT modify `identity/` CSS.
- **Performance:** Use lightweight CSS for the animation to ensure zero impact on load times.

## UI/UX Design
- During search: The button text (e.g., "search") disappears, and a small centered spinner (matching the button's text color) appears.
- Post-search: The button immediately returns to its normal state.

## Acceptance Criteria
- Clicking "search" manually triggers the spinner on the active button.
- Double-clicking a word triggers the spinner on the active button (DPD, BD, or TT depending on context).
- Pressing Enter in a search input triggers the spinner on the active button.
- The spinner persists until the search completes or fails.
- The original button text is correctly restored in all cases.
