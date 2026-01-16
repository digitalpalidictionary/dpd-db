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

### 4. Logo Behavior
Clicking the DPD logo clears the current search/screen.

### 5. Mobile Layout Consolidation
Consolidate input/option boxes and fix Tipiṭaka Translations tab:
- Line 1: Search box (full width)
- Line 2: "in" + Pāḷi/English dropdown + "in" + book dropdown (single line)
- Line 3: "only show results" + with/without dropdown (single line)
- Tipiṭaka Translations: Replicate CST Bold Definitions tab structure (table-based with clear headers/rows)

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
