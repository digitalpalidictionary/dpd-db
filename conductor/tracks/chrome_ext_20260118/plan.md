# Implementation Plan: Chrome Extension - Bug Fixes, Theme Detection & Chrome Store Release

## Phase 1: Migration to dpd-db Repository
- [x] Task: Move extension code to new location
- [x] Task: Create icon generation script from identity/logo
- [x] Task: Integrate CSS from identity/css
- [x] Task: Study and mimic webapp behavior
- [x] Task: Create initial package.json
- [x] Task: Set up build system

## Phase 2: Critical Bug Fixes
- [x] Task: Update API endpoint to dpdict.net
- [x] Task: Add host permissions to manifest.json
- [x] Task: Fix script loading order in background.js
- [x] Task: Replace external assets with local resources
- [x] Task: Implement JSON API rendering (remove iframe)
- [x] Task: Fix CSS styling issues (Restored table alignment and margins)
- [x] Task: Add comprehensive error handling

## Phase 3: Theme Detection System
- [x] Task: Implement URL-based theme detection
- [x] Task: Create pre-defined themes
- [x] Task: Implement theme dropdown (manual override)
- [x] Task: Implement dynamic color extraction (fallback)
- [x] Task: Implement theme application
- [x] Task: Implement theme persistence

## Phase 4: SuttaCentral Theme Refinement
- [x] Task: Refine SuttaCentral theme (Orange branding, static font, dynamic size)
- [x] Task: Add logo recoloring capability (CSS filters)

## Phase 5: Settings Menu Implementation
- [x] Task: Add settings cog icon to header
- [x] Task: Implement font size controls
- [x] Task: Implement niggahita ṃ/ṁ toggle
- [x] Task: Implement grammar sections toggle (initial load state)
- [x] Task: Implement examples sections toggle (initial load state)
- [x] Task: Implement summary visibility toggle (Robust CSS-state driven)
- [x] Task: Implement sandhi apostrophe toggle (Robust CSS-state driven with wrapApostrophesInHTML)
- [x] Task: Implement "One Button at a Time" toggle (Aligned with webapp)
- [x] Task: Implement audio voice toggle
- [x] Task: UI Polish (Pulsing loading message, sticky helper message, removed redundant greeting)
- [x] Task: Event Isolation (Switched word lookup to dblclick to prevent UI collisions)
- [x] Task: Declaration Safety (Moved globals to window object to prevent re-injection SyntaxErrors)

## Phase 6: Remaining Work & Preparation
- [x] Task: Fix Grammar Sorter (Restored 3-phase sorting and improved initialization)
- [x] Task: Create comprehensive documentation (Walkthrough, Behavior Notes, Conductor Track)
- [ ] Task: Prepare Chrome Web Store assets
- [x] Task: Perform comprehensive testing (Verified SC theme and generic lookups)
- [x] Task: Finalize build and packaging (Automated via npm run build/zip)

## Phase 7: UI & UX Refinements (Jan 2026)
- [x] Task: Refine SuttaCentral theme table styling (margins, padding, alignments)
- [x] Task: Implement grayscale/color icon toggle for extension state
- [x] Task: Remove ON/OFF text badge for cleaner logo visibility
- [x] Task: Configure optimized default settings for toggles
- [x] Task: Implement Digital Pāli Reader theme (Tiled background, specific colors)
- [x] Task: Standardize `<h3>` heading styling with `class="dpd"` and 130% font-size across all platforms.
- [x] Task: Implement VRI theme (tipitaka.org) with autodetection and specific branding colors.

## Phase 8: Sutta Central Dark Theme

- [x] Task: Define Sutta Central Dark theme in `themes.js`

- [x] Task: Implement dark mode detection logic for Sutta Central

- [x] Task: Style Chrome Extension accordingly
