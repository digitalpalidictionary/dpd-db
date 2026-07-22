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
- **Permissions**: `storage`, `activeTab`.
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

**Auto-Domains** (`utils/domains.ts`): suttacentral.net, suttacentral.express, suttacentral.now, digitalpalireader.online, thebuddhaswords.net, tipitaka.org, tipitaka.lk, open.tipitaka.lk, tipitaka.paauksociety.org, s.4nt.org. Excluded: discourse.suttacentral.net. Matching is exact-host or subdomain (`.endsWith`).

**Event Handlers**:
- `onInstalled`: Sets first-run flag.
- `onClicked`: Toggles extension state per domain. If the site is already popped out, focuses the popout window instead of a no-op toggle.
- `onUpdated` / `onActivated`: Synchronizes icon state.
- `onMessage`: 
    - `fetchData`: Proxies API requests to bypass CORS and handle dynamic server routing. Returns `{success:false}` on non-OK HTTP status so callers fall back to GoldenDict.
    - `getApiBaseUrl`: Returns the currently detected base URL to content scripts.
    - `openPopout` / `popIn`: Detach the dictionary into / return it from a popup window (see Popout below).
    - `popoutSearch` / `popoutTheme`: Host-scoped broadcasts forwarding a selection / a resolved theme key to the site's popout.
- `onBoundsChanged`: Saves a popout's size+position (`popout_geometry`) for reuse on the next open.
- `windows.onRemoved`: A popout closed via its X dismisses DPD across the site; closed via pop-in restores the in-page panel on every tab.

**Popout (Chromium-only)**: One popout **per site**, keyed by hostname in `popout_host_<host>` (`storage.local`) and validated with `windows.get` so stale flags self-heal. Every open tab of a site watches `storage.onChanged` to hide/show its in-page panel in sync (and tears down on `state_<host> → OFF`). The popout is a real OS window created with `neverMinimize: true`. Gated off on Firefox (detached extension-page windows misbehave there).

#### `entrypoints/content.ts`
**Purpose**: Content script injection and user interaction handling.

**Key Functions**:
- `handleSelectedWord(word)`: Global word search handler. When popped out, forwards the word (host-tagged) to the site's popout instead of the hidden in-page panel; otherwise delegates to the shared `searchWord`.
- `init()`: Initializes panel, event listeners, and theme application.
- `teardown()` (message `destroy`): Cleans up extension elements and listeners.
- `storage.onChanged` watcher: keeps every open tab of a site in sync (hide/show on `popout_host_<host>`, tear down on `state_<host> → OFF`).

#### `utils/search.ts`
**Purpose**: Single source of truth for a lookup, shared by the content script and the popout so their behaviour can't drift.
- `searchWord(rawWord, panel)`: cleanWord → "Use GoldenDict" preference → Loading → offline GoldenDict fallback → `fetchData` → success/empty/error (API error also falls back to GoldenDict).
- **Race guard**: a monotonic `searchGeneration` counter; a slow earlier response is dropped if a newer search has started.

### UI Components

#### `components/dictionary-panel.ts`
**Purpose**: Main dictionary panel UI with search, settings, and content display.

**Class: DictionaryPanel**
Constructed with `{ neverMinimize?: boolean }`. The popout passes `neverMinimize: true`: it never shows the minimized sliver, and its settings dropdown hides the rows that make no sense in a standalone window (**Minimize Panel**, **Panel Left / Right**, **Use GoldenDict**).

**Properties**:
- `content`: HTMLDivElement for dictionary content.
- `searchInput`: HTMLInputElement with Velthuis-to-Unicode transliteration.
- `history`: Session-based search history queue (max 50 entries).
- `historyIndex`: Current position in the history queue.

**Settings persistence**: `_loadInitialSettings()` restores all `settings*` keys from `storage.local` (incl. `settingsGoldenDict`) and applies per-domain niggahita defaults (DPR/SC/TBW/VRI/Tipitaka.lk off/on, s.4nt.org on).

**Key Methods**:
- `setContent(html, isNavigation)`: Sets content and manages the history queue.
- `uniCoder(textInput)`: Converts Velthuis sequences (aa -> ā, .t -> ṭ) in real-time.
- `_navigateHistory(direction)`: Moves back/forward in history instantaneously without new network calls.
- `_playAudio(headword, gender)`: Plays audio pronunciation, dynamically resolving the correct server URL.
- `_showInfo()`: Displays browser-specific instructions (Chrome vs Firefox) for pinning the extension, how to search, and a pop-out note (Chrome/Edge only).

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
    - `default` (Light), `dpd_dark` (Dark)
    - `dpr`, `suttacentral`(+`_dark`), `tbw_light`/`tbw_dark`, `vri`, `tipitakalk`, `paauksociety`, `s4nt_light`/`s4nt_dark`.
    - All selectable from the manual theme dropdown; also auto-detected by URL.
- **Logic**:
    - Automatic theme detection based on URL.
    - `dark-mode` class toggling for component-specific styles.
    - Robust color extraction for unknown sites, falling back to page styles.
    - **Live sync to popout**: when the host page's `auto` theme resolves to a new key (dark/light toggle), the content script broadcasts `popoutTheme` so the site's popout re-applies it.

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
