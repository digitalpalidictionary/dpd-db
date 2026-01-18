# Webapp Behavior & Extension Migration Notes

## HTML Structure
The Webapp uses `dpd_headword.html` template.
- **Structure**: `h3` (Headword) -> `div.dpd.summary` -> `div.button-box` -> `div.content` sections (hidden by default).
- **Classes**: `dpd`, `summary`, `button-box`, `button`, `play`, `content`, `hidden`.
- **Icons**: Embedded SVG.

## Interaction Logic (`dpd.js`)
- **Event Delegation**: Listens on `document` for clicks.
- **Play Audio**:
  - Finds `.button.play`.
  - Calls `playAudio(headword, gender)`.
  - `playAudio` constructs URL: `/audio/HEADWORD?gender=...`.
  - **Issue for Extension**: Relative URL `/audio/` will fail. Must be updated to `https://www.dpdict.net/audio/`.
- **Toggling Content**:
  - Finds `.button[data-target]`.
  - Toggles `.hidden` on `document.getElementById(data-target)`.
  - Toggles `.active` on the button.
  - Supports "One Button Toggle" (auto-closing others) via `localStorage`.
  - **Issue for Extension**: `localStorage` belongs to the host page. Should use `chrome.storage` or internal state.
  - **Issue for Extension**: `getElementById` assumes unique IDs. DPD IDs are like `sutta_info_lemma_1`. Should be unique enough, but scoped lookup is safer.

## Migration Plan
1.  **CSS**:
    -   Already integrated `dpd.css` and `dpd-variables.css`.
    -   Need to ensure `custom-style.css` replacement (`chrome-extension.css`) handles the layout and variables.
    -   Need to ensure `dpd.css` styles don't leak (Phase 2 Shadow DOM).

2.  **JS Interactions**:
    -   Port `dpd.js` to `chrome-extension/scripts/dpd-interactions.js` (or part of `dictionary-panel.js`).
    -   Refactor `document.addEventListener` to `panelContainer.addEventListener` to scope events.
    -   Refactor `playAudio` to use absolute URL `https://www.dpdict.net/audio/`.
    -   Refactor `localStorage` usage to `chrome.storage.local` (async!) or simple memory state if persistence across page loads isn't critical for "One Button Toggle" (it is a preference, so `chrome.storage` is best).

3.  **API Integration**:
    -   `/search_json` endpoint returns `{summary_html, dpd_html}`.
    -   We simply inject `dpd_html` into the container.
    -   The injected HTML will contain the structure expected by the JS.
