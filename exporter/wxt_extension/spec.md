# DPD WXT Extension - Complete Specification

## Overview
The Digital Pāḷi Dictionary (DPD) browser extension built with WXT framework for cross-browser compatibility (Chrome and Firefox) using TypeScript. The extension allows users to search Pāli words by double-clicking anywhere or selecting text on the webpage.

## Architecture

### Framework & Build System
- **WXT Framework**: Modern web extension framework supporting cross-browser development.
- **TypeScript**: Strict mode enabled with comprehensive type definitions.
- **Vite**: Fast compilation and bundling via WXT.
- **webextension-polyfill**: Unified browser API across Chrome and Firefox.

### Browser Support
- **Chrome**: Manifest V3.
- **Firefox**: Manifest V3 (production), Manifest V2 (development hot-reload support).

## File Structure & Functionality

### Configuration Files

#### `package.json`
- **Scripts**: 
    - `dev:chrome` / `dev:firefox`: Development with hot-reload.
    - `build:chrome` / `build:firefox`: Production builds (MV3).
    - `zip:chrome` / `zip:firefox`: Packaging for distribution.
    - `package`: Combined build and zip for all supported browsers.
- **Dependencies**: `webextension-polyfill` for browser API compatibility.
- **Dev Dependencies**: TypeScript, WXT framework, and type definitions.

#### `wxt.config.ts`
- **Manifest Configuration**: Extension metadata (DPD Dictionary), description, and versioning.
- **Action Block**: Explicitly defines `default_icon` for Manifest V3 compliance.
- **Permissions**: `storage`, `activeTab`, `scripting`.
- **Host Permissions**: `dpdict.net` and multiple local development addresses (`127.1.1.1:8080`, `0.0.0.0:8080`, etc.).
- **Web Accessible Resources**: Exposes icons, SVG assets, and CSS files to host pages.
- **Browser-Specific Settings**: Gecko ID for Firefox identity.

#### `tsconfig.json`
- **Compiler Options**: ESNext target, strict mode, path aliases (`@/*`).

### Core Entrypoints

#### `entrypoints/background.ts`
**Purpose**: Service worker handling extension lifecycle and API communication.

**Key Functions**:
- `updateIcon(tabId, state)`: Updates extension icon based on activation state (Color vs Gray).
- `getDomainState(url)`: Determines if extension should be active for domain.
- `handleAutoDomains()`: Manages predefined auto-activation domains.

**Auto-Domains**: suttacentral.net, suttacentral.express, suttacentral.now, digitalpalireader.online, thebuddhaswords.net, tipitaka.org, tipitaka.lk, open.tipitaka.lk, tipitaka.paauksociety.org

**Event Handlers**:
- `onInstalled`: Sets first-run flag.
- `onClicked`: Toggles extension state per domain.
- `onUpdated` / `onActivated`: Synchronizes icon state.
- `onMessage`: 
    - `fetchData`: Proxies API requests to bypass CORS and handle dynamic server routing.
    - `getApiBaseUrl`: Returns the currently detected base URL to content scripts.

#### `entrypoints/content.ts`
**Purpose**: Content script injection and user interaction handling.

**Key Functions**:
- `handleSelectedWord(word)`: Global word search handler.
    - **Normalization**: Lowercases queries to handle diacritics (e.g., `Ṭhānaṁ` -> `ṭhānaṁ`).
    - **Cleaning**: Strips punctuation, quotes, and numbers while preserving internal spaces.
- `init()`: Initializes panel, event listeners, and theme application.
- `destroy()`: Cleans up extension elements and listeners.

### UI Components

#### `components/dictionary-panel.ts`
**Purpose**: Main dictionary panel UI with search, settings, and content display.

**Class: DictionaryPanel**
**Properties**:
- `content`: HTMLDivElement for dictionary content.
- `searchInput`: HTMLInputElement with Velthuis-to-Unicode transliteration.
- `history`: Session-based search history queue (max 50 entries).
- `historyIndex`: Current position in the history queue.

**Key Methods**:
- `setContent(html, isNavigation)`: Sets content and manages the history queue.
- `uniCoder(textInput)`: Converts Velthuis sequences (aa -> ā, .t -> ṭ) in real-time.
- `_navigateHistory(direction)`: Moves back/forward in history instantaneously without new network calls.
- `_playAudio(headword, gender)`: Plays audio pronunciation, dynamically resolving the correct server URL.
- `_showInfo()`: Displays browser-specific instructions (Chrome vs Firefox) for pinning the extension.

**Grammar Table Sorting**:
- `_initGrammarSorter()`: Pāḷi alphabet-aware collation for grammar tables.

### Utility Modules

#### `utils/api.ts`
**Purpose**: Centralized API routing and server detection.
- **Dynamic Probing**: Tests for local servers at `127.1.1.1:8080`, `localhost:8080`, etc., using root `GET` requests.
- **Caching**: Probing results are cached for 1 minute to ensure performance.
- **Synchronization**: Content scripts automatically sync their base URL with the background script's detection results via messaging.

#### `utils/utils.ts`
**Purpose**: Text selection and event handling utilities.
- **Refined Word Expansion**: 
    - Stops at opening quotes (`‘`, `“`) and numbers.
    - **Includes** closing quotes and apostrophes (e.g., `jhānan”ti`) to capture full grammatical units.
- **Selection Handlers**: Handles both double-click and drag-selection (drag-selection is disabled within the sidebar to allow text copying).
- **Safety**: Excludes UI buttons and inputs from triggering searches.

#### `utils/themes.ts`
**Purpose**: Theme detection, application, and color management.
- **Theme Collection**: 
    - `default` (Light)
    - `dpd_dark` (Dark mode matching main CSS)
    - `dpr`, `suttacentral`, `tbw`, `vri`, `tipitakalk`, `paauksociety`.
- **Logic**:
    - Automatic theme detection based on URL.
    - `dark-mode` class toggling for component-specific styles.
    - Robust color extraction for unknown sites, falling back to page styles.

### Styling

#### `assets/styles/chrome-extension.css`
- **Layout**: Fixed sidebar using CSS Grid on the host body.
- **Responsive Header**:
    - **Container Queries**: Layout adapts to panel width, not screen width.
    - **3-Stage Wrap**: 
        1. Wide: Title (Left), Nav (Center), Icons (Right).
        2. Medium: Title centered top row, Nav/Icons split second row.
        3. Narrow: Full vertical stack, shortened title ("DPD Dictionary") swaps in.
- **Interaction**: `user-select: none` on header/footer to prevent UI search triggers.
- **Polished Visuals**: Minimalist placeholders and compact spacing for sidebar efficiency.

## Development & Deployment

### Commands
- `npm run package`: Builds and zips both Chrome and Firefox versions.
- `uv run python scripts/build/zip_wxt_extension.py`: Python wrapper for packaging.

### Deployment
- **Chrome**: Upload `.output/chrome-mv3/*.zip`.
- **Firefox**: Upload `.output/firefox-mv3/*.zip`. Source code archive (`-sources.zip`) included for AMO auditing.
