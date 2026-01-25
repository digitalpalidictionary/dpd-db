# WXT Cross-Browser Extension Implementation with TypeScript

## Overview
Migrate the existing DPD Chrome extension to use the WXT framework for cross-browser compatibility, supporting both Chrome and Firefox from a single TypeScript codebase while maintaining all current functionality. This will be created in a new `exporter/wxt_extension` folder, keeping the existing `chrome_extension` folder intact.

## Functional Requirements

### Core Feature Preservation
- [ ] Double-click word lookup functionality
- [ ] Theme switching (auto/light/dark) with host page detection
- [ ] Domain auto-enable for Dhamma websites (suttacentral.net, etc.)
- [ ] Icon state management (gray/colored for on/off states)
- [ ] Per-domain settings persistence
- [ ] Dictionary panel UI with search results display
- [ ] API integration with dpdict.net for dictionary data
- [ ] Pāḷi-aware table sorting for grammar dictionary
- [ ] Word selection expansion across text nodes
- [ ] Drag selection handling
- [ ] Panel resizing functionality

### Cross-Browser Compatibility
- [ ] Chrome extension (Manifest V3) generation
- [ ] Firefox extension (Manifest V3) generation
- [ ] Unified API usage via webextension-polyfill
- [ ] Browser-specific manifest configurations
- [ ] Cross-browser testing support

### TypeScript Migration
- [ ] Convert all JavaScript files to TypeScript
- [ ] Add proper type definitions for browser APIs
- [ ] Type safety for all extension interfaces
- [ ] Maintain existing functionality during conversion
- [ ] Strict TypeScript configuration

### Build System Modernization
- [ ] WXT framework integration with Vite
- [ ] Hot reload development mode for both browsers
- [ ] Automated packaging for Chrome (.zip) and Firefox (.xpi)
- [ ] TypeScript compilation and type checking
- [ ] Asset management (icons, CSS, images)

## Non-Functional Requirements

### Development Experience
- [ ] Single command development: `wxt dev -b chrome,firefox`
- [ ] Fast build times with Vite and TypeScript
- [ ] Clear error messages and debugging support
- [ ] Maintained code structure and organization
- [ ] Type safety and IntelliSense support

### Code Quality
- [ ] 95%+ code reuse between browsers
- [ ] Full TypeScript coverage with strict types
- [ ] Consistent API usage throughout codebase
- [ ] Proper error handling and logging
- [ ] No implicit any types

### Performance
- [ ] Minimal extension size
- [ ] Fast content script injection
- [ ] Efficient resource loading
- [ ] Low memory footprint
- [ ] Optimized TypeScript compilation

## Acceptance Criteria

### Chrome Extension
- [ ] Loads and functions identically to current extension
- [ ] Passes Chrome Web Store validation
- [ ] All existing features work without regression
- [ ] Proper icon states and theme switching
- [ ] TypeScript compilation produces valid JS

### Firefox Extension
- [ ] Installs and loads in Firefox without errors
- [ ] All features match Chrome functionality
- [ ] Proper Firefox-specific manifest settings
- [ ] Compatible with Firefox Add-on guidelines
- [ ] TypeScript types work correctly in Firefox context

### Build System
- [ ] `wxt build -b chrome` produces working Chrome extension
- [ ] `wxt build -b firefox` produces working Firefox extension
- [ ] Development mode works for both browsers simultaneously
- [ ] TypeScript compilation passes without errors
- [ ] Asset generation (icons, CSS) works correctly

### Code Migration
- [ ] All JavaScript files converted to TypeScript
- [ ] All browser APIs properly typed
- [ ] No Chrome-specific API dependencies remain
- [ ] Clean, maintainable TypeScript code structure
- [ ] Strict TypeScript configuration enforced

## Migration Strategy

### Complete Replacement Approach
- [ ] Create new exporter/wxt_extension structure with WXT
- [ ] Preserve existing chrome_extension folder unchanged
- [ ] Maintain all existing functionality without regression
- [ ] Single codebase approach for long-term maintainability
- [ ] TypeScript-first development approach

### Current Extension Inventory
- [ ] Background service worker (background.js → background.ts, 67 lines)
- [ ] Content script main (main.js → content.ts, 137 lines)
- [ ] UI components (dictionary-panel.js → dictionary-panel.ts)
- [ ] Theme management (themes.js → themes.ts)
- [ ] Utility functions (utils.js → utils.ts, 161 lines)
- [ ] Table sorting (sorter.js → sorter.ts, 132 lines)
- [ ] Asset pipeline (sharp for icons → WXT asset handling)
- [ ] Manifest V3 configuration (WXT-generated)

## Technical Implementation Details

### Specific Chrome API Migration
- [ ] chrome.runtime.* → browser.runtime.* (onInstalled, onMessage, sendMessage)
- [ ] chrome.action.* → browser.action.* (setIcon, onClicked)
- [ ] chrome.tabs.* → browser.tabs.* (onUpdated, onActivated, sendMessage)
- [ ] chrome.storage.local.* → browser.storage.local.* (get, set)

### Content Script Dependencies
- [ ] utils.ts (word selection, event handlers, DOM manipulation)
- [ ] themes.ts (theme detection and application logic)
- [ ] dictionary-panel.ts (UI panel component with settings)
- [ ] sorter.ts (Pāḷi-aware table sorting)
- [ ] content.ts (main initialization and coordination)

### TypeScript Conversion Requirements
- [ ] Configure strict TypeScript settings
- [ ] Add @types/webextension-polyfill for browser APIs
- [ ] Create interfaces for extension data structures
- [ ] Type all function parameters and return values
- [ ] Add proper error handling with typed exceptions
- [ ] Ensure no implicit any types remain
- [ ] Type DOM manipulation and event handlers
- [ ] Type storage data structures

### Asset Management Migration
- [ ] Copy all assets from chrome_extension to wxt_extension
- [ ] Migrate icon generation from sharp to WXT asset pipeline
- [ ] Migrate CSS build process to WXT
- [ ] Preserve all existing icon sizes and states (16, 32, 64, 128px)
- [ ] Maintain current CSS organization and variables
- [ ] Add TypeScript types for asset imports

### CSS Assets Migration
- [ ] Copy chrome-extension.css to styles/chrome-extension.css
- [ ] Copy dpd-variables.css to styles/dpd-variables.css
- [ ] Copy dpd.css to styles/dpd.css
- [ ] Maintain CSS organization and imports
- [ ] Preserve all styling functionality

### Icon Assets Migration
- [ ] Copy all icon sizes: 16, 32, 64, 128px
- [ ] Preserve both normal and gray states
- [ ] Copy SVG assets (dpd-logo.svg)
- [ ] Copy additional assets (dpr_imgbk.png, pin_extension.png)
- [ ] Replace sharp generation with WXT asset handling

### Build Script Migration
- [ ] Replace sharp-based icon generation with WXT
- [ ] Replace custom CSS build with WXT asset pipeline
- [ ] Migrate packaging from bestzip to WXT output
- [ ] Preserve all asset files during migration
- [ ] Update package.json scripts for WXT workflow

### Host Permissions and Resources
- [ ] Preserve host permissions: https://dpdict.net/*, http://0.0.0.0:8080/*
- [ ] Maintain web accessible resources configuration
- [ ] Preserve content script matches: <all_urls>
- [ ] Maintain permissions: activeTab, scripting, storage

### Auto-Domains Synchronization
- [ ] Preserve AUTO_DOMAINS array in both background and content scripts
- [ ] Ensure domain detection logic remains consistent
- [ ] Maintain auto-enable functionality for Dhamma sites

### Development Workflow
- [ ] `wxt dev -b chrome,firefox` for simultaneous development
- [ ] `wxt build -b chrome` for Chrome production build
- [ ] `wxt build -b firefox` for Firefox production build
- [ ] Hot reload support for both browsers
- [ ] TypeScript compilation and type checking
- [ ] Linting with TypeScript-aware tools

## Out of Scope

- [ ] Safari/Edge support (future enhancement)
- [ ] New features beyond current functionality
- [ ] Backend API changes
- [ ] Mobile browser extensions
- [ ] Extension store publishing process
- [ ] Modifications to existing chrome_extension folder

## Technical Notes

### File Structure
```
exporter/wxt_extension/
├── entrypoints/
│   ├── background.ts
│   ├── content.ts
│   ├── dictionary-panel.ts
│   ├── themes.ts
│   ├── utils.ts
│   └── sorter.ts
├── assets/
│   ├── icons/
│   │   ├── dpd-logo_16.png
│   │   ├── dpd-logo_32.png
│   │   ├── dpd-logo_64.png
│   │   ├── dpd-logo_128.png
│   │   ├── dpd-logo-gray_16.png
│   │   ├── dpd-logo-gray_32.png
│   │   ├── dpd-logo-gray_64.png
│   │   ├── dpd-logo-gray_128.png
│   │   ├── dpd-logo.svg
│   │   ├── dpr_imgbk.png
│   │   └── pin_extension.png
│   └── styles/
│       ├── chrome-extension.css
│       ├── dpd-variables.css
│       └── dpd.css
├── types/
│   └── extension.d.ts
├── wxt.config.ts
└── package.json
```

### Browser-Specific Configurations
- Chrome: Standard Manifest V3 settings
- Firefox: Add browser_specific_settings with gecko ID
- Both: Shared permissions, content scripts, and resources
- TypeScript: Unified types across both browsers

### TypeScript Configuration
- Strict mode enabled
- No implicit any
- Proper browser API typing
- Custom interfaces for extension data
- Error handling with typed exceptions
- DOM event handler typing
- Storage data structure typing