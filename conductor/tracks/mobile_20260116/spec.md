# Mobile Layout Improvements - Track Specification

## Overview
Improve the DPD webapp layout for mobile users (smartphones) by consolidating spacing, adding collapsible panels, and fixing visual clutter. Focus exclusively on layout/CSS changes - no new functionality or external dependencies.

## Scope
- Target viewport: ≤576px width (typical smartphones)
- DPD tab improvements only (not the fork's Russian templates)
- CSS-only approach where possible, minimal JS for toggle behavior

## Requirements

### 1. Autofocus
All three tab textboxes (DPD, CST Bold Definitions, Tipiṭaka Translations) receive autofocus on page load.

### 2. Search Input Improvements (DPD tab)
- Add clear button on same line as search button
- Search button: 80% width, Clear button: 20% width

### 3. Collapsible Panels (DPD tab)
- History section: Convert to toggleable button on mobile
- Settings section: Convert to toggleable button on mobile
- Clear button behavior: When clicked, clear dpd pane without showing default start message (empty pane only, no other changes or side effects)
- Header icons: Move GitHub icon to top header with email and language icons
- Scrollbars: Ensure consistent theming across all scrollable elements

### 4. Logo Behavior
Clicking the DPD logo clears the current search/screen.

### 6. Dark/Light Theme Transition
Evaluate and disable if causing glitchy popup loading.

### 7. Dictionary Entry Spacing
Increase margin between dictionary entries for better readability on mobile.

### 8. Mobile Double-Tap to Search
Improve double-tap/double-click search functionality on mobile devices for better usability.

## Out of Scope
- jQuery UI autocomplete
- jQuery sortable tables
- Loading spinners
- Suttacentral/dhamma.gift external links
- Russian language templates

## Acceptance Criteria
- [ ] Layout verified on Pixel 9 (~412px) and iPhone Pro Max (~430px)
- [ ] All three tabs have autofocus
- [ ] DPD search box has clear button (80/20 split)
- [ ] History and Settings are collapsible on mobile
- [ ] Logo click clears search
- [ ] Search options consolidated to 3 lines max on mobile
- [ ] Tipiṭaka Translations tab uses structured table layout matching CST Bold Definitions
- [ ] Theme transitions don't cause visual glitches
- [ ] Clear history button shows empty DPD pane (no default message) when clicked
- [ ] Clear history button has no side effects
- [ ] Scrollbars have consistent theming across all elements
- [ ] GitHub icon moved to top header panel
