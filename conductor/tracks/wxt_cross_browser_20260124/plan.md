# WXT Cross-Browser Extension Implementation Plan

## Phase 1: Project Setup and WXT Configuration

### Task 1.1: Initialize WXT Project Structure
- [ ] Create exporter/wxt_extension directory structure
- [ ] Set up package.json with WXT dependencies
- [ ] Configure TypeScript settings for strict mode
- [ ] Create basic wxt.config.ts configuration
- [ ] Set up entrypoints directory structure

### Task 1.2: Configure WXT for Cross-Browser Support
- [ ] Configure manifest generation for Chrome and Firefox
- [ ] Set up browser-specific settings in wxt.config.ts
- [ ] Configure webextension-polyfill integration
- [ ] Set up asset handling for icons and CSS
- [ ] Test basic WXT build for both browsers

### Task 1.3: Migrate Assets to WXT Structure
- [ ] Copy all icon assets from chrome_extension to wxt_extension
- [ ] Copy all CSS files from chrome_extension to wxt_extension
- [ ] Configure asset imports in TypeScript
- [ ] Test asset loading in both browsers
- [ ] Remove old build scripts and dependencies

- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: TypeScript Migration and API Conversion

### Task 2.1: Create TypeScript Type Definitions
- [ ] Create extension.d.ts with browser API types
- [ ] Define interfaces for extension data structures
- [ ] Type storage data structures and settings
- [ ] Create types for DOM events and panel interactions
- [ ] Test TypeScript compilation with basic types

### Task 2.2: Convert Background Script to TypeScript
- [ ] Convert background.js to background.ts
- [ ] Replace chrome APIs with browser APIs
- [ ] Add TypeScript types for all functions
- [ ] Test background script functionality in both browsers
- [ ] Verify icon state management works correctly

### Task 2.3: Convert Utility Functions to TypeScript
- [ ] Convert utils.js to utils.ts with full typing
- [ ] Type DOM manipulation functions
- [ ] Type event handler functions
- [ ] Type word selection and expansion logic
- [ ] Test utility functions work identically

### Task 2.4: Convert Theme Management to TypeScript
- [ ] Convert themes.js to themes.ts
- [ ] Type theme detection functions
- [ ] Type color parsing and HSL conversion
- [ ] Type theme application logic
- [ ] Test theme switching in both browsers

### Task 2.5: Convert Dictionary Panel to TypeScript
- [ ] Convert dictionary-panel.js to dictionary-panel.ts
- [ ] Type panel class and all methods
- [ ] Type settings object and user preferences
- [ ] Type DOM creation and event handling
- [ ] Test panel functionality and interactions

### Task 2.6: Convert Table Sorter to TypeScript
- [ ] Convert sorter.js to sorter.ts
- [ ] Type Pāḷi sorting logic and letter mappings
- [ ] Type table manipulation functions
- [ ] Type event handlers for sorting
- [ ] Test table sorting functionality

### Task 2.7: Convert Main Content Script to TypeScript
- [ ] Convert main.js to content.ts
- [ ] Type initialization and coordination logic
- [ ] Type messaging between scripts
- [ ] Type domain detection and auto-enable logic
- [ ] Test complete content script functionality

- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Cross-Browser Integration and Testing

### Task 3.1: Configure Content Script Loading
- [ ] Set up proper content script loading order in WXT
- [ ] Configure script dependencies and injection
- [ ] Test content script initialization in both browsers
- [ ] Verify all scripts load in correct order
- [ ] Test script communication and messaging

### Task 3.2: Implement Cross-Browser API Compatibility
- [ ] Test browser API compatibility in both Chrome and Firefox
- [ ] Verify storage operations work identically
- [ ] Test messaging between background and content scripts
- [ ] Verify tab management and icon updates
- [ ] Test runtime messaging for data fetching

### Task 3.3: Test Core Functionality Cross-Browser
- [ ] Test double-click word lookup in both browsers
- [ ] Test theme switching and auto-detection
- [ ] Test domain auto-enable functionality
- [ ] Test icon state management
- [ ] Test settings persistence across sessions

### Task 3.4: Test UI Components Cross-Browser
- [ ] Test dictionary panel display and interactions
- [ ] Test panel resizing functionality
- [ ] Test table sorting in grammar dictionary
- [ ] Test word selection and expansion
- [ ] Test drag selection handling

### Task 3.5: Verify Asset Loading Cross-Browser
- [ ] Test icon loading and state changes
- [ ] Test CSS styling and theme application
- [ ] Test web accessible resources configuration
- [ ] Verify all assets load correctly in both browsers
- [ ] Test extension permissions and host access

- [ ] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Build System and Documentation

### Task 4.1: Finalize Build Configuration
- [ ] Configure production builds for both browsers
- [ ] Set up build scripts for Chrome and Firefox
- [ ] Test packaging (.zip for Chrome, .xpi for Firefox)
- [ ] Verify build outputs work correctly
- [ ] Test development mode with hot reload

### Task 4.2: Update Documentation
- [ ] Create README.md for wxt_extension folder
- [ ] Document development workflow and commands
- [ ] Create cross-browser testing guide
- [ ] Document TypeScript migration approach
- [ ] Update any relevant project documentation

### Task 4.3: Clean Up and Final Testing
- [ ] Clean up unused dependencies and scripts
- [ ] Perform final cross-browser testing
- [ ] Verify all functionality works identically
- [ ] Test extension installation and loading
- [ ] Final verification against chrome_extension functionality

- [ ] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)