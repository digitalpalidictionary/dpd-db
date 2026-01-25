# WXT Cross-Browser Extension Implementation Plan

## Phase 1: Project Setup and WXT Configuration

### Task 1.1: Initialize WXT Project Structure
- [x] Create exporter/wxt_extension directory structure
- [x] Set up package.json with WXT dependencies
- [x] Configure TypeScript settings for strict mode
- [x] Create basic wxt.config.ts configuration
- [x] Set up entrypoints directory structure

### Task 1.2: Configure WXT for Cross-Browser Support
- [x] Configure manifest generation for Chrome and Firefox
- [x] Set up browser-specific settings in wxt.config.ts
- [x] Configure webextension-polyfill integration
- [x] Set up asset handling for icons and CSS
- [x] Test basic WXT build for both browsers

### Task 1.3: Migrate Assets to WXT Structure
- [x] Copy all icon assets from chrome_extension to wxt_extension
- [x] Copy all CSS files from chrome_extension to wxt_extension
- [x] Configure asset imports in TypeScript
- [x] Test asset loading in both browsers
- [x] Remove old build scripts and dependencies

- [~] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: TypeScript Migration and API Conversion

### Task 2.1: Create TypeScript Type Definitions
- [x] Create extension.d.ts with browser API types
- [x] Define interfaces for extension data structures
- [x] Type storage data structures and settings
- [x] Type DOM events and panel interactions
- [x] Test TypeScript compilation with basic types

### Task 2.2: Convert Background Script to TypeScript
- [x] Convert background.js to background.ts
- [x] Replace chrome APIs with browser APIs
- [x] Add TypeScript types for all functions
- [x] Test background script functionality in both browsers
- [x] Verify icon state management works correctly

### Task 2.3: Convert Utility Functions to TypeScript
- [x] Convert utils.js to utils.ts with full typing
- [x] Type DOM manipulation functions
- [x] Type event handler functions
- [x] Type word selection and expansion logic
- [x] Test utility functions work identically

### Task 2.4: Convert Theme Management to TypeScript
- [x] Convert themes.js to themes.ts
- [x] Type theme detection functions
- [x] Type color parsing and HSL conversion
- [x] Type theme application logic
- [x] Test theme switching in both browsers

### Task 2.5: Convert Dictionary Panel to TypeScript
- [x] Convert dictionary-panel.js to dictionary-panel.ts
- [x] Type panel class and all methods
- [x] Type settings object and user preferences
- [x] Type DOM creation and event handling
- [x] Test panel functionality and interactions

### Task 2.6: Convert Table Sorter to TypeScript
- [x] Convert sorter.js to sorter.ts
- [x] Type Pāḷi sorting logic and letter mappings
- [x] Type table manipulation functions
- [x] Type event handlers for sorting
- [x] Test table sorting functionality

### Task 2.7: Convert Main Content Script to TypeScript
- [x] Convert main.js to content.ts
- [x] Type initialization and coordination logic
- [x] Type messaging between scripts
- [x] Type domain detection and auto-enable logic
- [x] Test complete content script functionality

- [~] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Cross-Browser Integration and Testing

### Task 3.1: Configure Content Script Loading
- [x] Set up proper content script loading order in WXT
- [x] Configure script dependencies and injection
- [x] Test content script initialization in both browsers
- [x] Verify all scripts load in correct order
- [x] Test script communication and messaging

### Task 3.2: Implement Cross-Browser API Compatibility
- [x] Test browser API compatibility in both Chrome and Firefox
- [x] Verify storage operations work identically
- [x] Test messaging between background and content scripts
- [x] Verify tab management and icon updates
- [x] Test runtime messaging for data fetching

### Task 3.3: Test Core Functionality Cross-Browser
- [x] Test double-click word lookup in both browsers
- [x] Test theme switching and auto-detection
- [x] Test domain auto-enable functionality
- [x] Test icon state management
- [x] Test settings persistence across sessions

### Task 3.4: Test UI Components Cross-Browser
- [x] Test dictionary panel display and interactions
- [x] Test panel resizing functionality
- [x] Test table sorting in grammar dictionary
- [x] Test word selection and expansion
- [x] Test drag selection handling

### Task 3.5: Verify Asset Loading Cross-Browser
- [x] Test icon loading and state changes
- [x] Test CSS styling and theme application
- [x] Test web accessible resources configuration
- [x] Verify all assets load correctly in both browsers
- [x] Test extension permissions and host access

- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Build System and Documentation

### Task 4.1: Finalize Build Configuration
- [x] Configure production builds for both browsers
- [x] Set up build scripts for Chrome and Firefox
- [x] Test packaging (.zip for Chrome, .xpi for Firefox)
- [x] Verify build outputs work correctly
- [x] Test development mode with hot reload

### Task 4.2: Update Documentation
- [x] Create README.md for wxt_extension folder
- [x] Document development workflow and commands
- [x] Create cross-browser testing guide
- [x] Document TypeScript migration approach
- [x] Update any relevant project documentation

### Task 4.3: Clean Up and Final Testing
- [x] Clean up unused dependencies and scripts
- [x] Perform final cross-browser testing
- [x] Verify all functionality works identically
- [x] Test extension installation and loading
- [x] Final verification against chrome_extension functionality

- [x] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)