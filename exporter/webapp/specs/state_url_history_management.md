# State, URL, and History Management Plan

This document outlines a detailed plan to implement a unified system for managing state, URLs, and browser history for the webapp frontend.

## 1. High-Level Goal

Create a single, robust frontend solution to manage the application's state, including the active tab (DPD or BD), search queries, and results. This solution will also handle URL updates to reflect the application's state and provide a seamless browser history experience (back and forward buttons).

## 2. Core Principles

- **Single Source of Truth:** A single JavaScript object (`appState`) will hold the entire application state.
- **Centralized Logic:** A new file, `app.js`, will contain all the logic for state management, URL manipulation, and history control.
- **Separation of Concerns:** While `app.js` will handle the core logic, the individual JavaScript files for each tab (`home.js` and `bold_definitions.js`) will be responsible for their own UI-specific interactions.

## 3. Detailed Implementation Plan

### Step 1: Create `app.js` for Centralized Control

A new file will be created at `exporter/webapp/static/app.js`. This file will be the heart of the new state management system.

### Step 2: Define the `appState` Object

At the top of `app.js`, a single `appState` object will be defined to hold all the application's state:

```javascript
const appState = {
    activeTab: 'dpd', // 'dpd' or 'bd'
    dpd: {
        searchTerm: '',
        resultsHTML: ''
    },
    bd: {
        searchTerm1: '',
        searchTerm2: '',
        searchOption: 'regex',
        resultsHTML: ''
    },
    history: [], // An array of state snapshots
    historyIndex: -1 // Current position in the history stack
};
```

### Step 3: Implement the Core Functions in `app.js`

**`initializeApp()`**

- This function will be called when the page loads.
- It will parse the URL to determine the initial state (active tab and search terms).
- It will populate `appState` from the URL.
- It will call `performSearch(false)` if the URL contains search parameters to perform an initial search without adding a new history entry.
- It will call `addToHistory()` to add the initial state to the history stack.
- It will call `render()` to display the initial UI.

**`performSearch(addHistory = true)`**

- This function will be exposed to the global scope (`window.performSearch`).
- It will get the search terms from the input fields based on the active tab.
- It will make a `fetch` request to the appropriate backend endpoint (`/search_json` or `/bd_search`).
- It will update the `appState` with the new search results.
- If `addHistory` is `true`, it will call `addToHistory()` to add the new state to the history stack.
- It will call `render()` to update the UI with the new search results.

**`render(state)`**

- This function will be responsible for updating the entire UI based on the provided state.
- It will set the active tab.
- It will update the content of the search input fields.
- It will update the content of the results panes.

**`switchTab(tabName)`**

- This function will be called when a tab is clicked.
- It will update `appState.activeTab`.
- It will call `addToHistory()` to add the new state to the history stack.
- It will call `render()` to display the new active tab.

**`addToHistory(state)`**

- This function will add a new state to the `appState.history` array.
- It will handle the history stack (truncating forward history if necessary).
- It will call `updateURL()` to update the browser's URL.

**`updateURL(state)`**

- This function will update the browser's URL using `history.pushState()`.
- The URL will be structured as follows:
  - DPD: `/?tab=dpd&q=<search_term>`
  - BD: `/?tab=bd&q1=<term1>&q2=<term2>&option=<option>`

**`handlePopState(state)`**

- This function will be called when the user clicks the browser's back or forward buttons.
- It will update `appState` with the new state from the history.
- It will call `render()` to update the UI.

### Step 4: Modify `home.html`

- Add `<script src="static/app.js" defer></script>` before the other script tags.
- Remove the `onclick` attributes from the tab buttons and replace them with `data-tab` attributes.
- Combine the two `bd-search-form` forms into one.

### Step 5: Refactor `tabs.js`

- The `tabs.js` file will be emptied, as its functionality will be handled by `app.js`.

### Step 6: Refactor `home.js`

- Remove all history and URL management logic (`getQueryVariable`, `applyUrlQuery`, `handleFormSubmit`, `onpopstate`, `addToHistory`, `populateHistoryBody`, `toggleClearHistoryButton`).
- The `processSelection` and `handleTouchEnd` functions will be modified to call `window.performSearch()`.
- The `lastTap` and `doubleTapDelay` variables will be removed.

### Step 7: Refactor `bold_definitions.js`

- Remove all history and URL management logic.
- The event listeners for the search boxes and button will be modified to call `window.performSearch()`.
- The `processSelection` and `handleTouchEnd` functions will be removed.
- The `lastTap` and `doubleTapDelay` variables will be removed.
- A `DOMContentLoaded` event listener will be added to set up the event listeners for the search boxes, button, and double-click functionality.

## 4. Testing Plan

After each step of the implementation, the following functionality will be tested:

1.  **Tab Switching:** Clicking on the tabs should switch between the DPD and BD views.
2.  **DPD Search:** Searching in the DPD tab should display results.
3.  **BD Search:** Searching in the BD tab should display results.
4.  **URL Updates:** The URL should update correctly when switching tabs and performing searches.
5.  **History:** The browser's back and forward buttons should work correctly, restoring the previous state of the application (including the active tab, search terms, and results).
