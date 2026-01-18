# Implementation Plan: Chrome Extension - Bug Fixes, Theme Detection & Chrome Store Release

## Phase 1: Migration to dpd-db Repository

- [x] Task: Move extension code to new location
  - [ ] Subtask: Copy `../dpd-chrome/` contents to `exporter/chrome_extension/`
  - [ ] Subtask: Update all file paths in source code to new location
  - [ ] Subtask: Remove hardcoded absolute paths from all JavaScript files
  - [ ] Subtask: Verify all imports/references are relative or use chrome.runtime API

- [x] Task: Create icon generation script from identity/logo
  - [ ] Subtask: Research SVG to PNG conversion tools for Node.js
  - [ ] Subtask: Write script `scripts/generate-icons.js` to generate 16x16, 32x32, 64x64, 128x128 PNG from `identity/logo/dpd-logo.svg`
  - [ ] Subtask: Test script locally to verify icon generation
  - [ ] Subtask: Update manifest.json to reference local icon paths

- [x] Task: Integrate CSS from identity/css
  - [ ] Subtask: Study `tools/css_manager.py` approach for CSS distribution
  - [ ] Subtask: Create extension-specific CSS file `chrome-extension.css` importing from identity/css
  - [ ] Subtask: Define CSS variables for themable properties (background, text, accents, fonts)
  - [ ] Subtask: Update custom-style.css to use CSS variables instead of hardcoded values

- [x] Task: Study and mimic webapp behavior
  - [ ] Subtask: Read `exporter/webapp/` templates to understand HTML structure
  - [ ] Subtask: Identify key interactive components (expand/collapse, navigation)
  - [ ] Subtask: Document differences between current extension and webapp behavior
  - [ ] Subtask: Create plan for reusing webapp templates/components in extension

- [x] Task: Create initial package.json
  - [ ] Subtask: Add extension metadata (name, version, description)
  - [ ] Subtask: Add `build` script for generating icons and copying resources
  - [ ] Subtask: Add `zip` script for creating Chrome Store package
  - [ ] Subtask: Add devDependencies for build tools

- [x] Task: Set up build system
  - [ ] Subtask: Create build script that runs icon generation
  - [ ] Subtask: Create build script that copies CSS from identity/css
  - [ ] Subtask: Add .gitignore for build artifacts (generated icons, zip files)
  - [ ] Subtask: Test complete build process end-to-end

- [x] Task: Conductor - User Manual Verification 'Phase 1: Migration to dpd-db Repository' (Protocol in workflow.md)

## Phase 2: Critical Bug Fixes

- [x] Task: Update API endpoint to dpdict.net
  - [ ] Subtask: Replace all occurrences of `dpd-proxy.snyatix.my.id` with `www.dpdict.net`
  - [ ] Subtask: Change endpoint from `/gd?search=` to `/search_json?q=`
  - [ ] Subtask: Update fetch call to expect JSON response
  - [ ] Subtask: Parse JSON response: `{summary_html: string, dpd_html: string}`

- [x] Task: Add host permissions to manifest.json
  - [ ] Subtask: Add `"host_permissions": ["https://www.dpdict.net/*"]` to manifest.json
  - [ ] Subtask: Verify CSP allows fetching from dpdict.net
  - [ ] Subtask: Test extension can successfully fetch from dpdict.net

- [x] Task: Fix script loading order in background.js
  - [ ] Subtask: Analyze current loading order and dependencies
  - [ ] Subtask: Reorder script loading: utils.js → dictionary-panel.js → main.js
  - [ ] Subtask: Verify all dependencies resolve correctly
  - [ ] Subtask: Test extension loads without JavaScript errors

- [x] Task: Replace external assets with local resources
  - [ ] Subtask: Replace external logo URL with `chrome.runtime.getURL("images/dpd-logo.svg")`
  - [ ] Subtask: Update all icon references in manifest.json to use local paths
  - [ ] Subtask: Verify all assets load correctly after build process
  - [ ] Subtask: Test extension works in Chrome Developer Mode

- [x] Task: Implement JSON API rendering (remove iframe)
  - [ ] Subtask: Remove iframe element from dictionary-panel.js
  - [ ] Subtask: Create container div for rendered HTML
  - [ ] Subtask: Implement fetch to `/search_json?q=` endpoint
  - [ ] Subtask: Parse JSON and render `summary_html` and `dpd_html` into container
  - [ ] Subtask: Mimic webapp HTML structure and styling exactly
  - [ ] Subtask: Test all interactive elements work (expand/collapse, navigation)
  - [ ] Subtask: Verify 4.5× performance improvement over iframe approach

- [x] Task: Fix CSS styling issues
  - [ ] Subtask: Remove iframe-specific CSS (height: 100vh, width: 100%)
  - [ ] Subtask: Fix aggressive `body` grid layout in `custom-style.css`
  - [ ] Subtask: Consider using Shadow DOM to isolate extension styles from host page
  - [ ] Subtask: Apply correct sizing to panel container div using CSS grid/flexbox
  - [ ] Subtask: Ensure responsive design works on screens 1024px and above
  - [ ] Subtask: Test on different screen sizes and browser window sizes

- [x] Task: Add comprehensive error handling
  - [ ] Subtask: Implement network timeout handling (30 seconds)
  - [ ] Subtask: Add empty result handling with user-friendly message
  - [ ] Subtask: Handle rate limiting (429 status) with retry logic
  - [ ] Subtask: Implement graceful degradation for API failures
  - [ ] Subtask: Add loading states for better UX
  - [ ] Subtask: Test all error scenarios (offline, API failures, timeout)

- [x] Task: Conductor - User Manual Verification 'Phase 2: Critical Bug Fixes' (Protocol in workflow.md)

## Phase 3: Theme Detection System

- [x] Task: Implement URL-based theme detection
- [x] Task: Create pre-defined themes
- [x] Task: Implement theme dropdown (manual override)
- [x] Task: Implement dynamic color extraction (fallback)
- [x] Task: Implement theme application
- [x] Task: Implement theme persistence
- [x] Task: Conductor - User Manual Verification 'Phase 3: Theme Detection System' (Protocol in workflow.md)

## Phase 4: SuttaCentral Theme Refinement

- [~] Task: Refine SuttaCentral theme (Orange branding, static font, dynamic size)
- [x] Task: Add logo recoloring capability (CSS filters)
- [ ] Task: Conductor - User Manual Verification 'Phase 4: SuttaCentral Theme Refinement'

## Phase 5: Settings Menu Implementation

- [x] Task: Add settings cog icon to header
  - [x] Subtask: Add cog/gear icon next to theme selector in panel header
  - [x] Subtask: Create settings dropdown menu structure in HTML
  - [x] Subtask: Style settings menu with theme colors (use CSS variables)
  - [x] Subtask: Implement toggle visibility on cog icon click
  - [x] Subtask: Close dropdown when clicking outside

- [x] Task: Implement font size controls
  - [x] Subtask: Add +/- buttons for font size adjustment
  - [x] Subtask: Display current font size value
  - [x] Subtask: Persist font size preference in chrome.storage.local
  - [x] Subtask: Load saved font size on panel open
  - [x] Subtask: Apply font size to panel container

- [x] Task: Implement niggahita ṃ/ṁ toggle
  - [x] Subtask: Add toggle switch for niggahita character display
  - [x] Subtask: Implement conversion function ṃ ↔ ṁ
  - [x] Subtask: Apply conversion to dpd-pane content
  - [x] Subtask: Persist preference in chrome.storage.local
  - [x] Subtask: Load saved preference and apply on panel open

- [x] Task: Implement grammar sections toggle
  - [x] Subtask: Add toggle switch for grammar sections visibility
  - [x] Subtask: Toggle grammar-button active class
  - [x] Subtask: Toggle grammar-div hidden class
  - [x] Subtask: Persist preference in chrome.storage.local
  - [x] Subtask: Load saved preference and apply on content load

- [x] Task: Implement examples sections toggle
  - [x] Subtask: Add toggle switch for example sections visibility
  - [x] Subtask: Toggle example-button active class
  - [x] Subtask: Toggle example-div hidden class
  - [x] Subtask: Persist preference in chrome.storage.local
  - [x] Subtask: Load saved preference and apply on content load

- [x] Task: Implement summary visibility toggle
  - [x] Subtask: Add toggle switch for summary section visibility
  - [x] Subtask: Wrap summary content in summary-results div
  - [x] Subtask: Toggle summary-results display (block/none)
  - [x] Subtask: Persist preference in chrome.storage.local
  - [x] Subtask: Load saved preference and apply on panel open

- [x] Task: Implement sandhi apostrophe toggle
  - [x] Subtask: Add toggle switch for sandhi apostrophe visibility
  - [x] Subtask: Hide/restore apostrophes in .sandhi elements
  - [x] Subtask: Persist preference in chrome.storage.local
  - [x] Subtask: Load saved preference and apply on content load

- [x] Task: Implement audio voice toggle
  - [x] Subtask: Add toggle switch for audio voice selection (male/female)
  - [x] Subtask: Store voice preference in chrome.storage.local
  - [x] Subtask: Load saved preference on audio playback

- [x] Task: Apply theme colors to settings menu
  - [x] Subtask: Use CSS variables for all colors (background, text, borders, accents)
  - [x] Subtask: Ensure settings menu inherits active theme colors
  - [x] Subtask: Test settings appearance across all themes

- [x] Task: Add collapse toggle for settings pane
  - [x] Subtask: Add collapse button to settings pane header
  - [x] Subtask: Implement collapse/expand functionality
  - [x] Subtask: Persist collapsed state in chrome.storage.local
  - [x] Subtask: Restore collapsed state on panel open

- [x] Task: Remove sans/serif font toggle
  - [x] Subtask: Remove toggle from settings menu
  - [x] Subtask: Remove all related code (listener, application function)

- [x] Task: Fix button layout
  - [x] Subtask: Group theme and settings buttons together in header
  - [x] Subtask: Position group on top right of header

- [x] Task: Test all settings functionality
  - [x] Subtask: Verify each toggle works correctly
  - [x] Subtask: Verify settings persist across panel open/close
  - [x] Subtask: Verify settings persist across browser sessions
  - [x] Subtask: Verify settings work with all themes

- [x] Task: Fix summary toggle not working
  - [x] Subtask: Identify why summary toggle fails
  - [x] Subtask: Fix summary toggle to match webapp behavior
  - [x] Subtask: Test summary toggle with and without summary content

- [x] Task: Fix sandhi toggle not working
  - [x] Subtask: Identify why sandhi toggle fails
  - [x] Subtask: Fix sandhi toggle to match webapp behavior
  - [x] Subtask: Test sandhi toggle with and without sandhi content

- [x] Task: Fix audio toggle not working
  - [x] Subtask: Identify why audio toggle fails
  - [x] Subtask: Fix audio toggle to match webapp behavior
  - [x] Subtask: Test audio playback with both voices

- [x] Task: Conductor - User Manual Verification 'Phase 5: Settings Menu Implementation' (Protocol in workflow.md)
  - [x] Subtask: Verify each toggle works correctly
  - [x] Subtask: Verify settings persist across panel open/close
  - [x] Subtask: Verify settings persist across browser sessions
  - [x] Subtask: Verify settings work with all themes

- [x] Task: Conductor - User Manual Verification 'Phase 5: Settings Menu Implementation' (Protocol in workflow.md)
  - [ ] Subtask: Add +/- buttons for font size adjustment
  - [ ] Subtask: Display current font size value
  - [ ] Subtask: Persist font size preference in chrome.storage.local
  - [ ] Subtask: Load saved font size on panel open
  - [ ] Subtask: Apply font size to panel container

- [ ] Task: Implement sans/serif font toggle
  - [ ] Subtask: Add toggle switch for sans/serif font selection
  - [ ] Subtask: Toggle between Source Serif 4 and Inter fonts
  - [ ] Subtask: Persist preference in chrome.storage.local
  - [ ] Subtask: Load saved preference on panel open

- [ ] Task: Implement niggahita ṃ/ṁ toggle
  - [ ] Subtask: Add toggle switch for niggahita character display
  - [ ] Subtask: Implement conversion function ṃ ↔ ṁ
  - [ ] Subtask: Apply conversion to dpd-pane and history-pane content
  - [ ] Subtask: Persist preference in chrome.storage.local
  - [ ] Subtask: Load saved preference and apply on panel open

- [ ] Task: Implement grammar sections toggle
  - [ ] Subtask: Add toggle switch for grammar sections visibility
  - [ ] Subtask: Toggle grammar-button active class
  - [ ] Subtask: Toggle grammar-div hidden class
  - [ ] Subtask: Persist preference in chrome.storage.local
  - [ ] Subtask: Load saved preference and apply on content load

- [ ] Task: Implement examples sections toggle
  - [ ] Subtask: Add toggle switch for example sections visibility
  - [ ] Subtask: Toggle example-button active class
  - [ ] Subtask: Toggle example-div hidden class
  - [ ] Subtask: Persist preference in chrome.storage.local
  - [ ] Subtask: Load saved preference and apply on content load

- [ ] Task: Implement summary visibility toggle
  - [ ] Subtask: Add toggle switch for summary section visibility
  - [ ] Subtask: Toggle summary-results display (block/none)
  - [ ] Subtask: Persist preference in chrome.storage.local
  - [ ] Subtask: Load saved preference and apply on panel open

- [ ] Task: Implement sandhi apostrophe toggle
  - [ ] Subtask: Add toggle switch for sandhi apostrophe visibility
  - [ ] Subtask: Add hide-apostrophes CSS class to dpd-results
  - [ ] Subtask: Toggle CSS class based on preference
  - [ ] Subtask: Persist preference in chrome.storage.local
  - [ ] Subtask: Load saved preference and apply on content load

- [ ] Task: Implement audio voice toggle
  - [ ] Subtask: Add toggle switch for audio voice selection (male/female)
  - [ ] Subtask: Store voice preference in chrome.storage.local
  - [ ] Subtask: Load saved preference on audio playback

- [ ] Task: Apply theme colors to settings menu
  - [ ] Subtask: Use CSS variables for all colors (background, text, borders, accents)
  - [ ] Subtask: Ensure settings menu inherits active theme colors
  - [ ] Subtask: Test settings appearance across all themes

- [ ] Task: Add collapse toggle for settings pane
  - [ ] Subtask: Add collapse button to settings pane header
  - [ ] Subtask: Implement collapse/expand functionality
  - [ ] Subtask: Persist collapsed state in chrome.storage.local
  - [ ] Subtask: Restore collapsed state on panel open

- [ ] Task: Test all settings functionality
  - [ ] Subtask: Verify each toggle works correctly
  - [ ] Subtask: Verify settings persist across panel open/close
  - [ ] Subtask: Verify settings persist across browser sessions
  - [ ] Subtask: Verify settings work with all themes

- [ ] Task: Conductor - User Manual Verification 'Phase 5: Settings Menu Implementation' (Protocol in workflow.md)

## Phase 6: Chrome Store Preparation

- [ ] Task: Create comprehensive documentation
  - [ ] Subtask: Write README.md with extension description and features
  - [ ] Subtask: Add installation instructions for Chrome Developer Mode
  - [ ] Subtask: Add usage guide for word selection and lookup
  - [ ] Subtask: Add theme selection guide with screenshots
  - [ ] Subtask: Add troubleshooting section for common issues
  - [ ] Subtask: Add FAQ section

- [ ] Task: Prepare Chrome Web Store assets
  - [ ] Subtask: Take screenshots of extension in action (1280x800, 640x400)
  - [ ] Subtask: Write detailed store description (features, benefits, usage)
  - [ ] Subtask: Create privacy policy document (if required by Chrome)
  - [ ] Subtask: Prepare store icon (128x128) from logo source
  - [ ] Subtask: Prepare promotional images and marketing materials

- [ ] Task: Perform comprehensive testing
  - [ ] Subtask: Test on Google Chrome latest version
  - [ ] Subtask: Test on Digital Pāli Reader website
  - [ ] Subtask: Test on SuttaCentral website
  - [ ] Subtask: Test on unknown/random websites
  - [ ] Subtask: Test theme dropdown functionality thoroughly
  - [ ] Subtask: Test theme persistence across sessions
  - [ ] Subtask: Test offline scenario (network failure handling)
  - [ ] Subtask: Test API failure scenarios
  - [ ] Subtask: Verify no console errors in normal operation
  - [ ] Subtask: Check for memory leaks over extended use
  - [ ] Subtask: Performance testing: ensure <2s rendering, <100ms theme detection

- [ ] Task: Finalize build and packaging
  - [ ] Subtask: Update version to 1.0.0 (follow semantic versioning)
  - [ ] Subtask: Run `npm run build` to generate all assets
  - [ ] Subtask: Run `npm run zip` to create Chrome Store package
  - [ ] Subtask: Verify zip file structure matches Chrome requirements
  - [ ] Subtask: Test loading extension from zip file in Chrome

- [ ] Task: Conductor - User Manual Verification 'Phase 4: Chrome Store Preparation' (Protocol in workflow.md)
