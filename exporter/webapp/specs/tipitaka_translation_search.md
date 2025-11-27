# Tipitaka Translation Search Tab Specs

## Overview
Add a third tab to the webapp for searching Tipitaka translations, mimicking `gui2/translations_view.py`.

## 1. Backend Database
- Use `tools.tipitaka_db` module.
- Expose `search_all_cst_texts` and `search_book` via FastAPI routes.
- New route `/tt_search` in `main.py`.
    - Parameters:
        - `q`: Search term (regex).
        - `book`: Book name or "all".
        - `lang`: Language ("Pāḷi" or "English").
    - Returns: JSON with HTML content for results.

## 2. Frontend HTML
- Update `home.html` to include:
    - A new tab button "Tipiṭaka Translations".
    - A new tab content div `#tt-tab`.
    - Inside `#tt-tab`:
        - Header pane with title.
        - Search controls:
            - Language dropdown (Pāḷi, English).
            - Search term input.
            - Book dropdown (all, ...).
            - Search button.
            - Clear button.
            - Search in results input.
        - Results pane `#tt-results`.

## 3. Frontend JS
- Create `static/tipitaka_translations.js`.
- Implement `performTTSearch` function.
    - Fetch data from `/tt_search`.
    - Render results in `#tt-results`.
    - Handle "Search in results" filtering (client-side).
- Implement `clearTTSearch` function.
- Integrate with `app.js` for tab switching and history.
    - Update `appState` to include `tt` state.
    - Update `switchTab` to handle `tt` tab.
    - Update `updateURL` and `handlePopState`.

## 4. Navigation History
- Mimic `bd` tab behavior.
- Store state in `appState.tt`.
    - `searchTerm`: regex string.
    - `book`: selected book.
    - `language`: selected language.
    - `resultsHTML`: cached HTML results.
- Push state to history stack on search.
- Restore state on popstate (back/forward).
- Update URL parameters: `?tab=tt&q=...&book=...&lang=...`.

## Implementation Details

### `main.py`
```python
@app.get("/tt_search", response_class=JSONResponse)
def tt_search(request: Request, q: str, book: str, lang: str):
    # ... implementation ...
```

### `home.html`
```html
<button class="tab-link" data-tab="tt-tab">Tipiṭaka Translations</button>
...
<div id="tt-tab" class="tab-content">
    <!-- ... controls ... -->
    <div id="tt-results"></div>
</div>
```

### `app.js`
- Add `tt` to `appState`.
- Update `render` to handle `tt` tab.
- Update `updateURL` to include `tt` params.

### `tipitaka_translations.js`
- Event listeners for controls.
- Search logic.
- Result rendering logic (highlighting).
