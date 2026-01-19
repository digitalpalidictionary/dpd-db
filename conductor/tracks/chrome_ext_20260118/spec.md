# Specification: Chrome Extension - Bug Fixes, Theme Detection & Chrome Store Release

## Overview

Fix critical bugs in the existing DPD Chrome extension, move it to `dpd-db/exporter/chrome_extension`, implement JSON API-based dictionary rendering to match the webapp, add intelligent theme detection with manual override, and prepare for Chrome Web Store release.

### Repository Structure

- **New Location**: `dpd-db/exporter/chrome_extension/`
- **Shared Resources**:
  - Logos from `dpd-db/identity/logo/`
  - CSS from `dpd-db/identity/css/`
  - Webapp templates from `dpd-db/exporter/webapp/`
- **Build Output**: Extension zip file for Chrome Store and releases

### Current Issues Identified

1. **Invalid API Proxy**: Using `dpd-proxy.snyatix.my.id` instead of official `www.dpdict.net`
2. **Missing CSP Permissions**: No `host_permissions` in manifest.json to fetch from external APIs
3. **Script Loading Order Bug**: `utils.js` calls functions from `main.js` but loads first
4. **External Asset Dependencies**: Panel logo loads from external URL instead of local images
5. **Iframe Architecture**: Using iframe for dictionary results prevents proper theming and is 4.5× slower
6. **No Build System**: Missing package.json, no version management or build tooling
7. **Missing Documentation**: No README or installation instructions
8. **iframe CSS Issues**: Height/width styling incorrectly applied
9. **No Error Handling**: Missing network failure and empty result handling
10. **Repository Location**: Currently in separate repo, needs to move to dpd-db

## Functional Requirements

### 1. Migration to dpd-db Repository

#### 1.1 Move Extension Code
- Move entire `dpd-chrome/` directory to `dpd-db/exporter/chrome_extension/`
- Update all file paths and references
- Ensure no hardcoded absolute paths remain

#### 1.2 Shared Logo Assets
- Create script to generate icon sizes from `identity/logo/dpd-logo.svg`
- Generate: 16x16, 32x32, 64x64, 128x128 PNG icons
- Copy to `exporter/chrome_extension/images/` directory
- Update manifest.json to reference local icon paths
- Add to build process to regenerate when logo changes

#### 1.3 Shared CSS Management
- Import base styles from `identity/css/` (following existing CSS management pattern)
- Use `tools/css_manager.py` approach for CSS distribution
- Create extension-specific CSS overrides in separate file
- Ensure CSS variables are available for theming

#### 1.4 Mimic Webapp Behavior
- Study `exporter/webapp/` templates and components
- Copy/reuse HTML structure for dictionary results
- Ensure identical behavior to dpdict.net:
  - Expand/collapse sections
  - Navigation within results
  - Styling and layout
  - Interactive elements

### 2. Critical Bug Fixes

#### 2.1 Update API Endpoint
- Replace `https://dpd-proxy.snyatix.my.id/gd?search=` with `https://www.dpdict.net/search_json?q=`
- Use JSON response format: `{summary_html: string, dpd_html: string}`
- Add proper error handling for API failures

#### 2.2 Grammar Sorter (FIXED)
- **Status**: Functional.
- **Goal**: Restore 3-phase Pāḷi sorting (Asc -> Desc -> Reset) for grammar tables.
- **Fix**: Re-implemented sorter logic within `dictionary-panel.js` to ensure reliable initialization on dynamically loaded extension content.

#### 2.2 Add Host Permissions
- Update manifest.json to include:
  ```json
  "host_permissions": ["https://www.dpdict.net/*"]
  ```
- Ensure CSP allows fetching from dpdict.net

#### 2.3 Fix Script Loading Order
- In background.js, change load order to:
  1. utils.js
  2. dictionary-panel.js
  3. main.js (after utils.js is loaded)
- Ensure dependencies are properly established

#### 2.4 Use Local Assets
- Replace external logo URL with `chrome.runtime.getURL("images/dpd-logo.svg")`
- Update all icon references in manifest.json to use local files
- Build script generates icons from `identity/logo` source

#### 2.5 JSON API Rendering (Architecture Change)
- **Remove iframe-based rendering**
- Use `fetch()` to call `/search_json?q=<word>` endpoint
- Parse JSON response and render HTML directly into panel div
- Mimic `exporter/webapp` HTML structure and styling exactly
- Ensure all interactive elements work (expand/collapse, navigation, etc.)

#### 2.6 Fix CSS Styling Issues
- Remove iframe-specific CSS (height: 100vh, width: 100%)
- **Fix aggressive `body` styling that breaks host pages**
- **Implement CSS isolation (e.g., Shadow DOM) to prevent style leakage**
- Apply correct sizing to panel container div
- Ensure responsive design works on different screen sizes
- Import and use CSS variables from identity/css

#### 2.7 Add Error Handling
- Network timeout handling (30 seconds)
- Empty result handling with user-friendly message
- Rate limiting handling (429 status)
- Graceful degradation for API failures

#### 2.8 Create Build System
- Add package.json with:
  - Extension name, version, description
  - Scripts: `build` (generate icons, copy resources), `zip` (create Chrome Store package)
  - DevDependencies: version management, build tools
- Add .gitignore for build artifacts
- Create build scripts:
  - Generate icon sizes from logo source
  - Copy CSS from identity/css
  - Copy webapp templates if needed
  - Zip extension for Chrome Store submission

### 3. Theme Detection System

#### 3.1 URL-Based Theme Detection
- Detect Digital Pāli Reader: URL contains "digitalpalireader"
- Detect SuttaCentral: URL contains "suttacentral"
- Apply pre-configured theme based on detected site
- Cache detected theme per domain to avoid recalculating

#### 3.2 Pre-Defined Themes
- **Digital Pāli Reader Theme**: Match DPR's color scheme (light background, warm accents)
- **SuttaCentral Theme**: Match SuttaCentral's color scheme (modern, clean, potentially dark mode)
- **Default Theme**: Fallback theme for unknown sites
- Themes defined in separate file: `themes.js`
- Each theme includes: background, text, accent colors, font family, font size

#### 3.3 Theme Dropdown (Manual Override)
- Add theme selector icon in top-left header of panel
- Dropdown shows list of all available themes:
  - Auto (default - automatic detection)
  - Digital Pāli Reader
  - SuttaCentral
  - Default
  - [Future themes]
- User selection persists for current domain only
- Auto mode re-enables automatic detection
- Selection updates immediately without page refresh

#### 3.4 Dynamic Color Extraction (Fallback)
- For unknown sites in Auto mode, use `window.getComputedStyle()` to extract:
  - Background color
  - Text color
  - Font family
  - Font size
  - Accent colors (buttons, links, headers)
- Map extracted colors to extension panel CSS variables
- Cache extracted theme per domain to avoid recalculating
- Fallback to Default theme if extraction fails

#### 3.5 Theme Application
- Apply theme colors to panel container
- Ensure good contrast and readability
- Support both light and dark variants
- Allow theme to update when page changes (SPA navigation)
- Use CSS variables for all themable properties

#### 3.6 Theme Persistence
- Store theme preference per domain in chrome.storage.local
- On extension load, retrieve saved theme for current domain
- If no saved theme, use Auto mode
- Persist theme dropdown selection

### 4. Settings Menu Implementation

#### 4.1 Settings Menu Structure
- Add cog/gear icon to panel header next to theme selector
- Clicking cog icon toggles settings dropdown menu visibility
- Settings menu positioned below cog icon
- Clicking outside closes the dropdown
- Collapsible settings pane with collapse toggle button

#### 4.2 Font Size Controls
- Add +/- buttons for font size adjustment
- Display current font size value (in pixels)
- Font size adjustable within reasonable range (e.g., 12px - 24px)
- Apply font size to panel container
- Persist font size preference in chrome.storage.local
- Load saved font size on panel open
- Update content dynamically when font size changes

#### 4.3 Font Family Toggle (Sans/Serif)
- Add toggle switch for sans/serif font selection
- Sans font: Inter (same as webapp)
- Serif font: Source Serif 4 (same as webapp)
- Apply font family to panel container and inputs
- Persist preference in chrome.storage.local
- Load saved preference on panel open

#### 4.4 Niggahita Character Toggle (ṃ/ṁ)
- Add toggle switch for niggahita character display
- When ON: convert all ṃ to ṁ
- When OFF: convert all ṁ to ṃ
- Apply conversion to dpd-pane and history-pane content
- Persist preference in chrome.storage.local
- Load saved preference and apply on content load
- Re-apply when new content is loaded via API

#### 4.5 Grammar Sections Toggle
- Add toggle switch for grammar sections visibility
- When ON: show all grammar sections (add active class to grammar-button, remove hidden class from grammar-div)
- When OFF: hide all grammar sections (remove active class, add hidden class)
- Persist preference in chrome.storage.local
- Load saved preference and apply on content load
- Re-apply when new content is loaded via API

#### 4.6 Example Sections Toggle
- Add toggle switch for example sections visibility
- When ON: show all example sections (add active class to example-button, remove hidden class from example-div)
- When OFF: hide all example sections (remove active class, add hidden class)
- Persist preference in chrome.storage.local
- Load saved preference and apply on content load
- Re-apply when new content is loaded via API

#### 4.7 Summary Visibility Toggle
- Add toggle switch for summary section visibility
- When ON: show summary-results (display: block)
- When OFF: hide summary-results (display: none)
- Persist preference in chrome.storage.local
- Load saved preference on panel open
- Apply immediately when toggled

#### 4.8 Sandhi Apostrophe Toggle
- Add toggle switch for sandhi apostrophe visibility
- When ON: show apostrophes in sandhi
- When OFF: hide apostrophes in sandhi (add hide-apostrophes CSS class to dpd-results)
- Persist preference in chrome.storage.local
- Load saved preference and apply on content load
- Re-apply when new content is loaded via API

#### 4.9 Audio Voice Toggle
- Add toggle switch for audio voice selection
- When ON: male voice
- When OFF: female voice
- Store voice preference in chrome.storage.local
- Load saved preference on audio playback

#### 4.10 Theme Integration
- Settings menu must use CSS variables for all colors
- All colors inherit from active theme:
  - Background color
  - Text color
  - Border colors
  - Accent/highlight colors
  - Hover states
- Settings menu appearance updates when theme changes
- Settings menu works correctly across all themes (DPR, SuttaCentral, Default, Auto)

#### 4.11 Settings Persistence
- All settings stored in chrome.storage.local
- Settings load on panel initialization
- Settings apply immediately when toggled
- Settings persist across browser sessions
- No data sent to external servers

### 5. Chrome Store Preparation (Final Step)

#### 5.1 Create Documentation
- README.md with:
  - Extension description and features
  - Installation instructions (Chrome Developer Mode)
  - Usage guide
  - Theme selection guide
  - Settings guide
  - Troubleshooting common issues

#### 5.2 Chrome Web Store Assets
- Prepare all required screenshots (1280x800, 640x400)
- Write detailed store description
- Create privacy policy (if needed)
- Prepare store icon (128x128)

#### 5.3 Testing Checklist
- Test on Google Chrome latest version
- Test on different websites (DPR, SuttaCentral, unknown sites)
- Test theme dropdown functionality
- Test theme persistence across sessions
- Test all settings functionality
- Test settings persistence across sessions
- Test error scenarios (offline, API failures)
- Verify no console errors
- Check memory leaks and performance

## Non-Functional Requirements

### Performance
- Panel rendering should complete within 2 seconds of word selection
- Theme detection should complete within 100ms
- Theme dropdown should appear within 50ms
- Settings menu should appear within 50ms
- Settings changes should apply immediately (<100ms)
- Memory usage should remain stable (no leaks over extended use)

### Maintainability
- Code should follow project's existing JavaScript conventions
- Type hints should be added where appropriate (JSDoc comments)
- CSS should use variables for theming, not hardcoded values
- Follow existing CSS management pattern (identity/css as source of truth)

### Security
- Use Content Security Policy appropriately
- No inline scripts or styles
- All external requests go only to dpdict.net
- No user data collection or storage beyond theme and settings preferences
- Theme and settings interactions use chrome.storage.local API
- No sensitive data transmitted externally

### Compatibility
- Works with Chrome 88+
- Works with Chromium-based browsers (Edge, Brave, Opera)
- Responsive design works on screens 1024px and above
- Theme dropdown accessible via keyboard navigation
- Settings menu accessible via keyboard navigation

## Acceptance Criteria

### Migration
- [ ] Extension moved to `dpd-db/exporter/chrome_extension/`
- [ ] All file paths updated correctly
- [ ] Icons generated from `identity/logo/dpd-logo.svg`
- [ ] CSS imported from `identity/css/`
- [ ] Build system generates icons and copies resources

### Bug Fixes
- [ ] Extension loads without errors in Chrome Developer Mode
- [ ] Word selection triggers dictionary lookup using dpdict.net
- [ ] Results display correctly using JSON API (not iframe)
- [ ] All local assets (logos, icons) load correctly
- [ ] Network errors display user-friendly messages
- [ ] No console errors in normal operation

### Theme Detection
- [ ] DPR website applies correct pre-defined theme
- [ ] SuttaCentral website applies correct pre-defined theme
- [ ] Unknown websites extract colors dynamically in Auto mode
- [ ] Theme updates when navigating within single-page apps
- [ ] Panel styling is readable and well-contrasted

### Theme Dropdown
- [ ] Theme selector icon appears in top-left header
- [ ] Dropdown shows all available themes
- [ ] Manual theme selection works immediately
- [ ] Auto mode re-enables automatic detection
- [ ] Theme preference persists per domain
- [ ] Dropdown is keyboard accessible

### Settings Menu
- [ ] Settings cog icon appears in panel header next to theme selector
- [ ] Clicking cog icon opens settings dropdown menu
- [ ] Settings menu displays all available options:
  - Font size (+/- buttons with current value display)
  - Sans/serif font toggle
  - Niggahita ṃ/ṁ toggle
  - Grammar sections toggle (closed/open)
  - Example sections toggle (closed/open)
  - Summary visibility toggle (hide/show)
  - Sandhi apostrophe toggle (hide/show)
  - Audio voice toggle (male/female)
- [ ] Settings menu can be collapsed/expanded
- [ ] All settings persist in chrome.storage.local
- [ ] Settings load on panel open
- [ ] Settings apply immediately when toggled
- [ ] Settings menu colors inherit from active theme using CSS variables
- [ ] Settings menu is keyboard accessible
- [ ] Niggahita conversion works correctly on dpd-pane and history-pane
- [ ] Grammar sections show/hide correctly
- [ ] Example sections show/hide correctly
- [ ] Summary section shows/hides correctly
- [ ] Sandhi apostrophes show/hide correctly
- [ ] Font size adjustments apply correctly to panel
- [ ] Font family toggle switches between Inter and Source Serif 4

### Settings Menu
- [ ] Settings cog icon appears in panel header next to theme selector
- [ ] Clicking cog icon opens settings dropdown menu
- [ ] Settings menu displays all available options:
  - Font size (+/- buttons with current value display)
  - Sans/serif font toggle
  - Niggahita ṃ/ṁ toggle
  - Grammar sections toggle (closed/open)
  - Example sections toggle (closed/open)
  - Summary visibility toggle (hide/show)
  - Sandhi apostrophe toggle (hide/show)
  - Audio voice toggle (male/female)
- [ ] Settings menu can be collapsed/expanded
- [ ] All settings persist in chrome.storage.local
- [ ] Settings load on panel open
- [ ] Settings apply immediately when toggled
- [ ] Settings menu colors inherit from active theme using CSS variables
- [ ] Settings menu is keyboard accessible
- [ ] Niggahita conversion works correctly on dpd-pane and history-pane
- [ ] Grammar sections show/hide correctly
- [ ] Example sections show/hide correctly
- [ ] Summary section shows/hides correctly
- [ ] Sandhi apostrophes show/hide correctly
- [ ] Font size adjustments apply correctly to panel
- [ ] Font family toggle switches between Inter and Source Serif 4

### Build System
- [ ] package.json exists with correct metadata
- [ ] `npm run build` generates icons and copies resources
- [ ] `npm run zip` creates valid Chrome extension zip file
- [ ] README.md provides clear installation instructions
- [ ] Build process uses identity/logo as source of truth

### Chrome Store Ready
- [ ] Store description written and approved
- [ ] Screenshots prepared (1280x800, 640x400)
- [ ] Privacy policy created (if required)
- [ ] Extension tested and verified bug-free
- [ ] Version follows semantic versioning (e.g., 1.0.0)

## Out of Scope

- Mobile browsers (mobile Safari, mobile Chrome)
- Firefox/Microsoft Edge extension formats (though Chromium-based browsers will work)
- User accounts or authentication beyond local theme preferences
- Offline functionality
- Custom dictionaries beyond dpdict.net
- Advanced features like bookmarks, history, favorites (can be added later)
- Internationalization/languages other than English
